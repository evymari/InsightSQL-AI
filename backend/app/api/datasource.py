from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.config import settings
from ..services.runtime import get_query_service, get_schema_service

router = APIRouter(prefix="/api/datasource", tags=["datasource"])


class SwitchDataSourceRequest(BaseModel):
    source: str
    database_name: Optional[str] = None


@router.get("/health")
async def datasource_health() -> Dict[str, Any]:
    schema_service = get_schema_service()
    query_service = get_query_service()

    if not query_service:
        raise HTTPException(status_code=503, detail="Services are not initialized")

    mcp_connection = False
    details: Dict[str, Any] = {}
    if schema_service and schema_service.mcp_client:
        mcp_connection = await schema_service.mcp_client.health_check()
        details["mcp"] = "Connected" if mcp_connection else "Disconnected"

    source = await query_service.get_current_source_info()

    return {
        "status": "healthy" if (mcp_connection or not settings.use_mcp_schema) else "degraded",
        "mcp_connection": mcp_connection,
        "execution_mode": query_service.get_execution_mode(),
        "current_source": source,
        "details": details,
    }


@router.get("/current")
async def current_source() -> Dict[str, Any]:
    query_service = get_query_service()
    if not query_service:
        raise HTTPException(status_code=503, detail="Query service not initialized")
    source = await query_service.get_current_source_info()
    return {
        "status": "success",
        "execution_mode": query_service.get_execution_mode(),
        "source": source,
    }


@router.post("/switch")
async def switch_source(request: SwitchDataSourceRequest) -> Dict[str, Any]:
    schema_service = get_schema_service()
    if not schema_service:
        raise HTTPException(status_code=503, detail="Schema service not initialized")

    result = await schema_service.switch_data_source(
        source=request.source,
        database_name=request.database_name,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"status": "success", "result": result}
