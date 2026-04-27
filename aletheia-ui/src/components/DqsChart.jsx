"use client"
import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function DqsChart({ data = [] }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Evolución DQS</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <XAxis dataKey="timestamp" />
          <YAxis domain={[0, 1]} />
          <Tooltip />
          <Line type="monotone" dataKey="dqs" stroke="#3b82f6" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

