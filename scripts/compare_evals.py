#!/usr/bin/env python3
"""
Compare deux configurations RustSensei a partir de leurs rapports d'evaluation.

Chaque cote (reference / candidat) peut regrouper plusieurs rapports, par exemple
un par seed : le score de chaque prompt est alors moyenne sur les seeds avant la
comparaison. Seuls les prompts presents des deux cotes sont compares.

L'ecart global est accompagne d'un intervalle de confiance a 95 % obtenu par
bootstrap apparie sur les prompts : un ecart dont l'intervalle contient 0 n'est
pas distinguable du bruit.

Usage:
    python scripts/compare_evals.py --ref reports/eval_rag_A_s*.json \\
        --new reports/eval_rag_B_s*.json
"""

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

BOOTSTRAP_SAMPLES = 10_000


def load_reports(paths: list[Path]) -> list[dict]:
    """Charge des rapports d'evaluation JSON."""
    reports = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            reports.append(json.load(f))
    return reports


def per_prompt_scores(reports: list[dict]) -> dict[int, dict]:
    """
    Regroupe les resultats par prompt sur plusieurs rapports (seeds).

    Returns:
        {prompt_id: {"category", "prompt", "scores": [...], "blocks", "compiled"}}
    """
    prompts: dict[int, dict] = {}
    for report in reports:
        for result in report["results"]:
            entry = prompts.setdefault(
                result["prompt_id"],
                {
                    "category": result["category"],
                    "prompt": result["prompt"],
                    "scores": [],
                    "blocks": 0,
                    "compiled": 0,
                },
            )
            entry["scores"].append(result["evaluation"]["scores"]["auto_composite"])
            compilation = result["evaluation"]["auto_checks"].get("compilation") or {}
            if compilation.get("has_code"):
                entry["blocks"] += compilation.get("blocks_count", 0)
                entry["compiled"] += compilation.get("compiled", 0)
    return prompts


def paired_bootstrap_ci(
    deltas: list[float],
    samples: int = BOOTSTRAP_SAMPLES,
    seed: int = 0,
) -> tuple[float, float]:
    """Intervalle de confiance a 95 % de la moyenne des ecarts (bootstrap)."""
    if not deltas:
        return (0.0, 0.0)
    rng = random.Random(seed)
    means = sorted(
        statistics.fmean(rng.choices(deltas, k=len(deltas))) for _ in range(samples)
    )
    return means[int(0.025 * samples)], means[int(0.975 * samples) - 1]


def compare(ref: dict[int, dict], new: dict[int, dict]) -> dict:
    """Compare deux ensembles de scores par prompt (prompts communs uniquement)."""
    common = sorted(set(ref) & set(new))
    deltas = [
        statistics.fmean(new[pid]["scores"]) - statistics.fmean(ref[pid]["scores"])
        for pid in common
    ]
    low, high = paired_bootstrap_ci(deltas)

    by_category = defaultdict(lambda: {"ref": [], "new": []})
    for pid in common:
        cat = ref[pid]["category"]
        by_category[cat]["ref"].append(statistics.fmean(ref[pid]["scores"]))
        by_category[cat]["new"].append(statistics.fmean(new[pid]["scores"]))

    def compile_rate(side: dict[int, dict]) -> tuple[int, int]:
        blocks = sum(side[pid]["blocks"] for pid in common)
        compiled = sum(side[pid]["compiled"] for pid in common)
        return compiled, blocks

    return {
        "n_prompts": len(common),
        "ref_mean": statistics.fmean(statistics.fmean(ref[p]["scores"]) for p in common)
        if common
        else 0.0,
        "new_mean": statistics.fmean(statistics.fmean(new[p]["scores"]) for p in common)
        if common
        else 0.0,
        "delta": statistics.fmean(deltas) if deltas else 0.0,
        "ci95": (low, high),
        "significant": low > 0 or high < 0,
        "wins": sum(d > 1e-9 for d in deltas),
        "losses": sum(d < -1e-9 for d in deltas),
        "by_category": {
            cat: {
                "n": len(v["ref"]),
                "ref": statistics.fmean(v["ref"]),
                "new": statistics.fmean(v["new"]),
            }
            for cat, v in sorted(by_category.items())
        },
        "compilation": {"ref": compile_rate(ref), "new": compile_rate(new)},
        "deltas": dict(zip(common, deltas)),
    }


def seed_spread(reports: list[dict]) -> list[float]:
    """Score global de chaque rapport (une valeur par seed)."""
    return [
        statistics.fmean(r["evaluation"]["scores"]["auto_composite"] for r in rep["results"])
        for rep in reports
    ]


def _fmt_rate(compiled: int, blocks: int) -> str:
    return f"{compiled}/{blocks} ({compiled / blocks:.0%})" if blocks else "0/0"


def main():
    parser = argparse.ArgumentParser(description="Comparaison de rapports d'evaluation")
    parser.add_argument("--ref", nargs="+", required=True, type=Path, help="Rapports de reference")
    parser.add_argument("--new", nargs="+", required=True, type=Path, help="Rapports candidats")
    args = parser.parse_args()

    ref_reports, new_reports = load_reports(args.ref), load_reports(args.new)
    result = compare(per_prompt_scores(ref_reports), per_prompt_scores(new_reports))

    for name, reports in (("Reference", ref_reports), ("Candidat", new_reports)):
        spread = seed_spread(reports)
        detail = ", ".join(f"{s:.2f}" for s in spread)
        print(f"{name:10} {len(reports)} rapport(s) : {detail}")

    low, high = result["ci95"]
    verdict = "significatif" if result["significant"] else "non significatif"
    print(
        f"\nPrompts communs : {result['n_prompts']}\n"
        f"Score : {result['ref_mean']:.2f} -> {result['new_mean']:.2f} "
        f"({result['delta']:+.3f}, IC95 [{low:+.2f}, {high:+.2f}], {verdict})\n"
        f"Prompts en hausse / baisse : {result['wins']} / {result['losses']}\n"
        f"Compilation : {_fmt_rate(*result['compilation']['ref'])} -> "
        f"{_fmt_rate(*result['compilation']['new'])}"
    )

    print("\nPar categorie :")
    for cat, v in result["by_category"].items():
        print(f"  {cat:18} n={v['n']:2}  {v['ref']:.2f} -> {v['new']:.2f} ({v['new'] - v['ref']:+.2f})")


if __name__ == "__main__":
    main()
