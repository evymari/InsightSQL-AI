from pydantic import BaseModel
from typing import List, Optional


class Intencion(BaseModel):
    metrica: str            # "ventas_totales"
    dimension: str          # "mes"
    filtro: str             # "año 2017"
    granularidad: str       # "mensual"
    ambigua: bool           # si necesita aclaración


class SqlBlock(BaseModel):
    query: str              # el SELECT generado
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
    resultado: List[dict]   # filas devueltas por la BD
    insight: Insight
