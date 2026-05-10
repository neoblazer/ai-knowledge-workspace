import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing. Please add it in backend/.env")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"


def generate_answer_from_context(question: str, context: str) -> str:
    try:
        prompt = f"""
You are an AI study assistant.

Answer the user's question using ONLY the provided document context.

Rules:
1. If the answer is present in the context, answer clearly.
2. If the answer is not present in the context, say:
   "I could not find this information in the uploaded document."
3. Do not use outside knowledge.
4. Keep the answer simple and useful.

Document Context:
{context}

User Question:
{question}

Answer:
"""

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        if not response or not response.text:
            return "Gemini did not return an answer. Please try again."

        return response.text

    except Exception as e:
        return f"Gemini error: {str(e)}"