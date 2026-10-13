from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    book_id: str | None = None
    session_id: str = Field(default="anonymous", max_length=64)


class AskResponse(BaseModel):
    answer: str
    provider: str
    citations: list[str] = []

