from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..schemas.chat import ChatRequest
from ..agent.pipeline import run_pipeline

router = APIRouter()


@router.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Endpoint principal del agente conversacional SQL.
    Recibe pregunta en español, descompone intención, genera SQL y devuelve insights.
    """
    try:
        result = await run_pipeline(request.message, request.session_id, request.role)
        
        # Devuelve como SSE stream
        async def stream():
            yield f"data: {result.model_dump_json()}\n\n"
        return StreamingResponse(stream(), media_type="text/event-stream")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
