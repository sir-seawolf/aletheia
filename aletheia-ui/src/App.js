import { useEffect, useMemo, useState } from "react";
import "./App.css";

import DashboardKPIs from './components/DashboardKPIs';
import DqsChart from './components/DqsChart';
import DecisionList from './components/DecisionList';
import DecisionInput from './components/DecisionInput';  // stub for now
import DecisionResult from './components/DecisionResult';  // stub for now

const API_URL = "http://localhost:8000";

export default function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [metrics, setMetrics] = useState({});
  const [recentDecisions, setRecentDecisions] = useState([]);
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (activeView === 'dashboard') {
      fetch(`${API_URL}/system/metrics`)
        .then(res => res.json())
        .then(setMetrics);
      // Recent decisions stub - fetch from backend later
      setRecentDecisions([]);
    }
  }, [activeView]);

  const runSimulation = async () => {
    try {
      const res = await fetch(`${API_URL}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          domain: "general",
          question
        })
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow p-6">
        <div className="max-w-7xl mx-auto flex space-x-8">
          <button 
            onClick={() => setActiveView('dashboard')} 
            className={activeView === 'dashboard' ? 'font-bold text-blue-600 border-b-2 border-blue-600 pb-1' : 'hover:text-blue-600'}
          >
            Dashboard
          </button>
          <button 
            onClick={() => setActiveView('simulate')} 
            className={activeView === 'simulate' ? 'font-bold text-blue-600 border-b-2 border-blue-600 pb-1' : 'hover:text-blue-600'}
          >
            Nueva decisión
          </button>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto p-8">
        {activeView === 'dashboard' && (
          <div>
            <DashboardKPIs metrics={metrics} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
              <DqsChart data={[]} />
              <DecisionList decisions={recentDecisions} />
            </div>
          </div>
        )}

        {activeView === 'simulate' && (
          <div className="max-w-2xl">
            <h1 className="text-4xl font-bold mb-8">Nueva decisión</h1>
            <textarea
              className="w-full p-6 border-2 border-gray-200 rounded-xl text-xl resize-vertical mb-4"
              rows="3"
              placeholder="Describe tu decisión aquí... Ej: ¿Debería cambiar de trabajo? Tengo X en ahorros, gasto Y, oferta Z"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button 
              onClick={runSimulation}
              className="bg-blue-600 text-white px-12 py-4 rounded-xl text-xl font-semibold hover:bg-blue-700"
              disabled={!question.trim()}
            >
              Analizar
            </button>
{result && <DecisionResult report={result} />}

          </div>
        )}
      </main>
    </div>
  );
}

