from fastapi import APIRouter
from pydantic import BaseModel
from services.rag_service import search_relevant_chunks
from services.gemini_service import generate_answer_from_context
from services.db_service import save_chat_history, get_chat_history

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    question: str
    filename: str | None = None


@router.post("/ask")
def ask_question(request: ChatRequest):
    result = search_relevant_chunks(
        question=request.question,
        filename=request.filename,
    )

    context = "\n\n".join(result["chunks"])

    if not context.strip():
        return {
            "question": request.question,
            "answer": "I could not find any relevant content in the selected document.",
            "retrieved_context": "",
            "sources": [],
        }

    answer = generate_answer_from_context(request.question, context)

    save_chat_history(
        filename=request.filename or "Unknown",
        question=request.question,
        answer=answer,
        sources=result["sources"],
    )

    return {
        "question": request.question,
        "answer": answer,
        "retrieved_context": context,
        "sources": result["sources"],
    }


@router.get("/history")
def list_chat_history(filename: str | None = None):
    history = get_chat_history(filename)

    return {
        "history": history,
        "count": len(history),
    }