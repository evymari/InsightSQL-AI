export default function QueryForm({ query, setQuery, handleSubmit }) {
  return (
    <form onSubmit={handleSubmit} className="mb-6">
      <textarea
        className="w-full p-3 border rounded shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        rows={4}
        placeholder="Escribe tu pregunta analítica aquí..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="mt-3 flex justify-center">
        <button
          onClick={handleSubmit}
          className="bg-blue-600 text-white px-5 py-2 rounded-md text-sm hover:bg-blue-700"
        >
          Generate SQL & Insight
        </button>
      </div>
       
    </form>
    
  );
}