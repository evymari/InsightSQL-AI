#!/usr/bin/env python3
"""Standalone MCP smoke test for Fabric + PostgreSQL without backend."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any, Dict

import httpx


async def call_tool(client: httpx.AsyncClient, mcp_endpoint: str, name: str, arguments: Dict[str, Any]) -> Any:
    response = await client.post(
        mcp_endpoint,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        details = response.text[:300].strip() if response.text else "<empty body>"
        if response.status_code == 405:
            raise RuntimeError(
                f"Tool {name} failed with 405 on {mcp_endpoint}. "
                "This usually means MCP transport mismatch (SSE vs streamable-http). "
                f"Response: {details}"
            ) from exc
        raise RuntimeError(
            f"Tool {name} failed with HTTP {response.status_code} on {mcp_endpoint}. Response: {details}"
        ) from exc
    payload = response.json()
    if "error" in payload:
        raise RuntimeError(f"Tool {name} failed: {payload['error']}")
    result = payload.get("result", {})
    content = result.get("content") if isinstance(result, dict) else None
    if isinstance(content, list) and content and isinstance(content[0], dict) and "text" in content[0]:
        text = content[0]["text"]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return result


async def main() -> int:
    parser = argparse.ArgumentParser(description="MCP standalone smoke test")
    parser.add_argument("--base-url", default="http://localhost:8000", help="MCP base URL")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--postgres-schema", default="public", help="PostgreSQL schema for list tables")
    parser.add_argument("--fabric-query", default="SELECT TOP 1 name FROM sys.tables", help="Read-only query for Fabric")
    parser.add_argument("--postgres-query", default="SELECT 1 AS ok", help="Read-only query for PostgreSQL")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    mcp_endpoint = f"{base_url}/mcp"

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(args.timeout),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    ) as client:
        health = await client.get(f"{base_url}/health")
        if health.status_code != 200:
            print(f"[FAIL] health returned {health.status_code}")
            return 1
        print("[OK] health")

        current = await call_tool(client, mcp_endpoint, "get_current_source", {})
        print(f"[OK] current source: {current}")

        switched_fabric = await call_tool(client, mcp_endpoint, "switch_data_source", {"source": "fabric"})
        print(f"[OK] switched to fabric: {switched_fabric}")

        fabric_tables = await call_tool(client, mcp_endpoint, "list_fabric_tables", {})
        print(f"[OK] fabric tables sample: {str(fabric_tables)[:200]}")

        try:
            fabric_query = await call_tool(client, mcp_endpoint, "query", {"sql": args.fabric_query})
            print(f"[OK] fabric query sample: {str(fabric_query)[:200]}")
        except Exception as exc:
            print(f"[WARN] fabric query failed: {exc}")

        switched_postgres = await call_tool(client, mcp_endpoint, "switch_data_source", {"source": "postgres"})
        print(f"[OK] switched to postgres: {switched_postgres}")

        postgres_tables = await call_tool(
            client,
            mcp_endpoint,
            "list_postgres_tables",
            {"schema": args.postgres_schema},
        )
        print(f"[OK] postgres tables sample: {str(postgres_tables)[:200]}")

        postgres_query = await call_tool(client, mcp_endpoint, "query", {"sql": args.postgres_query})
        print(f"[OK] postgres query sample: {str(postgres_query)[:200]}")

    print("[PASS] MCP standalone smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
