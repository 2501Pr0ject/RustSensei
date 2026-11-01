"""Tests unitaires du module scripts.rescore_reports."""

from rescore_reports import rescore_report


def _report():
    return {
        "mode": "rag",
        "results": [
            {
                "prompt_id": 1,
                "category": "async",
                "prompt": "Thread ou tâche ?",
                "response": "Planifié par le système d’exploitation.  [end of text]",
                "evaluation": {"scores": {"auto_composite": 0.0}},
            }
        ],
    }


def test_rescore_report_cleans_and_rescores_without_touching_original():
    original = _report()
    prompts = {1: {"id": 1, "expected_topics": [["OS", "système d'exploitation"]]}}

    rescored = rescore_report(original, prompts, "reports/x.json", "eval/p.jsonl")

    result = rescored["results"][0]
    assert result["response"] == "Planifié par le système d’exploitation."
    assert result["evaluation"]["auto_checks"]["expected_topics"] == 1.0
    assert rescored["scorer_version"] == 2
    assert rescored["rescored"]["responses_cleaned"] == 1
    assert rescored["rescored"]["original_scorer_version"] == 1
    assert rescored["rescored"]["from"] == "reports/x.json"
    assert rescored["mode"] == "rag"
    assert original["results"][0]["response"].endswith("[end of text]")
