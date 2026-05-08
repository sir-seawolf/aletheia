/**
 * BrainLoader — animated cognitive processing indicator.
 *
 * Props:
 *   domain: string
 *   activeAgent: "explorer" | "simulator" | "guardian" | null
 *   agentConfidence: number 0-1
 */
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

const AGENTS = [
  { key: "explorer",  icon: "🔍", label: "Explorador",  color: "#818cf8" },
  { key: "simulator", icon: "🎲", label: "Simulador",   color: "#34d399" },
  { key: "guardian",  icon: "🛡️", label: "Guardián",   color: "#f59e0b" },
];

export default function BrainLoader({ domain = 'tecnologia', activeAgent = null, agentConfidence = 0 }) {
  const canvasRef = useRef(null);
  const rafRef    = useRef(null);
  const agentRef  = useRef(activeAgent);

  useEffect(() => { agentRef.current = activeAgent; }, [activeAgent]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const cfg = CONFIGS[domain] || CONFIGS.tecnologia;

    canvas.width  = canvas.offsetWidth  || 220;
    canvas.height = canvas.offsetHeight || 220;
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;

    const particles = Array.from({ length: 110 }, () => ({
      angle: Math.random() * Math.PI * 2,
      dist:  Math.random() * 75 + 20,
      speed: (Math.random() * 0.008 + 0.004) * (Math.random() > 0.5 ? 1 : -1),
    }));
    const floats = Array.from({ length: 28 }, (_, i) => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      s: Math.random() * 1.2 + 0.4,
      sym: cfg.symbols[i % cfg.symbols.length],
    }));

    let pulse = 0;

    const agentHues = { explorer: 240, simulator: 150, guardian: 40 };

    const frame = () => {
      ctx.fillStyle = 'rgba(0,0,0,0.18)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      pulse += 0.04;

      const agent = agentRef.current;
      const h = agent ? agentHues[agent] ?? cfg.hue : cfg.hue;
      const scale = 1 + Math.sin(pulse) * (agent ? 0.12 : 0.07);

      // floating symbols
      ctx.font = '11px monospace';
      floats.forEach(d => {
        ctx.globalAlpha = 0.22;
        ctx.fillStyle = `hsl(${h}, 100%, 60%)`;
        ctx.fillText(d.sym, d.x, d.y);
        d.y = (d.y + d.s) % canvas.height;
      });
      ctx.globalAlpha = 1;

      // outer pulse ring — pulses faster when an agent is active
      const ringAlpha = 0.12 + Math.sin(pulse * (agent ? 2 : 1)) * 0.10;
      ctx.strokeStyle = `hsl(${h}, 100%, 55%)`;
      ctx.lineWidth = agent ? 2.5 : 1.5;
      ctx.globalAlpha = ringAlpha;
      ctx.beginPath();
      ctx.arc(cx, cy, 105, 0, Math.PI * 2);
      ctx.stroke();
      ctx.globalAlpha = 1;

      // second ring (rotates when active)
      if (agent) {
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(pulse * 0.5);
        ctx.strokeStyle = `hsl(${h}, 80%, 45%)`;
        ctx.lineWidth = 1;
        ctx.globalAlpha = 0.25;
        ctx.setLineDash([8, 16]);
        ctx.beginPath();
        ctx.arc(0, 0, 95, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.restore();
        ctx.globalAlpha = 1;
      }

      // particles + synapses
      particles.forEach((p, i) => {
        p.angle += p.speed;
        const x = cx + Math.cos(p.angle) * p.dist * scale;
        const y = cy + Math.sin(p.angle) * p.dist * scale;

        ctx.fillStyle = `hsl(${h}, 100%, 65%)`;
        ctx.beginPath();
        ctx.arc(x, y, agent ? 2.4 : 1.8, 0, Math.PI * 2);
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const x2 = cx + Math.cos(p2.angle) * p2.dist * scale;
          const y2 = cy + Math.sin(p2.angle) * p2.dist * scale;
          const d  = Math.hypot(x - x2, y - y2);
          if (d < 38) {
            ctx.globalAlpha = (1 - d / 38) * (agent ? 0.5 : 0.35);
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

  const activeIdx = AGENTS.findIndex(a => a.key === activeAgent);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, padding: '1.5rem 0' }}>
      <canvas
        ref={canvasRef}
        style={{ width: 220, height: 220, background: '#000', borderRadius: '50%', display: 'block' }}
      />

      {/* Agent progress strip */}
      <div style={{ display: 'flex', gap: 0, alignItems: 'center' }}>
        {AGENTS.map((agent, idx) => {
          const isPast   = activeIdx > idx;
          const isActive = activeIdx === idx;
          const isFuture = activeIdx < idx || activeIdx === -1;
          return (
            <div key={agent.key} style={{ display: 'flex', alignItems: 'center' }}>
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
                padding: '6px 14px', borderRadius: 10,
                background: isActive ? `${agent.color}22` : 'transparent',
                border: `1px solid ${isActive ? agent.color : isPast ? '#374151' : '#1f2937'}`,
                transition: 'all 0.4s',
              }}>
                <span style={{ fontSize: 18, filter: isFuture && !isActive ? 'grayscale(1) opacity(0.3)' : 'none' }}>
                  {isPast ? '✓' : agent.icon}
                </span>
                <span style={{
                  fontSize: 10, fontWeight: isActive ? 700 : 400,
                  color: isActive ? agent.color : isPast ? '#6b7280' : '#374151',
                  letterSpacing: '0.05em',
                }}>
                  {agent.label}
                </span>
                {isActive && agentConfidence > 0 && (
                  <div style={{ width: 40, height: 3, background: '#1f2937', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${agentConfidence * 100}%`, background: agent.color, transition: 'width 0.4s' }} />
                  </div>
                )}
              </div>
              {idx < AGENTS.length - 1 && (
                <div style={{ width: 24, height: 1, background: isPast ? '#4b5563' : '#1f2937', margin: '0 2px' }} />
              )}
            </div>
          );
        })}
      </div>

      <p style={{ color: '#6b7280', fontSize: 13, margin: 0 }}>
        {activeAgent
          ? `${AGENTS.find(a => a.key === activeAgent)?.label} procesando…`
          : 'Iniciando pipeline cognitivo…'}
      </p>
    </div>
  );
}
