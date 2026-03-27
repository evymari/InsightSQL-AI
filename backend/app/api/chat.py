from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..schemas.chat import ChatRequest
from ..agent.pipeline import run_pipeline
import json

router = APIRouter()


@router.post("/api/chat")
async def chat(request: ChatRequest):
    async def event_generator():
        # Consumimos el generador paso a paso
        async for step in run_pipeline(request.message, request.session_id):
            # Enviamos cada paso al frontend inmediatamente
            yield f"data: {json.dumps(step)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no", # Vital para Codespaces/Nginx
            "Cache-Control": "no-cache"
        }
    )
