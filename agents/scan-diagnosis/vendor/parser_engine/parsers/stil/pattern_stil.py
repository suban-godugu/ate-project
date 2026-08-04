import re
import os
from typing import Dict, List, Set, Tuple, Any, Optional

class STILValidationError(Exception):
    """Custom exception raised during STIL validation errors."""
    def __init__(self, message: str, line_number: int):
        super().__init__(f"Line {line_number}: {message}")
        self.message = message
        self.line_number = line_number

class STILParser:
    """
    An industry-grade, memory-efficient STIL (Standard Test Interface Language) parser
    designed to perform 100% structural validation on huge STIL pattern files.
    """
    def __init__(self):
        # Symbol Table
        self.signals: Dict[str, str] = {}  # name -> direction (In, Out, InOut)
        self.signal_groups: Dict[str, List[str]] = {}  # group_name -> list of signals
        self.scan_chains: Dict[str, Dict[str, Any]] = {}  # chain_name -> details dict
        self.timing_tables: Set[str] = set()  # set of Timing WaveformTable names
        self.referenced_timing_sets: Set[str] = set()
        self.pending_waveform_refs: List[Tuple[int, str]] = []
        self.warnings: List[Tuple[int, str]] = []
        self.waveform_table_mode: str = "auto"
        self.external_timing_references: List[str] = []
        self.timing_validation_mode: str = "strict"
        
        # Validation state
        self.errors: List[Tuple[int, str]] = []  # list of (line_number, error_message)
        self.brace_stack: List[Tuple[str, int]] = []  # stack of (block_name, line_number)
        
        # Parsed Patterns metadata
        self.pattern_bursts: List[Dict[str, Any]] = []
        self.patterns_metadata: List[Dict[str, Any]] = []
        self.patterns_count = 0
        
        # Common Vector Model (CVM)
        self.cycles: List[Dict[str, Any]] = []
        self.current_cycle_info: Dict[str, Any] = {"cycle_number": None, "vector_type": None}
        self.current_cycle: Optional[Dict[str, Any]] = None
        
        # General file info
        self.line_count = 0
        self.file_size_bytes = 0
        
    def add_error(self, message: str, line_num: int):
        self.errors.append((line_num, message))

    def add_warning(self, message: str, line_num: int):
        self.warnings.append((line_num, message))

    @staticmethod
    def normalize_timing_table_name(raw_name: str) -> str:
        return str(raw_name or "").strip().strip('"\'').strip(";")

    def resolve_block_open_context(self, current_tokens: List[str]) -> str:
        """Resolve brace block label; prefer last named block keyword in buffer."""
        if not current_tokens:
            return "unknown"
        named_blocks = ("WaveformTable", "ScanChain", "Macro", "Pattern")
        for idx in range(len(current_tokens) - 1, -1, -1):
            tok = current_tokens[idx]
            if tok in named_blocks and idx + 1 < len(current_tokens):
                name = self.normalize_timing_table_name(current_tokens[idx + 1])
                return f"{tok}:{name}"
        first_tok = current_tokens[0]
        if first_tok in (
            "Signals",
            "SignalGroups",
            "Timing",
            "ScanStructures",
            "MacroDefs",
            "PatternBurst",
            "PatternExec",
            "Loop",
            "Shift",
            "V",
        ):
            return first_tok
        if len(current_tokens) > 1 and first_tok in named_blocks:
            name = self.normalize_timing_table_name(current_tokens[1])
            return f"{first_tok}:{name}"
        return "unknown"

    def register_waveform_table(self, raw_name: str) -> None:
        name = self.normalize_timing_table_name(raw_name)
        if name:
            self.timing_tables.add(name)

    def finalize_waveform_references(self) -> None:
        has_embedded_timing = bool(self.timing_tables)
        mode = (self.waveform_table_mode or "auto").lower()
        external_refs = sorted(
            name for name in self.referenced_timing_sets if name not in self.timing_tables
        )
        for line_num, table_name in self.pending_waveform_refs:
            if table_name in self.timing_tables:
                continue
            message = f"Unresolved WaveformTable reference: '{table_name}'"
            if mode == "warn" or (mode == "auto" and not has_embedded_timing):
                self.add_warning(
                    f"{message} (timing set referenced externally; not defined in STIL file)",
                    line_num,
                )
            else:
                self.add_error(message, line_num)
        self.external_timing_references = external_refs
        if has_embedded_timing:
            self.timing_validation_mode = "embedded"
        elif external_refs:
            self.timing_validation_mode = "external"
        else:
            self.timing_validation_mode = "strict" if mode == "strict" else "external"

    def map_vector_to_cycle_type(self, vec_type: Optional[str]) -> str:
        if not vec_type:
            return "CAPTURE"
        if vec_type == "LOAD_UNLOAD":
            return "SHIFT"
        elif vec_type == "TEST_SETUP":
            return "TEST_SETUP"
        else:
            return "CAPTURE"

    def expand_vector_values(self, tokens: List[str], line_num: int) -> str:
        """
        Expands run-length encoded vector assignments.
        e.g., ['010', '\\r10', '0', 'X'] -> '010000000000X'
        """
        expanded = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok.startswith('\\r'):
                # It is a repeat clause
                try:
                    count_str = tok[2:]
                    count = int(count_str)
                except ValueError:
                    self.add_error(f"Invalid repeat statement format: '{tok}'", line_num)
                    i += 1
                    continue
                
                # The next token is the value to repeat
                if i + 1 < len(tokens):
                    val = tokens[i + 1]
                    val = val.strip('"\'')
                    expanded.append(val * count)
                    i += 2
                else:
                    self.add_error(f"Repeat statement '{tok}' has no value to repeat", line_num)
                    i += 1
            else:
                expanded.append(tok.strip('"\''))
                i += 1
        return "".join(expanded)

    def parse(
        self,
        file_path: str,
        max_size_gb: float = 10.0,
        *,
        waveform_table_mode: str = "auto",
    ) -> Dict[str, Any]:
        """
        Parses and validates a STIL file. Returns the Common Pattern Model (CPM) report.
        """
        self.waveform_table_mode = waveform_table_mode or "auto"
        self.external_timing_references = []
        self.timing_validation_mode = "strict"
        self.file_size_bytes = os.path.getsize(file_path)
        max_bytes = max_size_gb * 1024 * 1024 * 1024
        if self.file_size_bytes > max_bytes:
            err_msg = f"File size ({self.file_size_bytes / (1024**3):.2f} GB) exceeds configured limit ({max_size_gb:.2f} GB)"
            self.errors = [(0, err_msg)]
            return self.build_cpm_report(file_path, status="FAIL")

        token_re = re.compile(
            r'({|}|;|==?|\+|:|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'|[a-zA-Z_0-9\.\-\\\/\[\]#\r]+|\S)'
        )

        in_multiline_comment = False
        self.brace_stack = []
        self.errors = []
        self.line_count = 0
        
        self.signals = {}
        self.signal_groups = {}
        self.scan_chains = {}
        self.timing_tables = set()
        self.referenced_timing_sets = set()
        self.pending_waveform_refs = []
        self.warnings = []
        self.pattern_bursts = []
        self.patterns_metadata = []
        self.patterns_count = 0
        self.cycles = []
        self.current_cycle_info = {"cycle_number": None, "vector_type": None}
        self.current_cycle = None
        max_pattern_idx = -1
        
        tokens_stack = []
        current_tokens = []
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    self.line_count += 1
                    
                    # Scan annotations/comments for pattern numbers
                    pattern_end_match = re.search(r'pattern_end\s*=\s*(\d+)', line)
                    if pattern_end_match:
                        max_pattern_idx = max(max_pattern_idx, int(pattern_end_match.group(1)))
                    else:
                        pattern_num_match = re.search(r'pattern_numer:(\d+)', line)
                        if pattern_num_match:
                            max_pattern_idx = max(max_pattern_idx, int(pattern_num_match.group(1)))
                        else:
                            pattern_idx_match = re.search(r'Pattern:(\d+)', line)
                            if pattern_idx_match:
                                max_pattern_idx = max(max_pattern_idx, int(pattern_idx_match.group(1)))
                                
                    # Scan annotations/comments for cycle numbers
                    cycle_match = re.search(r'cycle_number:(\d+)\s+vector_type:(\w+)', line)
                    if cycle_match:
                        self.current_cycle_info["cycle_number"] = int(cycle_match.group(1))
                        self.current_cycle_info["vector_type"] = cycle_match.group(2)
                                
                    line_strip = line.strip()
                    
                    if in_multiline_comment:
                        if "*/" in line_strip:
                            parts = line_strip.split("*/", 1)
                            line_strip = parts[1].strip()
                            in_multiline_comment = False
                        else:
                            continue
                    
                    if "//" in line_strip:
                        line_strip = line_strip.split("//", 1)[0].strip()
                        
                    if "/*" in line_strip:
                        if "*/" in line_strip:
                            line_strip = re.sub(r'/\*.*?\*/', '', line_strip).strip()
                        else:
                            parts = line_strip.split("/*", 1)
                            line_strip = parts[0].strip()
                            in_multiline_comment = True
                    
                    if not line_strip:
                        continue
                    
                    tokens = token_re.findall(line_strip)
                    for tok in tokens:
                        if tok == '{':
                            block_context = self.resolve_block_open_context(current_tokens)
                            if block_context.startswith("WaveformTable:"):
                                self.register_waveform_table(block_context.split(":", 1)[1])

                            self.brace_stack.append((block_context, self.line_count))
                            if block_context == "V":
                                is_inside_pattern = any(item[0].startswith("Pattern:") for item in self.brace_stack)
                                if is_inside_pattern:
                                    self.current_cycle = {
                                        "cycle_number": self.current_cycle_info["cycle_number"] if self.current_cycle_info["cycle_number"] is not None else len(self.cycles),
                                        "vector_type": self.current_cycle_info["vector_type"] or "UNKNOWN",
                                        "cycle_type": self.map_vector_to_cycle_type(self.current_cycle_info["vector_type"]),
                                        "assignments": {}
                                    }
                                else:
                                    self.current_cycle = None
                            tokens_stack.append(current_tokens)
                            current_tokens = []
                            
                        elif tok == '}':
                            if not self.brace_stack:
                                self.add_error("Unbalanced closing brace '}' without opening '{'", self.line_count)
                                continue
                            
                            popped_block, opened_line = self.brace_stack.pop()
                            if popped_block == "V":
                                if self.current_cycle is not None:
                                    self.cycles.append(self.current_cycle)
                                    self.current_cycle = None
                                    self.current_cycle_info = {"cycle_number": None, "vector_type": None}
                                    
                            if not tokens_stack:
                                self.add_error("Internal parsing error: tokens stack empty on closing brace", self.line_count)
                                current_tokens = []
                                continue
                                
                            outer_tokens = tokens_stack.pop()
                            header_tokens, stripped_outer = self.extract_header_and_strip(outer_tokens)
                            
                            # Full block tokens: header + '{' + body + '}'
                            full_block_tokens = header_tokens + ["{"] + current_tokens + ["}"]
                            self.process_block_close(full_block_tokens, self.line_count)
                            
                            current_tokens = stripped_outer
                            
                        elif tok == ';':
                            current_tokens.append(tok)
                            statement, stripped = self.extract_header_and_strip(current_tokens)
                            self.process_statement(statement, self.line_count)
                            current_tokens = stripped
                            
                        else:
                            current_tokens.append(tok)
                            
        except Exception as e:
            self.add_error(f"File reading error: {str(e)}", self.line_count)

        if in_multiline_comment:
            self.add_error("File truncated: unclosed multiline comment '/*'", self.line_count)
        
        if self.brace_stack:
            unclosed_block, open_line = self.brace_stack[-1]
            self.add_error(f"File truncated / unbalanced braces: unclosed '{unclosed_block}' block opened at line {open_line}", self.line_count)

        self.finalize_waveform_references()

        self.patterns_count = max_pattern_idx + 1 if max_pattern_idx != -1 else len(self.patterns_metadata)
        status = "PASS" if not self.errors else "FAIL"
        return self.build_cpm_report(file_path, status)

    def extract_header_and_strip(self, tokens: List[str]) -> Tuple[List[str], List[str]]:
        if not tokens:
            return [], []
        boundary_idx = -1
        for idx in range(len(tokens) - 2, -1, -1):
            if tokens[idx] in ('{', '}', ';'):
                boundary_idx = idx
                break
        header = tokens[boundary_idx + 1:]
        stripped = tokens[:boundary_idx + 1]
        return header, stripped

    def process_statement(self, tokens: List[str], line_num: int):
        if not tokens:
            return
            
        first_token = tokens[0]
        active_block = self.brace_stack[-1][0] if self.brace_stack else ""
        
        # Split block type and parameter (e.g. ScanChain:chain_name)
        if ":" in active_block:
            block_type, block_name = active_block.split(":", 1)
        else:
            block_type, block_name = active_block, ""
            
        if block_type == "Signals":
            i = 0
            while i < len(tokens):
                if tokens[i] == ';':
                    i += 1
                    continue
                if i + 1 < len(tokens):
                    sig_name = tokens[i].strip('"\'')
                    direction = tokens[i+1]
                    if direction in ("In", "Out", "InOut"):
                        self.signals[sig_name] = direction
                    i += 2
                else:
                    i += 1
                    
        elif block_type == "SignalGroups":
            if "=" in tokens:
                eq_idx = tokens.index("=")
                group_name = tokens[0].strip('"\'')
                definition_tokens = tokens[eq_idx+1:]
                def_str = " ".join(definition_tokens)
                
                referenced_sigs = re.findall(r'"([^"]+)"', def_str)
                for sig in referenced_sigs:
                    if sig not in self.signals:
                        self.add_error(f"Unresolvable signal reference: '{sig}' inside SignalGroup '{group_name}'", line_num)
                
                self.signal_groups[group_name] = referenced_sigs

        elif block_type == "ScanChain":
            # Populate scan chain details dynamically
            self.scan_chains.setdefault(block_name, {})
            if len(tokens) >= 2:
                key = tokens[0]
                val = tokens[1].strip('"\' ;')
                self.scan_chains[block_name][key] = val
                
                if key == "ScanIn":
                    if val not in self.signals:
                        self.add_error(f"Unresolvable ScanIn signal reference: '{val}'", line_num)
                elif key == "ScanOut":
                    if val not in self.signals:
                        self.add_error(f"Unresolvable ScanOut signal reference: '{val}'", line_num)
                elif key == "ScanMasterClock":
                    if val not in self.signals:
                        self.add_error(f"Unresolvable ScanMasterClock signal reference: '{val}'", line_num)

        elif block_type == "V":
            self.validate_vector_assignment(tokens, line_num)

        elif block_type in ("Pattern", "Loop"):
            if first_token == "W" and len(tokens) >= 2:
                table_name = self.normalize_timing_table_name(tokens[1])
                if table_name:
                    self.pending_waveform_refs.append((line_num, table_name))
                    self.referenced_timing_sets.add(table_name)

    def process_block_close(self, tokens: List[str], line_num: int):
        if not tokens:
            return
            
        first_token = tokens[0]
        
        if first_token == "V":
            content_tokens = tokens[2:-1]
            stmt: List[str] = []
            for tok in content_tokens:
                if tok == ';':
                    self.validate_vector_assignment(stmt, line_num)
                    stmt = []
                else:
                    stmt.append(tok)
            if stmt:
                self.validate_vector_assignment(stmt, line_num)

        elif first_token == "WaveformTable" and len(tokens) >= 2:
            self.register_waveform_table(tokens[1])

        elif first_token == "ScanChain" and len(tokens) >= 2:
            # Already populated dynamically during statement processing
            pass

        elif first_token == "PatternBurst" and len(tokens) >= 2:
            burst_name = tokens[1]
            self.pattern_bursts.append({"name": burst_name})

        elif first_token == "Pattern" and len(tokens) >= 2:
            pat_name = tokens[1]
            self.patterns_metadata.append({"name": pat_name})

    def validate_vector_assignment(self, tokens: List[str], line_num: int):
        is_inside_pattern = any(item[0].startswith("Pattern:") for item in self.brace_stack)
        if not is_inside_pattern:
            return
            
        if not tokens or "=" not in tokens:
            return
            
        eq_idx = tokens.index("=")
        lhs = tokens[0].strip('"\'')
        rhs_tokens = tokens[eq_idx+1:]
        if rhs_tokens and rhs_tokens[-1] == ';':
            rhs_tokens = rhs_tokens[:-1]
        
        is_signal = lhs in self.signals
        is_group = lhs in self.signal_groups
        
        if not is_signal and not is_group:
            self.add_error(f"Unresolved signal or group reference: '{lhs}' in vector assignment", line_num)
            return

        expanded_val = self.expand_vector_values(rhs_tokens, line_num)
        
        expected_len = 1
        if is_group:
            expected_len = len(self.signal_groups[lhs])
            
        if '#' not in expanded_val:
            if len(expanded_val) != expected_len:
                self.add_error(
                    f"Vector assignment size mismatch for '{lhs}': assigned length is {len(expanded_val)} but expected {expected_len}",
                    line_num
                )
                
        # Save to CVM cycle object
        if self.current_cycle is not None:
            self.current_cycle["assignments"][lhs] = expanded_val

    def build_cpm_report(self, file_path: str, status: str) -> Dict[str, Any]:
        # Compute pattern features & metadata (PA-FR-003)
        lengths = []
        scan_in_pins = set()
        scan_out_pins = set()
        for chain_data in self.scan_chains.values():
            length_str = chain_data.get("ScanLength", "0")
            try:
                lengths.append(int(length_str))
            except ValueError:
                pass
            if "ScanIn" in chain_data:
                scan_in_pins.add(chain_data["ScanIn"])
            if "ScanOut" in chain_data:
                scan_out_pins.add(chain_data["ScanOut"])
        
        max_chain_length = max(lengths) if lengths else 0
        total_flip_flops = sum(lengths)
        external_channels = len(scan_in_pins)
        compression_ratio = round(len(self.scan_chains) / max(1, external_channels), 2) if len(self.scan_chains) > 0 else 0.0

        metadata = {
            "pattern_count": self.patterns_count,
            "chain_count": len(self.scan_chains),
            "max_chain_length": max_chain_length,
            "total_flip_flops": total_flip_flops,
            "external_channels": external_channels,
            "compression_ratio": compression_ratio,
            "vector_count": len(self.cycles),
            "scan_in_pins": list(scan_in_pins),
            "scan_out_pins": list(scan_out_pins)
        }

        return {
            "file_name": os.path.basename(file_path),
            "file_path": os.path.abspath(file_path),
            "file_size_bytes": self.file_size_bytes,
            "line_count": self.line_count,
            "status": status,
            "signals_count": len(self.signals),
            "groups_count": len(self.signal_groups),
            "scan_chains_count": len(self.scan_chains),
            "patterns_count": self.patterns_count,
            "cycles_count": len(self.cycles),
            "cycles": self.cycles,
            "signals": self.signals,
            "signal_groups": self.signal_groups,
            "scan_chains": self.scan_chains,
            "timing_tables": sorted(self.timing_tables),
            "referenced_timing_sets": sorted(self.referenced_timing_sets),
            "external_timing_references": sorted(self.external_timing_references),
            "timing_validation_mode": self.timing_validation_mode,
            "errors": [{"line": err[0], "message": err[1]} for err in self.errors],
            "warnings": [{"line": warn[0], "message": warn[1]} for warn in self.warnings],
            "warning_count": len(self.warnings),
            "structural_validation_pass_ratio": 0.0 if self.errors else 100.0,
            "metadata": metadata
        }

if __name__ == "__main__":
    # Test execution
    parser = STILParser()
    report = parser.parse("Production_SCAN_stuck_at_1000pat.stil")
    print(f"File status: {report['status']}")
    print(f"Errors count: {len(report['errors'])}")
    for err in report['errors']:
        print(f"  Line {err['line']}: {err['message']}")
    print(f"Signals count: {report['signals_count']}")
    print(f"Groups count: {report['groups_count']}")
    print(f"Scan chains count: {report['scan_chains_count']}")
