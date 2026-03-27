import pyodbc
import os
import struct
from dotenv import load_dotenv
from azure.identity import AzureCliCredential, InteractiveBrowserCredential, DeviceCodeCredential, ClientSecretCredential, DefaultAzureCredential
import sys

load_dotenv()

# Constants for AAD authentication
SQL_SERVER_SCOPE = "https://database.windows.net/.default"
# SQL_COPT_SS_ACCESS_TOKEN is a constant used by pyodbc to set the access token
# It's defined in msodbcsql.h, usually value is 1256
SQL_COPT_SS_ACCESS_TOKEN = 1256

# Module-level variable for connection reuse
_cached_connection = None

def get_aad_token():
    """Obtains an AAD access token for SQL Server using multi-method strategy."""
    token = None

    # 1. Try Service Principal from environment variables
    if os.getenv("AZURE_TENANT_ID") and os.getenv("AZURE_CLIENT_ID") and os.getenv("AZURE_CLIENT_SECRET"):
        try:
            print(f"Trying Service Principal authentication for SQL Server...", file=sys.stderr)
            credential = ClientSecretCredential(
                tenant_id=os.getenv("AZURE_TENANT_ID"),
                client_id=os.getenv("AZURE_CLIENT_ID"),
                client_secret=os.getenv("AZURE_CLIENT_SECRET")
            )
            token_obj = credential.get_token(SQL_SERVER_SCOPE)
            token = token_obj.token
            print(f"SQL Server token obtained using Service Principal", file=sys.stderr)
            return token
        except Exception as sp_error:
            print(f"Service Principal failed for SQL Server: {sp_error}", file=sys.stderr)
            token = None

    # 2. Try Azure CLI credentials (from az login)
    if not token:
        try:
            print(f"Trying Azure CLI authentication for SQL Server...", file=sys.stderr)
            credential = AzureCliCredential()
            token_obj = credential.get_token(SQL_SERVER_SCOPE)
            token = token_obj.token
            print(f"SQL Server token obtained using Azure CLI", file=sys.stderr)
            return token
        except Exception as cli_error:
            print(f"Azure CLI authentication failed for SQL Server: {cli_error}", file=sys.stderr)
            token = None

    # 3. Try Device Code Flow (works in Docker and headless environments)
    if not token:
        try:
            print(f"Trying Device Code authentication for SQL Server...", file=sys.stderr)
            print(f"You will need to authenticate in a browser on any device", file=sys.stderr)
            credential = DeviceCodeCredential(
                tenant_id=os.getenv("AZURE_TENANT_ID", "ee671ff4-00bc-4321-b324-449896173882")
            )
            token_obj = credential.get_token(SQL_SERVER_SCOPE)
            token = token_obj.token
            print(f"SQL Server token obtained using Device Code", file=sys.stderr)
            return token
        except Exception as device_error:
            print(f"Device Code authentication failed for SQL Server: {device_error}", file=sys.stderr)
            token = None

    # 4. Last resort: DefaultAzureCredential
    if not token:
        try:
            print(f"Trying DefaultAzureCredential for SQL Server as last resort...", file=sys.stderr)
            credential = DefaultAzureCredential()
            token_obj = credential.get_token(SQL_SERVER_SCOPE)
            token = token_obj.token
            print(f"SQL Server token obtained using DefaultAzureCredential", file=sys.stderr)
            return token
        except Exception as e:
            print(f"Error obtaining AAD token: {e}", file=sys.stderr)
            raise ConnectionError(f"Failed to obtain AAD token: {e}") from e

def get_db_connection():
    """Establishes a pyodbc connection to SQL Server using AAD token authentication. Reuses the connection within a session."""
    global _cached_connection
    if _cached_connection is not None:
        try:
            # Check if the connection is still open
            _cached_connection.cursor().execute("SELECT 1")
            return _cached_connection
        except Exception:
            # Connection is closed or invalid, reset it
            _cached_connection = None

    server_name = os.getenv("SQL_SERVER_NAME")
    database_name = os.getenv("SQL_DATABASE_NAME")
    odbc_driver = os.getenv("ODBC_DRIVER", "{ODBC Driver 18 for SQL Server}") # Default to Driver 18

    if not server_name or not database_name:
        raise ConnectionError("SQL_SERVER_NAME and/or SQL_DATABASE_NAME environment variables are not set.")

    try:
        access_token = get_aad_token()
        token_bytes = access_token.encode("utf-16-le")
        token_struct = struct.pack(f"<i{len(token_bytes)}s", len(token_bytes), token_bytes)
        conn_str = f"DRIVER={odbc_driver};SERVER={server_name};DATABASE={database_name};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=2;"
        _cached_connection = pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
        return _cached_connection
    except pyodbc.Error as db_err:
        print(f"PyODBC Error: {db_err}", file=sys.stderr)
        raise ConnectionError(f"Database connection failed: {db_err}") from db_err
    except ConnectionError: # To re-raise ConnectionError from get_aad_token
        raise
    except Exception as e:
        print(f"Error establishing database connection: {e}", file=sys.stderr)
        raise ConnectionError(f"An unexpected error occurred during database connection: {e}") from e


def close_db_connection():
    """Closes the cached database connection, if it exists."""
    global _cached_connection
    if _cached_connection is not None:
        try:
            _cached_connection.close()
        except Exception:
            pass
        _cached_connection = None

