"""
TTS engine with sentence streaming (Sprint 2) and emotional modulation (Sprint 3).

Priority order:
  1. Piper TTS   pip install piper-tts
                 ONNX neural, Python 3.14 compatible, ~65 MB model.
                 Supports length_scale / noise_scale for voice modulation.

  2. pyttsx3     pip install pyttsx3  (always-available Windows fallback)

Sprint 2 — sentence streaming:
  Text is split at sentence boundaries. Each sentence is synthesised and
  played immediately, creating a natural streaming effect without waiting
  for the full response to be ready.

Sprint 3 — emotional modulation:
  Piper's length_scale and noise_scale are driven by the current emotional
  state (from core.cognition.emotional_state). No extra dependencies needed.
"""

import re
import time
import os
import threading
from pathlib import Path

import numpy as np

_backend: str | None = None
_engine = None
_stop_event = threading.Event()

_PIPER_DIR   = Path(__file__).parent.parent.parent / "PALACE" / "voice_models" / "piper"
_PIPER_MODEL = "es_ES-sharvard-medium"
_PIPER_HF_REPO   = "rhasspy/piper-voices"
_PIPER_HF_PREFIX = "es/es_ES/sharvard/medium"
_PIPER_ONNX  = _PIPER_DIR / _PIPER_HF_PREFIX / f"{_PIPER_MODEL}.onnx"
_PIPER_JSON  = _PIPER_DIR / _PIPER_HF_PREFIX / f"{_PIPER_MODEL}.onnx.json"

# Sentence boundary pattern — split at . ! ? followed by space or end
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

# Silence (seconds) injected between sentences
_PAUSE_SENTENCE = 0.28
_PAUSE_SHORT    = 0.12   # after comma-ending fragments


# ── Sprint 3 — voice profiles ──────────────────────────────────────────────

_VOICE_PROFILES: dict[str, dict[str, float]] = {
    "positivo_activo":    {"length_scale": 0.88, "noise_scale": 0.70},
    "positivo_tranquilo": {"length_scale": 1.05, "noise_scale": 0.50},
    "negativo_tenso":     {"length_scale": 0.92, "noise_scale": 0.80},
    "negativo_tranquilo": {"length_scale": 1.15, "noise_scale": 0.40},
    "neutro_activo":      {"length_scale": 0.95, "noise_scale": 0.65},
    "neutro":             {"length_scale": 1.00, "noise_scale": 0.67},
}


def _voice_params(emotion_label: str | None) -> dict[str, float]:
    if emotion_label and emotion_label in _VOICE_PROFILES:
        return _VOICE_PROFILES[emotion_label]
    return _VOICE_PROFILES["neutro"]


# ── Sprint 2 — sentence splitting ─────────────────────────────────────────

def _split_sentences(text: str) -> list[str]:
    """Split text at sentence boundaries, keeping punctuation attached."""
    parts = _SENTENCE_RE.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def _silence(seconds: float, samplerate: int) -> np.ndarray:
    """Generate a silent numpy array of given duration."""
    return np.zeros(int(seconds * samplerate), dtype=np.float32)


# ── Piper init ─────────────────────────────────────────────────────────────

def _download_piper() -> tuple[Path, Path]:
    from huggingface_hub import hf_hub_download
    _PIPER_DIR.mkdir(parents=True, exist_ok=True)
    onnx = hf_hub_download(
        repo_id=_PIPER_HF_REPO,
        filename=f"{_PIPER_HF_PREFIX}/{_PIPER_MODEL}.onnx",
        local_dir=str(_PIPER_DIR),
        local_dir_use_symlinks=False,
    )
    cfg = hf_hub_download(
        repo_id=_PIPER_HF_REPO,
        filename=f"{_PIPER_HF_PREFIX}/{_PIPER_MODEL}.onnx.json",
        local_dir=str(_PIPER_DIR),
        local_dir_use_symlinks=False,
    )
    return Path(onnx), Path(cfg)


