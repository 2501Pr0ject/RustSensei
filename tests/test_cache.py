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


def test_clear_persists_empty_cache(tmp_path):
    path = tmp_path / "cache.json"
    cache = ResponseCache(ttl_seconds=60, path=path)
    cache.set("Question", "reponse")

    cache.clear()

    reloaded = ResponseCache(ttl_seconds=60, path=path)
    assert reloaded.get("Question") is None