def _connect(
    server_name: str,
    database_name: str | None = None,
    odbc_driver: str | None = None,
    timeout: int = 15
):
    """
    Crea y retorna una conexión pyodbc usando AAD (Azure CLI login) con token bearer.
    Si `database_name` es None, conecta sólo al servidor (útil para consultar sys.databases en Azure SQL);
    en Microsoft Fabric normalmente conectas directo a un Warehouse (DB específica).
    """
    driver = odbc_driver or os.getenv("ODBC_DRIVER", "{ODBC Driver 18 for SQL Server}")
    access_token = get_aad_token()
    # En caso de que get_aad_token devuelva un objeto con .token
    if hasattr(access_token, "token"):
        access_token = access_token.token

    token_bytes = access_token.encode("utf-16-le")
    token_struct = struct.pack(f"<i{len(token_bytes)}s", len(token_bytes), token_bytes)

    parts = [f"DRIVER={driver}", f"SERVER={server_name}"]
    if database_name:
        parts.append(f"DATABASE={database_name}")
    parts += [
        "Encrypt=yes",
        "TrustServerCertificate=no",
        f"Connection Timeout={timeout}",
    ]
    conn_str = ";".join(parts) + ";"
    return pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})

# --- NUEVO: utilidades de descubrimiento para Microsoft Fabric (SQL) ---
def list_databases() -> list[str]:
    """
    Lista las bases de datos accesibles en el servidor Fabric/SQL.
    """
    server_name = os.getenv("SQL_SERVER_NAME")
    if not server_name:
        raise ConnectionError("SQL_SERVER_NAME no está definido.")
    
    try:
        # Intenta usar la conexión actual primero
        conn = get_db_connection()
        cur = conn.cursor()
        
        # En Fabric/SQL Server, puedes consultar sys.databases desde cualquier DB
        cur.execute("""
            SELECT name
            FROM sys.databases
            WHERE state = 0 
              AND name NOT IN ('master', 'tempdb', 'model', 'msdb')
            ORDER BY name
        """)
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"Error listing databases with current connection: {e}", file=sys.stderr)
        
        # Fallback: crear conexión temporal al master o sin DB específica
        try:
            driver = os.getenv("ODBC_DRIVER", "{ODBC Driver 18 for SQL Server}")
            conn = _connect(server_name=server_name, database_name="master", 
                          odbc_driver=driver, timeout=15)
            cur = conn.cursor()
            cur.execute("""
                SELECT name
                FROM sys.databases
                WHERE state = 0 
                  AND name NOT IN ('master', 'tempdb', 'model', 'msdb')
                ORDER BY name
            """)
            result = [row[0] for row in cur.fetchall()]
            conn.close()
            return result
        except Exception as e2:
            print(f"Error listing databases with master connection: {e2}", file=sys.stderr)
            raise

def list_schemas(database_name: str | None = None) -> list[str]:
    """Lista schemas en la base dada o en la actual."""
    try:
        # Usa la conexión actual si no se especifica database
        if not database_name:
            conn = get_db_connection()
        else:
            server_name = os.getenv("SQL_SERVER_NAME")
            driver = os.getenv("ODBC_DRIVER", "{ODBC Driver 18 for SQL Server}")
            conn = _connect(server_name=server_name, database_name=database_name, 
                          odbc_driver=driver)
        
        cur = conn.cursor()
        cur.execute("""
            SELECT name 
            FROM sys.schemas 
            WHERE name NOT IN ('sys', 'INFORMATION_SCHEMA', 'guest', 'db_owner', 
                              'db_accessadmin', 'db_securityadmin', 'db_ddladmin',
                              'db_backupoperator', 'db_datareader', 'db_datawriter', 
                              'db_denydatareader', 'db_denydatawriter')
            ORDER BY name
        """)
        result = [row[0] for row in cur.fetchall()]
        
        # Solo cerrar si creamos una conexión nueva
        if database_name:
            conn.close()
            
        return result
    except Exception as e:
        print(f"Error listing schemas: {e}", file=sys.stderr)
        raise

def list_tables(database_name: str | None = None, schema: str | None = None, 
                include_views: bool = True) -> list[str]:
    """Lista tablas y opcionalmente vistas."""
    try:
        if not database_name:
            conn = get_db_connection()
        else:
            server_name = os.getenv("SQL_SERVER_NAME")
            driver = os.getenv("ODBC_DRIVER", "{ODBC Driver 18 for SQL Server}")
            conn = _connect(server_name=server_name, database_name=database_name, 
                          odbc_driver=driver)
        
        cur = conn.cursor()
        
        table_types = "('BASE TABLE', 'VIEW')" if include_views else "('BASE TABLE')"
        
        if schema:
            query = f"""
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE IN {table_types} 
                  AND TABLE_SCHEMA = ?
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            cur.execute(query, schema)
        else:
            query = f"""
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE IN {table_types}
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            cur.execute(query)
        
        result = [f"{r[0]}.{r[1]}" for r in cur.fetchall()]
        
        if database_name:
            conn.close()
            
        return result
    except Exception as e:
        print(f"Error listing tables: {e}", file=sys.stderr)
        raise

def switch_database(new_database: str):
    """
    Fuerza el cambio de base “actual” para futuras conexiones cacheadas.
    """
    global _cached_connection
    os.environ["SQL_DATABASE_NAME"] = new_database
    # invalida la conexión cacheada para que se cree una nueva con la DB elegida
    if _cached_connection is not None:
        try:
            _cached_connection.close()
        except Exception:
            pass
        _cached_connection = None