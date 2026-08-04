import re
import os
from typing import Dict, Any, Tuple

class ATEParser:
    def __init__(self):
        # Matches lines like: P1 | CH1 EXPECTED_OUTPUT:wave or P000004 | CH02 EXPECTED_OUTPUT:wave
        self.exp_pattern = re.compile(r'^(P\d+)\s*\|\s*(CH\d+)\s+EXPECTED_OUTPUT:(.*)$', re.IGNORECASE)
        self.act_pattern = re.compile(r'^\s*ACTUAL_OUTPUT:(.*)$', re.IGNORECASE)
        self.status_pattern = re.compile(r'^\s*STATUS:(.*)$', re.IGNORECASE)

    def expand_waveform(self, s: str) -> str:
        s = s.strip()
        # Handle X@{n} and @{n}X formats
        s = re.sub(r'X@\{(\d+)\}', lambda m: 'X' * int(m.group(1)), s)
        s = re.sub(r'@\{(\d+)\}X', lambda m: 'X' * int(m.group(1)), s)
        # Handle cases where other characters are compressed
        s = re.sub(r'([HLX])@\{(\d+)\}', lambda m: m.group(1) * int(m.group(2)), s)
        s = re.sub(r'@\{(\d+)\}([HLX])', lambda m: m.group(2) * int(m.group(1)), s)
        return s

    def parse(self, file_path: str) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Parses ATE log file.
        Returns:
            Dict: {
                "pattern_id": {
                    "channel_id": {
                        "expected": "expanded_expected_string",
                        "actual": "expanded_actual_string",
                        "status": "PASS/FAIL"
                    }
                }
            }
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ATE log file not found at: {file_path}")

        data: Dict[str, Dict[str, Dict[str, str]]] = {}
        
        current_pat = None
        current_ch = None
        current_expected = None
        current_actual = None
        
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                # Check for EXPECTED_OUTPUT
                m_exp = self.exp_pattern.match(line_stripped)
                if m_exp:
                    current_pat = m_exp.group(1).upper()
                    current_ch = m_exp.group(2).upper()
                    current_expected = self.expand_waveform(m_exp.group(3))
                    current_actual = None
                    continue
                
                # Check for ACTUAL_OUTPUT
                m_act = self.act_pattern.match(line_stripped)
                if m_act and current_pat and current_ch:
                    current_actual = self.expand_waveform(m_act.group(1))
                    continue
                
                # Check for STATUS
                m_status = self.status_pattern.match(line_stripped)
                if m_status and current_pat and current_ch:
                    status = m_status.group(1).strip().upper()
                    # Normalize status to PASS or FAIL
                    if status in ("P", "PASS"):
                        status_norm = "PASS"
                    else:
                        status_norm = "FAIL"
                        
                    if current_pat not in data:
                        data[current_pat] = {}
                        
                    data[current_pat][current_ch] = {
                        "expected": current_expected or "",
                        "actual": current_actual or "",
                        "status": status_norm
                    }
                    
                    # Reset channel tracking
                    current_ch = None
                    current_expected = None
                    current_actual = None
                    
        return data
