"""PostgreSQL specific tools for metadata discovery and database switching."""

from typing import Dict, List, Union, Any

from fastmcp import FastMCP

from src.param_validator import ensure_non_empty
from src.services import DataSource


def register_postgres_tools(app: FastMCP, connection_manager):
    @app.tool(
        name="list_postgres_databases",
        description="List available PostgreSQL databases.",
    )
    async def list_postgres_databases() -> Union[List[str], Dict[str, str]]:
        try:
            if connection_manager.current_source != DataSource.POSTGRES:
                return {
                    "error": f"Current source is {connection_manager.current_source.value}, not postgres",
                    "action": "Use switch_data_source(source='postgres') first",
                }
            dbs = connection_manager.list_available_databases()
            return dbs if dbs else {"message": "No PostgreSQL databases found"}
        except Exception as exc:
            return {"error": f"Failed to list PostgreSQL databases: {str(exc)}"}

    @app.tool(
        name="list_postgres_schemas",
        description="List available schemas in active PostgreSQL database.",
    )
    async def list_postgres_schemas() -> Union[List[str], Dict[str, str]]:
        try:
            if connection_manager.current_source != DataSource.POSTGRES:
                return {"error": "Current source is not postgres. Use switch_data_source(source='postgres')."}
            schemas = connection_manager.list_available_schemas()
            return schemas if schemas else {"message": "No PostgreSQL schemas found"}
        except Exception as exc:
            return {"error": f"Failed to list PostgreSQL schemas: {str(exc)}"}

    @app.tool(
        name="list_postgres_tables",
        description="List PostgreSQL tables and views for the active database.",
    )
    async def list_postgres_tables(schema: str = "public") -> Union[List[str], Dict[str, str]]:
        try:
            if connection_manager.current_source != DataSource.POSTGRES:
                return {"error": "Current source is not postgres. Use switch_data_source(source='postgres')."}
            tables = connection_manager.list_available_tables(schema=schema)
            return tables if tables else {"message": "No PostgreSQL tables found"}
        except Exception as exc:
            return {"error": f"Failed to list PostgreSQL tables: {str(exc)}"}

    @app.tool(
        name="switch_postgres_database",
        description="Switch active PostgreSQL database.",
    )
    async def switch_postgres_database(database_name: str) -> Dict[str, Any]:
        if error := ensure_non_empty(database_name, "database_name"):
            return error

        try:
            return connection_manager.switch_postgres_database(database_name)
        except Exception as exc:
            return {"error": f"Failed to switch PostgreSQL database: {str(exc)}"}
