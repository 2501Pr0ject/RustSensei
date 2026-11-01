"""Tests unitaires du module scripts.evaluate."""

from pathlib import Path

from evaluate import evaluate_response, load_prompts, load_rubric

RESPONSE_WITH_ALL_SECTIONS = """## TL;DR
La variable a ete deplacee vers s2.

## Problème
Le code compile mais la variable n est plus visible.

## Solution
let s2 = s.clone();

## Explication
Cette erreur est due au deplacement de la valeur.

## À retenir
La variable originale ne peut plus etre utilisee.
"""


def test_load_prompts():
    prompts = load_prompts(Path("eval/prompts_fr.jsonl"))

    assert len(prompts) > 0
    for prompt_data in prompts:
        assert "id" in prompt_data
        assert "category" in prompt_data
        assert "difficulty" in prompt_data
        assert "prompt" in prompt_data
        assert isinstance(prompt_data.get("expected_topics", []), list)


def test_load_rubric():
    rubric = load_rubric(Path("eval/rubric.json"))

    assert "criteria" in rubric
    assert len(rubric["criteria"]) >= 5


def test_evaluate_response_format_score():
    result = evaluate_response(RESPONSE_WITH_ALL_SECTIONS, {"expected_topics": []})

    assert result["sections_found"] == 5
    assert result["scores"]["format"] == 5.0


def test_evaluate_response_expected_topics():
    response = (
        "## TL;DR\n"
        "L ownership en Rust utilise le move pour transfeter la propriete.\n"
        "\n"
        "## Problème\n"
        "Le move rend la valeur invalide.\n"
        "\n"
        "## Solution\n"
        "let s2 = s.clone();\n"
        "\n"
        "## Explication\n"
        "Le move transfere la propriete au scope suivant.\n"
        "\n"
        "## À retenir\n"
        "La propriete passe d un scope a l autre."
    )
    prompt_data = {
        "expected_topics": ["ownership", "move"],
        "category": "ownership",
        "difficulty": "intermediaire",
    }

    result = evaluate_response(response, prompt_data)

    assert result["auto_checks"]["expected_topics"] == 1.0


def test_evaluate_response_response_length():
    long_response = " ".join(["explication pedagogique"] * 60)
    short_response = "court"

    result_long = evaluate_response(long_response, {"expected_topics": []})
    result_short = evaluate_response(short_response, {"expected_topics": []})

    assert result_long["auto_checks"]["response_length"] is True
    assert result_short["auto_checks"]["response_length"] is False


def test_parse_seeds_keeps_order_and_removes_duplicates():
    from evaluate import parse_seeds

    assert parse_seeds("42, 1,2,42") == [42, 1, 2]


def test_parse_seeds_rejects_empty():
    import argparse

    import pytest
    from evaluate import parse_seeds

    with pytest.raises(argparse.ArgumentTypeError):
        parse_seeds(" , ")


def test_average_score():
    from evaluate import average_score

    results = [
        {"evaluation": {"scores": {"auto_composite": 2.0}}},
        {"evaluation": {"scores": {"auto_composite": 4.0}}},
    ]

    assert average_score(results) == 3.0
    assert average_score([]) == 0.0


def test_run_metadata_records_model_and_seed():
    from pathlib import Path

    from evaluate import run_metadata

    config = {
        "paths": {"model": "models/inexistant.gguf"},
        "inference": {"seed": 7},
    }

    meta = run_metadata(config, use_rag=False, prompts_file=Path("eval/prompts_fr.jsonl"))

    assert meta["model_path"] == "models/inexistant.gguf"
    assert meta["model_size_bytes"] is None
    assert meta["seed"] == 7
    assert meta["rag_settings"] is None


def test_topics_coverage_normalizes_case_and_accents():
    from evaluate import topics_coverage

    assert topics_coverage(["Propriété", "léger"], "la PROPRIETE d'un thread legere") == 1.0
    assert topics_coverage(["système d'exploitation"], "le système d’exploitation") == 1.0


def test_topics_coverage_alternatives():
    from evaluate import topics_coverage

    topics = [["OS", "système d'exploitation"], "coopérati"]

    assert topics_coverage(topics, "planifié par l'OS, de façon coopérative") == 1.0
    assert topics_coverage(topics, "le systeme d'exploitation") == 0.5
    assert topics_coverage([["a", "b"], "c"], "c") == 0.5


def test_topics_coverage_left_word_boundary():
    from evaluate import topics_coverage

    assert topics_coverage([["OS"]], "je propose un dossier") == 0.0
    assert topics_coverage(["bug"], "en mode debug") == 0.0
    assert topics_coverage(["réalloc"], "une réallocation du buffer") == 1.0


def test_topics_coverage_symbol_keywords():
    from evaluate import topics_coverage

    assert topics_coverage(["move ||"], "thread::spawn(move || { })") == 1.0
    assert topics_coverage([" if "], "Some(x) if x > 5 =>") == 1.0
    assert topics_coverage([": Fn"], "fn appliquer<F: Fn(i32)>(f: F)") == 1.0
    assert topics_coverage([], "x") == 1.0


def test_run_metadata_records_scorer_version():
    from pathlib import Path

    from evaluate import SCORER_VERSION, run_metadata

    config = {"paths": {"model": "models/x.gguf"}, "inference": {"seed": 1}}

    meta = run_metadata(config, use_rag=False, prompts_file=Path("eval/prompts_fr.jsonl"))

    assert meta["scorer_version"] == SCORER_VERSION == 2