def _try_piper() -> bool:
    global _engine, _backend
    try:
        from piper.voice import PiperVoice
        onnx, cfg = _PIPER_ONNX, _PIPER_JSON
        if not onnx.exists():
            print(f"  [voz] Descargando Piper {_PIPER_MODEL} (~65 MB, solo la primera vez)...")
            onnx, cfg = _download_piper()
        _engine = PiperVoice.load(str(onnx), config_path=str(cfg))
        _backend = "piper"
        print(f"  [voz] Piper TTS listo  ({_PIPER_MODEL}).")
        return True
    except Exception as exc:
        print(f"  [voz] Piper no disponible ({exc}), usando pyttsx3.")
        return False


def _try_pyttsx3() -> bool:
    global _engine, _backend
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        spanish = [
            v for v in voices
            if any(n in v.name.lower() for n in ("spanish", "helena", "elvira", "pablo"))
            or "es" in (v.languages[0] if v.languages else "").lower()
        ]
        if spanish:
            engine.setProperty("voice", spanish[0].id)
            print(f"  [voz] pyttsx3  ({spanish[0].name})")
        else:
            print("  [voz] pyttsx3  (sin voz española — usando voz por defecto)")
        engine.setProperty("rate", 155)
        engine.setProperty("volume", 0.95)
        _engine = engine
        _backend = "pyttsx3"
        return True
    except Exception as exc:
        print(f"  [voz] pyttsx3 no disponible ({exc}).")
        return False


def _init() -> None:
    global _backend
    if _backend is not None:
        return
    if not _try_piper() and not _try_pyttsx3():
        _backend = "none"
        print("  [voz] Sin motor TTS — respuestas solo por texto.")


# ── public API ─────────────────────────────────────────────────────────────

def stop() -> None:
    """Interrupt any ongoing TTS playback immediately."""
    _stop_event.set()
    try:
        import sounddevice as sd
        sd.stop()
    except Exception:
        pass


def speak(text: str, emotion: str | None = None) -> None:
    """
    Synthesise and play text with optional emotional modulation.

    Sprint 2: streams sentence by sentence with natural pauses.
    Sprint 3: modulates Piper voice params from emotion label.
    Interruptible: call stop() from any thread to cut playback mid-sentence.
    Falls back gracefully to pyttsx3 or print if Piper unavailable.
    """
    _stop_event.clear()
    _init()

    if _backend == "piper":
        import sounddevice as sd
        from piper.config import SynthesisConfig

        params = _voice_params(emotion)
        sr     = _engine.config.sample_rate
        sents  = _split_sentences(text)

        syn_config = SynthesisConfig(
            length_scale=params["length_scale"],
            noise_scale=params["noise_scale"],
        )

        for i, sentence in enumerate(sents):
            if _stop_event.is_set():
                break
            if not sentence:
                continue

            chunks = list(_engine.synthesize(sentence, syn_config=syn_config))

            if not chunks:
                continue

            audio = np.concatenate([c.audio_int16_array for c in chunks]).astype(np.float32) / 32768.0
            sd.play(audio, samplerate=sr)
            sd.wait()

            if _stop_event.is_set():
                break

            # Natural pause between sentences (not after the last one)
            if i < len(sents) - 1:
                ends_abruptly = not sentence.rstrip().endswith((".", "!", "?"))
                pause = _PAUSE_SHORT if ends_abruptly else _PAUSE_SENTENCE
                time.sleep(pause)

    elif _backend == "pyttsx3":
        # Sprint 3 for pyttsx3: adjust rate by emotion
        params = _voice_params(emotion)
        base_rate = 155
        rate = int(base_rate / params["length_scale"])   # inverse: lower scale = faster
        _engine.setProperty("rate", rate)
        _engine.say(text)
        _engine.runAndWait()

    else:
        print(f"  [Aletheia]: {text}")


def preload() -> None:
    """Eagerly initialise TTS so first response has no loading delay."""
    _init()


def list_voices() -> list[str]:
    """Return available pyttsx3 voice names (diagnostic helper)."""
    try:
        import pyttsx3
        e = pyttsx3.init()
        return [v.name for v in e.getProperty("voices")]
    except Exception:
        return []
