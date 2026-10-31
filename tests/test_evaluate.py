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
