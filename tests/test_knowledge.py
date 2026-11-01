"""Tests unitaires du graphe de connaissances Rust (KAG)."""

import pytest

from app.knowledge import Concept, KnowledgeGraph, normalize_text


@pytest.fixture
def graph():
    return KnowledgeGraph(
        [
            Concept("rc", "Rc", ["rc", "compte de references"], ["arc", "send-sync"]),
            Concept("arc", "Arc", ["arc"], ["send-sync", "mutex"]),
            Concept("send-sync", "Send et Sync", ["send", "sync"], []),
            Concept("mutex", "Mutex", ["mutex"], []),
        ]
    )


def test_normalize_lowercases_and_removes_accents():
    assert normalize_text("Durée de vie") == "duree de vie"
    assert normalize_text("  RC ") == "rc"


def test_detect_matches_alias_case_insensitive(graph):
    matched = graph.detect("Pourquoi le Rc compte les references ?")

    assert [concept.id for concept in matched] == ["rc"]


def test_detect_no_match(graph):
    matched = graph.detect("Comment fonctionne la mecanique quantique ?")

    assert matched == []


def test_detect_word_boundary_no_substring(graph):
    # "searchbar" contient "arc" mais pas sur des frontieres de mots
    assert [c.id for c in graph.detect("searchbar")] == []
    assert [c.id for c in graph.detect("Python arc en Rust ?")] == ["arc"]


def test_detect_matches_plural(graph):
    matched = graph.detect("les rebonds des syncs et des hits")

    assert [c.id for c in matched] == ["send-sync"]


def test_related_deduplicates_and_skips_detected(graph):
    detected = graph.detect("Rc arc")

    related = graph.related(detected)

    assert [c.id for c in related] == ["send-sync", "mutex"]


def test_expand_returns_related_terms(graph):
    expansions = graph.expand("Rc")

    assert len(expansions) <= 2
    assert all("Arc" in term or "Send" in term for term in expansions)


def test_expand_no_match_returns_empty(graph):
    assert graph.expand("la mecanique quantique") == []


def test_expand_cap(graph):
    expansions = graph.expand("Rc et Arc", max_expansions=1)

    assert len(expansions) == 1


def test_empty_graph_expands_nothing():
    empty = KnowledgeGraph([])

    assert empty.expand("Rc") == []
    assert empty.is_empty


def test_load_curated_file_ids_and_links_valid():
    graph = KnowledgeGraph.load()

    assert not graph.is_empty
    ids = {c.id for c in graph.concepts}
    assert len(ids) == len(graph.concepts), "ids uniques"
    for concept in graph.concepts:
        for rid in concept.related:
            assert rid in ids, "related {} inconnu".format(rid)


def test_load_missing_file_returns_empty_graph(tmp_path):
    graph = KnowledgeGraph.load(tmp_path / "missing.yaml")

    assert graph.is_empty


def test_load_corrupted_file_returns_empty_graph(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("{ not yaml: [", encoding="utf-8")

    assert KnowledgeGraph.load(path).is_empty
