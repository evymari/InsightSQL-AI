from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    message: str
    session_id: str
    role: str = "analyst"


class Intencion(BaseModel):
    metrica: str
    dimension: str
    filtro: str
    granularidad: str
    ambigua: bool = False


class SqlBlock(BaseModel):
    query: str
    tiene_limit: bool
    usa_cte: bool


class Insight(BaseModel):
    resumen_ejecutivo: str
    dato_clave: str
    siguiente_pregunta: str


class AgentResponse(BaseModel):
    session_id: str
    intencion: Intencion
    sql: SqlBlock
    requiere_aprobacion: bool
    advertencias: List[str]
    resultado: List[dict]
    insight: Insight
