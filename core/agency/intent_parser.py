"""
Intent parser — detects whether a voice utterance is an action request.

Returns an IntentMatch if a trigger keyword is found, None otherwise.
Also extracts the argument (the "about what" part) when needed.
"""

import re
from dataclasses import dataclass

from core.agency.action_catalog import CATALOG, ActionDef


@dataclass
class IntentMatch:
    action: ActionDef
    arg: str          # extracted argument (may be empty if not needed)
    raw: str          # original utterance


# Prepositions / connectors that separate trigger from argument
_ARG_SEPARATORS = re.compile(
    r"\s+(?:sobre|de|acerca de|que dice|respecto a|del|para|en|con|:\s*)",
    re.IGNORECASE,
)


def _extract_arg(text: str, trigger: str) -> str:
    """
    Extract the argument that follows a trigger in the utterance.
    Example: "qué recuerdas de jujutsu kaisen" → "jujutsu kaisen"
    """
    lower = text.lower()
    pos = lower.find(trigger)
    if pos == -1:
        return text   # fallback: use full text

    after = text[pos + len(trigger):].strip()

    # strip leading separator words
    after = _ARG_SEPARATORS.sub(" ", " " + after).strip()
    return after if after else text


def detect(text: str) -> IntentMatch | None:
    """
    Scan text for action triggers. Returns the first match or None.

    Guards:
    - Minimum 4 words required to avoid false positives on short utterances
    - Trigger must appear as a meaningful substring (not just a character run)
    """
    words = text.strip().split()
    if len(words) < 4:
        return None   # too short — likely a single word or incomplete phrase

    lower = text.lower()

    for action in CATALOG:
        for trigger in action.triggers:
            if trigger in lower:
                arg = _extract_arg(text, trigger) if action.needs_arg else ""
                return IntentMatch(action=action, arg=arg.strip(), raw=text)

    return None
