"""Connection manager for Fabric and PostgreSQL data sources."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List
import os
import sys
from dotenv import load_dotenv

load_dotenv()

class DataSource(Enum):
    FABRIC = "fabric"
    POSTGRES = "postgres"


class ConnectionManager:
    """Manage active data source and route operations to the right backend service."""

    def __init__(self) -> None:
        default_source = os.getenv("MCP_DEFAULT_SOURCE", "postgres").strip().lower()
        self.current_source = DataSource.FABRIC if default_source == "fabric" else DataSource.POSTGRES

    def set_data_source(self, source: str, database_name: str | None = None, **_: Any) -> Dict[str, str]:
        source_lower = (source or "").strip().lower()
        print(f"ConnectionManager: switching source to {source_lower}", file=sys.stderr)

        if source_lower == DataSource.FABRIC.value:
            self.current_source = DataSource.FABRIC
            if database_name:
                from .db_connection import switch_database

                switch_database(database_name)
            return {"status": "success", "source": "fabric", "message": "Switched to Microsoft Fabric"}

        if source_lower == DataSource.POSTGRES.value:
            self.current_source = DataSource.POSTGRES
            if database_name:
                from .postgres_connection import switch_postgres_database

                switch_postgres_database(database_name)
            return {"status": "success", "source": "postgres", "message": "Switched to PostgreSQL"}

        raise ValueError("Unknown data source. Use 'fabric' or 'postgres'.")

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        if self.current_source == DataSource.FABRIC:
            connection = self.get_connection()
            cursor = connection.cursor()
            try:
                cursor.execute(sql)
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            finally:
                cursor.close()

        from .postgres_connection import execute_query as execute_postgres_query

        return execute_postgres_query(sql)

    def execute_ddl(self, sql: str) -> Dict[str, Any]:
        if self.current_source == DataSource.FABRIC:
            connection = self.get_connection()
            cursor = connection.cursor()
            try:
                cursor.execute(sql)
                if hasattr(connection, "commit"):
                    connection.commit()
                rows_affected = cursor.rowcount if hasattr(cursor, "rowcount") else 0
                return {"success": True, "rows_affected": rows_affected, "data_source": "fabric"}
            finally:
                cursor.close()

        from .postgres_connection import execute_ddl as execute_postgres_ddl

        return execute_postgres_ddl(sql)

    def get_connection(self):
        if self.current_source == DataSource.FABRIC:
            from .db_connection import get_db_connection

            return get_db_connection()

        from .postgres_connection import get_postgres_connection

        return get_postgres_connection()

    def get_current_source_info(self) -> Dict[str, Any]:
        if self.current_source == DataSource.FABRIC:
            return {
                "source": "fabric",
                "type": "Microsoft Fabric",
                "database": os.getenv("SQL_DATABASE_NAME"),
                "server": os.getenv("SQL_SERVER_NAME"),
            }

        return {
            "source": "postgres",
            "type": "PostgreSQL",
            "database": os.getenv("POSTGRES_DB"),
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
        }

    def list_available_databases(self) -> List[str]:
        if self.current_source == DataSource.FABRIC:
            from .db_connection import list_databases

            return list_databases()

        from .postgres_connection import list_databases as list_postgres_databases

        return list_postgres_databases()

    def list_available_schemas(self, schema: str | None = None) -> List[str]:
        if self.current_source == DataSource.FABRIC:
            from .db_connection import list_schemas

            return list_schemas()

        from .postgres_connection import list_schemas as list_postgres_schemas

        # The schema argument is ignored here because this method lists schemas.
        _ = schema
        return list_postgres_schemas()

    def list_available_tables(self, schema: str | None = None) -> List[str]:
        if self.current_source == DataSource.FABRIC:
            from .db_connection import list_tables

            return list_tables(schema=schema)

        from .postgres_connection import list_tables as list_postgres_tables

        return list_postgres_tables(schema=schema)

    def switch_fabric_database(self, database_name: str) -> Dict[str, Any]:
        from .db_connection import switch_database

        switch_database(database_name)
        return {"status": "success", "source": "fabric", "message": f"Switched Fabric database to '{database_name}'"}

    def switch_postgres_database(self, database_name: str) -> Dict[str, Any]:
        from .postgres_connection import switch_postgres_database

        switch_postgres_database(database_name)
        return {"status": "success", "source": "postgres", "message": f"Switched PostgreSQL database to '{database_name}'"}

    def close_all_connections(self) -> None:
        try:
            from .db_connection import close_db_connection
            from .postgres_connection import close_postgres_connection

            close_db_connection()
            close_postgres_connection()
        except Exception as exc:
            print(f"Error closing connections: {exc}", file=sys.stderr)
