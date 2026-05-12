"""CEL Memory Bridge: Unified memory + palace."""

from typing import Dict, Any, List
from memory.service import retrieve_context
from core.palace.reader import read_palace

def get_unified_context(domain: str) -> Dict[str, Any]:
    """Merge memory + palace for CEL."""
    memory = retrieve_context(domain)
    palace = read_palace(domain)
    return {
        "memory": memory[-10:],  # Recent
        "palace": palace[:15],   # Top relevant
        "total_hits": len(memory) + len(palace)
    }

