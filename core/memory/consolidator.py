"""
Memory consolidator — moves episodic PALACE entries into the semantic graph.

Converts lived experiences (PALACE text files) into structured knowledge
(SQLite concept graph). Safe to call multiple times — upserts, not inserts.
Runs silently at voice session startup via run_at_startup().
"""

from core.palace.reader import read_palace
from core.palace.classifier import AREAS_KEYWORDS
from core.memory.semantic_graph import add_concept, add_relation
from core.memory.emotional_tagger import tag as emotion_tag

_AREAS = list(AREAS_KEYWORDS.keys())


def _concept_tags_from_entry(entry: dict) -> list[str]:
    """Extract non-trivial concept strings from an entry's tags field."""
    raw = entry.get("tags", "")
    if isinstance(raw, str):
        tags = [t.strip().lower() for t in raw.split(",")]
    elif isinstance(raw, list):
        tags = [str(t).strip().lower() for t in raw]
    else:
        tags = []
    return [t for t in tags if len(t) > 2]


def consolidate(verbose: bool = False) -> int:
    """
    Read all PALACE areas and upsert concept nodes + co-occurrence relations
    into the semantic graph. Returns total nodes processed.

    Domain of each node = the PALACE area (CREACION, PSIQUE, etc.),
    not the first tag — this keeps the graph correctly organised by area.
    """
    total = 0
    for area in _AREAS:
        entries = read_palace(area)
        for entry in entries:
            content_str = entry.get("content", "")
            concepts = _concept_tags_from_entry(entry)
            if not concepts:
                continue

            emotion = emotion_tag(content_str)
            domain  = area.lower()   # use the PALACE area as the semantic domain

            for concept in concepts:
                add_concept(
                    title=concept,
                    domain=domain,
                    content={"excerpt": content_str[:400], "area": area},
                    emotion=emotion.label,
                    tags=concepts,
                )
                total += 1

            # Link co-occurring concepts within the same entry
            for i, c1 in enumerate(concepts):
                for c2 in concepts[i + 1:]:
                    add_relation(c1, c2, domain, relation="co_ocurre_con", weight=0.5)

    if verbose:
        print(f"  [memory] Consolidacion: {total} nodos procesados.")
    return total


def run_at_startup() -> None:
    """Silent consolidation — never raises, never blocks startup."""
    try:
        consolidate(verbose=False)
    except Exception:
        pass
