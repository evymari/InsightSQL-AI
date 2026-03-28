import json
from typing import Dict, Any, AsyncGenerator
from .prompt import SYSTEM_PROMPT
from .llm import llm
from .schemas import AgentResponse
from ..core.database import db
from ..services.runtime import get_query_service, get_schema_service


def _build_agent_response(session_id: str, data: Dict[str, Any], rows: list[dict]) -> AgentResponse:
    return AgentResponse(
        session_id=session_id,
        resultado=rows,
        intencion=data.get("intencion", {
            "metrica": "",
            "dimension": "",
            "filtro": "",
            "granularidad": "",
            "ambigua": False
        }),
        sql=data.get("sql", {
            "query": "",
            "tiene_limit": False,
            "usa_cte": False
        }),
        requiere_aprobacion=data.get("requiere_aprobacion", False),
        advertencias=data.get("advertencias", []),
        insight=data.get("insight", {
            "resumen_ejecutivo": "",
            "dato_clave": "",
            "siguiente_pregunta": ""
        })
    )


async def run_pipeline(message: str, session_id: str, role: str = "analyst") -> AsyncGenerator[Dict[str, Any], None]:
    """
    Pipeline principal con streaming: LLM → Parse JSON → Ejecutar SQL.
    Emite eventos intermedios y un evento final con el AgentResponse serializado.
    """
    yield {
        "type": "stage",
        "stage": "started",
        "session_id": session_id,
        "message": "Iniciando pipeline"
    }
    
    schema_service = get_schema_service()
    query_service = get_query_service()

    if schema_service:
        schema_text = await schema_service.get_schema_for_role(role)
    else:
        schema_text = "## PASO 2 - Schema disponible\n- public.orders\n- public.order_items\n- public.products"

    yield {
        "type": "stage",
        "stage": "schema_ready",
        "session_id": session_id,
        "message": "Schema cargado"
    }

    prompt = SYSTEM_PROMPT.replace("{schema}", schema_text)

    # 1. Llamar al LLM
    try:
        response_text = await llm.generate_response(message, prompt)
    except Exception as e:
        yield {
            "type": "error",
            "stage": "llm",
            "session_id": session_id,
            "message": f"Error calling LLM: {str(e)}"
        }
        return

    yield {
        "type": "stage",
        "stage": "llm_done",
        "session_id": session_id,
        "message": "Respuesta del LLM recibida"
    }
    
    # 2. Parsear JSON — si falla, reintentar una vez con el error como contexto
    try:
        data = json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        # Reintento con el error como contexto
        retry_prompt = f"{prompt}\n\nTu respuesta anterior no fue JSON válido: {response_text}\n\nError: {str(e)}\n\nResponde ÚNICAMENTE con JSON válido, sin markdown ni texto adicional."
        yield {
            "type": "warning",
            "stage": "json_parse",
            "session_id": session_id,
            "message": "JSON inválido del LLM, reintentando"
        }
        try:
            retry_response = await llm.generate_response(
                f"Por favor corrige tu respuesta. Usuario preguntó: {message}", 
                retry_prompt
            )
            data = json.loads(retry_response.strip())
        except json.JSONDecodeError:
            yield {
                "type": "error",
                "stage": "json_parse",
                "session_id": session_id,
                "message": f"Failed to parse JSON after retry: {retry_response}"
            }
            return

    yield {
        "type": "stage",
        "stage": "json_ready",
        "session_id": session_id,
        "message": "JSON validado"
    }
    
    # 3. Ejecutar el SQL via MCP-first con fallback a PostgreSQL
    rows: list[dict] = []
    yield {
        "type": "stage",
        "stage": "sql_started",
        "session_id": session_id,
        "message": "Iniciando ejecución SQL"
    }
    try:
        query = data.get("sql", {}).get("query", "")
        if query:
            if query_service:
                query_result = await query_service.execute_query(query)
                rows = query_result if isinstance(query_result, list) else []
                if isinstance(query_result, dict) and "error" in query_result:
                    raise Exception(query_result["error"])
            else:
                rows = await db.execute_query(query)
        else:
            rows = []
    except Exception as e:
        # Si el SQL falla, devolver el error en advertencias
        rows = []
        if "advertencias" not in data:
            data["advertencias"] = []
        data["advertencias"].append(f"Error ejecutando SQL: {str(e)}")
        yield {
            "type": "warning",
            "stage": "sql",
            "session_id": session_id,
            "message": f"Error ejecutando SQL: {str(e)}"
        }

    yield {
        "type": "stage",
        "stage": "sql_done",
        "session_id": session_id,
        "message": f"Ejecución SQL finalizada con {len(rows)} filas"
    }
    
    # 4. Emitir evento final con objeto tipado serializado
    final_response = _build_agent_response(session_id, data, rows)
    yield {
        "type": "final",
        "stage": "completed",
        "session_id": session_id,
        "data": final_response.model_dump(mode="json")
    }
