"""SQL query tools for executing read-only queries."""

import sys
from typing import Union, List, Dict
from fastmcp import FastMCP
from src.sql_validator import is_readonly_query
from src.param_validator import ensure_non_empty


def register_sql_tools(app: FastMCP, connection_manager):
    """Register SQL-related tools with the FastMCP application.

    Args:
        app: The FastMCP application instance
        connection_manager: The ConnectionManager instance for database operations
    """

    @app.tool(name="saludar_usuario",
        description="Saluda al usuario",
        )
    async def saludar_usuario(name: str) -> str:
        """
        A tool that returns a greeting message
        Args:
            name: The name of the person to greet.
        Returns:
            str: A greeting message for the given name.
        """
        # Validate required parameters
        if error := ensure_non_empty(name, "name"):
            return error
            
        return f"Hello {name}, how are you today?"

    @app.tool(
        name="query",
        description="Executes a read-only SQL query against the active Fabric or PostgreSQL source.",
    )
    async def query(sql: str) -> Union[List[Dict], Dict[str, str]]:
        """Executes a read-only SQL query against the current data source.

        Args:
            sql: The SELECT SQL query to execute.

        Returns:
            A list of dictionaries, where each dictionary represents a row from the query result.
            If no results are found, returns a dictionary with a message.

        Raises:
            FastMCPError: If the query is not a SELECT statement, if database connection fails,
                          or if any other error occurs during query execution.
        """
        # Validate required parameters
        if error := ensure_non_empty(sql, "sql"):
            return error

        if not is_readonly_query(sql):
            return {
                "error": "Invalid Query Type: The provided SQL query is not a read-only SELECT statement. Only SELECT queries are allowed.",
            }

        try:
            # Execute query using the connection manager
            results = connection_manager.execute_query(sql)

            # Check if results are empty
            if not results:
                return {"message": "No results found for the specified query."}

            return results

        except ConnectionError as conn_err:
            error_message = f"Database connection failed: {str(conn_err)}"
            print(error_message, file=sys.stderr)
            return {
                "error": "Database Connection Error: " + error_message,
            }
        except Exception as e:
            error_message = f"An unexpected error occurred during query execution: {str(e)}"
            print(error_message, file=sys.stderr)
            return {
                "error": "Unexpected Server Error: " + error_message,
            }

    @app.tool(
        name="analyze_data_source",
        description="Analyze current data source and provide recommendations for optimization",
    )
    async def analyze_data_source(sql: str) -> Dict[str, any]:
        """Analyze query and data source to provide insights and recommendations.

        Args:
            sql: The SQL query to analyze

        Returns:
            Dictionary with analysis results and recommendations
        """
        # Validate required parameters
        if error := ensure_non_empty(sql, "sql"):
            return error
            
        try:
            if not is_readonly_query(sql):
                return {
                    "error": "Only SELECT queries can be analyzed",
                }

            # Basic query analysis
            analysis = {
                "query_type": "SELECT",
                "estimated_complexity": "unknown",
                "recommendations": [],
                "warnings": []
            }

            # Analyze query patterns
            sql_upper = sql.upper()

            # Check for potential issues
            if "SELECT *" in sql_upper:
                analysis["warnings"].append("Using SELECT * - consider specifying only needed columns")

            if "JOIN" in sql_upper:
                join_count = sql_upper.count("JOIN")
                analysis["estimated_complexity"] = "high" if join_count > 3 else "medium"
                analysis["recommendations"].append(f"Query contains {join_count} JOIN(s) - ensure proper indexing")

            if "WHERE" not in sql_upper and "LIMIT" not in sql_upper:
                analysis["warnings"].append("No WHERE clause or LIMIT - query may return large result set")

            if "DISTINCT" in sql_upper:
                analysis["recommendations"].append("DISTINCT operation can be expensive - consider if it's necessary")

            # Add data source info
            source_info = connection_manager.get_current_source_info()
            analysis["current_source"] = source_info

            return {
                "status": "success",
                "analysis": analysis
            }

        except Exception as e:
            error_message = f"Analysis failed: {str(e)}"
            print(error_message, file=sys.stderr)
            return {
                "error": error_message
            }
