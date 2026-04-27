import React from 'react';

export default function DecisionResult({ report }) {
  if (!report) return null;

  return (
    <div className="max-w-4xl bg-white rounded-xl shadow-lg p-8">
      <div className="flex justify-between items-start mb-6">
        <h2 className="text-3xl font-bold">{report.question}</h2>
        <div className="text-right">
          <div className="text-2xl font-bold text-green-600">
            DQS: {report.dqs ? (report.dqs * 100).toFixed(0) + '%' : 'N/A'}
          </div>
          <div className="text-sm text-gray-500">
            Confianza: {(report.confidence * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {report.regulation && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <strong>Modo regulación:</strong> {report.regulation.mode} 
          <span className="ml-2 text-sm text-gray-600">
            memory_weight: {report.regulation.memory_weight}
          </span>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-8 mb-8">
        <div>
          <h3 className="text-xl font-semibold mb-4">Escenarios</h3>
          <div className="space-y-3">
            {report.scenarios?.map((s, i) => (
              <div key={i} className="p-4 border rounded-lg hover:shadow-md">
                <div className="font-medium">{s.description}</div>
                <div className="text-sm text-gray-600">Outcome: {s.outcome || 'N/A'}</div>
                {s.probability && <div>Prob: {(s.probability * 100).toFixed(0)}%</div>}
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-xl font-semibold mb-4">Riesgos</h3>
          <pre className="bg-gray-50 p-4 rounded text-sm max-h-64 overflow-auto">
            {JSON.stringify(report.risks, null, 2)}
          </pre>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        <div>
          <h3 className="text-xl font-semibold mb-4">Guardian</h3>
          {report.guardian_block ? (
            <div className="bg-red-50 p-4 border border-red-200 rounded-lg">
              🚫 <strong>Bloqueado</strong> - {report.guardian_recommendation}
            </div>
          ) : (
            <div className="bg-green-50 p-4 border border-green-200 rounded-lg">
              ✅ Validado ({report.guardian_severity})
            </div>
          )}
          <div className="mt-2 text-sm">
            Issues: {report.guardian_trace?.issues?.length || 0}
          </div>
        </div>

        <div>
          <h3 className="text-xl font-semibold mb-4">Insight LLM</h3>
          <p className="whitespace-pre-wrap">{report.llm_insight?.insight}</p>
        </div>
      </div>

      {report.node_id && (
        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <button className="bg-blue-600 text-white px-6 py-2 rounded-lg">
            Añadir resultado real
          </button>
        </div>
      )}
    </div>
  );
}

