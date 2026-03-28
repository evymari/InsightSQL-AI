"""Connection management tools for switching between Fabric and PostgreSQL."""

from typing import Dict, Any
from fastmcp import FastMCP


def register_connection_tools(app: FastMCP, connection_manager):
    """Register connection management tools with the FastMCP application.

    Args:
        app: The FastMCP application instance
        connection_manager: The ConnectionManager instance for database operations
    """

    @app.tool(
        name="switch_data_source",
        description="Switch active data source between Fabric and PostgreSQL",
    )
    async def switch_data_source(
        source: str,
        database_name: str = None,
        catalog: str = None,
        schema: str = None,
        storage_account: str = None,
        filesystem: str = None,
    ) -> Dict[str, str]:
        """Switch active source.

        Args:
            source: Target source ('fabric' or 'postgres')
            database_name: Optional target database for the selected source
            catalog: Legacy parameter accepted for compatibility
            schema: Legacy parameter accepted for compatibility
            storage_account: Legacy parameter accepted for compatibility
            filesystem: Legacy parameter accepted for compatibility

        Returns:
            A dictionary with status information about the connection switch.
        """
        try:
            legacy_database = database_name or catalog
            _ = (schema, storage_account, filesystem)
            result = connection_manager.set_data_source(source=source, database_name=legacy_database)
            return result
        except Exception as e:
            return {"error": f"Failed to switch data source: {str(e)}"}

    @app.tool(
        name="get_current_source",
        description="Get information about the current data source connection",
    )
    async def get_current_source() -> Dict[str, Any]:
        """Get information about the current data source connection.

        Returns:
            A dictionary with information about the current connection.
        """
        try:
            return connection_manager.get_current_source_info()
        except Exception as e:
            return {"error": f"Failed to get connection info: {str(e)}"}

    @app.tool(
        name="get_current_connection",
        description="Compatibility alias for get_current_source",
    )
    async def get_current_connection() -> Dict[str, Any]:
        return await get_current_source()
