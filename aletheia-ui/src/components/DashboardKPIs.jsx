import React from 'react';

const Card = ({ title, value }) => (
  <div className="p-4 border rounded-lg shadow">
    <h3 className="text-sm font-medium text-gray-500">{title}</h3>
    <p className="text-2xl font-bold">{value}</p>
  </div>
);

export default function DashboardKPIs({ metrics }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <Card title="DQS medio" value={metrics.avg_dqs || 0} />
      <Card title="Drift" value={metrics.drift_detected ? '⚠️ Sí' : '✅ OK'} />
      <Card title="Guardian Block Rate" value={`${(metrics.guardian_block_rate * 100).toFixed(1)}%`} />
    </div>
  );
}

