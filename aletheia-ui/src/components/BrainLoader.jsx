import { useEffect, useRef } from 'react';

const CONFIGS = {
  finanzas:    { hue: 45,  symbols: ['$', '€', '%', 'ROI', '0', '1'] },
  tecnologia:  { hue: 200, symbols: ['<>', '//', '{}', '0', '1', 'λ'] },
  salud:       { hue: 150, symbols: ['♥', '+', 'Hz', 'O₂', 'ADN', '℃'] },
  carrera:     { hue: 30,  symbols: ['↑', '★', 'CV', 'MBA', '$', '▲'] },
  relaciones:  { hue: 330, symbols: ['♥', '∞', 'Ψ', '☯', '↔', '≈'] },
  objetivos:   { hue: 260, symbols: ['★', '◎', '→', 'NOW', 'OK', '✓'] },
  aprendizaje: { hue: 180, symbols: ['∑', 'π', 'α', 'β', 'γ', '∞'] },
  creatividad: { hue: 290, symbols: ['✦', '⊕', 'idea', '!', '☆', 'crit'] },
};

export default function BrainLoader({ domain = 'tecnologia' }) {
  const canvasRef = useRef(null);
  const rafRef   = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const cfg = CONFIGS[domain] || CONFIGS.tecnologia;

    canvas.width  = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;

    const particles = Array.from({ length: 110 }, () => ({
      angle: Math.random() * Math.PI * 2,
      dist:  Math.random() * 75 + 20,
    }));
    const floats = Array.from({ length: 28 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      s: Math.random() * 1.2 + 0.4,
    }));

    let pulse = 0;

    const frame = () => {
      ctx.fillStyle = 'rgba(0,0,0,0.18)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      pulse += 0.04;
      const scale = 1 + Math.sin(pulse) * 0.07;
      const h = cfg.hue;

      // floating symbols
      ctx.font = '11px monospace';
      floats.forEach((d, i) => {
        ctx.globalAlpha = 0.22;
        ctx.fillStyle = `hsl(${h}, 100%, 60%)`;
        ctx.fillText(cfg.symbols[i % cfg.symbols.length], d.x, d.y);
        d.y = (d.y + d.s) % canvas.height;
      });
      ctx.globalAlpha = 1;

      // outer pulse ring
      ctx.strokeStyle = `hsl(${h}, 100%, 55%)`;
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = 0.12 + Math.sin(pulse) * 0.07;
      ctx.beginPath();
      ctx.arc(cx, cy, 105, 0, Math.PI * 2);
      ctx.stroke();
      ctx.globalAlpha = 1;

      // particles + synapses
      particles.forEach((p, i) => {
        const x = cx + Math.cos(p.angle) * p.dist * scale;
        const y = cy + Math.sin(p.angle) * p.dist * scale;

        ctx.fillStyle = `hsl(${h}, 100%, 65%)`;
        ctx.beginPath();
        ctx.arc(x, y, 1.8, 0, Math.PI * 2);
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const x2 = cx + Math.cos(p2.angle) * p2.dist * scale;
          const y2 = cy + Math.sin(p2.angle) * p2.dist * scale;
          const d = Math.hypot(x - x2, y - y2);
          if (d < 38) {
            ctx.globalAlpha = (1 - d / 38) * 0.35;
            ctx.strokeStyle = `hsl(${h}, 100%, 60%)`;
            ctx.lineWidth = 0.6;
            ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x2, y2); ctx.stroke();
            ctx.globalAlpha = 1;
          }
        }
      });

      rafRef.current = requestAnimationFrame(frame);
    };

    frame();
    return () => cancelAnimationFrame(rafRef.current);
  }, [domain]);

  return (
    <div className="flex flex-col items-center gap-4 py-10">
      <canvas
        ref={canvasRef}
        style={{ width: 220, height: 220, background: '#000', borderRadius: '50%' }}
      />
      <p className="text-gray-400 text-sm">Procesando decisión cognitiva...</p>
      <div className="flex gap-2 text-xs text-gray-500">
        <span className="animate-pulse">🔍 Explorando</span>
        <span>→</span>
        <span className="animate-pulse" style={{ animationDelay: '0.4s' }}>🎲 Simulando</span>
        <span>→</span>
        <span className="animate-pulse" style={{ animationDelay: '0.8s' }}>🛡️ Validando</span>
      </div>
    </div>
  );
}
