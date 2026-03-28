"""PostgreSQL connection utilities for MCP tools."""

from __future__ import annotations

import os
from dotenv import load_dotenv
import sys
from typing import Any, Dict, List

import psycopg
from psycopg.rows import dict_row

_cached_connection: psycopg.Connection | None = None

load_dotenv()

def _build_dsn(database_name: str | None = None) -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db = database_name or os.getenv("POSTGRES_DB", "postgres")
    print("host", host)
    print("port", port)
    print("user", user)
    print("password", password)
    # return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    # "postgresql://myuser:mypassword@localhost:5432/mydb"
    return "postgresql://postgres:smdev97ecSADpg@localhost:5432/insightsql"


def get_postgres_connection() -> psycopg.Connection:
    """Return a cached PostgreSQL connection."""
    global _cached_connection

    if _cached_connection is not None and not _cached_connection.closed:
        return _cached_connection

    try:
        _cached_connection = psycopg.connect(_build_dsn(), autocommit=True, row_factory=dict_row)
        return _cached_connection
    except Exception as exc:
        print(f"PostgreSQL connection failed: {exc}", file=sys.stderr)
        raise ConnectionError(f"PostgreSQL connection failed: {exc}") from exc


def close_postgres_connection() -> None:
    global _cached_connection
    if _cached_connection is not None and not _cached_connection.closed:
        try:
            _cached_connection.close()
        except Exception:
            pass
    _cached_connection = None


def switch_postgres_database(database_name: str) -> None:
    """Switch default database and reset cached connection."""
    os.environ["POSTGRES_DB"] = database_name
    close_postgres_connection()


def execute_query(sql: str) -> List[Dict[str, Any]]:
    conn = get_postgres_connection()
    with conn.cursor() as cursor:
        cursor.execute(sql)
        if cursor.description is None:
            return []
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def execute_ddl(sql: str) -> Dict[str, Any]:
    conn = get_postgres_connection()
    with conn.cursor() as cursor:
        cursor.execute(sql)
    return {"success": True, "rows_affected": 0, "data_source": "postgres"}


def list_databases() -> List[str]:
    sql = """
        SELECT datname
        FROM pg_database
        WHERE datistemplate = false
        ORDER BY datname
    """
    rows = execute_query(sql)
    return [row["datname"] for row in rows]


def list_schemas() -> List[str]:
    sql = """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schema_name
    """
    rows = execute_query(sql)
    return [row["schema_name"] for row in rows]


def list_tables(schema: str | None = None, include_views: bool = True) -> List[str]:
    table_types = ["BASE TABLE"]
    if include_views:
        table_types.append("VIEW")

    if schema:
        sql = """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = ANY(%s)
              AND table_schema = %s
            ORDER BY table_schema, table_name
        """
        params = (table_types, schema)
    else:
        sql = """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = ANY(%s)
              AND table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name
        """
        params = (table_types,)

    conn = get_postgres_connection()
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    return [f"{row['table_schema']}.{row['table_name']}" for row in rows]
