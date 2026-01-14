#!/usr/bin/env python3
"""
Évaluation RustSensei via llama-cli.

Supporte le mode RAG pour comparaison baseline vs RAG.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml
from compile_check import check_response as check_compilation
from rich.console import Console
from rich.progress import track
from rich.table import Table

console = Console()

PROJECT_ROOT = Path(__file__).parent.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"
EVAL_DIR = PROJECT_ROOT / "eval"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Add app to path for imports
sys.path.insert(0, str(PROJECT_ROOT))

# RAG retriever (lazy loaded)
_rag_retriever = None


def get_rag_retriever():
    """Retourne le retriever RAG (lazy loading)."""
    global _rag_retriever
    if _rag_retriever is None:
        from app.rag import RAGRetriever
        _rag_retriever = RAGRetriever()
    return _rag_retriever


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


def build_prompt(user_message: str, config: dict, context: str = None) -> str:
    """Construit le prompt avec le template ChatML."""
    system = config["prompt"]["system"]
    template = config["prompt"]["template"]

    # Ajouter le contexte RAG si présent
    if context:
        augmented_message = (
            f"Contexte de la documentation Rust officielle :\n{context}\n\n"
            f"---\nQuestion : {user_message}"
        )
        return template.format(system=system, user=augmented_message)

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
    """Evalue une reponse selon la grille."""
    scores = {}
    auto_checks = {}

    # 1. Langue francaise
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

    # 4. Longueur de reponse
    word_count = len(response.split())
    auto_checks["response_length"] = 100 <= word_count <= 800

    # 5. Compilation du code Rust
    compile_result = check_compilation(response)
    auto_checks["compilation"] = compile_result

    # Score de format (sections presentes)
    sections = ["## TL;DR", "## Problème", "## Solution", "## Explication", "## À retenir"]
    sections_found = sum(1 for s in sections if s in response)
    scores["format"] = sections_found / len(sections) * 5

    # Score composite (inclut compilation si code present)
    compilation_score = 0
    if compile_result["has_code"]:
        compilation_score = compile_result["compilation_rate"] if compile_result["compilation_rate"] else 0

    auto_score = (
        (1 if auto_checks["language"] else 0) * 0.2
        + (1 if auto_checks["code_blocks"] else 0) * 0.15
        + auto_checks["expected_topics"] * 0.35
        + (1 if auto_checks["response_length"] else 0) * 0.15
        + compilation_score * 0.15  # Bonus compilation
    )
    scores["auto_composite"] = auto_score * 5

    return {
        "scores": scores,
        "auto_checks": auto_checks,
        "word_count": word_count,
        "sections_found": sections_found,
    }


def run_evaluation(prompts: list[dict], config: dict, use_rag: bool = False) -> list[dict]:
    """Exécute l'évaluation sur tous les prompts."""
    results = []
    retriever = None

    if use_rag:
        try:
            console.print("[dim]Chargement index RAG...[/dim]")
            retriever = get_rag_retriever()
            console.print("[green]Mode RAG activé[/green]\n")
        except FileNotFoundError as e:
            console.print(f"[red]{e}[/red]")
            sys.exit(1)
        except ImportError as e:
            console.print(f"[red]Dépendances RAG manquantes: {e}[/red]")
            sys.exit(1)

    mode_desc = "Évaluation (RAG)" if use_rag else "Évaluation"

    for prompt_data in track(prompts, description=f"{mode_desc}..."):
        # RAG: récupérer le contexte
        context = None
        citations = []
        if retriever:
            chunks = retriever.retrieve(prompt_data["prompt"])
            if chunks:
                context = retriever.format_context(chunks)
                citations = retriever.get_citations(chunks)

        # Construire le prompt
        full_prompt = build_prompt(prompt_data["prompt"], config, context=context)

        # Appeler llama-cli
        response = call_llama_cli(full_prompt, config)

        # Évaluer
        eval_result = evaluate_response(response, prompt_data)

        result = {
            "prompt_id": prompt_data["id"],
            "category": prompt_data["category"],
            "difficulty": prompt_data["difficulty"],
            "prompt": prompt_data["prompt"],
            "response": response,
            "evaluation": eval_result,
        }

        # Ajouter les citations si RAG
        if citations:
            result["citations"] = citations

        results.append(result)

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

    # Compilation rate
    total_blocks = 0
    compiled_blocks = 0
    for r in results:
        comp = r["evaluation"]["auto_checks"].get("compilation", {})
        if comp.get("has_code"):
            total_blocks += comp.get("blocks_count", 0)
            compiled_blocks += comp.get("compiled", 0)

    if total_blocks > 0:
        comp_rate = compiled_blocks / total_blocks * 100
        console.print(f"  [bold]compilation[/bold]: {compiled_blocks}/{total_blocks} ({comp_rate:.0f}%)")


def save_results(results: list[dict], config: dict, output_path: Path, use_rag: bool = False):
    """Sauvegarde les résultats avec métadonnées pour reproductibilité."""
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "mode": "rag" if use_rag else "baseline",
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


def get_scores_by_category(results: list[dict]) -> dict[str, float]:
    """Extrait les scores moyens par catégorie."""
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r["evaluation"]["scores"].get("auto_composite", 0))

    return {cat: sum(scores) / len(scores) for cat, scores in categories.items()}


