import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .core.config import settings
from .core.database import db
from .middleware.cors import add_cors_middleware
from .api.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect()
    yield
    # Shutdown
    await db.disconnect()


app = FastAPI(
    title="InsightSQL API",
    description="Agente SQL conversacional con dataset Olist",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
add_cors_middleware(app)

# Include routers
app.include_router(chat_router)


@app.get("/")
async def root():
    return {"message": "InsightSQL API - Agente SQL Conversacional"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "provider": settings.llm_provider}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
