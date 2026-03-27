// History.jsx
export default function History({ history, onSelectEntry, onClearHistory }) {
  if (!history || history.length === 0) {
    return <p className="text-gray-500 italic mt-4">No hay consultas anteriores.</p>;
  }

  return (
    <div className="mt-4">
      <div className="flex justify-between items-center mb-2">
        <h2 className="font-semibold text-lg">Historial de consultas</h2>
        <button
          onClick={onClearHistory}
          className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600 transition"
        >
          Limpiar historial
        </button>
      </div>

      <div className="flex flex-col gap-4">
        {history.map((entry, index) => (
          <div
            key={index}
            className="bg-white p-4 rounded shadow hover:shadow-md transition-shadow relative"
          >
            <p>
              <span className="font-semibold">Pregunta:</span> {entry.question}
            </p>
            <p className="mt-1">
              <span className="font-semibold">SQL:</span> {entry.sql}
            </p>
            {entry.insight && (
              <p className="mt-1 text-green-600">
                <span className="font-semibold">Insight:</span> {entry.insight}
              </p>
            )}
            {entry.error && (
              <p className="mt-1 text-red-600">
                <span className="font-semibold">Error:</span> {entry.error}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}