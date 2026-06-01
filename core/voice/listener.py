"""
Audio capture and speech-to-text using faster-whisper (100% offline).

Model is downloaded once to PALACE/voice_models/whisper/ and cached.
Silence detection stops recording automatically after SILENCE_DURATION seconds
of audio below SILENCE_THRESHOLD RMS energy.

WakeWordDetector — continuous background listener that calls a callback when
"Aletheia" (or common variants) is detected. Uses silero-VAD gate + faster-whisper
tiny model for low-latency classification. Requires sounddevice; degrades gracefully.
"""

import re
import threading
import time
import numpy as np
from pathlib import Path
from typing import Callable

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024
SILENCE_THRESHOLD = 0.015   # RMS energy — adjust if too sensitive
SILENCE_DURATION = 1.8      # seconds of silence before stopping
MAX_DURATION = 45           # safety cap in seconds

_MODEL_DIR = Path(__file__).parent.parent.parent / "PALACE" / "voice_models" / "whisper"
_model = None
_vad_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _MODEL_DIR.mkdir(parents=True, exist_ok=True)
        print("  [voz] Cargando modelo STT (primera vez ~150MB)...")
        _model = WhisperModel(
            "base",
            download_root=str(_MODEL_DIR),
            device="cpu",
            compute_type="int8",
        )
        print("  [voz] Modelo STT listo.")
    return _model


def record_until_silence() -> np.ndarray:
    """Capture mic audio, stop automatically when silence is detected."""
    import sounddevice as sd

    chunks: list[np.ndarray] = []
    speech_started = False
    silence_blocks = 0
    silence_limit = int(SILENCE_DURATION * SAMPLE_RATE / BLOCK_SIZE)

    print("  Escuchando... (habla ahora)", end="", flush=True)

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=BLOCK_SIZE) as stream:
        while True:
            block, _ = stream.read(BLOCK_SIZE)
            chunks.append(block.copy())

            rms = float(np.sqrt(np.mean(block ** 2)))

            if not speech_started:
                if rms > SILENCE_THRESHOLD:
                    speech_started = True
            else:
                if rms < SILENCE_THRESHOLD:
                    silence_blocks += 1
                    if silence_blocks >= silence_limit:
                        break
                else:
                    silence_blocks = 0

            total_secs = len(chunks) * BLOCK_SIZE / SAMPLE_RATE
            if total_secs > MAX_DURATION:
                break

    print()
    audio = np.concatenate(chunks, axis=0).flatten()
    return audio


def transcribe(audio: np.ndarray, language: str = "es") -> str:
    """Transcribe audio array to text using faster-whisper."""
    model = _get_model()
    segments, _ = model.transcribe(
        audio,
        language=language,
        beam_size=5,
        vad_filter=True,          # filter non-speech segments
        vad_parameters={"min_silence_duration_ms": 300},
    )
    return " ".join(seg.text for seg in segments).strip()


def transcribe_file(path: str, language: str = "es") -> str:
    """Transcribe an audio file (WAV, WebM, MP3, …) to text.
    faster-whisper accepts file paths directly.
    """
    model = _get_model()
    segments, _ = model.transcribe(
        path,
        language=language,
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300},
    )
    return " ".join(seg.text for seg in segments).strip()


def _get_vad_model():
    """Load silero-vad once; return False if unavailable (fail-open)."""
    global _vad_model
    if _vad_model is not None:
        return _vad_model
    try:
        from silero_vad import load_silero_vad
        _vad_model = load_silero_vad()
        print("  [voz] silero-VAD listo.")
    except Exception:
        _vad_model = False
    return _vad_model


def is_speech_present(audio: np.ndarray, min_speech_secs: float = 0.5) -> bool:
    """Return True if silero-vad detects >= min_speech_secs of speech.

    Falls back to True (pass-through) when silero-vad is not installed.
    """
    model = _get_vad_model()
    if not model:
        return True
    try:
        import torch
        from silero_vad import get_speech_timestamps
        tensor = torch.from_numpy(audio).float()
        timestamps = get_speech_timestamps(tensor, model, sampling_rate=SAMPLE_RATE)
        total_secs = sum(t["end"] - t["start"] for t in timestamps) / SAMPLE_RATE
        return total_secs >= min_speech_secs
    except Exception:
        return True  # fail-open


def preload():
    """Eagerly load the STT model so first response is fast."""
    _get_model()
    _get_vad_model()


# ── Wake word detection ───────────────────────────────────────────────────────

_WAKE_MODEL_DIR = Path(__file__).parent.parent.parent / "PALACE" / "voice_models"
_OWW_MODEL_PATH = _WAKE_MODEL_DIR / "oww" / "aletheia.onnx"

# Whisper-based fallback constants
_WAKE_CHUNK_SECS = 2.0
_wake_whisper_model = None

