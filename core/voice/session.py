"""
Voice session — the main conversational loop.

Flow per turn:
  [ENTER] -> record -> STT -> intent_parser?
                               ├── action → confirm → execute  (Sprint 7)
                               └── question → process_request  (pipeline)

Sprint integrations:
  Sprint 4 — working_memory, emotional_tagger, consolidator
  Sprint 5 — proactive_engine: startup briefing + pattern detection
  Sprint 6 — emotional_state: persistent state updated after each turn
  Sprint 7 — agency: intent detection + safe action execution
"""

import re

from core.voice.listener import record_until_silence, transcribe, preload as preload_stt
from core.voice.speaker import speak, preload as preload_tts
from core.orchestrator import process_request
from core.llm import router as llm_router
from core.memory.working_memory import session as wm
from core.memory.emotional_tagger import tag as emotion_tag
from core.memory.consolidator import run_at_startup
from core.cognition.proactive_engine import briefing, pattern_check
from core.cognition.emotional_state import (
    get as get_state,
    update_from_result,
    update_from_session,
    note_pattern_detected,
)
from core.agency.intent_parser import detect as detect_intent
from core.agency.action_executor import execute as run_action
from core.ecosystem.coordinator import debate as ecosystem_debate, is_complex

_BANNER = """
╔══════════════════════════════════════════════╗
║         ALETHEIA -- Sesion de voz            ║
║  Push-to-talk: ENTER para hablar             ║
║  Salir: Ctrl+C                               ║
╚══════════════════════════════════════════════╝
"""

_DOMAIN = "voz"
_MAX_VOICE_CHARS = 350
_MARKDOWN_RE = re.compile(r"(\*{1,2}|_{1,2}|`{1,3}|#{1,6}\s?|>\s?|[-*+]\s)")


# ── text helpers ───────────────────────────────────────────────────────────

def _clean_for_voice(text: str) -> str:
    text = _MARKDOWN_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > _MAX_VOICE_CHARS:
        cut = text[:_MAX_VOICE_CHARS]
        last_stop = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
        text = cut[: last_stop + 1] if last_stop > 50 else cut + "..."
    return text


def _is_mock(text: str) -> bool:
    return text.startswith("[MOCK") or "Fallback response" in text


def _extract_response(result: dict) -> str:
    insight = (result.get("llm_insight") or "").strip()
    if insight and not _is_mock(insight) and len(insight) > 10:
        return _clean_for_voice(insight)

    prediction = (result.get("prediction") or "").strip()
    if prediction and " " in prediction and not _is_mock(prediction):
        return _clean_for_voice(prediction)

    parts = [
        s.get("outcome") or s.get("description") or ""
        for s in result.get("scenarios", [])[:2]
    ]
    parts = [p for p in parts if p and not _is_mock(p)]
    if parts:
        return _clean_for_voice(" ".join(parts))

    return (
        "Necesito que Ollama este activo para responderte. "
        "Puedes arrancarlo con ollama serve en otra terminal."
    )


def _say(text: str, emotion: str | None = None) -> None:
    print(f"  Aletheia: {text}\n")
    try:
        speak(text, emotion=emotion)
    except Exception as exc:
        print(f"  [error TTS] {exc}")


# ── per-turn helpers ───────────────────────────────────────────────────────

def _record_and_transcribe() -> str | None:
    try:
        audio = record_until_silence()
    except Exception as exc:
        print(f"  [error grabacion] {exc}")
        return None
    try:
        text = transcribe(audio)
    except Exception as exc:
        print(f"  [error STT] {exc}")
        return None
    if not text:
        print("  (no se detecto texto -- intenta de nuevo)")
        return None
    return text


def _confirm_action(description: str) -> bool:
    """Ask the user to confirm before executing an action. Returns True = confirmed."""
    print(f"  [accion] {description}")
    print("  Confirmas? [ENTER = si / escribe 'c' + ENTER = cancelar]")
    try:
        answer = input("  > ").strip().lower()
        return answer not in ("c", "cancel", "no", "cancelar")
    except (KeyboardInterrupt, EOFError):
        return False


def _handle_agency(text: str) -> bool:
    """
    Sprint 7 — check if text is an action intent.
    If yes: confirm and execute. Returns True if handled, False if pipeline should run.
    """
    match = detect_intent(text)
    if match is None:
        return False

    action = match.action
    arg    = match.arg

    # Build confirmation message
    if action.needs_arg and arg:
        description = f"{action.name}: '{arg}'"
    else:
        description = action.name

    if not _confirm_action(description):
        _say("Accion cancelada.", emotion=get_state().label)
        return True

    result_text = run_action(action.id, arg)
    _say(result_text, emotion=get_state().label)
    wm.add(question=text, response=result_text, emotion_label="neutro_activo")
    return True


