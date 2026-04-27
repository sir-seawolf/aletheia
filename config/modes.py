"""
Execution modes for Aletheia Kernel v1.0.
Loaded by runtime/config to adapt behavior.
"""

from typing import Dict, Any

MODES: Dict[str, Dict[str, Any]] = {
    "DEV": {
        "verbose": True,
        "memory_verbose": True,
        "llm_randomness": True,  # temperature=0.7
        "event_bus": True,
        "debug": True,
    },
    "TEST": {
        "verbose": False,
        "memory_verbose": False,
        "llm_randomness": False,  # temperature=0.0, deterministic
        "event_bus": False,
        "debug": False,
        "deterministic": True,
    },
    "PROD": {
        "verbose": False,
        "memory_verbose": False,
        "llm_randomness": False,
        "event_bus": False,
        "debug": False,
        "safe_mode": True,
    }
}

def get_mode(mode_name: str = "DEV") -> Dict[str, Any]:
    return MODES.get(mode_name.upper(), MODES["DEV"])

