import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .core.config import settings
from .core.database import db
from .middleware.cors import add_cors_middleware
from .api.chat import router as chat_router
from .api.datasource import router as datasource_router
from .services import QueryService, SchemaService, initialize_services

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    schema_service = SchemaService()

    # Startup
    await db.connect()
    await schema_service.initialize()
    query_service = QueryService(schema_service.mcp_client, settings.use_mcp_schema)
    initialize_services(schema_service, query_service)

    yield

    # Shutdown
    await schema_service.close()
    await db.disconnect()


app = FastAPI(
    title="InsightSQL API",
    description="Agente SQL conversacional con schema dinamico via MCP",
    version="1.1.0",
    lifespan=lifespan
)

# Add CORS middleware
add_cors_middleware(app)

# Include routers
app.include_router(chat_router)
app.include_router(datasource_router)


@app.get("/")
async def root():
    return {"message": "InsightSQL API - Agente SQL Conversacional"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "provider": settings.llm_provider,
        "mcp_enabled": settings.use_mcp_schema,
        "default_source": settings.default_data_source,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
