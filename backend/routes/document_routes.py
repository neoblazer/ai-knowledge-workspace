import logging
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pypdf.errors import PdfReadError

from auth import AuthenticatedUser
from config import get_settings
from services.db_service import (
    delete_chat_history_for_document,
    delete_document_metadata,
    get_all_documents,
    get_document,
    save_document_metadata,
)
from services.pdf_service import create_chunks_from_pages, extract_pages_from_pdf
from services.rag_service import delete_document_from_chroma, store_document_in_chroma


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])
PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}


def _safe_display_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="A filename is required")
    safe_name = Path(filename).name.strip()
    if not safe_name or safe_name in {".", ".."} or "\x00" in safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    return safe_name


def _remove_file_if_safe(file_path: Path) -> None:
    upload_dir = get_settings().upload_dir.resolve()
    resolved = file_path.resolve()
    if resolved.is_relative_to(upload_dir) and resolved.is_file():
        resolved.unlink()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_pdf(user: AuthenticatedUser, file: UploadFile = File(...)):
    settings = get_settings()
    filename = _safe_display_filename(file.filename)
    if file.content_type and file.content_type.lower() not in PDF_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="The uploaded file is not a PDF")

    contents = await file.read(settings.max_upload_size_bytes + 1)
    await file.close()
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    if len(contents) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The uploaded PDF exceeds the configured size limit",
        )
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF")

    document_id = uuid4()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = settings.upload_dir / f"{document_id}.pdf"
    vectors_stored = False

    try:
        file_path.write_bytes(contents)
        pages = extract_pages_from_pdf(str(file_path))
        chunks = create_chunks_from_pages(
            pages,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        if not chunks:
            raise HTTPException(status_code=422, detail="The PDF contains no extractable text")

        chroma_result = store_document_in_chroma(
            document_id=document_id,
            user_id=user.user_id,
            filename=filename,
            chunks=chunks,
        )
        vectors_stored = True
        characters_extracted = sum(len(page.text) for page in pages)
        save_document_metadata(
            document_id=document_id,
            user_id=user.user_id,
            filename=filename,
            file_path=str(file_path),
            characters_extracted=characters_extracted,
            chunks_stored=chroma_result["chunks_stored"],
        )
    except PdfReadError:
        _remove_file_if_safe(file_path)
        raise HTTPException(status_code=422, detail="The PDF could not be read") from None
    except HTTPException:
        _remove_file_if_safe(file_path)
        raise
    except Exception as exc:
        if vectors_stored:
            try:
                delete_document_from_chroma(document_id, user.user_id)
            except Exception:
                logger.error("Failed to roll back vector data for document %s", document_id)
        _remove_file_if_safe(file_path)
        logger.error("Document ingestion failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Unable to process the PDF right now",
        ) from None

    return {
        "message": "PDF uploaded and indexed successfully",
        "document_id": str(document_id),
        "filename": filename,
        "characters_extracted": characters_extracted,
        "chunks_stored": chroma_result["chunks_stored"],
        "preview": pages[0].text[:500],
    }


@router.get("/")
def list_documents(user: AuthenticatedUser):
    documents = get_all_documents(user.user_id)
    return {"documents": documents, "count": len(documents)}


@router.delete("/{document_id}")
def delete_document(document_id: UUID, user: AuthenticatedUser):
    document = get_document(document_id, user.user_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        delete_document_from_chroma(document_id, user.user_id)
        delete_chat_history_for_document(document_id, user.user_id)
        stored_path = document.get("file_path")
        if stored_path:
            _remove_file_if_safe(Path(stored_path))
        delete_document_metadata(document_id, user.user_id)
    except Exception as exc:
        logger.error("Document deletion failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Unable to delete the document right now",
        ) from None
    return {"message": "Document deleted successfully", "document_id": str(document_id)}
