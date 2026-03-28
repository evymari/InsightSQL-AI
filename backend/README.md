# InsightSQL - Agente SQL Conversacional

Backend FastAPI con agente inteligente que procesa preguntas en español, descompone intención y genera consultas SQL sobre el dataset Olist Brazilian E-Commerce.

## 🚀 ¿Qué hace el proyecto?

1. **Recibe preguntas en español**: Ej: "ventas por mes en 2017"
2. **Descompone la intención automáticamente**:
   - `metrica`: "ventas_totales" 
   - `dimension`: "mes"
   - `filtro`: "año 2017"
   - `granularidad`: "mensual"
3. **Genera SQL optimizado** para PostgreSQL con el schema Olist
4. **Ejecuta la consulta** y devuelve resultados en tiempo real
5. **Crea insights automáticos** con resumen ejecutivo y sugerencias

## 🔧 Características Técnicas

- **FastAPI** con StreamingResponse (Server-Sent Events)
- **OpenAI Azure** integrado para generación de SQL
- **PostgreSQL** con asyncpg para consultas asíncronas
- **Reintento automático** si el LLM no devuelve JSON válido
- **Schema Olist completo** integrado en el prompt del agente

## 📋 Requisitos

- Python 3.8+
- PostgreSQL 12+
- Azure OpenAI API Key

## 🛠️ Instalación

```bash
# 1. Clonar y entrar al directorio
cd backend

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp env.example .env
# Editar .env con tus credenciales de Azure OpenAI
```

## ⚙️ Configuración

Variables de entorno principales:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/insightsql

# Azure OpenAI (recomendado)
LLM_PROVIDER=azure_openai
OPENAI_AZURE_API_KEY=tu_azure_key_aqui
OPENAI_AZURE_ENDPOINT=https://tu-resource.openai.azure.com/
OPENAI_MODEL=gpt-4  # o tu deployment name
OPENAI_AZURE_VERSION=2024-02-15-preview

# Application
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

## 🏃‍♂️ Ejecutar

```bash
python app.py
```

La API estará disponible en `http://localhost:8000`

## 📚 Probar el Endpoint

### Con PowerShell (recomendado para testing)

```powershell
# Streaming sin buffer
curl -i -N -X POST http://0.0.0.0:8000/api/chat \
     -H "Content-Type: application/json" \
     -H "Accept: text/event-stream" \
     -d '{
           "message": "Cuáles fueron las ventas totales por mes en 2017?",
           "session_id": "121",
           "role": "analyst"
         }'
```

### Con Bruno/Postman/Insomnia

**Headers requeridos:**
```
Content-Type: application/json
Accept: text/event-stream
Cache-Control: no-cache
```

**Body (JSON):**
```json
{
  "message": "ventas por mes en 2017",
  "session_id": "test-1"
}
```

**Importante:** No necesitas activar un "botón de streaming" especial, pero configura los headers correctamente. Algunas herramientas UI guardan la respuesta en buffer antes de mostrarla.

### Ejemplos de preguntas

- `"ventas por mes en 2017"`
- `"productos más vendidos por categoría"`
- `"promedio de calificación por estado"`
- `"top 5 vendedores por monto de ventas"`

## 📋 Respuesta Esperada (SSE)

El endpoint emite **múltiples eventos SSE** durante el procesamiento (`stage`, `warning`, `error`) y un evento final con el resultado consolidado.

Ejemplo de evento intermedio:

```json
{
  "type": "stage",
  "stage": "sql_started",
  "session_id": "test-1",
  "message": "Iniciando ejecución SQL"
}
```

Ejemplo de evento final:

```json
{
  "type": "final",
  "stage": "completed",
  "session_id": "test-1",
  "data": {
    "session_id": "test-1",
    "intencion": {
      "metrica": "ventas_totales",
      "dimension": "mes", 
      "filtro": "año 2017",
      "granularidad": "mensual",
      "ambigua": false
    },
    "sql": {
      "query": "SELECT EXTRACT(MONTH FROM o.order_purchase_timestamp) AS mes, SUM(oi.price + oi.freight_value) AS ventas_totales FROM orders o JOIN order_items oi ON o.order_id = oi.order_id WHERE EXTRACT(YEAR FROM o.order_purchase_timestamp) = 2017 GROUP BY EXTRACT(MONTH FROM o.order_purchase_timestamp) ORDER BY mes LIMIT 1000",
      "tiene_limit": true,
      "usa_cte": false
    },
    "requiere_aprobacion": false,
    "advertencias": [],
    "resultado": [...],
    "insight": {
      "resumen_ejecutivo": "Las ventas mensuales en 2017 muestran...",
      "dato_clave": "El mes de mayor actividad fue...",
      "siguiente_pregunta": "¿Quieres ver el desglose por categoría?"
    }
  }
}
```

## 🏗️ Arquitectura

```
app/
├── api/chat.py          # Endpoint /api/chat con streaming SSE
├── agent/               # Sistema del agente inteligente
│   ├── schemas.py       # Modelos Pydantic internos
│   ├── prompt.py        # System prompt con schema Olist
│   ├── llm.py          # Wrapper para Azure OpenAI
│   └── pipeline.py     # Orquestador principal
├── core/               # Configuración y base de datos
│   ├── config.py       # Variables de entorno
│   └── database.py     # Conexión PostgreSQL
├── middleware/         # Middleware CORS
└── main.py            # App FastAPI principal
```

## 🔍 Schema de Base de Datos

El sistema conoce automáticamente las tablas del dataset Olist:
- **customers**: Información de clientes
- **sellers**: Datos de vendedores  
- **products**: Catálogo de productos
- **orders**: Pedidos (tabla central)
- **order_items**: Ítems de pedidos
- **order_payments**: Pagos
- **order_reviews**: Reseñas y calificaciones

## 🧪 Testing Rápido

```bash
# 1. Iniciar servidor
python app.py

# 2. En otra terminal, probar con PowerShell
curl.exe -N -i -X POST http://localhost:8000/api/chat `
  -H "Content-Type: application/json" `
  -H "Accept: text/event-stream" `
  -d '{"message":"¿cuántas ventas totales hay?","session_id":"test"}'
```

## 📝 Notas Técnicas

- **Streaming SSE real**: El pipeline emite eventos intermedios con `yield` y no espera al resultado final para comenzar a responder
- **Reintento JSON**: Si el LLM no devuelve JSON válido, reintenta con contexto del error
- **Seguridad SQL**: Todas las consultas incluyen LIMIT 1000
- **Azure OpenAI**: Configurado específicamente para Azure con deployment names
