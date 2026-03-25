import json
from typing import Dict, Any
from .prompt import SYSTEM_PROMPT
from .llm import llm
from .schemas import AgentResponse
from ..core.database import db


async def run_pipeline(message: str, session_id: str) -> AgentResponse:
    """
    Pipeline principal: LLM → Parse JSON → Ejecutar SQL → Retornar respuesta tipada
    """
    
    # 1. Llamar al LLM
    try:
        response_text = await llm.generate_response(message, SYSTEM_PROMPT)
    except Exception as e:
        raise Exception(f"Error calling LLM: {str(e)}")
    
    # 2. Parsear JSON — si falla, reintentar una vez con el error como contexto
    try:
        data = json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        # Reintento con el error como contexto
        retry_prompt = f"{SYSTEM_PROMPT}\n\nTu respuesta anterior no fue JSON válido: {response_text}\n\nError: {str(e)}\n\nResponde ÚNICAMENTE con JSON válido, sin markdown ni texto adicional."
        try:
            retry_response = await llm.generate_response(
                f"Por favor corrige tu respuesta. Usuario preguntó: {message}", 
                retry_prompt
            )
            data = json.loads(retry_response.strip())
        except json.JSONDecodeError:
            raise Exception(f"Failed to parse JSON after retry: {retry_response}")
    
    # 3. Ejecutar el SQL contra PostgreSQL
    try:
        query = data.get("sql", {}).get("query", "")
        if query:
            rows = await db.execute_query(query)
        else:
            rows = []
    except Exception as e:
        # Si el SQL falla, devolver el error en advertencias
        rows = []
        if "advertencias" not in data:
            data["advertencias"] = []
        data["advertencias"].append(f"Error ejecutando SQL: {str(e)}")
    
    # 4. Devolver objeto tipado
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
