from typing import List, Dict, Any, Optional
from pathlib import Path
import re

def parse_entry(block: str) -> Dict[str, Any]:
    '''
    Parse single ---ENTRY--- block to dict.
    '''
    entry = {}
    lines = block.strip().split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            entry[key.strip()] = value.strip()
    return entry

def read_palace(area: Optional[str] = None) -> List[Dict[str, Any]]:
    '''
    Read palace entries. If area, one file; else all areas unified.
    '''
    entries = []
    areas_list = ["CREACION", "PROFESION", "PSIQUE", "ROL", "TECNOLOGIA", "VIDA"]
    target_areas = [area] if area else areas_list
    for a in target_areas:
        path = Path(f"PALACE/{a}/memory.txt")
        if path.exists():
            content = path.read_text(encoding='utf-8')
            for block in re.finditer(r'---ENTRY---(.*?)(?=---ENTRY---|---END---|$)', content, re.DOTALL):
                block_text = block.group(1).strip()
                if 'timestamp:' in block_text:
                    entries.append(parse_entry(block_text))
    return entries

