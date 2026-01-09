#!/usr/bin/env python3
"""
Évaluation RustSensei via llama-cli.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml
from rich.console import Console
from rich.progress import track
from rich.table import Table

console = Console()

PROJECT_ROOT = Path(__file__).parent.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"
EVAL_DIR = PROJECT_ROOT / "eval"
REPORTS_DIR = PROJECT_ROOT / "reports"


def load_config() -> dict:
    """Charge la configuration du modèle."""
    config_path = CONFIGS_DIR / "model_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_prompts(prompts_file: Path) -> list[dict]:
    """Charge les prompts d'évaluation."""
    prompts = []
    with open(prompts_file, encoding="utf-8") as f:
        for line in f:
            prompts.append(json.loads(line))
    return prompts


def load_rubric(rubric_file: Path) -> dict:
    """Charge la grille d'évaluation."""
    with open(rubric_file, encoding="utf-8") as f:
        return json.load(f)


def build_prompt(user_message: str, config: dict) -> str:
    """Construit le prompt avec le template ChatML."""
    system = config["prompt"]["system"]
    template = config["prompt"]["template"]
    return template.format(system=system, user=user_message)


def call_llama_cli(prompt: str, config: dict) -> str:
    """Appelle llama-cli et retourne la réponse."""
    llama_cli = PROJECT_ROOT / config["paths"]["llama_cli"]
    model_path = PROJECT_ROOT / config["paths"]["model"]

    if not llama_cli.exists():
        console.print(f"[red]llama-cli non trouvé: {llama_cli}[/red]")
        console.print("[yellow]Lancez: make install-llama[/yellow]")
        sys.exit(1)

    if not model_path.exists():
        console.print(f"[red]Modèle non trouvé: {model_path}[/red]")
        console.print("[yellow]Lancez: make download-model[/yellow]")
        sys.exit(1)

    inf = config["inference"]

    cmd = [
        str(llama_cli),
        "-m", str(model_path),
        "-p", prompt,
        "-n", str(inf.get("n_predict", 1024)),
        "-c", str(inf.get("n_ctx", 4096)),
        "-t", str(inf.get("threads", 8)),
        "-ngl", str(inf.get("n_gpu_layers", 99)),
        "--temp", str(inf.get("temp", 0.7)),
        "--top-p", str(inf.get("top_p", 0.9)),
        "--top-k", str(inf.get("top_k", 40)),
        "--repeat-penalty", str(inf.get("repeat_penalty", 1.1)),
        "-s", str(inf.get("seed", 42)),  # Seed pour reproductibilité
        "--no-display-prompt",
        "-no-cnv",  # Disable conversation mode for batch eval
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutes max
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {e}]"


def evaluate_response(response: str, prompt_data: dict) -> dict:
    """Évalue une réponse selon la grille."""
    scores = {}
    auto_checks = {}

    # 1. Langue française
    french_words = ["le", "la", "les", "de", "du", "des", "un", "une", "est", "sont"]
    french_count = sum(1 for word in french_words if f" {word} " in response.lower())
    auto_checks["language"] = french_count >= 3

    # 2. Blocs de code
    auto_checks["code_blocks"] = "```rust" in response or "```" in response

    # 3. Topics couverts
    expected_topics = prompt_data.get("expected_topics", [])
    if expected_topics:
        covered = sum(
            1 for topic in expected_topics if topic.lower() in response.lower()
        )
        auto_checks["expected_topics"] = covered / len(expected_topics)
    else:
        auto_checks["expected_topics"] = 1.0

    # 4. Longueur de réponse
    word_count = len(response.split())
    auto_checks["response_length"] = 100 <= word_count <= 800

    # Score de format (sections présentes)
    sections = ["## TL;DR", "## Problème", "## Solution", "## Explication", "## À retenir"]
    sections_found = sum(1 for s in sections if s in response)
    scores["format"] = sections_found / len(sections) * 5

    # Score composite
    auto_score = (
        (1 if auto_checks["language"] else 0) * 0.2
        + (1 if auto_checks["code_blocks"] else 0) * 0.2
        + auto_checks["expected_topics"] * 0.4
        + (1 if auto_checks["response_length"] else 0) * 0.2
    )
    scores["auto_composite"] = auto_score * 5

    return {
        "scores": scores,
        "auto_checks": auto_checks,
        "word_count": word_count,
        "sections_found": sections_found,
    }


