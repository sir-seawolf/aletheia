"""
Audio capture and speech-to-text using faster-whisper (100% offline).

Model is downloaded once to PALACE/voice_models/whisper/ and cached.
Silence detection stops recording automatically after SILENCE_DURATION seconds
of audio below SILENCE_THRESHOLD RMS energy.
"""

import numpy as np
from pathlib import Path

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
