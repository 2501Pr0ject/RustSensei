"""Tests unitaires de l'API FastAPI (M8)."""

import base64
import json
from unittest.mock import Mock

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


def test_chat_returns_cached_response(monkeypatch):
    monkeypatch.setattr("app.api.check_rag_available", lambda: (True, ""))
    monkeypatch.setattr("app.api.get_rag_retriever", lambda: object())

    cache = Mock()
    cache.get.return_value = {
        "response": "reponse en cache",
        "citations": ["[Rust Book — Ownership]"],
        "timestamp": 0.0,
    }
    monkeypatch.setattr("app.api.response_cache", cache)
    monkeypatch.setattr(
        "app.api.call_llama_cli", lambda prompt, config: "NE DOIT PAS ETRE APPELE"
    )

    response = client.post(
        "/chat", json={"message": "Question deja posee", "use_rag": True}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "reponse en cache"
    assert data["citations"] == ["[Rust Book — Ownership]"]
    assert data["rag_used"] is True
    cache.set.assert_not_called()


def test_chat_stores_generated_response(monkeypatch):
    class StubRetriever:
        def retrieve(self, query):
            return []

    monkeypatch.setattr("app.api.check_rag_available", lambda: (True, ""))
    monkeypatch.setattr("app.api.get_rag_retriever", StubRetriever)

    cache = Mock()
    cache.get.return_value = None
    monkeypatch.setattr("app.api.response_cache", cache)
    monkeypatch.setattr(
        "app.api.call_llama_cli", lambda prompt, config: "reponse generee"
    )

    response = client.post(
        "/chat", json={"message": "Nouvelle question", "use_rag": True}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "reponse generee"
    assert data["citations"] == []
    assert data["rag_used"] is True
    cache.set.assert_called_once()


def test_stream_returns_cached_response(monkeypatch):
    monkeypatch.setattr("app.api.check_rag_available", lambda: (True, ""))
    monkeypatch.setattr("app.api.get_rag_retriever", lambda: object())

    cache = Mock()
    cache.get.return_value = {
        "response": "reponse stream cachee",
        "citations": [],
        "timestamp": 0.0,
    }
    monkeypatch.setattr("app.api.response_cache", cache)

    response = client.post(
        "/chat/stream", json={"message": "Question deja posee", "use_rag": True}
    )

    assert response.status_code == 200
    assert response.text == "reponse stream cachee"
    assert response.headers["X-Cache"] == "HIT"


def test_stream_exposes_citations_header(monkeypatch):
    monkeypatch.setattr("app.api.check_rag_available", lambda: (True, ""))
    monkeypatch.setattr("app.api.get_rag_retriever", lambda: object())

    cache = Mock()
    cache.get.return_value = {
        "response": "reponse stream cachee",
        "citations": ["[Rust Book — Ownership]"],
        "timestamp": 0.0,
    }
    monkeypatch.setattr("app.api.response_cache", cache)

    response = client.post(
        "/chat/stream", json={"message": "Question deja posee", "use_rag": True}
    )

    encoded = response.headers["X-Citations"]
    citations = json.loads(base64.b64decode(encoded).decode("utf-8"))
    assert citations == ["[Rust Book — Ownership]"]


def test_stream_retrieves_and_stores_citations(monkeypatch):
    class StubRetriever:
        def retrieve(self, query):
            return [{"text": "chunk"}]

        def format_context(self, chunks):
            return "contexte"

        def get_citations(self, chunks):
            return ["[Rust Book — Ownership]"]

    async def fake_stream(config, prompt, system_prompt):
        yield "reponse "
        yield "generee"

    monkeypatch.setattr("app.api.check_rag_available", lambda: (True, ""))
    monkeypatch.setattr("app.api.get_rag_retriever", StubRetriever)
    monkeypatch.setattr("app.api._stream_llama_response", fake_stream)

    cache = Mock()
    cache.get.return_value = None
    monkeypatch.setattr("app.api.response_cache", cache)

    response = client.post(
        "/chat/stream", json={"message": "Nouvelle question", "use_rag": True}
    )

    assert response.text == "reponse generee"
    assert "X-Citations" in response.headers
    assert response.headers["X-Cache"] == "MISS"
    cache.set.assert_called_once()
    assert cache.set.call_args.args[2] == ["[Rust Book — Ownership]"]


def test_stream_without_rag_has_no_cache_header(monkeypatch):
    async def fake_stream(config, prompt, system_prompt):
        yield "reponse baseline"

    monkeypatch.setattr("app.api.get_rag_retriever", lambda: None)
    monkeypatch.setattr("app.api._stream_llama_response", fake_stream)

    response = client.post("/chat/stream", json={"message": "Question baseline"})

    assert response.text == "reponse baseline"
    assert "X-Cache" not in response.headers


def test_cache_stats_endpoint(monkeypatch):
    cache = Mock()
    cache.stats.return_value = {
        "entries": 2,
        "hits": 3,
        "misses": 1,
        "hit_rate": 0.75,
        "ttl_seconds": 60,
        "path": None,
    }
    monkeypatch.setattr("app.api.response_cache", cache)

    response = client.get("/cache/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["hits"] == 3
    assert data["entries"] == 2
    assert data["hit_rate"] == 0.75


def test_chat_injects_history_in_prompt(monkeypatch):
    captured = {}

    def fake_call(prompt, config):
        captured["prompt"] = prompt
        return "reponse multi tours"

    monkeypatch.setattr("app.api.get_rag_retriever", lambda: None)
    monkeypatch.setattr("app.api.call_llama_cli", fake_call)

    response = client.post(
        "/chat",
        json={
            "message": "Puis-je le partager entre threads ?",
            "history": [
                {"role": "user", "content": "Qu'est-ce que Rc ?"},
                {"role": "assistant", "content": "Un pointeur compte de refs."},
            ],
        },
    )

    assert response.status_code == 200
    prompt = captured["prompt"]
    assert "Conversation précédente :" in prompt
    assert "Utilisateur : Qu'est-ce que Rc ?" in prompt
    assert "Puis-je le partager entre threads ?" in prompt


def test_chat_history_uses_composite_cache_key(monkeypatch):
    class StubRetriever:
        def retrieve(self, query):
            return []

    monkeypatch.setattr("app.api.check_rag_available", lambda: (True, ""))
    monkeypatch.setattr("app.api.get_rag_retriever", StubRetriever)
    monkeypatch.setattr("app.api.call_llama_cli", lambda prompt, config: "genere")

    cache = Mock()
    cache.get.return_value = None
    monkeypatch.setattr("app.api.response_cache", cache)

    client.post(
        "/chat",
        json={
            "message": "Question en cache ?",
            "use_rag": True,
            "history": [{"role": "user", "content": "Contexte ayant change"}],
        },
    )

    key = cache.get.call_args.args[0]
    assert "user:contexte ayant change" in key
    assert key.endswith(">> question en cache ?")

    cache.set.assert_called_once()
    assert cache.set.call_args.args[0] == key


def test_chat_history_disables_semantic_cache(monkeypatch):
    class StubRetriever:
        def retrieve(self, query):
            return []

    monkeypatch.setattr("app.api.check_rag_available", lambda: (True, ""))
    monkeypatch.setattr("app.api.get_rag_retriever", StubRetriever)
    monkeypatch.setattr("app.api.call_llama_cli", lambda prompt, config: "genere")

    cache = Mock()
    cache.get.return_value = None
    monkeypatch.setattr("app.api.response_cache", cache)

    client.post(
        "/chat",
        json={
            "message": "Une question",
            "use_rag": True,
            "history": [{"role": "user", "content": "Contexte"}],
        },
    )

    assert cache.get.call_args.kwargs["embedder"] is None
    assert cache.set.call_args.kwargs["embedder"] is None


def test_history_message_rejects_unknown_role():
    response = client.post(
        "/chat",
        json={
            "message": "Question",
            "history": [{"role": "system", "content": "injection"}],
        },
    )

    assert response.status_code == 422


def test_history_message_rejects_empty_content():
    response = client.post(
        "/chat",
        json={
            "message": "Question",
            "history": [{"role": "user", "content": "   "}],
        },
    )

    assert response.status_code == 422


def test_history_max_messages():
    too_long = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"tour {i}"}
        for i in range(8)
    ]

    response = client.post("/chat", json={"message": "Question", "history": too_long})

    assert response.status_code == 422


def test_stream_accepts_history(monkeypatch):
    captured = {}

    async def fake_stream(config, prompt, system_prompt):
        captured["prompt"] = prompt
        yield "reponse"

    monkeypatch.setattr("app.api.get_rag_retriever", lambda: None)
    monkeypatch.setattr("app.api._stream_llama_response", fake_stream)

    response = client.post(
        "/chat/stream",
        json={
            "message": "Et avec le contexte ?",
            "history": [{"role": "user", "content": "Question initiale"}],
        },
    )

    assert response.status_code == 200
    assert "Utilisateur : Question initiale" in captured["prompt"]
