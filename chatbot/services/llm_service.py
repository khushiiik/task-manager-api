import google.generativeai as genai
from django.conf import settings

genai.configure(api_key=settings.GEMINI_API_KEY)


def generate_response(prompt: str, system_instruction: str = None) -> str:

    model = genai.GenerativeModel(
        model_name="gemini-flash-latest", system_instruction=system_instruction
    )
    response = model.generate_content(prompt)
    return response.text


def generate_embeddings(text: str) -> list[float]:
    result = genai.embed_content(
        model="models/gemini-embedding-001", content=text, task_type="retrieval_document"
    )
    return result["embedding"]


def chat_with_tools(prompt: str, tools: list, system_instruction: str = None) -> str:
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        tools=tools,
        system_instruction=system_instruction,
    )
    chat = model.start_chat(enable_automatic_function_calling=True)
    response = chat.send_message(prompt)
    return response.text