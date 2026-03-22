# InsightSQL - Agente SQL Conversacional

Backend FastAPI con agente inteligente que procesa preguntas en español, descompone intención y genera consultas SQL sobre el dataset Olist Brazilian E-Commerce.

## 🚀 Características

- **Descomposición de intención**: Analiza preguntas en español y extrae métrica, dimensión, filtro y granularidad
- **Generación SQL automática**: Crea consultas SQL optimizadas para PostgreSQL
- **Múltiples LLMs**: Soporte para OpenAI, Azure OpenAI y Anthropic Claude
- **Streaming SSE**: Respuestas en tiempo real
- **Schema integrado**: Conoce automáticamente las tablas y relaciones del dataset Olist

## 📋 Requisitos

- Python 3.8+
- PostgreSQL 12+
- Credenciales de LLM (OpenAI o Anthropic)

## 🛠️ Instalación

1. **Clonar y configurar entorno**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configurar variables de entorno**
```bash
cp env.example .env
# Editar .env con tus credenciales
```

3. **Configurar base de datos PostgreSQL**
```sql
CREATE DATABASE insightsql;
-- Las tablas se asumen creadas según el schema Olist
```

## ⚙️ Configuración

Variables de entorno principales:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/insightsql

# LLM Provider (elegir uno)
LLM_PROVIDER=anthropic  # Opciones: anthropic, openai, azure_openai
ANTHROPIC_API_KEY=your_key_here
# O para OpenAI
OPENAI_API_KEY=your_key_here
# O para Azure OpenAI
OPENAI_AZURE_ENDPOINT=https://your-resource.openai.azure.com/
OPENAI_AZURE_API_KEY=your_azure_key_here
```

## 🏃‍♂️ Ejecutar

### Opción 1: Usando el archivo app.py (recomendado)
```bash
python app.py
```

### Opción 2: Directamente con uvicorn
```bash
python -m app.main
```

### Opción 3: Con uvicorn explícito
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

La API estará disponible en `http://localhost:8000`

## 📚 Uso

### Endpoint principal

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "ventas por mes en 2017",
    "session_id": "test-1"
  }'
```

### Ejemplos de preguntas

- "ventas totales por categoría de producto"
- "promedio de calificación por estado"
- "productos más vendidos en São Paulo"
- "evolución de pedidos mensuales 2017-2018"
- "top 5 vendedores por monto de ventas"

## 🏗️ Arquitectura

```
app/
├── api/chat.py          # Endpoint /api/chat con streaming SSE
├── agent/               # Sistema del agente inteligente
│   ├── schemas.py       # Modelos Pydantic internos
│   ├── prompt.py        # System prompt con schema Olist
│   ├── llm.py          # Wrapper para múltiples LLMs
│   └── pipeline.py     # Orquestador principal
├── core/               # Configuración y base de datos
│   ├── config.py       # Variables de entorno
│   └── database.py     # Conexión PostgreSQL
├── middleware/         # Middleware CORS
└── main.py            # App FastAPI principal
```

## 🔍 Schema de Base de Datos

El sistema conoce automáticamente las siguientes tablas del dataset Olist:

- **customers**: Información de clientes
- **sellers**: Datos de vendedores  
- **products**: Catálogo de productos
- **orders**: Pedidos (tabla central)
- **order_items**: Ítems de pedidos
- **order_payments**: Pagos
- **order_reviews**: Reseñas y calificaciones

## 🧪 Testing

```bash
# Test básico del endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"¿cuántas ventas totales hay?","session_id":"test"}'
```

## 📝 Notas

- El sistema incluye reintento automático si el LLM no devuelve JSON válido
- Todas las consultas SQL incluyen LIMIT 1000 para seguridad
- Los insights se generan automáticamente después de ejecutar el SQL
- Soporta cambio dinámico de proveedor LLM mediante variables de entorno
