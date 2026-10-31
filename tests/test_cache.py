"""Tests unitaires du module app.cache (CAG - Cache Augmented Generation)."""

from app.cache import ResponseCache


def test_set_then_get_returns_entry():
    cache = ResponseCache(ttl_seconds=60)
    cache.set("Quelle est la difference ?", "reponse")

    entry = cache.get("Quelle est la difference ?")

    assert entry is not None
    assert entry["response"] == "reponse"
    assert entry["citations"] == []


def test_get_missing_returns_none():
    cache = ResponseCache(ttl_seconds=60)

    assert cache.get("inconnue") is None


def test_normalize_key_is_case_insensitive_and_collapses_whitespace():
    cache = ResponseCache(ttl_seconds=60)
    cache.set("  Quelle   est   la difference ?", "reponse")

    assert cache.get("Quelle EST la difference ?") is not None


def test_get_expired_returns_none():
    cache = ResponseCache(ttl_seconds=10)
    cache.set("Question", "reponse", timestamp=0.0)

    assert cache.get("Question", now=100.0) is None


def test_set_stores_citations():
    cache = ResponseCache(ttl_seconds=60)
    cache.set("Question", "reponse", citations=["[Rust Book — Ownership]"])

    entry = cache.get("Question")

    assert entry is not None
    assert entry["citations"] == ["[Rust Book — Ownership]"]


def test_clear_removes_entries():
    cache = ResponseCache(ttl_seconds=60)
    cache.set("Question", "reponse")
    cache.clear()

    assert cache.get("Question") is None


def test_disabled_cache_returns_none():
    cache = ResponseCache(ttl_seconds=0)
    cache.set("Question", "reponse")

    assert cache.get("Question") is None


def test_cache_persists_entries_to_disk(tmp_path):
    path = tmp_path / "cache.json"
    cache = ResponseCache(ttl_seconds=60, path=path)
    cache.set(
        "Question persistante",
        "reponse",
        citations=["[Rust Book — Ownership]"],
    )

    reloaded = ResponseCache(ttl_seconds=60, path=path)

    entry = reloaded.get("Question persistante")
    assert entry is not None
    assert entry["response"] == "reponse"
    assert entry["citations"] == ["[Rust Book — Ownership]"]


def test_cache_ignores_corrupted_file(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text("{not json", encoding="utf-8")

    cache = ResponseCache(ttl_seconds=60, path=path)

    assert cache.get("Question") is None


def test_stats_counts_hits_and_misses():
    cache = ResponseCache(ttl_seconds=60)
    cache.set("Question", "reponse")

    cache.get("Question")
    cache.get("Inconnue")

    stats = cache.stats()
    assert stats["entries"] == 1
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 0.5
    assert stats["ttl_seconds"] == 60


def test_stats_on_empty_cache():
    cache = ResponseCache(ttl_seconds=60)

    stats = cache.stats()

    assert stats["entries"] == 0
    assert stats["hit_rate"] == 0.0


def test_clear_persists_empty_cache(tmp_path):
    path = tmp_path / "cache.json"
    cache = ResponseCache(ttl_seconds=60, path=path)
    cache.set("Question", "reponse")

    cache.clear()

    reloaded = ResponseCache(ttl_seconds=60, path=path)
    assert reloaded.get("Question") is None


def fake_embedder(text):
    """Vecteurs unitaires prédéfinis : proche de [1, 0] ou orthogonal."""
    vectors = {
        "question initiale": [1.0, 0.0],
        "question proche": [0.99, 0.14],
        "question lointaine": [0.0, 1.0],
    }
    return vectors[text.strip().lower()]


def make_semantic_cache(**kwargs):
    options = {"ttl_seconds": 60, "semantic_enabled": True, "semantic_threshold": 0.9}
    options.update(kwargs)
    return ResponseCache(**options)


def test_semantic_cache_returns_close_question():
    cache = make_semantic_cache()
    cache.set("Question initiale", "reponse", embedder=fake_embedder)

    entry = cache.get("Question proche", embedder=fake_embedder)

    assert entry is not None
    assert entry["response"] == "reponse"


def test_semantic_cache_rejects_distant_question():
    cache = make_semantic_cache()
    cache.set("Question initiale", "reponse", embedder=fake_embedder)

    assert cache.get("Question lointaine", embedder=fake_embedder) is None


def test_semantic_cache_skips_entries_without_embedding():
    cache = make_semantic_cache()
    cache.set("Question initiale", "reponse")

    assert cache.get("Question proche", embedder=fake_embedder) is None


def test_semantic_cache_disabled_never_calls_embedder():
    calls = []

    def embedder(text):
        calls.append(text)
        return [1.0, 0.0]

    cache = ResponseCache(ttl_seconds=60)
    cache.set("Question initiale", "reponse")

    assert cache.get("Question proche", embedder=embedder) is None
    assert calls == []


def test_exact_match_does_not_call_embedder():
    calls = []

    def embedder(text):
        calls.append(text)
        return [1.0, 0.0]

    cache = make_semantic_cache()
    cache.set("Question initiale", "reponse")

    entry = cache.get("Question initiale", embedder=embedder)

    assert entry is not None
    assert calls == []


def test_embedder_failure_falls_back_to_exact_match():
    def broken_embedder(text):
        raise RuntimeError("modele indisponible")

    cache = make_semantic_cache()
    cache.set("Question initiale", "reponse", embedder=broken_embedder)

    assert cache.get("Question initiale", embedder=broken_embedder) is not None
    assert cache.get("Question proche", embedder=broken_embedder) is None


def test_semantic_embedding_persists_to_disk(tmp_path):
    path = tmp_path / "cache.json"
    cache = make_semantic_cache(path=path)
    cache.set("Question initiale", "reponse", embedder=fake_embedder)

    reloaded = make_semantic_cache(path=path)
    entry = reloaded.get("Question proche", embedder=fake_embedder)

    assert entry is not None
    assert entry["response"] == "reponse"
