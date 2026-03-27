import json
from typing import Dict, Any
from .prompt import SYSTEM_PROMPT
from .llm import llm
from .schemas import AgentResponse
from ..core.database import db


async def run_pipeline(message: str, session_id: str):
    """
    Pipeline que hace yield de diccionarios con el estado actual.
    """
    # 1. Fase LLM
    yield {"status": "llm_start", "message": "Generando consulta SQL..."}
    try:
        response_text = await llm.generate_response(message, SYSTEM_PROMPT)
    except Exception as e:
        yield {"status": "error", "message": f"Error en LLM: {str(e)}"}
        return

    # 2. Fase Parseo (Omito el código de retry por brevedad, pero sigue la misma lógica)
    yield {"status": "parsing", "message": "Validando estructura de datos..."}
    try:
        data = json.loads(response_text.strip())
    except Exception as e:
        # Aquí iría tu lógica de reintento...
        yield {"status": "error", "message": "Error al parsear respuesta"}
        return

    # 3. Fase Base de Datos
    query = data.get("sql", {}).get("query", "")
    if query:
        yield {"status": "sql_executing", "message": "Consultando base de datos...", "query": query}
        try:
            rows = await db.execute_query(query)
        except Exception as e:
            rows = []
            data.setdefault("advertencias", []).append(f"Error SQL: {str(e)}")
    else:
        rows = []

    # 4. Resultado Final
    # Construimos el objeto final pero lo enviamos como el último evento del stream
    final_response = {
        "session_id": session_id,
        "resultado": rows,
        "intencion": data.get("intencion", {}),
        "sql": data.get("sql", {}),
        "insight": data.get("insight", {}),
        "advertencias": data.get("advertencias", []),
        "status": "complete"
    }
    yield {"status": "done", "data": final_response}