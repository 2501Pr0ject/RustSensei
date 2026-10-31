"""
API REST FastAPI pour RustSensei (M8).

Expose le pipeline de chat (llama.cpp + RAG) via HTTP.
"""
import json
import socket
import subprocess
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.exceptions import FastAPIError
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .chat import build_prompt, call_llama_cli, get_rag_retriever, load_config
from .rag import check_rag_available

app = FastAPI(
    title="RustSensei",
    description="Assistant Rust local - API",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    """Requete de chat."""

    message: str
    use_rag: bool = False


class ChatResponse(BaseModel):
    """Reponse du chat."""

    response: str
    citations: list[str] = []
    rag_used: bool = False


LLAMA_SERVER_BIN = (
    Path(__file__).parent.parent / "vendor" / "llama.cpp" / "build" / "bin" / "llama-server"
)


def _find_free_port() -> int:
    """Retourne un port TCP libre."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def _stream_llama_response(
    config: dict, prompt: str, system: str
) -> AsyncIterator[str]:
    """
    Genere une reponse via llama-server (API OpenAI-compatible) en streaming.

    Args:
        config: Configuration du modele/inference.
        prompt: Prompt complet (ChatML) de la question.
        system: Prompt system.

    Yields:
        Tokens de contenu au fur et a mesure.
    """
    port = _find_free_port()
    model_path = str(
        (Path(__file__).parent.parent / config["paths"]["model"]).resolve()
    )
    proc = subprocess.Popen(
        [
            str(LLAMA_SERVER_BIN),
            "-m",
            model_path,
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        # Attendre que le serveur soit pret (max ~60s)
        async with httpx.AsyncClient(timeout=30.0) as client:
            for _ in range(240):
                try:
                    health = await client.get(f"http://127.0.0.1:{port}/health")
                    if health.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                await _sleep(0.25)
            else:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                raise RuntimeError("llama-server did not start in time")

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"http://127.0.0.1:{port}/v1/chat/completions",
                json={
                    "model": "rustsensei",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": True,
                },
            ) as response:
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
                    delta = (chunk.get("choices") or [{}])[0].get("delta") or {}
                    content = delta.get("content") or ""
                    if content:
                        yield content
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


async def _sleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Repond a une question en utilisant le pipeline RAG + llama.cpp."""
    config = load_config()

    context = None
    citations = []
    use_rag = request.use_rag

    retriever = None
    if use_rag:
        available, error_msg = check_rag_available()
        if not available:
            raise FastAPIError(message=f"RAG indisponible: {error_msg}")

    if use_rag:
        retriever = get_rag_retriever()

    if retriever:
        chunks = retriever.retrieve(request.message)
        if chunks:
            context = retriever.format_context(chunks)
            citations = retriever.get_citations(chunks)

    full_prompt = build_prompt(request.message, config, context=context)
    response = call_llama_cli(full_prompt, config)

    return ChatResponse(
        response=response,
        citations=citations,
        rag_used=retriever is not None,
    )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Genere une reponse en streaming via llama-server (SSE -> tokens)."""
    config = load_config()

    context = None
    use_rag = request.use_rag
    retriever = None
    if use_rag:
        available, error_msg = check_rag_available()
        if not available:
            raise FastAPIError(message=f"RAG indisponible: {error_msg}")

    if use_rag:
        retriever = get_rag_retriever()

    if retriever:
        chunks = retriever.retrieve(request.message)
        if chunks:
            context = retriever.format_context(chunks)

    full_prompt = build_prompt(request.message, config, context=context)

    async def token_stream():
        async for token in _stream_llama_response(
            config, full_prompt, config["prompt"]["system"]
        ):
            yield token

    return StreamingResponse(token_stream(), media_type="text/plain; charset=utf-8")


@app.get("/health")
def health() -> dict:
    """Verifie la sante du service."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
