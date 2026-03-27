"""DDL (Data Definition Language) tools for creating tables, views, and managing schema.

IMPORTANT: These tools execute DDL statements that modify database schema.
Use with caution and ensure proper permissions.
"""

import sys
from typing import Dict, Any
from fastmcp import FastMCP
from src.param_validator import ensure_non_empty


def register_ddl_tools(app: FastMCP, connection_manager):
    """Register DDL tools with the FastMCP application.

    Args:
        app: The FastMCP application instance
        connection_manager: The ConnectionManager instance for database operations
    """

    @app.tool(
        name="execute_ddl",
        description="Execute DDL statements (CREATE, ALTER, DROP) with safety validations",
    )
    async def execute_ddl(sql: str) -> Dict[str, Any]:
        """Execute a DDL statement with safety validations.

        Args:
            sql: The DDL SQL statement to execute

        Returns:
            Dictionary with execution status and details
        """
        # Validate required parameters
        if error := ensure_non_empty(sql, "sql"):
            return error
            
        try:
            # Basic safety validations
            sql_upper = sql.strip().upper()

            # Check if it's a DDL statement
            if not any(sql_upper.startswith(cmd) for cmd in ['CREATE', 'ALTER', 'DROP']):
                return {
                    "error": "Only DDL statements (CREATE, ALTER, DROP) are allowed",
                    "suggestion": "Use the query tool for SELECT statements"
                }

            # Warn about DROP statements
            if sql_upper.startswith('DROP'):
                return {
                    "warning": "DROP statements are destructive and permanently delete objects",
                    "message": "Please confirm this is intentional. This tool requires additional confirmation for DROP statements."
                }

            # Execute DDL
            result = connection_manager.execute_ddl(sql)
            return result

        except Exception as e:
            error_message = f"Failed to execute DDL: {str(e)}"
            print(error_message, file=sys.stderr)
            return {"error": error_message}

    @app.tool(
        name="validate_ddl",
        description="Validate DDL syntax without executing",
    )
    async def validate_ddl(sql: str) -> Dict[str, Any]:
        """Validate DDL syntax without executing the statement.

        Args:
            sql: The DDL SQL statement to validate

        Returns:
            Dictionary with validation results
        """
        # Validate required parameters
        if error := ensure_non_empty(sql, "sql"):
            return error
            
        try:
            sql_upper = sql.strip().upper()

            validations = {
                "is_ddl": any(sql_upper.startswith(cmd) for cmd in ['CREATE', 'ALTER', 'DROP']),
                "is_destructive": sql_upper.startswith('DROP'),
                "statement_type": None,
                "warnings": [],
                "suggestions": []
            }

            if sql_upper.startswith('CREATE'):
                validations["statement_type"] = "CREATE"
            elif sql_upper.startswith('ALTER'):
                validations["statement_type"] = "ALTER"
                validations["warnings"].append("ALTER statements modify existing objects")
            elif sql_upper.startswith('DROP'):
                validations["statement_type"] = "DROP"
                validations["warnings"].append("DROP statements permanently delete objects")
            else:
                validations["suggestions"].append("This does not appear to be a DDL statement")

            return {
                "status": "success",
                "validations": validations
            }

        except Exception as e:
            error_message = f"Failed to validate DDL: {str(e)}"
            print(error_message, file=sys.stderr)
            return {"error": error_message}

    @app.tool(
        name="create_table_from_query",
        description="Create a new table from a SELECT query result",
    )
    async def create_table_from_query(
        table_name: str,
        select_query: str,
        schema: str = "dbo"
    ) -> Dict[str, Any]:
        """Create a new table from SELECT query results (CREATE TABLE AS SELECT).

        Args:
            table_name: Name for the new table
            select_query: SELECT query to populate the table
            schema: Schema name (default: "dbo")

        Returns:
            Dictionary with creation status
        """
        try:
            # Validate query is a SELECT
            if not select_query.strip().upper().startswith('SELECT'):
                return {"error": "Only SELECT queries are allowed"}

            source = connection_manager.get_current_source_info().get("source", "fabric")
            if source == "postgres":
                ddl = f"CREATE TABLE {schema}.{table_name} AS {select_query}"
            else:
                ddl = f"SELECT * INTO [{schema}].[{table_name}] FROM ({select_query}) AS source_query"

            result = connection_manager.execute_ddl(ddl)
            return result

        except Exception as e:
            error_message = f"Failed to create table from query: {str(e)}"
            print(error_message, file=sys.stderr)
            return {"error": error_message}

    @app.tool(
        name="create_view_from_query",
        description="Create a view from a SELECT query",
    )
    async def create_view_from_query(
        view_name: str,
        select_query: str,
        schema: str = "dbo",
        replace_existing: bool = False
    ) -> Dict[str, Any]:
        """Create a view from a SELECT query.

        Args:
            view_name: Name for the new view
            select_query: SELECT query that defines the view
            schema: Schema name (default: "dbo")
            replace_existing: Whether to drop and recreate if view exists

        Returns:
            Dictionary with creation status
        """
        try:
            # Validate query is a SELECT
            if not select_query.strip().upper().startswith('SELECT'):
                return {"error": "Only SELECT queries are allowed"}

            source = connection_manager.get_current_source_info().get("source", "fabric")

            # Construct CREATE VIEW statement
            if replace_existing:
                if source == "postgres":
                    drop_ddl = f"DROP VIEW IF EXISTS {schema}.{view_name}"
                else:
                    drop_ddl = f"DROP VIEW IF EXISTS [{schema}].[{view_name}]"
                connection_manager.execute_ddl(drop_ddl)

            if source == "postgres":
                create_ddl = f"CREATE VIEW {schema}.{view_name} AS {select_query}"
            else:
                create_ddl = f"CREATE VIEW [{schema}].[{view_name}] AS {select_query}"

            result = connection_manager.execute_ddl(create_ddl)
            return result

        except Exception as e:
            error_message = f"Failed to create view: {str(e)}"
            print(error_message, file=sys.stderr)
            return {"error": error_message}

    @app.tool(
        name="get_ddl_templates",
        description="Get DDL statement templates for common scenarios",
    )
    async def get_ddl_templates() -> Dict[str, Any]:
        """Get DDL templates for common database operations.

        Returns:
            Dictionary with DDL templates
        """
        current_source = connection_manager.get_current_source_info().get("source", "fabric")

        fabric_templates = {
            "create_table": """
CREATE TABLE [schema].[table_name] (
    id INT PRIMARY KEY IDENTITY(1,1),
    name NVARCHAR(100) NOT NULL,
    created_date DATETIME2 DEFAULT GETDATE()
);
            """,
            "create_view": """
CREATE VIEW [schema].[view_name] AS
SELECT
    column1,
    column2,
    column3
FROM [schema].[source_table]
WHERE condition = 'value';
            """,
            "add_column": """
ALTER TABLE [schema].[table_name]
ADD new_column NVARCHAR(50) NULL;
            """,
            "create_index": """
CREATE INDEX idx_table_column
ON [schema].[table_name] (column_name);
            """,
            "drop_table": """
DROP TABLE IF EXISTS [schema].[table_name];
            """,
            "create_table_from_select": """
SELECT * INTO [schema].[new_table]
FROM (
    SELECT col1, col2
    FROM [schema].[source_table]
) AS source;
            """
        }

        postgres_templates = {
            "create_table": """
CREATE TABLE schema.table_name (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
            """,
            "create_view": """
CREATE OR REPLACE VIEW schema.view_name AS
SELECT
    column1,
    column2,
    column3
FROM schema.source_table
WHERE condition = 'value';
            """,
            "add_column": """
ALTER TABLE schema.table_name
ADD COLUMN new_column VARCHAR(50);
            """,
            "create_index": """
CREATE INDEX idx_table_column
ON schema.table_name (column_name);
            """,
            "drop_table": """
DROP TABLE IF EXISTS schema.table_name;
            """,
            "create_table_from_select": """
CREATE TABLE schema.new_table AS
SELECT col1, col2
FROM schema.source_table;
            """,
        }

        templates = postgres_templates if current_source == "postgres" else fabric_templates

        return {
            "status": "success",
            "source": current_source,
            "templates": templates,
            "usage_notes": [
                "Replace [schema] and [table_name] with actual names",
                "Always use validation before executing DDL",
                "Test DDL in a development environment first",
                "Be cautious with DROP statements"
            ]
        }
