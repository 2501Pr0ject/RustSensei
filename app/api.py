"""
API REST FastAPI pour RustSensei (M8).

Expose le pipeline de chat (llama.cpp + RAG) via HTTP.
"""
import asyncio
import base64
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator, model_validator

from .cache import ResponseCache, response_cache
from .chat import (
    MAX_HISTORY_MESSAGES,
    build_prompt,
    build_user_content,
    call_llama_cli,
    get_rag_retriever,
    load_config,
    truncate_history_content,
)
from .inference import (
    LENGTH_LIMIT_NOTE,
    ContextOverflowError,
    generation_signature,
    overflow_message,
    sampling_params,
    server_payload_sampling,
)
from .llama_server import (
    find_free_port,
    is_persistent,
    server_manager,
    start_process,
    stop_process,
    wait_healthy,
)
from .rag import check_rag_available

logger = logging.getLogger(__name__)

RAG_WARMUP_QUERY = "Comment déclarer une variable mutable en Rust ?"


def warm_up_rag() -> bool:
    """
    Charge les modeles du RAG (embeddings, reranker, BM25) avant la premiere question.

    Sans cela, la premiere question avec RAG apres le demarrage attend environ 10 s.
    """
    available, _ = check_rag_available()
    if not available:
        return False
    get_rag_retriever().retrieve(RAG_WARMUP_QUERY)
    return True


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lance le llama-server persistant et prechauffe le RAG ; arrete le serveur a la fin."""
    config = load_config()
    if is_persistent(config):
        try:
            await server_manager.ensure(config)
            logger.info("llama-server pret (%s)", server_manager.status())
        except Exception as exc:  # relance a la premiere requete
            logger.warning("llama-server non demarre : %s", exc)
    try:
        if await asyncio.to_thread(warm_up_rag):
            logger.info("RAG prechauffe")
    except Exception as exc:  # le RAG se chargera a la premiere question
        logger.warning("prechauffage du RAG impossible : %s", exc)
    yield
    server_manager.stop()


app = FastAPI(
    title="RustSensei",
    description="Assistant Rust local - API",
    version="0.1.0",
    lifespan=lifespan,
)


class HistoryMessage(BaseModel):
    """Un tour precedent de conversation."""

    role: Literal["user", "assistant"]
    content: str

    @field_validator("content")
    @classmethod
    def _strip_non_empty(cls, value: str) -> str:
        stripped = (value or "").strip()
        if not stripped:
            raise ValueError("Le contenu du message ne peut pas etre vide")
        # Les longues reponses sont tronquees (et non rejetees) pour que
        # l'historique complet reste dans le budget MAX_HISTORY_CHARS.
        return truncate_history_content(stripped)


class ChatRequest(BaseModel):
    """Requete de chat."""

    message: str
    use_rag: bool = False
    history: list[HistoryMessage] = Field(default_factory=list)

    @model_validator(mode="after")
    def _cap_history(self):
        if self.history and len(self.history) > MAX_HISTORY_MESSAGES:
            raise ValueError(
                f"L'historique est limite a {MAX_HISTORY_MESSAGES} messages"
            )
        return self


class ChatResponse(BaseModel):
    """Reponse du chat."""

    response: str
    citations: list[str] = []
    rag_used: bool = False


async def _chat_completion_stream(
    base_url: str, config: dict, user_content: str, system: str
) -> AsyncIterator[str]:
    """Requete de chat en streaming vers un llama-server deja pret."""
    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream(
            "POST",
            f"{base_url}/v1/chat/completions",
            json={
                "model": "rustsensei",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                "stream": True,
                # Meme echantillonnage que l'evaluation (source unique)
                **server_payload_sampling(sampling_params(config)),
            },
        ) as response:
            if response.status_code != 200:
                body = (await response.aread()).decode("utf-8", errors="replace")
                try:
                    error = json.loads(body).get("error", body)
                except (json.JSONDecodeError, AttributeError):
                    error = body
                raise _llama_server_error(error)

            finish_reason = None
            async for line in response.aiter_lines():
                line = line.strip()
                if not line.startswith("data: "):
                    continue
                payload = line[len("data: ") :].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if "error" in chunk:
                    raise _llama_server_error(chunk["error"])
                choice = (chunk.get("choices") or [{}])[0]
                finish_reason = choice.get("finish_reason") or finish_reason
                content = (choice.get("delta") or {}).get("content") or ""
                if content:
                    yield content

            # Pas de troncature silencieuse : limite de tokens ou contexte plein
            if finish_reason == "length":
                yield LENGTH_LIMIT_NOTE


async def _stream_llama_response(
    config: dict, user_content: str, system: str
) -> AsyncIterator[str]:
    """
    Genere une reponse via llama-server (API OpenAI-compatible) en streaming.

    llama-server applique lui-meme le template de chat du modele : le contenu
    utilisateur ne doit donc pas etre deja formate en ChatML. En mode persistant
    (defaut), le serveur lance au demarrage de l'API est reutilise ; sinon un
    serveur est lance pour la requete puis arrete.

    Args:
        config: Configuration du modele/inference.
        user_content: Contenu du message utilisateur (sans template ChatML).
        system: Prompt system.

    Yields:
        Tokens de contenu au fur et a mesure.
    """
    if is_persistent(config):
        base_url = await server_manager.ensure(config)
        async for token in _chat_completion_stream(base_url, config, user_content, system):
            yield token
        return

    port = find_free_port()
    proc = start_process(config, port)
    try:
        await wait_healthy(port, proc)
        async for token in _chat_completion_stream(
            f"http://127.0.0.1:{port}", config, user_content, system
        ):
            yield token
    finally:
        stop_process(proc)


def _llama_server_error(error) -> Exception:
    """Convertit une erreur de llama-server en exception explicite."""
    if isinstance(error, dict):
        message = str(error.get("message") or error)
        error_type = error.get("type")
    else:
        message = str(error)
        error_type = None
    if error_type == "exceed_context_size_error" or "context size" in message:
        return ContextOverflowError(overflow_message(message))
    return RuntimeError(f"llama-server : {message}")


def _generate(prompt: str, config: dict) -> str:
    """Generation llama-completion ; depassement de contexte -> HTTP 413."""
    try:
        return call_llama_cli(prompt, config)
    except ContextOverflowError as e:
        raise HTTPException(status_code=413, detail=str(e)) from e


def _history_dicts(request: ChatRequest) -> list[dict]:
    """Retourne l'historique de la requete comme liste de dicts."""
    return [msg.model_dump() for msg in request.history]


