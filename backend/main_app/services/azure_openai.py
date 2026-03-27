# services/azure_openai.py
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import json, re

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
            {"role": "system", "content": "Eres un experto en SQL. Solo devuelves consultas SQL válidas."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()


# services/azure_openai.py
def generate_analytic_questions(keyword=""):
    """
    Genera preguntas analíticas que se pueden convertir en SQL,
    filtradas o inspiradas en una palabra clave.
    """
    prompt = f"""
You are a business data analysis assistant.
Generate 5 clear analytic questions that can be converted into SQL queries.
Focus on the keyword: '{keyword}'.
Return only the list of questions, without explanations or markdown.

Example output: ["Total sales by region", "Number of new customers this month"]
    """
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "You are an expert in data analysis and SQL. Only return analytic questions."},
            {"role": "user", "content": prompt}
        ]
    )
    text = response.choices[0].message.content.strip()
    
    try:
        questions = json.loads(text)
    except:
        import re
        questions = re.findall(r'"([^"]+)"', text)
    
    return questions