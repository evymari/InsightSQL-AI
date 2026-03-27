import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ..core.config import settings
from ..mcp.client import MCPClient

logger = logging.getLogger(__name__)


class SchemaService:
    def __init__(self) -> None:
        self.mcp_client: Optional[MCPClient] = None
        self.cache_ttl = timedelta(minutes=15)
        self.schema_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_time: Dict[str, datetime] = {}

    async def initialize(self) -> None:
        self.mcp_client = MCPClient(
            base_url=settings.mcp_server_url,
            timeout=settings.mcp_timeout,
            retry_attempts=settings.mcp_retry_attempts,
        )
        healthy = await self.mcp_client.health_check()
        if healthy:
            logger.info("MCP schema service connected")
        else:
            logger.warning("MCP schema service is unavailable, fallback schema will be used")

    async def close(self) -> None:
        if self.mcp_client:
            await self.mcp_client.close()

    async def get_schema_for_role(self, role: str = "analyst") -> str:
        if not settings.use_mcp_schema or not self.mcp_client:
            return self._fallback_schema(role)

        cache_key = f"{role}:{settings.default_data_source}"
        if self._is_cached(cache_key):
            return self.schema_cache[cache_key]["schema"]

        try:
            source_info = await self.mcp_client.get_current_source()
            source = source_info.get("source", settings.default_data_source) if isinstance(source_info, dict) else settings.default_data_source

            if source == "fabric":
                tables = await self.mcp_client.list_fabric_tables()
                formatted = self._format_table_list("fabric", tables)
            else:
                tables = await self.mcp_client.list_postgres_tables(schema="public")
                formatted = self._format_table_list("postgres", tables)

            schema_text = f"## PASO 2 - Schema disponible (source: {source})\n{formatted}"
            self._cache(cache_key, schema_text)
            return schema_text
        except Exception as exc:
            logger.warning("Failed dynamic schema lookup from MCP: %s", exc)
            return self._fallback_schema(role)

    async def get_current_source_info(self) -> Dict[str, Any]:
        if not self.mcp_client:
            return {"source": "postgres", "mode": "fallback"}
        source_info = await self.mcp_client.get_current_source()
        if isinstance(source_info, dict):
            return source_info
        return {"source": "unknown", "raw": source_info}

    async def switch_data_source(self, source: str, database_name: Optional[str] = None) -> Dict[str, Any]:
        if not self.mcp_client:
            return {"error": "MCP client unavailable"}
        result = await self.mcp_client.switch_data_source(source=source, database_name=database_name)
        self.schema_cache.clear()
        self.cache_time.clear()
        if isinstance(result, dict):
            return result
        return {"result": result}

    def _is_cached(self, cache_key: str) -> bool:
        if cache_key not in self.cache_time:
            return False
        return datetime.now() - self.cache_time[cache_key] < self.cache_ttl

    def _cache(self, cache_key: str, schema: str) -> None:
        self.schema_cache[cache_key] = {"schema": schema}
        self.cache_time[cache_key] = datetime.now()

    @staticmethod
    def _format_table_list(source: str, tables: Any) -> str:
        if not isinstance(tables, list) or not tables:
            return "No se encontraron tablas disponibles."

        lines = [f"Tablas detectadas en {source}:"]
        for item in tables:
            if isinstance(item, dict):
                schema = item.get("schema")
                name = item.get("name")
                if schema and name:
                    lines.append(f"- {schema}.{name}")
                elif name:
                    lines.append(f"- {name}")
            elif isinstance(item, str):
                lines.append(f"- {item}")
        return "\n".join(lines)

    @staticmethod
    def _fallback_schema(role: str) -> str:
        base = [
            "## PASO 2 - Schema disponible (fallback)",
            "Tablas base:",
            "- public.orders",
            "- public.order_items",
            "- public.products",
            "- public.customers",
        ]
        if role in {"analyst", "admin"}:
            base.extend([
                "- public.order_payments",
                "- public.order_reviews",
                "- public.sellers",
            ])
        return "\n".join(base)
