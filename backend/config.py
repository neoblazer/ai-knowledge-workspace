import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _csv(name: str, default: str = "") -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, default).split(",") if item.strip())


def _path(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default))
    return (value if value.is_absolute() else BASE_DIR / value).resolve()


def _optional_float(name: str) -> float | None:
    value = os.getenv(name, "").strip()
    return float(value) if value else None


@dataclass(frozen=True)
class Settings:
    allowed_origins: tuple[str, ...]
    clerk_secret_key: str
    clerk_jwt_key: str
    clerk_authorized_parties: tuple[str, ...]
    supabase_url: str
    supabase_key: str
    gemini_api_key: str
    upload_dir: Path
    chroma_path: Path
    max_upload_size_bytes: int
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    rag_top_k: int
    rag_max_distance: float | None
    gemini_model: str


@lru_cache
def get_settings() -> Settings:
    allowed_origins = _csv("ALLOWED_ORIGINS", "http://localhost:5173")
    upload_dir = _path("UPLOAD_DIR", "uploads")
    chroma_path = _path("CHROMA_PATH", "chroma_db")
    chunk_size = max(1, int(os.getenv("CHUNK_SIZE", "800")))
    chunk_overlap = max(0, int(os.getenv("CHUNK_OVERLAP", "150")))
    if chunk_overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")

    return Settings(
        allowed_origins=allowed_origins,
        clerk_secret_key=os.getenv("CLERK_SECRET_KEY", "").strip(),
        clerk_jwt_key=os.getenv("CLERK_JWT_KEY", "").replace("\\n", "\n").strip(),
        clerk_authorized_parties=_csv(
            "CLERK_AUTHORIZED_PARTIES", ",".join(allowed_origins)
        ),
        supabase_url=os.getenv("SUPABASE_URL", "").strip(),
        supabase_key=(
            os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_KEY", "").strip()
        ),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        upload_dir=upload_dir,
        chroma_path=chroma_path,
        max_upload_size_bytes=int(float(os.getenv("MAX_UPLOAD_SIZE_MB", "10")) * 1024 * 1024),
        embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2").strip(),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        rag_top_k=max(1, int(os.getenv("RAG_TOP_K", "3"))),
        rag_max_distance=_optional_float("RAG_MAX_DISTANCE"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
    )
