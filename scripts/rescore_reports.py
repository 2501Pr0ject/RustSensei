#!/usr/bin/env python3
"""
Renote des rapports d'evaluation a partir des reponses stockees, sans regenerer.

Utile quand la notation (SCORER_VERSION) ou les mots-cles attendus changent :
toutes les evaluations a comparer doivent etre notees de la meme facon.

- Le marqueur "[end of text]" de llama-cli est retire des reponses (rapports
  anterieurs au 01/11/2026) avant la notation.
- Les rapports d'origine ne sont pas modifies : les copies renotees sont ecrites
  dans reports/rescored/ (meme nom de fichier), avec scorer_version et la trace
  de la renotation dans les metadonnees.

Usage:
    python scripts/rescore_reports.py reports/eval_rag_A.json reports/eval_rag_B_s*.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from evaluate import (
    EVAL_DIR,
    PROJECT_ROOT,
    SCORER_VERSION,
    evaluate_response,
    load_prompts,
)

from app.chat import clean_llama_output

DEFAULT_OUT_DIR = PROJECT_ROOT / "reports" / "rescored"


def rescore_report(report: dict, prompts: dict[int, dict], source: str, prompts_file: str) -> dict:
    """Renote un rapport (copie) avec la notation et les prompts courants."""
    rescored = {k: v for k, v in report.items() if k != "results"}
    results = []
    cleaned = 0
    for result in report["results"]:
        response = clean_llama_output(result["response"])
        cleaned += response != result["response"]
        prompt = prompts[result["prompt_id"]]
        results.append(
            {
                **result,
                "response": response,
                "evaluation": evaluate_response(response, prompt),
            }
        )
    rescored.update(
        {
            "scorer_version": SCORER_VERSION,
            "prompts_file": prompts_file,
            "rescored": {
                "from": source,
                "at": datetime.now().isoformat(timespec="seconds"),
                "original_scorer_version": report.get("scorer_version", 1),
                "responses_cleaned": cleaned,
            },
            "results": results,
        }
    )
    return rescored


def main():
    parser = argparse.ArgumentParser(description="Renotation de rapports d'evaluation")
    parser.add_argument("reports", nargs="+", type=Path, help="Rapports a renoter")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--prompts", type=Path, default=EVAL_DIR / "prompts_fr.jsonl")
    args = parser.parse_args()

    prompts = {p["id"]: p for p in load_prompts(args.prompts)}
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for path in args.reports:
        with open(path, encoding="utf-8") as f:
            report = json.load(f)
        rescored = rescore_report(report, prompts, str(path), str(args.prompts))
        out = args.out_dir / path.name
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rescored, f, ensure_ascii=False, indent=2)
        results = rescored["results"]
        score = sum(r["evaluation"]["scores"]["auto_composite"] for r in results) / len(results)
        print(
            f"{path.name}: {len(results)} reponses, {rescored['rescored']['responses_cleaned']} "
            f"nettoyees, score v{SCORER_VERSION} {score:.2f} -> {out}"
        )


if __name__ == "__main__":
    main()
