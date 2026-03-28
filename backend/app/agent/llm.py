import os
from dotenv import load_dotenv
from pathlib import Path

from typing import Optional
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from ..core.config import settings
env_path = Path(__file__).parent.parent.parent / ".env"
print("env_path llm.py", env_path)
load_dotenv(env_path)

class LLMProvider:
    def __init__(self):
        self.provider = settings.llm_provider
        self.client = None
        self.model = None

    def _setup_client(self):
        if self.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_model

        elif self.provider == "azure_openai":
            if not settings.openai_azure_api_key:
                raise ValueError(
                    "OPENAI_AZURE_API_KEY are required for Azure OpenAI"
                )
            if not settings.openai_azure_endpoint:
                raise ValueError(
                    "OPENAI_AZURE_ENDPOINT are required for Azure OpenAI"
                )
            # Para Azure OpenAI, necesitamos extraer el endpoint base
            base_url = (
                settings.openai_azure_endpoint.rstrip("/")
                + "/openai/deployments/"
                + settings.openai_model
            )
            self.client = AsyncOpenAI(
                api_key=settings.openai_azure_api_key,
                base_url=base_url,
                default_query={"api-version": settings.openai_azure_version},
            )
            self.model = settings.openai_model

        elif self.provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            self.model = settings.anthropic_model
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def generate_response(self, message: str, system_prompt: str) -> str:
        """Generate response from the LLM provider"""
        if not self.client:
            self._setup_client()

        if self.provider == "openai":
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            return response.choices[0].message.content

        elif self.provider == "azure_openai":
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            return response.choices[0].message.content

        elif self.provider == "anthropic":
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": message}],
                temperature=0.3,
            )
            return response.content[0].text

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")


# Global LLM instance (lazy initialization)
llm = LLMProvider()
