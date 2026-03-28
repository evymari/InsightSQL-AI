# install: pip install mcp-client
from mcp import Client

# Conectar a tu MCP en modo stdio
client = Client(
    command="python", 
    args=["src/server.py"]
)

# Usar Ollama como LLM local
import ollama

# Obtener tools del MCP
tools = client.list_tools()

# Llamar una tool
result = client.call_tool("list_fabric_tables")
