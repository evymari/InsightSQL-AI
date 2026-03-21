export default function Results({ sql, insight, error }) {
  
  return (
    <div className="grid md:grid-cols-2 gap-4 mb-6">
      {sql && (
        <div className="bg-white p-4 rounded-2xl shadow">
          <h3 className="font-semibold mb-2">SQL Generated</h3>
          <pre className="bg-blue-50 p-3 rounded text-xs text-blue-800">
            {sql}
          </pre>
        </div>
      )}

      {insight && (
        <div className="bg-white p-4 rounded-2xl shadow">
          <h3 className="font-semibold mb-2">Insight</h3>
          <p className="text-gray-600">{insight}</p>
        </div>
      )}
    </div>
  );
}