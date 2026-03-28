"""MCP Server - Modularized Version.

This is the main server file that initializes the FastMCP application
and registers all tool modules.
"""

import logging
import os
import sys

# Ensure the project root is in sys.path so 'src' is importable
# when running this file directly (e.g. python src/server.py)
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from dotenv import load_dotenv

# Load .env before any service or tool imports so env vars are available at init time
load_dotenv()

# Configure logging to stderr — stdout is reserved for the MCP protocol in stdio mode
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("mcp-minimal")

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

# Import services from services package
from src.services import (
    ConnectionManager
)

# Import tool registration functions
from src.tools import (
    register_sql_tools,
    register_connection_tools,
    register_fabric_tools,
    register_postgres_tools,
    register_ddl_tools
)

# Initialize FastMCP application
mcp_server = FastMCP("MCP Lakehouses")

# Initialize the connection manager
connection_manager = ConnectionManager()

# Register all tool modules
logger.info("Registering SQL tools...")
register_sql_tools(mcp_server, connection_manager)

logger.info("Registering connection management tools...")
register_connection_tools(mcp_server, connection_manager)

logger.info("Registering Fabric tools...")
register_fabric_tools(mcp_server, connection_manager)

logger.info("Registering PostgreSQL tools...")
register_postgres_tools(mcp_server, connection_manager)

logger.info("Registering DDL tools...")
register_ddl_tools(mcp_server, connection_manager)

logger.info("All tools registered successfully.")


@mcp_server.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "mcp-minimal"})


# ASGI app for uvicorn using streamable HTTP transport.
# Stateless JSON mode keeps compatibility with simple JSON-RPC POST clients.
app = mcp_server.http_app(
    path="/mcp",
    transport="streamable-http",
    stateless_http=True,
    json_response=True,
)

# Add CORS middleware for VSCode and other clients
# Temporarily disabled to test SSE compatibility
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "OPTIONS"],
#     allow_headers=["*"],
# )

if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    logger.info("Starting server with transport: %s", transport)
    logger.info("Environment MCP_TRANSPORT: %s", os.environ.get("MCP_TRANSPORT", "NOT_SET"))

    if transport == "http":
        import uvicorn
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "5000"))
        logger.info("HTTP server listening on %s:%d", host, port)
        logger.info("MCP endpoint available at: http://%s:%d/mcp", host, port)
        uvicorn.run(app, host=host, port=port)
    else:
        logger.info("Running in stdio mode")
        mcp_server.run(transport="stdio")
