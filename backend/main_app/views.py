from django.http import JsonResponse
from main_app.services.azure_openai import ask_ai

def home(request):
    return JsonResponse({"message": "API funcionando 🚀"})

def chat_ai(request):
    question = request.GET.get("q", "")

    if not question:
        return JsonResponse({"error": "No question provided"}, status=400)

    response = ask_ai(question)

    return JsonResponse({"response": response})