_CONVERSATIONAL_RE = re.compile(
    r"^[¿¡]?\s*(hola|buenos?\s+\w+|qu[eé]\s+tal|c[oó]mo\s+est[aá]s|c[oó]mo\s+te\s+encuentras"
    r"|qu[eé]\s+haces|cu[eé]ntame\s+algo|qu[eé]\s+eres|qui[eé]n\s+eres"
    r"|cu[eé]ntame\s+de\s+ti|qu[eé]\s+piensas|y\s+t[uú]|gracias|adi[oó]s|hasta\s+luego)",
    re.IGNORECASE,
)

def _is_conversational(text: str) -> bool:
    if len(text.split()) <= 8 and _CONVERSATIONAL_RE.search(text):
        return True
    return False


def _respond_conversational(text: str, noted_patterns: set[str]) -> bool:
    prompt = (
        f"Eres Aletheia, una IA acompañante con presencia emocional. "
        f"Responde de forma natural, breve y cálida a: '{text}'"
    )
    try:
        response = llm_router.generate(
            task="chat",
            prompt=prompt,
            context={"domain": "conversacion"},
            temp=0.7,
        )
    except Exception as exc:
        print(f"  [error LLM conversacional] {exc}")
        return False

    response = _clean_for_voice(response or "")
    if not response:
        return False

    new_state = get_state()
    print(f"  Aletheia: {response}")
    wm.add(question=text, response=response, emotion_label="neutro")
    try:
        speak(response, emotion=new_state.label)
    except Exception as exc:
        print(f"  [error TTS] {exc}")

    suggestion = pattern_check(wm, noted_patterns)
    if suggestion:
        note_pattern_detected()
        print()
        _say(suggestion, emotion=new_state.label)

    return True


def _respond_pipeline(text: str, noted_patterns: set[str]) -> bool:
    """
    Run cognitive pipeline, speak response, update emotional state.
    For complex questions, runs ecosystem debate first (Sprint 8).
    Returns True on success.
    """
    user_emotion = emotion_tag(text)

    # Sprint 8 — ecosystem debate for complex questions
    if is_complex(text):
        try:
            eco = ecosystem_debate(text, _DOMAIN)
            print(f"  [ecosistema] {eco['winner']} lidera ({eco['confidence']:.0%})")
        except Exception:
            pass   # never block the main pipeline

    try:
        result = process_request(_DOMAIN, text)
    except Exception as exc:
        print(f"  [error pipeline] {exc}")
        return False

    response   = _extract_response(result)
    new_state  = update_from_result(result)
    confidence = result.get("confidence", 0)
    r_emotion  = emotion_tag(response)

    print(f"  Aletheia [{confidence:.0%} | {r_emotion.label} | est:{new_state.label}]: {response}")
    wm.add(question=text, response=response, emotion_label=user_emotion.label)

    # Sprint 3 — speak with current emotional state modulation
    try:
        speak(response, emotion=new_state.label)
    except Exception as exc:
        print(f"  [error TTS] {exc}")

    suggestion = pattern_check(wm, noted_patterns)
    if suggestion:
        note_pattern_detected()
        print()
        _say(suggestion, emotion=new_state.label)

    return True


# ── main session loop ──────────────────────────────────────────────────────

def run_voice_session() -> None:
    print(_BANNER)

    state = get_state()
    if state.label != "neutro":
        print(f"  Estado emocional: {state.label}  "
              f"(v={state.valence:+.2f} a={state.arousal:.2f})")

    print("  Iniciando motores (STT + TTS + memoria)...")
    preload_stt()
    preload_tts()
    run_at_startup()
    wm.clear()

    intro = briefing()
    current_emotion = get_state().label
    print()
    _say(intro, emotion=current_emotion) if intro else print("  Listo.\n")

    noted_patterns: set[str] = set()
    turn_count = 0

    while True:
        try:
            input("  [ENTER para hablar] ")
        except (KeyboardInterrupt, EOFError):
            print("\n  Sesion de voz cerrada.")
            update_from_session(turn_count)
            wm.clear()
            break

        text = _record_and_transcribe()
        if text is None:
            continue

        user_emotion = emotion_tag(text)
        print(f"\n  Tu [{user_emotion.label}]: {text}")

        # Sprint 7 — try agency first; then conversational bypass; then full pipeline
        handled = _handle_agency(text)
        if not handled:
            if _is_conversational(text):
                if _respond_conversational(text, noted_patterns):
                    turn_count += 1
            elif _respond_pipeline(text, noted_patterns):
                turn_count += 1
        else:
            turn_count += 1
