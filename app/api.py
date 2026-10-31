"""
API REST FastAPI pour RustSensei (M8).

Expose le pipeline de chat (llama.cpp + RAG) via HTTP.
"""
from fastapi import FastAPI
from fastapi.exceptions import FastAPIError
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


@app.get("/health")
def health() -> dict:
    """Verifie la sante du service."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
