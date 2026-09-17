from dataclasses import dataclass

from pypdf import PdfReader


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


@dataclass(frozen=True)
class DocumentChunk:
    text: str
    page_number: int
    chunk_index: int


def extract_pages_from_pdf(file_path: str) -> list[PageText]:
    reader = PdfReader(file_path)
    pages: list[PageText] = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()
        if page_text and page_text.strip():
            pages.append(PageText(page_number=page_number, text=page_text.strip()))
    return pages


def create_chunks_from_pages(
    pages: list[PageText], chunk_size: int = 800, overlap: int = 150
) -> list[DocumentChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    chunks: list[DocumentChunk] = []
    chunk_index = 0
    for page in pages:
        start = 0
        while start < len(page.text):
            text = page.text[start : start + chunk_size].strip()
            if text:
                chunks.append(
                    DocumentChunk(
                        text=text,
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                    )
                )
                chunk_index += 1
            start += chunk_size - overlap
    return chunks


def extract_text_from_pdf(file_path: str) -> str:
    """Compatibility helper for callers that only need the combined text."""
    return "\n".join(page.text for page in extract_pages_from_pdf(file_path)).strip()
