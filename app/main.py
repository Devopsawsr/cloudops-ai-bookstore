from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.ai.schemas import AskRequest, AskResponse
from app.ai.service import build_provider
from app.catalog import BOOKS
from app.config import get_settings
from app.database import Base, engine, get_db
from app.models import AIConversation

settings = get_settings()
app = FastAPI(title="CloudOps AI Bookstore", version="0.1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path("static/index.html"))


@app.get("/health")
def health():
    return {"status": "healthy", "environment": settings.app_env, "ai_provider": settings.ai_provider}


@app.get("/api/books")
def books():
    return {"items": BOOKS, "count": len(BOOKS)}


@app.post("/api/ai/ask", response_model=AskResponse)
def ask(request: AskRequest, db: Session = Depends(get_db)):
    try:
        answer = build_provider(settings).ask(request.question, request.book_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI provider request failed") from exc

    db.add(
        AIConversation(
            session_id=request.session_id,
            book_id=request.book_id,
            question=request.question,
            answer=answer.answer,
            provider=answer.provider,
        )
    )
    db.commit()
    return answer