def run_evaluation(prompts: list[dict], config: dict) -> list[dict]:
    """Exécute l'évaluation sur tous les prompts."""
    results = []

    for prompt_data in track(prompts, description="Évaluation..."):
        # Construire le prompt
        full_prompt = build_prompt(prompt_data["prompt"], config)

        # Appeler llama-cli
        response = call_llama_cli(full_prompt, config)

        # Évaluer
        eval_result = evaluate_response(response, prompt_data)

        results.append({
            "prompt_id": prompt_data["id"],
            "category": prompt_data["category"],
            "difficulty": prompt_data["difficulty"],
            "prompt": prompt_data["prompt"],
            "response": response,
            "evaluation": eval_result,
        })

    return results


def print_summary(results: list[dict]):
    """Affiche un résumé des résultats."""
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r["evaluation"]["scores"].get("auto_composite", 0))

    table = Table(title="Résumé évaluation")
    table.add_column("Catégorie", style="cyan")
    table.add_column("N", justify="right")
    table.add_column("Score", justify="right")

    for cat, scores in sorted(categories.items()):
        avg = sum(scores) / len(scores) if scores else 0
        color = "green" if avg >= 3.5 else "yellow" if avg >= 2.5 else "red"
        table.add_row(cat, str(len(scores)), f"[{color}]{avg:.2f}/5[/{color}]")

    all_scores = [s for scores in categories.values() for s in scores]
    total_avg = sum(all_scores) / len(all_scores) if all_scores else 0
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{len(results)}[/bold]",
        f"[bold]{total_avg:.2f}/5[/bold]",
        style="bold",
    )

    console.print(table)

    # Checks automatiques
    console.print("\n[bold]Checks:[/bold]")
    for check in ["language", "code_blocks", "response_length"]:
        passed = sum(
            1 for r in results if r["evaluation"]["auto_checks"].get(check, False)
        )
        pct = passed / len(results) * 100 if results else 0
        console.print(f"  {check}: {passed}/{len(results)} ({pct:.0f}%)")


def save_results(results: list[dict], config: dict, output_path: Path):
    """Sauvegarde les résultats avec métadonnées pour reproductibilité."""
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "model": config["model"],
        "inference_params": config["inference"],
        "llama_cpp_rev": "b4823",
        "total_prompts": len(results),
        "results": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    console.print(f"\n[green]Résultats: {output_path}[/green]")


def main():
    """Point d'entrée."""
    parser = argparse.ArgumentParser(description="Évaluation RustSensei")
    parser.add_argument("--limit", type=int, default=0, help="Limiter le nombre de prompts")
    parser.add_argument("--output", type=str, default=None, help="Fichier de sortie")
    args = parser.parse_args()

    console.print("[bold blue]Évaluation RustSensei[/bold blue]\n")

    # Charger config
    config = load_config()
    console.print(f"Modèle: {config['model']['name']}")
    console.print(f"llama-cli: {config['paths']['llama_cli']}\n")

    # Charger prompts et rubric
    prompts_file = EVAL_DIR / "prompts_fr.jsonl"
    rubric_file = EVAL_DIR / "rubric.json"

    if not prompts_file.exists():
        console.print(f"[red]Prompts non trouvés: {prompts_file}[/red]")
        return

    prompts = load_prompts(prompts_file)
    rubric = load_rubric(rubric_file)

    if args.limit > 0:
        prompts = prompts[:args.limit]

    console.print(f"Prompts: {len(prompts)}")
    console.print(f"Critères: {len(rubric['criteria'])}\n")

    # Évaluer
    results = run_evaluation(prompts, config)

    # Résumé et sauvegarde
    print_summary(results)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(args.output) if args.output else REPORTS_DIR / f"eval_{timestamp}.json"
    save_results(results, config, output_file)


if __name__ == "__main__":
    main()
