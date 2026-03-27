// src/pages/Dashboard.jsx
import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import QueryForm from "../components/QueryForm";
import Results from "../components/Results";
import { sendMessageToApi, generarPreguntasIA } from "../api";

// Validación simple de preguntas analíticas
const esPreguntaValida = (text) => {
  const palabras = text.trim().split(/\s+/);
  if (palabras.length < 3) return false;

  const keywords = ["venta", "producto", "cliente", "mes", "región", "tendencia", "cantidad", "total"];
  const textLower = text.toLowerCase();
  return keywords.some(k => textLower.includes(k));
};

export default function Dashboard() {
  const [query, setQuery] = useState("");
  const [sql, setSql] = useState("");
  const [insight, setInsight] = useState("");
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Cargar historial desde localStorage
  useEffect(() => {
    const saved = localStorage.getItem("sqlHistory");
    if (saved) setHistory(JSON.parse(saved));
  }, []);

  useEffect(() => {
    localStorage.setItem("sqlHistory", JSON.stringify(history));
  }, [history]);

  // Función para obtener sugerencias desde backend
  const generarSugerencias = async () => {
    setError("");
    try {
      const preguntas = await generarPreguntasIA(query);
      if (!preguntas || preguntas.length === 0) {
        setError("No se generaron preguntas");
        return;
      }
      setSuggestions(preguntas);
      setShowSuggestions(true);
    } catch (err) {
      console.error("Error obteniendo sugerencias:", err);
      setError("No se pudieron cargar sugerencias");
    }
  };

  const handleSelectSuggestion = (sug) => {
    setQuery(sug);
    setShowSuggestions(false);
  };

  // Enviar consulta al backend
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSql("");
    setInsight("");

    if (!query.trim()) {
      setError("Escribe una pregunta primero");
      return;
    }

    if (!esPreguntaValida(query)) {
      setError("Escribe una pregunta analítica con sentido, por ejemplo: 'ventas de productos por región en el último mes'");
      return;
    }

    try {
      const data = await sendMessageToApi(query);
      if (data.error) {
        setError(data.error);
        return;
      }

      const newInsight = "Insight generado por IA";
      const newEntry = {
        question: query,
        sql: data.response,
        insight: newInsight,
        error: data.error || "",
      };

      // Evitar duplicados en el historial
      setHistory((prev) =>
        prev.some((i) => i.question === newEntry.question && i.sql === newEntry.sql)
          ? prev
          : [newEntry, ...prev]
      );

      setSql(data.response);
      setInsight(newInsight);
      setQuery("");
    } catch (err) {
      console.error(err);
      setError("Error conectando con el backend");
    }
  };

  const handleClearQuery = () => {
    setQuery("");
    setSql("");
    setInsight("");
    setError("");
  };

  const handleClearHistory = () => {
    setHistory([]);
    localStorage.removeItem("sqlHistory");
  };

  const handleSelectEntry = (entry) => {
    setQuery(entry.question);
    setSql(entry.sql);
    setInsight(entry.insight);
    setError(entry.error);
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar
        history={history}
        onSelectEntry={handleSelectEntry}
        onClearHistory={handleClearHistory}
      />

      <main className="flex-1 p-6 overflow-auto">
        <Header />
        <QueryForm query={query} setQuery={setQuery} handleSubmit={handleSubmit} />

        <div className="mt-4">
          <button
            onClick={generarSugerencias}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Sugerir pregunta
          </button>
        </div>

        {showSuggestions && (
          <div className="bg-white p-4 mt-2 rounded shadow max-w-md">
            <h3 className="font-semibold mb-2">Sugerencias:</h3>
            <ul className="flex flex-col gap-2">
              {suggestions.map((sug, i) => (
                <li
                  key={i}
                  className="cursor-pointer p-2 hover:bg-gray-100 rounded border"
                  onClick={() => handleSelectSuggestion(sug)}
                >
                  {sug}
                </li>
              ))}
            </ul>
          </div>
        )}

        {error && (
          <div className="bg-red-100 p-3 rounded mb-4 text-red-700 font-semibold">
            {error}
          </div>
        )}

        {(sql || insight) && <Results sql={sql} insight={insight} error={error} />}

        <button
          onClick={handleClearQuery}
          className="mt-4 bg-gray-300 px-4 py-2 rounded hover:bg-gray-400"
        >
          Limpiar Consulta
        </button>
      </main>
    </div>
  );
}