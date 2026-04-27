import React from 'react';

export default function DecisionList({ decisions = [] }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Últimas decisiones</h3>
      <div className="space-y-3">
        {decisions.slice(0, 5).map((d) => (
          <div key={d.node_id} className="p-4 border rounded-lg hover:shadow-md">
            <div className="font-medium truncate">{d.question}</div>
            <div className="flex space-x-4 text-sm">
              <span>DQS: {d.dqs?.toFixed(2)}</span>
              <span>Conf: {(d.confidence * 100).toFixed(0)}%</span>
              <span>{d.guardian_block ? '🚫 Bloqueado' : '✅ OK'}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

