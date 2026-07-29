import json
from typing import Dict, Any, List

class CoverageCalculator:
    def __init__(self):
        pass

    def invert_bit(self, char: str) -> str:
        if char == 'H':
            return 'L'
        elif char == 'L':
            return 'H'
        return char

    def reconstruct_actual_stream(self, expected: str, actual: str, status: str) -> str:
        """
        Reconstructs the actual scan-out response stream based on the logic:
        1. Use expected STIL value as default.
        2. If actual value is present, use it directly.
        3. If actual is missing/unavailable and compare fails, invert the expected care bits.
        """
        if actual and len(actual) == len(expected):
            return actual
            
        reconstructed = []
        for i, exp_char in enumerate(expected):
            if actual and i < len(actual):
                reconstructed.append(actual[i])
            else:
                if status == "FAIL":
                    reconstructed.append(self.invert_bit(exp_char))
                else:
                    reconstructed.append(exp_char)
        return "".join(reconstructed)

    def count_transitions(self, stream: str) -> int:
        """
        Counts transitions from H->L or L->H in the expanded stream.
        Transitions involving X do not count.
        """
        toggles = 0
        last_val = None
        for char in stream:
            if char == 'H':
                curr_val = 1
            elif char == 'L':
                curr_val = 0
            else:
                curr_val = None # X
                
            if last_val is not None and curr_val is not None:
                if last_val != curr_val:
                    toggles += 1
            last_val = curr_val
        return toggles

    def count_bit_stats(self, stream: str) -> Dict[str, int]:
        """
        Counts 0 (L), 1 (H), and X bits and directional transitions in scan response stream.
        """
        zeros_count = 0
        ones_count = 0
        xs_count = 0
        zero_to_one_transitions = 0
        one_to_zero_transitions = 0
        last_val = None

        for char in stream:
            if char == 'H':
                curr_val = 1
                ones_count += 1
            elif char == 'L':
                curr_val = 0
                zeros_count += 1
            elif char == 'X':
                curr_val = None
                xs_count += 1
            else:
                curr_val = None

            if last_val is not None and curr_val is not None:
                if last_val == 0 and curr_val == 1:
                    zero_to_one_transitions += 1
                elif last_val == 1 and curr_val == 0:
                    one_to_zero_transitions += 1
            last_val = curr_val

        return {
            "zeros_count": zeros_count,
            "ones_count": ones_count,
            "xs_count": xs_count,
            "zero_to_one_transitions": zero_to_one_transitions,
            "one_to_zero_transitions": one_to_zero_transitions
        }

    def calculate_coverage(self, ate_data: Dict[str, Dict[str, Dict[str, str]]]) -> Dict[str, Any]:
        """
        Calculates toggle coverage and density metrics across three levels:
        File Rollup Level, Pattern Level, and Scan Chain Level.
        """
        pattern_reports = []
        scan_chain_reports = []
        
        # Track unique cells toggled across the entire file
        # Key: (scan_chain_id, cell_index)
        toggled_cells_global = set()
        total_toggle_count = 0
        
        patterns_analyzed = len(ate_data)
        unique_chains = set()
        # Geometry-driven denominator: compute physical cell counts from
        # actual expected stream lengths per scan chain (not a fixed 234).
        chain_lengths: Dict[str, int] = {}
        
        for pat_id, chains in ate_data.items():
            pat_toggles = 0
            pat_toggled_cells = set()
            pat_total_cells = 0
            pat_zeros_count = 0
            pat_ones_count = 0
            pat_xs_count = 0
            pat_zero_to_one = 0
            pat_one_to_zero = 0
            
            for ch_id, ch_data in chains.items():
                unique_chains.add(ch_id)
                expected = ch_data["expected"]
                actual = ch_data["actual"]
                status = ch_data["status"]

                expected_len = len(expected or "")
                if expected_len > 0:
                    chain_lengths[ch_id] = max(chain_lengths.get(ch_id, 0), expected_len)
                
                reconstructed = self.reconstruct_actual_stream(expected, actual, status)
                ch_len = len(reconstructed)
                pat_total_cells += ch_len
                
                ch_toggles = self.count_transitions(reconstructed)
                bit_stats = self.count_bit_stats(reconstructed)
                pat_toggles += ch_toggles
                pat_zeros_count += bit_stats["zeros_count"]
                pat_ones_count += bit_stats["ones_count"]
                pat_xs_count += bit_stats["xs_count"]
                pat_zero_to_one += bit_stats["zero_to_one_transitions"]
                pat_one_to_zero += bit_stats["one_to_zero_transitions"]
                total_toggle_count += ch_toggles
                
                # Identify toggled cells (transition index j toggles cell j)
                ch_toggled_cells_count = 0
                last_val = None
                for j, char in enumerate(reconstructed):
                    if char == 'H':
                        curr_val = 1
                    elif char == 'L':
                        curr_val = 0
                    else:
                        curr_val = None
                        
                    if last_val is not None and curr_val is not None:
                        if last_val != curr_val:
                            toggled_cells_global.add((ch_id, j - 1))
                            pat_toggled_cells.add((ch_id, j - 1))
                            ch_toggled_cells_count += 1
                    last_val = curr_val
                
                # Chain Level Metrics
                ch_cov_pct = (ch_toggled_cells_count / ch_len) * 100.0 if ch_len > 0 else 0.0
                ch_dens_pct = (ch_toggles / (ch_len - 1)) * 100.0 if ch_len > 1 else 0.0
                
                scan_chain_reports.append({
                    "pattern_id": pat_id,
                    "scan_chain_id": ch_id,
                    "toggle_count": ch_toggles,
                    "toggle_coverage_pct": round(ch_cov_pct, 4),
                    "toggle_density_pct": round(ch_dens_pct, 4),
                    "zeros_count": bit_stats["zeros_count"],
                    "ones_count": bit_stats["ones_count"],
                    "xs_count": bit_stats["xs_count"],
                    "zero_to_one_transitions": bit_stats["zero_to_one_transitions"],
                    "one_to_zero_transitions": bit_stats["one_to_zero_transitions"]
                })
                
            # Pattern Level Metrics
            pat_cov_pct = (len(pat_toggled_cells) / pat_total_cells) * 100.0 if pat_total_cells > 0 else 0.0
            pat_max_trans = pat_total_cells - len(chains)
            pat_dens_pct = (pat_toggles / pat_max_trans) * 100.0 if pat_max_trans > 0 else 0.0
            
            pattern_reports.append({
                "pattern_id": pat_id,
                "toggle_count": pat_toggles,
                "toggle_coverage_pct": round(pat_cov_pct, 4),
                "toggle_density_pct": round(pat_dens_pct, 4),
                "zeros_count": pat_zeros_count,
                "ones_count": pat_ones_count,
                "xs_count": pat_xs_count,
                "zero_to_one_transitions": pat_zero_to_one,
                "one_to_zero_transitions": pat_one_to_zero
            })
            
        scan_chains_analyzed = len(chain_lengths) if chain_lengths else len(unique_chains)
        # Sum actual physical cells across distinct scan chains.
        total_physical_cells = sum(chain_lengths.values()) if chain_lengths else (scan_chains_analyzed * 234)
        # If no geometry was inferred, fall back to the prior constant to avoid divide-by-zero.
        
        # File Rollup Level Metrics
        file_cov_pct = (len(toggled_cells_global) / total_physical_cells) * 100.0 if total_physical_cells > 0 else 0.0
        file_max_trans = patterns_analyzed * (total_physical_cells - scan_chains_analyzed)
        file_dens_pct = (total_toggle_count / file_max_trans) * 100.0 if file_max_trans > 0 else 0.0
        
        # Sort patterns by toggle_density_pct (highest to lowest) to establish ranking
        pattern_reports.sort(key=lambda x: x["toggle_density_pct"], reverse=True)
        
        return {
            "file_rollup": {
                "file_name": "",  # Will be populated by server
                "total_toggle_count": total_toggle_count,
                "toggle_coverage_pct": round(file_cov_pct, 4),
                "toggle_density_pct": round(file_dens_pct, 4),
                "patterns_analyzed": patterns_analyzed,
                "scan_chains_analyzed": scan_chains_analyzed
            },
            "pattern_level": pattern_reports,
            "scan_chain_level": scan_chain_reports
        }
