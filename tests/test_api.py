"""Tests unitaires de l'API FastAPI (M8)."""

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_without_rag(monkeypatch):
    monkeypatch.setattr("app.api.check_rag_available", lambda: (True, ""))
    monkeypatch.setattr("app.api.get_rag_retriever", lambda: None)
    monkeypatch.setattr("app.api.call_llama_cli", lambda prompt, config: "reponse mockee")

    response = client.post("/chat", json={"message": "Pourquoi ce code ne compile pas ?"})

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "reponse mockee"
    assert data["rag_used"] is False
