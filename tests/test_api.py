"""Tests unitaires de l'API FastAPI (M8)."""

import base64
import json
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_health(monkeypatch):
    monkeypatch.setattr("app.api.check_rag_available", lambda: (True, ""))

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert {k: data[k] for k in ("status", "rag_available", "rag_error")} == {
        "status": "ok",
        "rag_available": True,
        "rag_error": None,
    }
    assert set(data["llama_server"]) == {"running", "model", "ctx", "last_load_seconds", "loads"}


def test_health_reports_missing_rag_index(monkeypatch):
    monkeypatch.setattr(
        "app.api.check_rag_available", lambda: (False, "Index FAISS non trouvé")
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["rag_available"] is False
    assert response.json()["rag_error"] == "Index FAISS non trouvé"


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


def test_stream_sends_unformatted_user_content(monkeypatch):
    """llama-server applique le template : pas de ChatML dans le message user."""
    captured = {}

    async def fake_stream(config, user_content, system_prompt):
        captured["user_content"] = user_content
        captured["system"] = system_prompt
        yield "reponse"

    monkeypatch.setattr("app.api.get_rag_retriever", lambda: None)
    monkeypatch.setattr("app.api._stream_llama_response", fake_stream)

    response = client.post("/chat/stream", json={"message": "Qu'est-ce qu'un Rc ?"})

    assert response.status_code == 200
    assert "<|im_start|>" not in captured["user_content"]
    assert "Tu es RustSensei" not in captured["user_content"]
    assert captured["user_content"] == "Qu'est-ce qu'un Rc ?"
    assert "Tu es RustSensei" in captured["system"]


def test_long_history_is_truncated_not_rejected(monkeypatch):
    """Des reponses longues dans l'historique ne doivent pas provoquer de 422."""
    captured = {}

    async def fake_stream(config, user_content, system_prompt):
        captured["user_content"] = user_content
        yield "reponse"

    monkeypatch.setattr("app.api.get_rag_retriever", lambda: None)
    monkeypatch.setattr("app.api._stream_llama_response", fake_stream)

    history = [
        {"role": "user", "content": "Question 1"},
        {"role": "assistant", "content": "A" * 2300},
        {"role": "user", "content": "Question 2"},
        {"role": "assistant", "content": "B" * 2000},
        {"role": "user", "content": "Question 3"},
        {"role": "assistant", "content": "C" * 1500},
    ]

    response = client.post(
        "/chat/stream", json={"message": "Suite ?", "history": history}
    )

    assert response.status_code == 200
    assert "Utilisateur : Question 1" in captured["user_content"]
    assert "[…]" in captured["user_content"]
    assert "A" * 2300 not in captured["user_content"]


def test_chat_rag_unavailable_returns_503(monkeypatch):
    monkeypatch.setattr(
        "app.api.check_rag_available", lambda: (False, "index absent")
    )

    response = client.post("/chat", json={"message": "Question", "use_rag": True})

    assert response.status_code == 503
    assert response.json()["detail"] == "RAG indisponible: index absent"


def test_stream_rag_unavailable_returns_503(monkeypatch):
    monkeypatch.setattr(
        "app.api.check_rag_available", lambda: (False, "index absent")
    )

    response = client.post(
        "/chat/stream", json={"message": "Question", "use_rag": True}
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "RAG indisponible: index absent"


def test_stream_context_overflow_returns_413(monkeypatch):
    from app.inference import ContextOverflowError

    async def fake_stream(config, user_content, system_prompt):
        raise ContextOverflowError("La question, l'historique et la documentation dépassent le contexte du modèle (9100 tokens pour un maximum de 8192). Effacez la conversation ou raccourcissez la question.")
        yield  # pragma: no cover

    monkeypatch.setattr("app.api.get_rag_retriever", lambda: None)
    monkeypatch.setattr("app.api._stream_llama_response", fake_stream)

    response = client.post("/chat/stream", json={"message": "Question"})

    assert response.status_code == 413
    assert "9100 tokens pour un maximum de 8192" in response.json()["detail"]


def test_stream_server_failure_returns_503(monkeypatch):
    async def fake_stream(config, user_content, system_prompt):
        raise RuntimeError("llama-server did not start in time")
        yield  # pragma: no cover

    monkeypatch.setattr("app.api.get_rag_retriever", lambda: None)
    monkeypatch.setattr("app.api._stream_llama_response", fake_stream)

    response = client.post("/chat/stream", json={"message": "Question"})

    assert response.status_code == 503
    assert "Génération indisponible" in response.json()["detail"]


def test_chat_context_overflow_returns_413(monkeypatch):
    from app.inference import ContextOverflowError

    def overflow(prompt, config):
        raise ContextOverflowError("contexte dépassé")

    monkeypatch.setattr("app.api.get_rag_retriever", lambda: None)
    monkeypatch.setattr("app.api.call_llama_cli", overflow)

    response = client.post("/chat", json={"message": "Question"})

    assert response.status_code == 413
    assert response.json()["detail"] == "contexte dépassé"


def _patch_llama_server(monkeypatch, handler, captured):
    import httpx

    class FakeProc:
        def poll(self):
            return None

        def terminate(self):
            pass

        def wait(self, timeout=None):
            return 0

        def kill(self):
            pass

    def fake_popen(args, **kwargs):
        captured["args"] = args
        return FakeProc()

    real_client = httpx.AsyncClient
    monkeypatch.setattr("app.llama_server.subprocess.Popen", fake_popen)
    monkeypatch.setattr(
        httpx, "AsyncClient",
        lambda *a, **k: real_client(transport=httpx.MockTransport(handler), **k),
    )


def _collect(gen):
    import asyncio

    async def run():
        return [token async for token in gen]

    return asyncio.run(run())


def test_llama_server_gets_eval_sampling_context_and_flags_length(monkeypatch):
    import httpx

    from app.api import _stream_llama_response
    from app.chat import load_config

    captured = {}

    def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        captured["body"] = json.loads(request.content)
        sse = (
            'data: {"choices":[{"delta":{"content":"Bon"}}]}\n\n'
            'data: {"choices":[{"delta":{"content":"jour"},"finish_reason":"length"}]}\n\n'
            "data: [DONE]\n\n"
        )
        return httpx.Response(200, text=sse)

    _patch_llama_server(monkeypatch, handler, captured)

    config = load_config()
    config["server"] = {"persistent": False}
    tokens = _collect(_stream_llama_response(config, "Q", "S"))

    args = captured["args"]
    assert args[args.index("-c") + 1] == "8192"
    assert args[args.index("--parallel") + 1] == "1"
    body = captured["body"]
    from app.inference import sampling_params, server_payload_sampling

    expected = server_payload_sampling(sampling_params(config))
    assert {k: body[k] for k in expected} == expected
    assert tokens[:2] == ["Bon", "jour"]
    assert "limite de longueur atteinte" in tokens[2]


def test_llama_server_context_error_becomes_overflow(monkeypatch):
    import httpx
    import pytest

    from app.api import _stream_llama_response
    from app.chat import load_config
    from app.inference import ContextOverflowError

    def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(400, json={"error": {
            "code": 400,
            "type": "exceed_context_size_error",
            "message": "request (9100 tokens) exceeds the available context size (8192 tokens), try increasing it",
        }})

    _patch_llama_server(monkeypatch, handler, {})

    config = load_config()
    config["server"] = {"persistent": False}
    with pytest.raises(ContextOverflowError, match="9100 tokens pour un maximum de 8192"):
        _collect(_stream_llama_response(config, "Q", "S"))
