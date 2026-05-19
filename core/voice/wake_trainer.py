"""
Wake word trainer — genera y entrena el modelo personalizado 'Aletheia'.

Flujo:
  1. Genera ~150 clips WAV de "Aletheia" con variaciones (Piper TTS o espeak)
  2. Entrena con openWakeWord usando esos clips como clase positiva
  3. Guarda el modelo en PALACE/voice_models/oww/aletheia.onnx

Uso:
  python start.py --train-wake-word
  python -m core.voice.wake_trainer

Requisitos:
  pip install openwakeword torch torchaudio librosa soundfile
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_VOICE_MODELS  = Path(__file__).parent.parent.parent / "PALACE" / "voice_models"
_OWW_DIR       = _VOICE_MODELS / "oww"
_MODEL_OUT     = _OWW_DIR / "aletheia.onnx"
# Piper TTS Python package paths (same as speaker.py)
_PIPER_DIR     = _VOICE_MODELS / "piper"
_PIPER_MODEL   = "es_ES-sharvard-medium"
_PIPER_ONNX    = _PIPER_DIR / "es" / "es_ES" / "sharvard" / "medium" / f"{_PIPER_MODEL}.onnx"
_PIPER_JSON    = _PIPER_DIR / "es" / "es_ES" / "sharvard" / "medium" / f"{_PIPER_MODEL}.onnx.json"

# Positive phrases for "aletheia" in various phrasings
_POSITIVE_TEXTS = [
    "aletheia",
    "Aletheia",
    "hey aletheia",
    "oye aletheia",
    "hola aletheia",
    "aletheia escucha",
    "aletheia por favor",
    "a le teia",
    "aléteia",
]


def _check_deps() -> list[str]:
    missing = []
    try:
        import openwakeword  # noqa: F401
    except ImportError:
        missing.append("openwakeword")
    try:
        import torch  # noqa: F401
    except ImportError:
        missing.append("torch")
    try:
        import librosa  # noqa: F401
    except ImportError:
        missing.append("librosa")
    try:
        import soundfile  # noqa: F401
    except ImportError:
        missing.append("soundfile")
    return missing


def _tts_piper(text: str, out_path: Path) -> bool:
    """Generate WAV using piper-tts Python package. Returns True on success."""
    if not _PIPER_ONNX.exists():
        return False
    try:
        import wave
        import numpy as np
        from piper.voice import PiperVoice

        cfg_path = str(_PIPER_JSON) if _PIPER_JSON.exists() else None
        voice    = PiperVoice.load(str(_PIPER_ONNX), config_path=cfg_path)
        chunks   = list(voice.synthesize(text))

        if not chunks:
            return False

        audio = np.concatenate([c.audio_int16_array for c in chunks])
        sr    = voice.config.sample_rate

        with wave.open(str(out_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)   # int16 = 2 bytes
            wf.setframerate(sr)
            wf.writeframes(audio.tobytes())

        return out_path.exists() and out_path.stat().st_size > 0
    except Exception:
        return False


def _tts_espeak(text: str, out_path: Path) -> bool:
    """Generate WAV using espeak (system). Returns True on success."""
    try:
        result = subprocess.run(
            ["espeak", "-v", "es", "-s", "130", "-w", str(out_path), text],
            capture_output=True, timeout=10,
        )
        return result.returncode == 0 and out_path.exists()
    except FileNotFoundError:
        return False


def _tts_gtts(text: str, out_path: Path) -> bool:
    """Generate WAV using gTTS (requires internet). Returns True on success."""
    try:
        from gtts import gTTS
        import io
        tts = gTTS(text=text, lang="es", slow=False)
        mp3_buf = io.BytesIO()
        tts.write_to_fp(mp3_buf)
        mp3_buf.seek(0)

        import soundfile as sf
        import librosa
        y, sr = librosa.load(mp3_buf, sr=16000, mono=True)
        sf.write(str(out_path), y, 16000, subtype="PCM_16")
        return True
    except Exception:
        return False


def _generate_positive_samples(out_dir: Path, n_per_phrase: int = 6) -> int:
    """Generate positive WAV clips for 'Aletheia'. Returns count generated."""
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    # Try TTS backends in order of preference
    backends = [_tts_piper, _tts_espeak, _tts_gtts]

    for i, phrase in enumerate(_POSITIVE_TEXTS):
        for j in range(n_per_phrase):
            out_file = out_dir / f"aletheia_{i:02d}_{j:02d}.wav"
            if out_file.exists():
                count += 1
                continue
            for backend in backends:
                if backend(phrase, out_file):
                    count += 1
                    break
            time.sleep(0.05)

    return count


def _resample_to_16k(wav_path: Path) -> bool:
    """Ensure WAV is 16kHz mono PCM16. Returns True if ok."""
    try:
        import librosa
        import soundfile as sf
        y, sr = librosa.load(str(wav_path), sr=16000, mono=True)
        sf.write(str(wav_path), y, 16000, subtype="PCM_16")
        return True
    except Exception:
        return False


def _train_torch_direct(emb_pos: "np.ndarray", emb_neg: "np.ndarray", out_path: Path) -> bool:
    """
    Train a wake word classifier with pure PyTorch (no openwakeword.train needed).
    Exports a compatible ONNX that openwakeword.model.Model can load.

    Input embeddings shape: (N, 16, 96) — from AudioFeatures.embed_clips().
    """
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset

    class _WakeNet(nn.Module):
        def __init__(self):
            super().__init__()
            # GRU over the 16-frame sequence of 96-dim embeddings
            self.gru  = nn.GRU(96, 128, batch_first=True, num_layers=1)
            self.drop = nn.Dropout(0.3)
            self.fc   = nn.Linear(128, 1)

        def forward(self, x):                      # x: (B, 16, 96)
            _, h = self.gru(x)                     # h: (1, B, 128)
            return torch.sigmoid(self.fc(self.drop(h.squeeze(0))))  # (B, 1)

    # ── data ──────────────────────────────────────────────────────────────
    X = np.concatenate([emb_pos, emb_neg], axis=0).astype(np.float32)
    y = np.concatenate([
        np.ones(len(emb_pos), dtype=np.float32),
        np.zeros(len(emb_neg), dtype=np.float32),
    ]).reshape(-1, 1)

    # 80 / 20 split
    idx     = np.random.default_rng(0).permutation(len(X))
    n_val   = max(1, len(X) // 5)
    val_i, train_i = idx[:n_val], idx[n_val:]

    ds_tr   = TensorDataset(torch.from_numpy(X[train_i]), torch.from_numpy(y[train_i]))
    ds_val  = TensorDataset(torch.from_numpy(X[val_i]),   torch.from_numpy(y[val_i]))
    dl_tr   = DataLoader(ds_tr,  batch_size=32, shuffle=True)
    dl_val  = DataLoader(ds_val, batch_size=64)

    # ── train ─────────────────────────────────────────────────────────────
    model = _WakeNet()
    opt   = optim.Adam(model.parameters(), lr=3e-4)
    loss_fn = nn.BCELoss()

    best_val, best_state = 1e9, None
    for epoch in range(60):
        model.train()
        for xb, yb in dl_tr:
            opt.zero_grad()
            loss_fn(model(xb), yb).backward()
            opt.step()

        model.eval()
        with torch.no_grad():
            val_loss = sum(loss_fn(model(xb), yb).item() for xb, yb in dl_val)
        if val_loss < best_val:
            best_val  = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

        if (epoch + 1) % 10 == 0:
            print(f"         epoch {epoch+1}/60  val_loss={val_loss:.4f}")

    model.load_state_dict(best_state)

    # ── export ONNX ───────────────────────────────────────────────────────
    model.eval()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    dummy = torch.zeros(1, 16, 96)

    # Use TorchScript trace → ONNX (avoids onnxscript dependency in torch 2.x)
    try:
        traced = torch.jit.trace(model, dummy)
        torch.onnx.export(
            traced, dummy, str(out_path),
            input_names=["input"],
            output_names=["output"],
            dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}},
            opset_version=11,
        )
    except Exception:
        # Fallback: direct export (may need onnxscript on newer torch)
        torch.onnx.export(
            model, dummy, str(out_path),
            input_names=["input"],
            output_names=["output"],
            opset_version=11,
        )
    return out_path.exists()


def _load_clips_as_array(clips_dir: Path, target_len: int = 32000) -> "np.ndarray":
    """Load all WAVs in a directory into a (N, target_len) int16 array."""
    import numpy as np
    import librosa
    arrays = []
    for wav in sorted(clips_dir.glob("*.wav")):
        try:
            y, _ = librosa.load(str(wav), sr=16000, mono=True)
            arr = (y * 32767).astype(np.int16)
            if len(arr) < target_len:
                arr = np.pad(arr, (0, target_len - len(arr)))
            arrays.append(arr[:target_len])
        except Exception:
            pass
    return np.array(arrays) if arrays else np.zeros((0, target_len), dtype=np.int16)


def _generate_negative_clips(n: int = 120, target_len: int = 32000) -> "np.ndarray":
    """Generate diverse negative examples without audiomentations."""
    import numpy as np
    clips = []
    rng = np.random.default_rng(42)

    # 1. Silence + very low noise
    for _ in range(n // 4):
        clips.append((rng.normal(0, 50, target_len)).astype(np.int16))

    # 2. Other Spanish words via Piper
    neg_words = [
        "hola", "gracias", "buenos días", "por favor", "qué tal",
        "cómo estás", "adiós", "hasta luego", "sí", "no",
        "ayuda", "espera", "continua", "para", "siguiente",
        "uno dos tres", "información", "recuerda", "cronos", "sistema",
    ]
    neg_dir = _OWW_DIR / "_negatives_tmp"
    neg_dir.mkdir(parents=True, exist_ok=True)
    for i, word in enumerate(neg_words):
        out = neg_dir / f"neg_{i:02d}.wav"
        if not out.exists():
            _tts_piper(word, out)
    for wav in sorted(neg_dir.glob("*.wav")):
        try:
            import librosa
            y, _ = librosa.load(str(wav), sr=16000, mono=True)
            arr = (y * 32767).astype(np.int16)
            if len(arr) < target_len:
                arr = np.pad(arr, (0, target_len - len(arr)))
            clips.append(arr[:target_len])
        except Exception:
            pass

    # 3. Random band-limited noise (speech-like)
    while len(clips) < n:
        noise = rng.normal(0, 800, target_len).astype(np.int16)
        clips.append(noise)

    return np.array(clips[:n], dtype=np.int16)


def train(verbose: bool = True) -> bool:
    """
    Train a custom 'Aletheia' wake word model. Returns True on success.

    Strategy:
      1. Generate positive clips with Piper TTS (reuses existing ones if present)
      2. Generate negative clips (silence + other words)
      3. Embed both using openWakeWord's AudioFeatures (no audiomentations needed)
      4. Train the wake word model with auto_train
      5. Export as aletheia.onnx
    """
    import numpy as np

    print("\n══════════════════════════════════════════")
    print("  Entrenador de wake word — 'Aletheia'")
    print("══════════════════════════════════════════\n")

    missing = _check_deps()
    if missing:
        print(f"  [error] Dependencias faltantes: {', '.join(missing)}")
        print(f"  Instala con: pip install {' '.join(missing)}")
        return False

    _OWW_DIR.mkdir(parents=True, exist_ok=True)

    # ── Step 1: positive clips ────────────────────────────────────────────
    # Reuse saved clips if they exist from a previous run
    saved = _OWW_DIR / "positive_samples"
    if saved.exists() and len(list(saved.glob("*.wav"))) >= 10:
        positive_dir = saved
        n = len(list(positive_dir.glob("*.wav")))
        print(f"  [1/5] Reutilizando {n} clips positivos guardados.")
    else:
        saved.mkdir(parents=True, exist_ok=True)
        print("  [1/5] Generando muestras positivas de 'Aletheia'...")
        n = _generate_positive_samples(saved)
        if n == 0:
            print("  [error] No se pudieron generar muestras de audio.")
            return False
        positive_dir = saved
        print(f"         {n} clips generados.")

    # ── Step 2: normalize ─────────────────────────────────────────────────
    print("  [2/5] Normalizando audio a 16kHz...")
    for wav in positive_dir.glob("*.wav"):
        _resample_to_16k(wav)

    # ── Step 3: embed ─────────────────────────────────────────────────────
    print("  [3/5] Extrayendo embeddings con openWakeWord...")
    try:
        from openwakeword.utils import AudioFeatures, download_models
        download_models()
        F = AudioFeatures()

        TARGET = 32000  # 2 seconds at 16kHz
        X_pos = _load_clips_as_array(positive_dir, TARGET)
        print(f"         Positivos: {len(X_pos)} clips → embeddings...")
        emb_pos = F.embed_clips(X_pos)                        # (N, 16, 96)

        print("         Negativos: generando...")
        X_neg = _generate_negative_clips(n=max(120, len(X_pos) * 3), target_len=TARGET)
        emb_neg = F.embed_clips(X_neg)                        # (M, 16, 96)

        print(f"         Pos shape: {emb_pos.shape}  Neg shape: {emb_neg.shape}")
    except Exception as exc:
        print(f"  [error] Fallo en embedding: {exc}")
        return False

    # ── Step 4: train + export ────────────────────────────────────────────
    print("  [4/5] Entrenando modelo con PyTorch (2-5 min)...")
    trained = _train_torch_direct(emb_pos, emb_neg, _MODEL_OUT)

    if not trained:
        print("  [error] El entrenamiento PyTorch directo falló.")
        return False

    # ── Step 5: verify ────────────────────────────────────────────────────
    print("  [5/5] Verificando modelo...")

    if _MODEL_OUT.exists():
        size_kb = _MODEL_OUT.stat().st_size // 1024
        print(f"\n  ✅ Modelo guardado: {_MODEL_OUT}  ({size_kb} KB)")
        print("  Reinicia con: python start.py --voice --always-on")
        return True

    print("  [error] El archivo .onnx no se generó.")
    return False


def is_model_ready() -> bool:
    return _MODEL_OUT.exists()


def status() -> dict:
    return {
        "model_exists":   _MODEL_OUT.exists(),
        "model_path":     str(_MODEL_OUT),
        "oww_installed":  _oww_importable(),
        "piper_available": _PIPER_ONNX.exists(),
    }


def _oww_importable() -> bool:
    try:
        import openwakeword  # noqa: F401
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    success = train(verbose=True)
    sys.exit(0 if success else 1)
