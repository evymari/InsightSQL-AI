import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from main_app.services.azure_openai import ask_ai
from main_app.services.azure_openai import generate_analytic_questions
def home(request):
    return JsonResponse({"message": "API funcionando 🚀"})


@csrf_exempt
def chat_ai(request):

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            question = data.get("q", "")

            if not question:
                return JsonResponse({"error": "No question provided"}, status=400)

            response = ask_ai(question)

            return JsonResponse({"response": response})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST allowed"}, status=405)

# views.py
from django.http import JsonResponse
from .services.azure_openai import generate_analytic_questions

def generate_analytic_questions(request):
    keyword = request.GET.get("keyword", "")  # captura la palabra enviada
    if not keyword:
        return JsonResponse({"questions": []})

    # Aquí puedes reemplazar con tu lógica real de IA o preguntas analíticas
    # Por ejemplo, un ejemplo básico de sugerencias según keyword:
    preguntas = [
        f"¿Cuántas ventas se hicieron relacionadas con {keyword}?",
        f"¿Cuál fue el producto más vendido relacionado con {keyword}?",
        f"¿Cuál es la tendencia de {keyword} en los últimos meses?"
    ]

    return JsonResponse({"questions": preguntas})