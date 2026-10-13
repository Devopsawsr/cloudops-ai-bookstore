import os

os.environ["DATABASE_URL"] = "sqlite:///./test-cloudops.db"
os.environ["AI_PROVIDER"] = "mock"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_catalog():
    with TestClient(app) as client:
        response = client.get("/api/books")
    assert response.status_code == 200
    assert response.json()["count"] >= 6


def test_mock_ai_question():
    with TestClient(app) as client:
        response = client.post(
            "/api/ai/ask",
            json={"question": "Explain readiness probes", "book_id": "kubernetes", "session_id": "test"},
        )
    assert response.status_code == 200
    assert response.json()["provider"] == "mock"

