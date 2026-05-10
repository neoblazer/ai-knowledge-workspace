import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_service import extract_text_from_pdf
from services.rag_service import store_document_in_chroma
from services.db_service import save_document_metadata, get_all_documents

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "uploads"


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted_text = extract_text_from_pdf(file_path)

    chroma_result = store_document_in_chroma(file.filename, extracted_text)

    saved_document = save_document_metadata(
        filename=file.filename,
        file_path=file_path,
        characters_extracted=len(extracted_text),
        chunks_stored=chroma_result["chunks_stored"],
    )

    return {
        "message": "PDF uploaded, stored in ChromaDB, and metadata saved",
        "filename": file.filename,
        "file_path": file_path,
        "characters_extracted": len(extracted_text),
        "chunks_stored": chroma_result["chunks_stored"],
        "database_record": saved_document,
        "preview": extracted_text[:500],
    }


@router.get("/")
def list_documents():
    documents = get_all_documents()

    return {
        "documents": documents,
        "count": len(documents),
    }