_WAKE_RE = re.compile(
    r"aletheia|a\s*le\s*t[ei]a|hey\s+aletheia|oye\s+aletheia|"
    r"ale\s*t[ei]a|a\s+le\s*te\s*ya",
    re.IGNORECASE,
)

# openWakeWord: 80 ms chunks at 16 kHz
_OWW_CHUNK_FRAMES = 1280
_OWW_THRESHOLD    = 0.5
_OWW_COOLDOWN     = 1.5   # seconds to ignore after a detection


def _get_wake_whisper():
    global _wake_whisper_model
    if _wake_whisper_model is None:
        from faster_whisper import WhisperModel
        (_WAKE_MODEL_DIR / "whisper").mkdir(parents=True, exist_ok=True)
        _wake_whisper_model = WhisperModel(
            "tiny",
            download_root=str(_WAKE_MODEL_DIR / "whisper"),
            device="cpu",
            compute_type="int8",
        )
    return _wake_whisper_model


def _transcribe_wake(audio: np.ndarray) -> str:
    model = _get_wake_whisper()
    segments, _ = model.transcribe(
        audio, language="es", beam_size=1, vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 200},
    )
    return " ".join(seg.text for seg in segments).strip()


def _oww_available() -> bool:
    try:
        import openwakeword  # noqa: F401
        return True
    except ImportError:
        return False


class WakeWordDetector:
    """
    Continuous background listener for the 'Aletheia' wake word.

    Backend selection (automatic):
      1. openWakeWord + custom model  (PALACE/voice_models/oww/aletheia.onnx)
         → ~85 ms latency, ~3 % CPU
      2. Whisper-tiny fallback
         → ~2 s latency, ~15 % CPU
         (train the custom model with: python start.py --train-wake-word)

    Usage::

        detector = WakeWordDetector()
        if detector.start(callback):   # False if no microphone
            ...
        detector.stop()
        print(detector.backend)        # "oww_custom" | "whisper"
    """

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.backend: str = "none"

    def start(self, on_detected: Callable[[], None]) -> bool:
        try:
            import sounddevice as _sd  # noqa: F401
        except ImportError:
            return False

        self._stop_event.clear()

        if _oww_available() and _OWW_MODEL_PATH.exists():
            self.backend = "oww_custom"
            target = self._loop_oww
        else:
            self.backend = "whisper"
            target = self._loop_whisper
            if _oww_available() and not _OWW_MODEL_PATH.exists():
                print(
                    "  [wake] openWakeWord instalado pero sin modelo personalizado. "
                    "Usa: python start.py --train-wake-word"
                )

        self._thread = threading.Thread(
            target=target, args=(on_detected,), daemon=True,
            name="aletheia-wake-detector",
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=_WAKE_CHUNK_SECS + 1.0)

    # ── openWakeWord backend ──────────────────────────────────────────────

    def _loop_oww(self, on_detected: Callable[[], None]) -> None:
        import sounddevice as sd
        from openwakeword.model import Model

        _OWW_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        oww = Model(
            wakeword_models=[str(_OWW_MODEL_PATH)],
            inference_framework="onnx",
        )
        model_name = _OWW_MODEL_PATH.stem   # "aletheia"
        last_detected = 0.0

        print(f"  [wake] openWakeWord activo — modelo '{model_name}' (umbral {_OWW_THRESHOLD})")

        while not self._stop_event.is_set():
            try:
                chunk = sd.rec(
                    _OWW_CHUNK_FRAMES, samplerate=SAMPLE_RATE,
                    channels=1, dtype="int16",
                )
                sd.wait()
                if self._stop_event.is_set():
                    break

                prediction = oww.predict(chunk.flatten())
                confidence = float(prediction.get(model_name, 0.0))

                now = time.monotonic()
                if confidence >= _OWW_THRESHOLD and (now - last_detected) > _OWW_COOLDOWN:
                    last_detected = now
                    on_detected()

            except Exception:
                if not self._stop_event.is_set():
                    time.sleep(0.1)

    # ── Whisper-tiny fallback backend ─────────────────────────────────────

    def _loop_whisper(self, on_detected: Callable[[], None]) -> None:
        import sounddevice as sd

        chunk_frames = int(_WAKE_CHUNK_SECS * SAMPLE_RATE)
        while not self._stop_event.is_set():
            try:
                audio = sd.rec(
                    chunk_frames, samplerate=SAMPLE_RATE,
                    channels=1, dtype="float32",
                )
                sd.wait()
                if self._stop_event.is_set():
                    break

                audio_flat = audio.flatten()
                if not is_speech_present(audio_flat, min_speech_secs=0.3):
                    continue

                text = _transcribe_wake(audio_flat)
                if text and _WAKE_RE.search(text):
                    on_detected()

            except Exception:
                if not self._stop_event.is_set():
                    time.sleep(0.5)