def _cache_query(request: ChatRequest) -> str:
    """Cle de cache de la requete (inclut l'historique si present)."""
    return ResponseCache.composite_key(_history_dicts(request), request.message)


def _cache_embedder(request: ChatRequest, retriever):
    """
    Extrait un embedder pour le cache semantique, sans historique seulement.

    En multi-tours, le matching semantique est desactive : une reformulation
    dont le contexte a change doit generer une nouvelle reponse.
    """
    if request.history:
        return None
    return getattr(retriever, "embed_query", None)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Repond a une question en utilisant le pipeline RAG (avec cache) + llama.cpp."""
    config = load_config()

    context = None
    citations = []
    use_rag = request.use_rag

    retriever = None
    if use_rag:
        available, error_msg = check_rag_available()
        if not available:
            raise HTTPException(
                status_code=503, detail=f"RAG indisponible: {error_msg}"
            )

    if use_rag:
        retriever = get_rag_retriever()

    response = None
    cache_query = _cache_query(request)
    cache_embedder = _cache_embedder(request, retriever)

    if retriever:
        cached = response_cache.get(
            cache_query, embedder=cache_embedder, signature=generation_signature(config)
        )
        if cached is not None:
            response = cached["response"]
            citations = cached["citations"]
        else:
            chunks = retriever.retrieve(request.message)
            if chunks:
                context = retriever.format_context(chunks)
                citations = retriever.get_citations(chunks)

            response = _generate(
                build_prompt(
                    request.message,
                    config,
                    context=context,
                    history=_history_dicts(request),
                ),
                config,
            )
            response_cache.set(
                cache_query,
                response,
                citations,
                embedder=cache_embedder,
                signature=generation_signature(config),
            )

    if response is None:
        response = _generate(
            build_prompt(
                request.message,
                config,
                context=context,
                history=_history_dicts(request),
            ),
            config
        )

    return ChatResponse(
        response=response,
        citations=citations,
        rag_used=retriever is not None,
    )


def _encode_citations(citations: list[str]) -> str:
    """Encode les citations en base64 (UTF-8) pour un header HTTP."""
    payload = json.dumps(citations, ensure_ascii=False).encode("utf-8")
    return base64.b64encode(payload).decode("ascii")


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Genere une reponse en streaming via llama-server (avec cache) + SSE."""
    config = load_config()

    use_rag = request.use_rag
    retriever = None
    if use_rag:
        available, error_msg = check_rag_available()
        if not available:
            raise HTTPException(
                status_code=503, detail=f"RAG indisponible: {error_msg}"
            )

    if use_rag:
        retriever = get_rag_retriever()

    cache_query = _cache_query(request)
    cache_embedder = _cache_embedder(request, retriever)
    cached = None
    context = None
    citations = []

    if retriever is not None:
        cached = response_cache.get(
            cache_query, embedder=cache_embedder, signature=generation_signature(config)
        )
        if cached is not None:
            citations = cached["citations"]
        else:
            chunks = retriever.retrieve(request.message)
            if chunks:
                context = retriever.format_context(chunks)
                citations = retriever.get_citations(chunks)

    history = _history_dicts(request)

    headers = {}
    if retriever is not None:
        headers["X-Cache"] = "HIT" if cached is not None else "MISS"
    if citations:
        headers["X-Citations"] = _encode_citations(citations)

    # La generation demarre avant l'envoi des en-tetes : une erreur (contexte
    # depasse, llama-server indisponible) devient un vrai code HTTP avec un
    # message clair, au lieu d'une reponse vide ou tronquee.
    upstream = None
    first_token = ""
    if cached is None:
        user_content = build_user_content(
            request.message, context=context, history=history
        )
        upstream = _stream_llama_response(
            config, user_content, config["prompt"]["system"]
        )
        try:
            first_token = await upstream.__anext__()
        except StopAsyncIteration:
            first_token = ""
        except ContextOverflowError as e:
            raise HTTPException(status_code=413, detail=str(e)) from e
        except RuntimeError as e:
            raise HTTPException(
                status_code=503, detail=f"Génération indisponible : {e}"
            ) from e

    async def token_stream():
        if cached is not None:
            yield cached["response"]
            return

        full_response = first_token
        if first_token:
            yield first_token
        async for token in upstream:
            full_response += token
            yield token

        if retriever is not None and full_response:
            response_cache.set(
                cache_query,
                full_response,
                citations,
                embedder=cache_embedder,
                signature=generation_signature(config),
            )

    return StreamingResponse(
        token_stream(),
        media_type="text/plain; charset=utf-8",
        headers=headers,
    )


@app.get("/health")
def health() -> dict:
    """Verifie la sante du service et indique si l'index RAG est disponible."""
    rag_available, rag_error = check_rag_available()
    return {
        "status": "ok",
        "rag_available": rag_available,
        "rag_error": rag_error or None,
        "llama_server": server_manager.status(),
    }


@app.get("/cache/stats")
def cache_stats() -> dict:
    """Retourne les statistiques d'utilisation du cache (hits, misses)."""
    return response_cache.stats()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
