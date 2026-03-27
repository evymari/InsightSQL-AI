import logging
from typing import Any, Dict, List, Optional, Union

from ..core.database import db
from ..mcp.client import MCPClient

logger = logging.getLogger(__name__)


class QueryService:
    def __init__(self, mcp_client: Optional[MCPClient], use_mcp_schema: bool) -> None:
        self.mcp_client = mcp_client
        self.use_mcp_schema = use_mcp_schema

    async def execute_query(self, sql: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        if not sql.strip():
            return []

        if self.use_mcp_schema and self.mcp_client:
            try:
                mcp_result = await self.mcp_client.query(sql)
                if isinstance(mcp_result, list):
                    return mcp_result
                if isinstance(mcp_result, dict) and "error" not in mcp_result:
                    return [mcp_result]
                raise RuntimeError(str(mcp_result))
            except Exception as exc:
                logger.warning("MCP query failed, using direct PostgreSQL fallback: %s", exc)

        return await db.execute_query(sql)

    async def get_current_source_info(self) -> Dict[str, Any]:
        if self.use_mcp_schema and self.mcp_client:
            try:
                source_info = await self.mcp_client.get_current_source()
                if isinstance(source_info, dict):
                    return source_info
                return {"raw": source_info}
            except Exception as exc:
                logger.warning("Could not get source from MCP: %s", exc)

        return {"source": "postgres", "mode": "direct"}

    def get_execution_mode(self) -> str:
        if self.use_mcp_schema and self.mcp_client:
            return "mcp"
        return "direct"
