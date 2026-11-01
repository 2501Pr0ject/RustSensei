"""Tests unitaires du module scripts.compare_evals."""

from compare_evals import compare, paired_bootstrap_ci, per_prompt_scores, seed_spread


def _result(pid, score, category="basics", blocks=0, compiled=0):
    compilation = {"has_code": blocks > 0, "blocks_count": blocks, "compiled": compiled}
    return {
        "prompt_id": pid,
        "category": category,
        "prompt": f"question {pid}",
        "evaluation": {
            "scores": {"auto_composite": score},
            "auto_checks": {"compilation": compilation},
        },
    }


def _report(*results):
    return {"results": list(results)}


def test_per_prompt_scores_groups_seeds():
    reports = [
        _report(_result(1, 3.0, blocks=2, compiled=1)),
        _report(_result(1, 4.0, blocks=1, compiled=1)),
    ]

    grouped = per_prompt_scores(reports)

    assert grouped[1]["scores"] == [3.0, 4.0]
    assert grouped[1]["blocks"] == 3
    assert grouped[1]["compiled"] == 2


def test_compare_only_uses_common_prompts_and_averages_seeds():
    ref = per_prompt_scores([_report(_result(1, 2.0), _result(2, 3.0), _result(3, 5.0))])
    new = per_prompt_scores(
        [_report(_result(1, 3.0), _result(2, 3.0)), _report(_result(1, 4.0), _result(2, 3.0))]
    )

    result = compare(ref, new)

    assert result["n_prompts"] == 2
    assert result["deltas"] == {1: 1.5, 2: 0.0}
    assert result["delta"] == 0.75
    assert result["wins"] == 1
    assert result["losses"] == 0


def test_compare_flags_consistent_gain_as_significant():
    ref = per_prompt_scores([_report(*[_result(i, 2.0) for i in range(30)])])
    new = per_prompt_scores([_report(*[_result(i, 3.0 + (i % 3) * 0.1) for i in range(30)])])

    result = compare(ref, new)

    assert result["significant"] is True
    assert result["ci95"][0] > 0


def test_compare_noise_is_not_significant():
    ref = per_prompt_scores([_report(*[_result(i, 3.0) for i in range(20)])])
    new = per_prompt_scores(
        [_report(*[_result(i, 3.0 + (1.0 if i % 2 else -1.0)) for i in range(20)])]
    )

    result = compare(ref, new)

    assert result["delta"] == 0.0
    assert result["significant"] is False


def test_compare_by_category_and_compilation():
    ref = per_prompt_scores(
        [_report(_result(1, 2.0, "lifetimes", 2, 1), _result(2, 4.0, "traits", 1, 1))]
    )
    new = per_prompt_scores(
        [_report(_result(1, 3.0, "lifetimes", 2, 2), _result(2, 4.0, "traits", 0, 0))]
    )

    result = compare(ref, new)

    assert result["by_category"]["lifetimes"] == {"n": 1, "ref": 2.0, "new": 3.0}
    assert result["compilation"] == {"ref": (2, 3), "new": (2, 2)}


def test_paired_bootstrap_ci_is_deterministic_and_ordered():
    deltas = [0.5, -0.2, 0.1, 0.3, -0.1]

    first = paired_bootstrap_ci(deltas, samples=2000)
    second = paired_bootstrap_ci(deltas, samples=2000)

    assert first == second
    assert first[0] <= sum(deltas) / len(deltas) <= first[1]
    assert paired_bootstrap_ci([]) == (0.0, 0.0)


def test_seed_spread():
    reports = [_report(_result(1, 2.0), _result(2, 4.0)), _report(_result(1, 3.0), _result(2, 3.0))]

    assert seed_spread(reports) == [3.0, 3.0]


def test_held_out_ids_excludes_training_prompts(tmp_path):
    import json

    from compare_evals import held_out_ids

    prompts = tmp_path / "prompts.jsonl"
    prompts.write_text(
        "\n".join(
            json.dumps(p)
            for p in [
                {"id": 1, "prompt": "a"},
                {"id": 2, "prompt": "b", "in_lora_train": True},
                {"id": 3, "prompt": "c", "in_lora_train": False},
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert held_out_ids(prompts) == {1, 3}


def test_compare_restricted_to_ids():
    ref = per_prompt_scores([_report(_result(1, 2.0), _result(2, 2.0))])
    new = per_prompt_scores([_report(_result(1, 5.0), _result(2, 3.0))])

    result = compare(ref, new, only_ids={2})

    assert result["n_prompts"] == 1
    assert result["delta"] == 1.0


def test_repository_prompts_mark_lora_overlap():
    from pathlib import Path

    from compare_evals import held_out_ids

    prompts = Path(__file__).parent.parent / "eval" / "prompts_fr.jsonl"

    assert len(held_out_ids(prompts)) == 91 - 27


def test_parse_ids_ranges_and_lists():
    import argparse

    import pytest
    from compare_evals import parse_ids

    assert parse_ids("1-3,7, 10-11") == {1, 2, 3, 7, 10, 11}
    with pytest.raises(argparse.ArgumentTypeError):
        parse_ids("5-2")
    with pytest.raises(argparse.ArgumentTypeError):
        parse_ids(" , ")
