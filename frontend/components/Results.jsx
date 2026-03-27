// src/components/Results.js
export default function Results({ question, sql, insight, error }) {
  return (
    <div className="grid md:grid-cols-2 gap-4 mb-6">
      {question && (
        <div className="bg-white p-4 rounded-2xl shadow">
          <h3 className="font-semibold mb-2">Pregunta</h3>
          <p className="text-gray-700">{question}</p>
        </div>
      )}

      {sql && (
        <div className="bg-white p-4 rounded-2xl shadow">
          <h3 className="font-semibold mb-2">SQL Generado</h3>
          <pre className="bg-blue-50 p-3 rounded text-xs text-blue-800">
            {sql}
          </pre>
        </div>
      )}

      {insight && (
        <div className="bg-white p-4 rounded-2xl shadow md:col-span-2">
          <h3 className="font-semibold mb-2">Insight</h3>
          <p className="text-gray-600">{insight}</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 p-4 rounded-2xl shadow md:col-span-2">
          <p className="text-red-600 font-semibold">{error}</p>
        </div>
      )}
    </div>
  );
}