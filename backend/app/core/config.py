import os
from pathlib import Path
from dotenv import load_dotenv

from typing import Optional
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/insightsql"
    postgres_connection_string: str = "postgresql://postgres:password@localhost:5432/insightsql"

    # MCP / Data source configuration
    mcp_server_url: str = "http://localhost:5000"
    mcp_transport: str = "streamable-http"
    mcp_timeout: int = 30
    mcp_retry_attempts: int = 3
    use_mcp_schema: bool = False
    default_data_source: str = "postgres"

    fabric_connection_string: Optional[str] = None
    fabric_server_name: Optional[str] = None
    fabric_database_name: Optional[str] = None
    fabric_odbc_driver: str = "ODBC Driver 18 for SQL Server"
    
    # LLM Providers
    openai_api_key: Optional[str] = None
    openai_azure_endpoint: Optional[str] = None
    openai_azure_api_key: Optional[str] = None
    openai_azure_version: str = "2024-02-15-preview"
    
    anthropic_api_key: Optional[str] = None
    
    # LLM Configuration
    llm_provider: str = "anthropic"  # Options: anthropic, openai, azure_openai
    openai_model: str = "gpt-4"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    
    # Application
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file=ENV_FILE_PATH
        case_sensitive = False
        env_file_encoding = "utf-8"
        extra = "ignore"   # ← cambia "forbid" por "ignore"


settings = Settings()
