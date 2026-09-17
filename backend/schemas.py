from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    document_id: UUID

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question must contain text")
        return value


class Citation(BaseModel):
    document_id: UUID
    filename: str
    page: int | None = None
    chunk_index: int
    distance: float | None = None