def print_comparison_table(baseline_results: list[dict], rag_results: list[dict]):
    """Affiche un tableau comparatif baseline vs RAG par catégorie."""
    baseline_scores = get_scores_by_category(baseline_results)
    rag_scores = get_scores_by_category(rag_results)

    all_categories = sorted(set(baseline_scores.keys()) | set(rag_scores.keys()))

    table = Table(title="Comparaison Baseline vs RAG")
    table.add_column("Catégorie", style="cyan")
    table.add_column("Baseline", justify="right")
    table.add_column("RAG", justify="right")
    table.add_column("Δ", justify="right")

    total_baseline = []
    total_rag = []

    for cat in all_categories:
        b_score = baseline_scores.get(cat, 0)
        r_score = rag_scores.get(cat, 0)
        delta = r_score - b_score
        delta_pct = (delta / b_score * 100) if b_score > 0 else 0

        total_baseline.append(b_score)
        total_rag.append(r_score)

        # Couleur du delta
        if delta > 0.1:
            delta_str = f"[green]+{delta_pct:.0f}%[/green]"
        elif delta < -0.1:
            delta_str = f"[red]{delta_pct:.0f}%[/red]"
        else:
            delta_str = "[dim]~0%[/dim]"

        table.add_row(cat, f"{b_score:.2f}/5", f"{r_score:.2f}/5", delta_str)

    # Total
    avg_baseline = sum(total_baseline) / len(total_baseline) if total_baseline else 0
    avg_rag = sum(total_rag) / len(total_rag) if total_rag else 0
    total_delta = avg_rag - avg_baseline
    total_delta_pct = (total_delta / avg_baseline * 100) if avg_baseline > 0 else 0

    if total_delta > 0:
        total_delta_str = f"[bold green]+{total_delta_pct:.0f}%[/bold green]"
    elif total_delta < 0:
        total_delta_str = f"[bold red]{total_delta_pct:.0f}%[/bold red]"
    else:
        total_delta_str = "[bold]~0%[/bold]"

    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{avg_baseline:.2f}/5[/bold]",
        f"[bold]{avg_rag:.2f}/5[/bold]",
        total_delta_str,
        style="bold",
    )

    console.print(table)


def run_ab_comparison(prompts: list[dict], config: dict) -> tuple[list[dict], list[dict]]:
    """Exécute une comparaison A/B baseline vs RAG."""
    # Vérifier si RAG est disponible
    from app.rag import check_rag_available

    available, error_msg = check_rag_available()
    if not available:
        console.print(f"[red]RAG non disponible: {error_msg}[/red]")
        sys.exit(1)

    # Baseline
    console.print("[bold yellow]Phase 1: Baseline[/bold yellow]")
    baseline_results = run_evaluation(prompts, config, use_rag=False)

    console.print()

    # RAG
    console.print("[bold green]Phase 2: RAG[/bold green]")
    rag_results = run_evaluation(prompts, config, use_rag=True)

    return baseline_results, rag_results


def main():
    """Point d'entrée."""
    parser = argparse.ArgumentParser(description="Évaluation RustSensei")
    parser.add_argument("--limit", type=int, default=0, help="Limiter le nombre de prompts")
    parser.add_argument("--output", type=str, default=None, help="Fichier de sortie")
    parser.add_argument("--rag", action="store_true", help="Activer le mode RAG")
    parser.add_argument("--compare", action="store_true", help="Comparaison A/B baseline vs RAG")
    args = parser.parse_args()

    # Charger config
    config = load_config()

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

    # Mode comparaison A/B
    if args.compare:
        console.print("[bold blue]Évaluation A/B : Baseline vs RAG[/bold blue]\n")
        console.print(f"Modèle: {config['model']['name']}")
        console.print(f"Prompts: {len(prompts)}\n")

        baseline_results, rag_results = run_ab_comparison(prompts, config)

        console.print("\n")
        print_comparison_table(baseline_results, rag_results)

        # Sauvegarder les deux résultats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_results(baseline_results, config, REPORTS_DIR / f"eval_baseline_{timestamp}.json", use_rag=False)
        save_results(rag_results, config, REPORTS_DIR / f"eval_rag_{timestamp}.json", use_rag=True)
        return

    # Mode simple (baseline ou RAG)
    mode_str = "[green]RAG[/green]" if args.rag else "[yellow]Baseline[/yellow]"
    console.print(f"[bold blue]Évaluation RustSensei[/bold blue] ({mode_str})\n")

    console.print(f"Modèle: {config['model']['name']}")
    console.print(f"llama-cli: {config['paths']['llama_cli']}\n")

    console.print(f"Prompts: {len(prompts)}")
    console.print(f"Critères: {len(rubric['criteria'])}\n")

    # Évaluer
    results = run_evaluation(prompts, config, use_rag=args.rag)

    # Résumé et sauvegarde
    print_summary(results)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_suffix = "_rag" if args.rag else "_baseline"
    output_file = Path(args.output) if args.output else REPORTS_DIR / f"eval{mode_suffix}_{timestamp}.json"
    save_results(results, config, output_file, use_rag=args.rag)


if __name__ == "__main__":
    main()
