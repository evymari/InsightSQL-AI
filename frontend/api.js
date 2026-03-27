// api.js
export const sendMessageToApi = async (message) => {
  try {
    const response = await fetch("http://127.0.0.1:8000/chat/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ q: message }),
    });

    return await response.json();
  } catch (error) {
    console.error("Error:", error);
    return { error: "Network error" };
  }
};

// Generar preguntas analíticas desde backend
// src/api.js
export const generarPreguntasIA = async (keyword = "") => {
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/api/analytics/generarPreguntasIA/?keyword=${encodeURIComponent(keyword)}`
    );
    const data = await response.json();
    return data.questions || [];
  } catch (error) {
    console.error("Error:", error);
    return [];
  }
};