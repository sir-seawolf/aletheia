/**
 * VoiceInput — browser voice capture, two strategies:
 *
 *  1. Web Speech API  — instant, Chrome/Edge on localhost or HTTPS only.
 *  2. MediaRecorder → POST /api/voice/transcribe (Whisper backend).
 *
 * Props:
 *   onTranscript(text)  called when transcription is ready
 *   disabled: bool
 *   apiUrl: string
 */
import { useState, useRef, useEffect } from "react";

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition || null;

const TIMEOUT_MS = 25_000;   // 25 s — Whisper model cold-start can be slow

export default function VoiceInput({ onTranscript, disabled = false, apiUrl = "http://localhost:8000" }) {
  const [mode, setMode]         = useState(SpeechRecognition ? "webspeech" : "whisper");
  const [listening, setListening] = useState(false);
  const [status, setStatus]     = useState("");
  const [error, setError]       = useState("");
  const recogRef  = useRef(null);
  const mediaRef  = useRef(null);
  const chunksRef = useRef([]);
  const timerRef  = useRef(null);

  useEffect(() => () => { stopAll(); clearTimeout(timerRef.current); }, []);

  function stopAll() {
    recogRef.current?.stop();
    if (mediaRef.current?.state === "recording") mediaRef.current.stop();
  }

  /* ── Web Speech ───────────────────────────────────────────────────── */
  function startWebSpeech() {
    setError("");
    const recog = new SpeechRecognition();
    recog.lang = "es-ES";
    recog.interimResults = false;
    recog.maxAlternatives = 1;
    recogRef.current = recog;

    recog.onstart  = () => { setListening(true);  setStatus("Escuchando…"); };
    recog.onend    = () => { setListening(false); setStatus(""); };
    recog.onerror  = (e) => {
      setListening(false);
      const msg = {
        "not-allowed":  "Permiso de micrófono denegado.",
        "network":      "Error de red. Prueba el modo Whisper.",
        "no-speech":    "No se detectó voz. Intenta de nuevo.",
        "aborted":      "",
      }[e.error] || `Error: ${e.error}`;
      setError(msg);
      setStatus("");
    };
    recog.onresult = (e) => {
      const text = e.results[0][0].transcript.trim();
      if (text) onTranscript(text);
    };
    recog.start();
  }

  /* ── Whisper (MediaRecorder → backend) ───────────────────────────── */
  async function startWhisper() {
    setError("");
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError("Permiso de micrófono denegado o no disponible.");
      return;
    }

    // Pick the best available MIME type
    const mimeType = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg", "audio/mp4"]
      .find(m => MediaRecorder.isTypeSupported(m)) || "";

    const mr = new MediaRecorder(stream, mimeType ? { mimeType } : {});
    mediaRef.current = mr;
    chunksRef.current = [];

    mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
    mr.onstart  = () => { setListening(true); setStatus("Grabando… pulsa para detener"); };

    mr.onstop = async () => {
      setListening(false);
      stream.getTracks().forEach(t => t.stop());
      setStatus("Transcribiendo con Whisper…");
      clearTimeout(timerRef.current);

      try {
        const blob = new Blob(chunksRef.current, { type: mimeType || "audio/webm" });
        const fd   = new FormData();
        fd.append("audio", blob, "rec.webm");

        const ctrl = new AbortController();
        timerRef.current = setTimeout(() => {
          ctrl.abort();
          setError("Whisper tardó demasiado. ¿Está el servidor arrancado?");
          setStatus("");
        }, TIMEOUT_MS);

        const res  = await fetch(`${apiUrl}/api/voice/transcribe`, {
          method: "POST", body: fd, signal: ctrl.signal,
        });
        clearTimeout(timerRef.current);

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data.text) {
          onTranscript(data.text);
          setStatus("");
        } else {
          setStatus("No se detectó texto.");
        }
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(`Error de transcripción: ${err.message}`);
        }
        setStatus("");
      }
    };

    mr.start();
  }

  function handleClick() {
    if (disabled) return;
    if (listening) { stopAll(); return; }
    mode === "webspeech" ? startWebSpeech() : startWhisper();
  }

  const btnColor = listening ? "#ef4444" : "#6366f1";
  const canUseWebSpeech = !!SpeechRecognition;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
      {/* Mode toggle */}
      <div style={{ display: "flex", gap: 6 }}>
        {[
          ["webspeech", "Navegador", canUseWebSpeech],
          ["whisper",   "Whisper",   true],
        ].map(([m, label, available]) => (
          <button
            key={m}
            onClick={() => { if (!listening) setMode(m); setError(""); }}
            disabled={!available}
            title={!available ? "Solo disponible en Chrome/Edge" : ""}
            style={{
              padding: "3px 10px", borderRadius: 12,
              border: `1px solid ${mode === m ? "#6366f1" : "#374151"}`,
              background: mode === m ? "rgba(99,102,241,0.15)" : "transparent",
              color: !available ? "#374151" : mode === m ? "#818cf8" : "#6b7280",
              fontSize: 11, cursor: available ? "pointer" : "not-allowed",
            }}
          >
            {label}
            {!available && " ✗"}
          </button>
        ))}
      </div>

      {/* Mic button */}
      <button
        onClick={handleClick}
        disabled={disabled}
        title={listening ? "Detener" : "Hablar"}
        style={{
          width: 56, height: 56, borderRadius: "50%",
          border: `2px solid ${btnColor}`,
          background: listening ? "rgba(239,68,68,0.15)" : "rgba(99,102,241,0.12)",
          color: btnColor, fontSize: 24,
          cursor: disabled ? "not-allowed" : "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
          transition: "all 0.2s",
          boxShadow: listening ? `0 0 0 6px rgba(239,68,68,0.2)` : "none",
        }}
      >
        {listening ? "⏹" : "🎙"}
      </button>

      {status && <span style={{ fontSize: 12, color: "#9ca3af" }}>{status}</span>}
      {error  && (
        <div style={{
          fontSize: 12, color: "#f87171", maxWidth: 260, textAlign: "center",
          background: "rgba(239,68,68,0.08)", borderRadius: 8, padding: "4px 10px",
        }}>
          {error}
        </div>
      )}

      {mode === "whisper" && !listening && (
        <span style={{ fontSize: 10, color: "#4b5563", textAlign: "center" }}>
          El primer uso puede tardar 30 s<br />(carga modelo Whisper)
        </span>
      )}
    </div>
  );
}
