"""
Interface CLI pour RustSensei.
"""

import typer
from rich.console import Console

app = typer.Typer(
    name="rustsensei",
    help="RustSensei - Apprendre le Rust en français",
    add_completion=False,
)
console = Console()


@app.command()
def chat(
    rag: bool = typer.Option(False, "--rag", "-r", help="Activer le mode RAG"),
    model: str = typer.Option(None, "--model", "-m", help="Chemin vers le modèle GGUF"),
):
    """Lance une session de chat interactive."""
    from .chat import chat_loop

    chat_loop(use_rag=rag)


@app.command()
def eval(
    prompts_file: str = typer.Option(
        "eval/prompts_fr.jsonl", "--prompts", "-p", help="Fichier de prompts"
    ),
    output: str = typer.Option(
        "eval/results.json", "--output", "-o", help="Fichier de sortie"
    ),
):
    """Évalue le modèle sur les prompts de test."""
    console.print("[yellow]Évaluation non encore implémentée.[/yellow]")
    # TODO: Implémenter l'évaluation


@app.command()
def build_index(
    config: str = typer.Option(
        "configs/rag_config.yaml", "--config", "-c", help="Configuration RAG"
    ),
):
    """Construit l'index RAG à partir des documents."""
    console.print("[yellow]Construction de l'index non encore implémentée.[/yellow]")
    # TODO: Implémenter la construction de l'index


@app.command()
def info():
    """Affiche les informations du projet."""
    from . import __version__

    console.print(f"[bold blue]RustSensei[/bold blue] v{__version__}")
    console.print("Apprendre le Rust en français, localement")
    console.print()
    console.print("[dim]Commandes disponibles :[/dim]")
    console.print("  rustsensei chat     - Session de chat interactive")
    console.print("  rustsensei eval     - Évaluer le modèle")
    console.print("  rustsensei build-index - Construire l'index RAG")


if __name__ == "__main__":
    app()
