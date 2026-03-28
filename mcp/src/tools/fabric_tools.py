"""Microsoft Fabric specific tools for managing databases, schemas and tables."""

import sys
from typing import Union, List, Dict, Any
from fastmcp import FastMCP
from src.services import DataSource
from src.param_validator import ensure_non_empty


def register_fabric_tools(app: FastMCP, connection_manager):
    """Register Microsoft Fabric tools with the FastMCP application.

    Args:
        app: The FastMCP application instance
        connection_manager: The ConnectionManager instance for database operations
    """

    @app.tool(
        name="list_fabric_databases",
        description="Lista las bases de datos disponibles en el servidor Fabric/SQL."
    )
    async def list_fabric_databases() -> Union[List[str], Dict[str, str]]:
        try:
            if connection_manager.current_source != DataSource.FABRIC:
                return {
                    "error": f"Current source is {connection_manager.current_source.value}, not fabric",
                    "action": "Use switch_data_source(source='fabric') first",
                }

            dbs = connection_manager.list_available_databases()

            if not dbs:
                return {
                    "message": "No databases found",
                    "possible_reasons": [
                        "No permissions to view system databases",
                        "Connection issue with SQL Server",
                        "Check SQL_SERVER_NAME environment variable"
                    ]
                }

            return dbs

        except Exception as e:
            print(f"Error in list_fabric_databases: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return {"error": f"Failed to list Fabric databases: {str(e)}"}

    @app.tool(
        name="list_fabric_schemas",
        description="Lista los schemas disponibles en la base actual de Fabric."
    )
    async def list_fabric_schemas() -> Union[List[str], Dict[str, str]]:
        try:
            if connection_manager.current_source != DataSource.FABRIC:
                return {"error": "Current source is not fabric. Use switch_data_source(source='fabric')."}
            schemas = connection_manager.list_available_schemas()
            return schemas if schemas else {"message": "No se encontraron schemas"}
        except Exception as e:
            return {"error": f"Failed to list Fabric schemas: {str(e)}"}

    @app.tool(
        name="list_fabric_tables",
        description="Lista tablas (y vistas) disponibles en la base actual de Fabric."
    )
    async def list_fabric_tables() -> Union[List[str], Dict[str, str]]:
        try:
            if connection_manager.current_source != DataSource.FABRIC:
                return {"error": "Current source is not fabric. Use switch_data_source(source='fabric')."}
            tables = connection_manager.list_available_tables()
            return tables if tables else {"message": "No se encontraron tablas"}
        except Exception as e:
            return {"error": f"Failed to list Fabric tables: {str(e)}"}

    @app.tool(
        name="switch_fabric_database",
        description="Cambia la base de datos activa para Fabric."
    )
    async def switch_fabric_database(database_name: str) -> Dict[str, Any]:
        # Validate required parameters
        if error := ensure_non_empty(database_name, "database_name"):
            return error
            
        try:
            return connection_manager.switch_fabric_database(database_name)
        except Exception as e:
            return {"error": f"Failed to switch Fabric database: {str(e)}"}
