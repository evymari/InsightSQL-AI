import json
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from ..schemas.chat import ChatRequest
from ..agent.pipeline import run_pipeline
import json

router = APIRouter()


@router.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Endpoint principal del agente conversacional SQL.
    Recibe pregunta en español, descompone intención, genera SQL y devuelve insights.
    """
    try:
        # Devuelve como SSE stream real, emitiendo eventos durante todo el pipeline
        async def stream():
            try:
                async for event in run_pipeline(request.message, request.session_id, request.role):
                    json_safe_event = jsonable_encoder(event)
                    yield f"data: {json.dumps(json_safe_event, ensure_ascii=False)}\n\n"
            except Exception as e:
                error_event = {
                    "type": "error",
                    "stage": "chat_endpoint",
                    "session_id": request.session_id,
                    "message": str(e),
                }
                yield f"data: {json.dumps(jsonable_encoder(error_event), ensure_ascii=False)}\n\n"

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
