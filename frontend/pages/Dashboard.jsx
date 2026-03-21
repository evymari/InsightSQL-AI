import { useState } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import QueryForm from "../components/QueryForm";
import Results from "../components/Results";
import History from "./History";

export default function Dashboard() {
  const [query, setQuery] = useState("");
  const [sql, setSql] = useState("");
  const [insight, setInsight] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSql("");
    setInsight("");

    try {
      // Mock backend
      setSql(`SELECT * FROM sales WHERE month = 'January'`);
      setInsight(`Las ventas en Enero fueron altas comparadas con Diciembre.`);
    } catch (err) {
      setError("Error al generar SQL. Revisa tu consulta.");
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      
      <main className="flex-1 p-6 overflow-auto">
        <Header />
        <QueryForm query={query} setQuery={setQuery} handleSubmit={handleSubmit} />
        <Results sql={sql} insight={insight} error={error} />
        
      </main>
    </div>
  );
}