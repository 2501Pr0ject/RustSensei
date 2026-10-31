"""Tests unitaires du module app.rag (retrieval, formatage, citations)."""

from app.rag import _BM25, RAGRetriever, check_rag_available

RAG_CONFIG = {
    "retrieval": {
        "top_k": 5,
        "initial_k": 15,
        "score_threshold": 0.3,
        "max_citations": 4,
    },
    "rerank": {"enabled": False},
    "augmentation": {"max_context_tokens": 1500},
}


def make_retriever() -> RAGRetriever:
    """Crée un retriever sans charger l'index FAISS (instantiation légère)."""
    retriever = RAGRetriever.__new__(RAGRetriever)
    retriever.config = RAG_CONFIG
    return retriever


def test_check_rag_available_missing_index(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "app.rag.get_rag_config",
        lambda: {
            "index": {
                "path": str(tmp_path / "missing.faiss"),
                "metadata_path": str(tmp_path / "missing.pkl"),
            }
        },
    )

    available, error_msg = check_rag_available()

    assert available is False
    assert "Index FAISS non trouvé" in error_msg


def test_check_rag_available_missing_metadata(monkeypatch, tmp_path):
    index_path = tmp_path / "rustsensei.faiss"
    index_path.touch()
    metadata_path = tmp_path / "missing.pkl"

    monkeypatch.setattr(
        "app.rag.get_rag_config",
        lambda: {
            "index": {
                "path": str(index_path),
                "metadata_path": str(metadata_path),
            }
        },
    )

    available, error_msg = check_rag_available()

    assert available is False
    assert "Metadata non trouv" in error_msg


def test_check_rag_available_ok(monkeypatch, tmp_path):
    index_path = tmp_path / "rustsensei.faiss"
    index_path.touch()
    metadata_path = tmp_path / "metadata.pkl"
    metadata_path.touch()

    monkeypatch.setattr(
        "app.rag.get_rag_config",
        lambda: {
            "index": {
                "path": str(index_path),
                "metadata_path": str(metadata_path),
            }
        },
    )

    available, error_msg = check_rag_available()

    assert available is True
    assert error_msg == ""


def test_format_context_limits_tokens():
    retriever = make_retriever()
    chunks = [
        {"text": "chunk A", "source_name": "Rust Book", "heading": "Ownership", "token_count": 100},
        {"text": "chunk B", "source_name": "Rust Book", "heading": "Borrowing", "token_count": 100},
    ]

    context = retriever.format_context(chunks, max_tokens=150)

    assert "chunk A" in context
    assert "chunk B" not in context


def test_format_context_includes_guard():
    retriever = make_retriever()
    chunks = [
        {"text": "chunk A", "source_name": "Rust Book", "heading": "Ownership", "token_count": 10},
    ]

    context = retriever.format_context(chunks)

    assert "<reference_documentation>" in context
    assert "</reference_documentation>" in context
    assert "chunk A" in context


def test_format_context_joins_chunks():
    retriever = make_retriever()
    chunks = [
        {"text": "chunk A", "source_name": "Rust Book", "heading": "Ownership", "token_count": 10},
        {"text": "chunk B", "source_name": "Rust Book", "heading": "Borrowing", "token_count": 10},
    ]

    context = retriever.format_context(chunks, max_tokens=1500)

    assert "chunk A" in context
    assert "chunk B" in context
    assert context.count("---") >= 1


def test_format_citation_with_heading():
    retriever = make_retriever()

    citation = retriever.format_citation(
        {"source_name": "Rust Book", "heading": "Ownership"}
    )

    assert citation == "[Rust Book — Ownership]"


def test_format_citation_without_heading():
    retriever = make_retriever()

    citation = retriever.format_citation({"source_name": "Rust Book"})

    assert citation == "[Rust Book]"


def test_build_url_converts_markdown_to_html():
    retriever = make_retriever()

    url = retriever._build_url(
        {
            "base_url": "https://doc.rust-lang.org/book",
            "path": "ch04-01-what-is-ownership.md",
            "anchor": "what-is-ownership",
        }
    )

    assert url == "https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html#what-is-ownership"


def test_build_url_strips_readme_summary():
    retriever = make_retriever()

    url = retriever._build_url(
        {
            "base_url": "https://doc.rust-lang.org/book",
            "path": "SUMMARY.html",
            "anchor": "",
        }
    )

    # SUMMARY.md -> SUMMARY.html -> strip -> URL de base du repertoire
    assert url == "https://doc.rust-lang.org/book"


def test_get_citations_dedup_and_limit():
    retriever = make_retriever()
    chunks = [
        {"source_name": "Rust Book", "heading": "Ownership", "text": "t1"},
        {"source_name": "Rust Book", "heading": "Ownership", "text": "t2"},
        {"source_name": "Rust Book", "heading": "Borrowing", "text": "t3"},
    ]

    citations = retriever.get_citations(chunks, max_citations=2)

    assert len(citations) == 2
    assert citations[0] == "[Rust Book — Ownership]"
    assert citations[1] == "[Rust Book — Borrowing]"


def test_get_citations_no_duplicates():
    retriever = make_retriever()
    chunks = [
        {"source_name": "Rust Book", "heading": "Ownership", "text": "t1"},
        {"source_name": "Rust Book", "heading": "Ownership", "text": "t2"},
    ]

    citations = retriever.get_citations(chunks)

    assert len(citations) == 1
    assert citations[0] == "[Rust Book — Ownership]"


def test_bm25_scores_relevant_document_higher():
    bm25 = _BM25(
        [
            "Le borrow checker vérifie les références",
            "Les types primitifs en Rust",
            "ownership et borrow checker en Rust",
        ]
    )

    scores = bm25.scores("borrow checker")

    assert scores[0] > scores[1]
    assert scores[2] > scores[1]


def test_fuse_rrf_prefers_chunks_ranked_by_both():
    fused = RAGRetriever._fuse_rrf([0, 1, 2], [2, 1, 3], top_k=3, rrf_k=60)

    indices = [idx for idx, _ in fused]

    # 1 et 2 apparaissent dans les deux classements, 3 seulement dans le lexical
    assert indices[0] in (1, 2)
    assert 3 not in indices
