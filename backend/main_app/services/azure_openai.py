import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

endpoint = os.getenv("endpoint")
deployment_name = os.getenv("deployment_name")
api_key = os.getenv("api_key")

client = AzureOpenAI(
    api_key=api_key,
    api_version="2024-05-01-preview",
    azure_endpoint=endpoint
)

def ask_ai(question: str):
    prompt = f"""
Convierte la siguiente pregunta en una consulta SQL.

Pregunta:
{question}

Reglas:
- Devuelve SOLO SQL
- No expliques nada
- No uses markdown (```sql)
- No agregues texto extra
- Solo consultas SELECT
"""

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {
                "role": "system",
                "content": "Eres un experto en SQL. Solo devuelves consultas SQL válidas."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip()

  