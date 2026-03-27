import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union

import httpx

from .exceptions import MCPConnectionError, MCPTimeoutError, MCPToolError

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self, base_url: str, timeout: int = 30, retry_attempts: int = 3) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.mcp_endpoint = f"{self.base_url}/mcp"
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )

        logger.info("MCP Client initialized with URL: %s", self.mcp_endpoint)

    async def close(self) -> None:
        await self._client.aclose()

    async def health_check(self) -> bool:
        health_timeout = min(float(self.timeout), 10.0)
        try:
            response = await self._client.get(f"{self.base_url}/health", timeout=health_timeout)
            return response.status_code == 200
        except httpx.TimeoutException:
            logger.error("MCP health check timeout after %ss against %s/health", health_timeout, self.base_url)
            return False
        except httpx.HTTPError as exc:
            logger.error("MCP health check failed: %s", exc)
            return False

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], timeout: Optional[int] = None) -> Union[List[Dict[str, Any]], Dict[str, Any], str]:
        request_timeout = timeout or self.timeout

        for attempt in range(self.retry_attempts):
            try:
                response = await self._client.post(
                    self.mcp_endpoint,
                    json={
                        "jsonrpc": "2.0",
                        "id": attempt + 1,
                        "method": "tools/call",
                        "params": {"name": tool_name, "arguments": arguments},
                    },
                    timeout=httpx.Timeout(request_timeout),
                )
                response.raise_for_status()
                payload = response.json()
                if "error" in payload:
                    raise MCPToolError(str(payload["error"]))
                if "result" not in payload:
                    raise MCPToolError("Invalid MCP response: missing result")
                return self._parse_result(payload["result"])
            except httpx.TimeoutException as exc:
                if attempt == self.retry_attempts - 1:
                    raise MCPTimeoutError(f"Tool {tool_name} timed out after {request_timeout}s") from exc
                await asyncio.sleep(1)
            except httpx.HTTPError as exc:
                if attempt == self.retry_attempts - 1:
                    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 405:
                        raise MCPConnectionError(
                            "Failed to call tool "
                            f"{tool_name}: HTTP 405 on {self.mcp_endpoint}. "
                            "Likely MCP transport mismatch (SSE vs streamable-http)."
                        ) from exc
                    raise MCPConnectionError(f"Failed to call tool {tool_name}: {exc}") from exc
                await asyncio.sleep(1)
            except (MCPToolError, MCPConnectionError, MCPTimeoutError):
                raise
            except Exception as exc:  # pragma: no cover
                if attempt == self.retry_attempts - 1:
                    raise MCPToolError(f"Unexpected MCP client error for {tool_name}: {exc}") from exc
                await asyncio.sleep(1)

        raise MCPToolError(f"Failed to call tool {tool_name}")

    @staticmethod
    def _parse_result(result: Dict[str, Any]) -> Union[List[Dict[str, Any]], Dict[str, Any], str]:
        # FastMCP commonly wraps tool output as content/text.
        content = result.get("content")
        if isinstance(content, list) and content:
            first_item = content[0]
            if isinstance(first_item, dict) and "text" in first_item:
                text = first_item["text"]
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        return result

    async def query(self, sql: str) -> Union[List[Dict[str, Any]], Dict[str, Any], str]:
        return await self.call_tool("query", {"sql": sql})

    async def list_postgres_databases(self) -> Union[List[str], Dict[str, Any], str]:
        return await self.call_tool("list_postgres_databases", {})

    async def list_postgres_tables(self, schema: str = "public") -> Union[List[Dict[str, Any]], Dict[str, Any], str]:
        return await self.call_tool("list_postgres_tables", {"schema": schema})

    async def list_fabric_databases(self) -> Union[List[str], Dict[str, Any], str]:
        return await self.call_tool("list_fabric_databases", {})

    async def list_fabric_tables(self) -> Union[List[Dict[str, Any]], Dict[str, Any], str]:
        return await self.call_tool("list_fabric_tables", {})

    async def switch_data_source(self, source: str, database_name: Optional[str] = None) -> Union[Dict[str, Any], str, List[Dict[str, Any]]]:
        args: Dict[str, Any] = {"source": source}
        if database_name:
            args["database_name"] = database_name
        return await self.call_tool("switch_data_source", args)

    async def get_current_source(self) -> Union[Dict[str, Any], str, List[Dict[str, Any]]]:
        return await self.call_tool("get_current_source", {})
