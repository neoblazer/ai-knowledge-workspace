import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from auth import AuthenticatedUser
from schemas import ChatRequest
from services.db_service import get_chat_history, get_document, save_chat_history
from services.gemini_service import AnswerGenerationError, generate_answer_from_context
from services.rag_service import search_relevant_chunks


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])
NO_CONTEXT_ANSWER = "I could not find any relevant content in the selected document."


@router.post("/ask")
def ask_question(request: ChatRequest, user: AuthenticatedUser):
    document = get_document(request.document_id, user.user_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        result = search_relevant_chunks(
            question=request.question,
            document_id=request.document_id,
            user_id=user.user_id,
        )
    except Exception as exc:
        logger.error("Document retrieval failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Unable to search the document right now",
        ) from None

    if not result["chunks"]:
        answer = NO_CONTEXT_ANSWER
    else:
        sections = []
        for chunk, citation in zip(result["chunks"], result["citations"]):
            page_label = f", page {citation['page']}" if citation.get("page") else ""
            sections.append(
                f"[Source: {citation['filename']}{page_label}, chunk {citation['chunk_index']}]\n{chunk}"
            )
        try:
            answer = generate_answer_from_context(request.question, "\n\n".join(sections))
        except AnswerGenerationError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to generate an answer right now. Please try again.",
            ) from None

    try:
        save_chat_history(
            user_id=user.user_id,
            document_id=request.document_id,
            filename=document["filename"],
            question=request.question,
            answer=answer,
            citations=result["citations"],
        )
    except Exception as exc:
        logger.error("Chat history persistence failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="The answer was generated but could not be saved",
        ) from None

    return {
        "question": request.question,
        "document_id": str(request.document_id),
        "answer": answer,
        "citations": result["citations"],
    }


@router.get("/history")
def list_chat_history(
    user: AuthenticatedUser,
    document_id: UUID | None = Query(default=None),
):
    if document_id and not get_document(document_id, user.user_id):
        raise HTTPException(status_code=404, detail="Document not found")
    history = get_chat_history(user.user_id, document_id)
    return {"history": history, "count": len(history)}
