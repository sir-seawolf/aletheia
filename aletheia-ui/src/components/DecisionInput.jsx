import React from 'react';

export default function DecisionInput({ onSubmit }) {
  const [question, setQuestion] = useState('');

  return (
    <div className="max-w-2xl p-6">
      <textarea
        className="w-full p-6 border-2 border-gray-200 rounded-xl text-xl resize-vertical mb-4 focus:border-blue-400 focus:outline-none"
        rows="3"
        placeholder="Describe tu decisión aquí..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <button 
        onClick={() => onSubmit(question)}
        className="bg-blue-600 text-white px-12 py-4 rounded-xl text-xl font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        disabled={!question.trim()}
      >
        Simular decisión
      </button>
    </div>
  );
}

