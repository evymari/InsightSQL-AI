import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra='ignore'
    )
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/insightsql"
    
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

settings = Settings()
