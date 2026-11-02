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


def test_parse_llama_cpp_version():
    from evaluate import parse_llama_cpp_version

    assert parse_llama_cpp_version("version: 4823 (5bbe6a9f)\nbuilt with clang") == "b4823 (5bbe6a9f)"
    assert parse_llama_cpp_version("ggml_metal_init...\nversion: 12032 (a1b2c3d)") == "b12032 (a1b2c3d)"
    assert (
        parse_llama_cpp_version("version: 0.8.0-dev (build 12032, commit dde879bc4)")
        == "b12032 (dde879bc4)"
    )
    assert parse_llama_cpp_version("pas de version") is None


def test_run_metadata_records_llama_cpp_version_and_binary():
    from pathlib import Path

    from evaluate import run_metadata

    config = {
        "paths": {"model": "models/x.gguf", "llama_cli": "vendor/inexistant/llama-completion"},
        "inference": {"seed": 1},
    }

    meta = run_metadata(config, use_rag=False, prompts_file=Path("eval/prompts_fr.jsonl"))

    assert meta["llama_cli"] == "vendor/inexistant/llama-completion"
    assert meta["llama_cpp_rev"] is None


def test_truncation_status():
    from evaluate import truncation_status

    assert truncation_status("Réponse complète. [end of text]\n\n", "") == (False, None)
    assert truncation_status("Réponse coupée", "") == (True, "max_tokens")
    assert truncation_status(
        "Réponse coupée", "context full and context shift is disabled => stopping"
    ) == (True, "context_full")


def _eval_config(tmp_path, overrides=None):
    import evaluate

    config = evaluate.load_config()
    config["paths"] = {**config["paths"]}
    config["sampling_by_model"] = overrides or {}
    return config


def test_eval_generation_keeps_eval_context_and_marks_truncation(monkeypatch, tmp_path):
    import subprocess

    import evaluate

    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="Début de réponse sans fin", stderr="")

    monkeypatch.setattr(evaluate.subprocess, "run", fake_run)

    out = evaluate.call_llama_cli("prompt", _eval_config(tmp_path))

    cmd = captured["cmd"]
    assert cmd[cmd.index("-c") + 1] == "4096"
    assert cmd[cmd.index("--min-p") + 1] == "0.05"
    assert cmd[cmd.index("-s") + 1] == "42"
    assert out == {
        "response": "Début de réponse sans fin",
        "truncated": True,
        "truncated_reason": "max_tokens",
    }
    assert "limite de longueur" not in out["response"]


def test_eval_generation_applies_per_model_sampling(monkeypatch, tmp_path):
    import subprocess
    from pathlib import Path

    import evaluate

    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="Fin. [end of text]", stderr="")

    monkeypatch.setattr(evaluate.subprocess, "run", fake_run)
    config = _eval_config(tmp_path)
    model_file = Path(config["paths"]["model"]).name
    config["sampling_by_model"] = {model_file: {"top_k": 20, "top_p": 0.8, "min_p": 0.0}}

    out = evaluate.call_llama_cli("prompt", config)

    cmd = captured["cmd"]
    assert cmd[cmd.index("--top-k") + 1] == "20"
    assert cmd[cmd.index("--top-p") + 1] == "0.8"
    assert cmd[cmd.index("--min-p") + 1] == "0.0"
    assert out["truncated"] is False and out["response"] == "Fin."
    meta = evaluate.run_metadata(config, use_rag=False, prompts_file=Path("eval/prompts_fr.jsonl"))
    assert meta["sampling"]["top_k"] == 20
    assert meta["n_ctx"] == 4096
