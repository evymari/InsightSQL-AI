// src/utils/keywordsAnaliticas.js

export const keywordsAnaliticas = [
  "total", "suma", "promedio", "clientes", "ventas",
  "ingresos", "cantidad", "productos", "max", "min"
];

export function esPreguntaAnalitica(pregunta) {
  const preguntaMinuscula = pregunta.toLowerCase();
  return keywordsAnaliticas.some(keyword => preguntaMinuscula.includes(keyword));
}