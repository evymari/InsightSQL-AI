import os
from dotenv import load_dotenv
from pathlib import Path

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

env_path = Path(__file__).parent.parent / ".env"
print("env_path client.py", env_path)
load_dotenv(env_path)

async def get_schema_for_role(user_role: str) -> str:
    url = os.getenv("MCP_SSE_URL")
    headers = {"X-MS-API-ROLE": user_role}

    async with sse_client(url, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Lista todas las tools disponibles para este rol
            tools = await session.list_tools()

            # Convierte las tools a texto de schema para el prompt
            schema_text = ""
            for tool in tools.tools:
                # Cada tool es una entidad: "list-Orders", "get-Orders", etc.
                # Extrae el nombre de la entidad y sus campos del inputSchema
                entity = tool.name.replace("list-", "").replace("get-", "")
                if tool.inputSchema and "properties" in tool.inputSchema:
                    campos = ", ".join(tool.inputSchema["properties"].keys())
                    schema_text += f"- {entity}: {campos}\n"

            return schema_text