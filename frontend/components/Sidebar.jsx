import { Link } from "react-router-dom";

export default function Sidebar({ history, onSelectEntry, onClearHistory }) {
  return (
    <aside className="w-64 bg-white shadow p-4 flex flex-col h-full">
      <h2 className="text-xl font-bold mb-6">Analytics Agent</h2>

      <nav className="flex flex-col gap-2 mb-4">
        <Link to="/" className="px-2 py-1 hover:bg-blue-600 rounded">🏠 Dashboard</Link>
        <Link to="/history" className="px-2 py-1 hover:bg-blue-600 rounded">🕘 History</Link>
        <Link to="/settings" className="px-2 py-1 hover:bg-blue-600 rounded">⚙️ Settings</Link>
      </nav>

      <div className="flex-1 overflow-y-auto">
        <h3 className="font-semibold mb-2">Historial</h3>
        {history && history.length > 0 ? (
          <div className="flex flex-col gap-1">
            {history.map((entry, index) => (
              <div
                key={index}
                onClick={() => onSelectEntry(entry)}
                className="p-2 rounded cursor-pointer hover:bg-gray-100 border"
              >
                <p className="text-sm font-semibold truncate">{entry.question}</p>
                <p className="text-xs text-gray-500 truncate">{entry.sql}</p>
              </div>
            ))}
            <button
              onClick={onClearHistory}
              className="mt-2 bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600"
            >
              Limpiar historial
            </button>
          </div>
        ) : (
          <p className="text-gray-500 italic text-sm">No hay consultas</p>
        )}
      </div>
    </aside>
  );
}