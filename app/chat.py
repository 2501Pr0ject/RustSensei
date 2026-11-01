"""
Chat interactif RustSensei via llama-cli.
"""

import subprocess
import sys
from pathlib import Path

import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from .cache import ResponseCache, response_cache

console = Console()

PROJECT_ROOT = Path(__file__).parent.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"

# RAG retriever (lazy loaded)
_rag_retriever = None


def load_config() -> dict:
    """Charge la configuration du modèle."""
    config_path = CONFIGS_DIR / "model_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_prerequisites(config: dict) -> bool:
    """Vérifie que llama-cli et le modèle sont présents."""
    llama_cli = PROJECT_ROOT / config["paths"]["llama_cli"]
    model_path = PROJECT_ROOT / config["paths"]["model"]

    if not llama_cli.exists():
        console.print(f"[red]llama-cli non trouvé: {llama_cli}[/red]")
        console.print("[yellow]Lancez: make install-llama[/yellow]")
        return False

    if not model_path.exists():
        console.print(f"[red]Modèle non trouvé: {model_path}[/red]")
        console.print("[yellow]Lancez: make download-model[/yellow]")
        return False

    return True


def get_rag_retriever():
    """Retourne le retriever RAG (lazy loading)."""
    global _rag_retriever
    if _rag_retriever is None:
        from .rag import RAGRetriever
        _rag_retriever = RAGRetriever()
    return _rag_retriever


def format_history(history) -> str:
    """
    Formate l'historique de conversation pour le prompt.

    Args:
        history: Liste de messages {role: "user"|"assistant", content: str}.

    Returns:
        Bloc texte "Conversation precedente" (chaine vide si history vide).
    """
    lines = []
    for turn in history or []:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            continue
        speaker = "Utilisateur" if role == "user" else "RustSensei"
        lines.append(f"{speaker} : {content}")
    if not lines:
        return ""
    return "Conversation précédente :\n" + "\n".join(lines)


def build_user_content(
    user_message: str,
    context: str = None,
    history: list = None,
) -> str:
    """
    Construit le contenu du message utilisateur (sans template ChatML).

    Utilise tel quel par l'API chat de llama-server, qui applique lui-meme
    le template du modele, et par build_prompt pour llama-cli.

    Args:
        user_message: Question de l'utilisateur.
        context: Contexte RAG (documentation) optionnel.
        history: Tours precedents de la conversation ({role, content}).
    """
    if context:
        user_content = (
            f"Contexte de la documentation Rust officielle :\n{context}\n\n"
            f"---\nQuestion : {user_message}"
        )
    else:
        user_content = user_message

    history_block = format_history(history)
    if history_block:
        user_content = f"{history_block}\n\n---\n{user_content}"

    return user_content


def build_prompt(
    user_message: str,
    config: dict,
    context: str = None,
    history: list = None,
) -> str:
    """
    Construit le prompt complet avec le template ChatML (pour llama-cli).

    Args:
        user_message: Question de l'utilisateur.
        config: Configuration du modele.
        context: Contexte RAG (documentation) optionnel.
        history: Tours precedents de la conversation ({role, content}).
    """
    user_content = build_user_content(user_message, context=context, history=history)
    return config["prompt"]["template"].format(
        system=config["prompt"]["system"], user=user_content
    )


def call_llama_cli(prompt: str, config: dict) -> str:
    """Appelle llama-cli et retourne la réponse."""
    llama_cli = PROJECT_ROOT / config["paths"]["llama_cli"]
    model_path = PROJECT_ROOT / config["paths"]["model"]
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
        "--no-display-prompt",
        "-no-cnv",  # Disable llama.cpp's conversation mode (we handle it ourselves)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[Timeout - la génération a pris trop de temps]"
    except Exception as e:
        return f"[Erreur: {e}]"


def chat_loop(use_rag: bool = False):
    """Boucle de chat interactive."""
    config = load_config()

    if not check_prerequisites(config):
        sys.exit(1)

    console.print(
        Panel.fit(
            "[bold blue]RustSensei[/bold blue]",
            subtitle="'quit' pour quitter",
        )
    )

    retriever = None
    if use_rag:
        from .rag import check_rag_available

        available, error_msg = check_rag_available()
        if not available:
            console.print(f"[yellow]RAG non disponible: {error_msg}[/yellow]")
            console.print("[dim]Fallback vers mode baseline...[/dim]\n")
            use_rag = False
        else:
            try:
                console.print("[dim]Chargement index RAG...[/dim]")
                retriever = get_rag_retriever()
                console.print("[green]Mode RAG activé[/green]\n")
            except ImportError as e:
                console.print(f"[yellow]Dépendances RAG manquantes: {e}[/yellow]")
                console.print("[dim]Fallback vers mode baseline...[/dim]\n")
                use_rag = False

    console.print(f"[dim]Modèle: {config['model']['name']}[/dim]\n")

    history: list[dict] = []

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]Vous[/bold green]")

            if user_input.lower() in ("quit", "exit", "q"):
                console.print("[dim]À bientôt ![/dim]")
                break

            if not user_input.strip():
                continue

            history.append({"role": "user", "content": user_input})
            history = history[-6:]

            # RAG: récupérer le contexte (ou la réponse en cache)
            context = None
            citations = []
            response = None

            retriever_embedder = None
            if retriever:
                retriever_embedder = getattr(retriever, "embed_query", None)

            cache_query = ResponseCache.composite_key(history[:-1], user_input)
            cache_embedder = retriever_embedder if not history[:-1] else None

            if retriever:
                cached = response_cache.get(
                    cache_query, embedder=cache_embedder
                )
                if cached is not None:
                    response = cached["response"]
                    citations = cached["citations"]
                    console.print("[dim]Réponse servie depuis le cache[/dim]")
                else:
                    console.print("[dim]Recherche dans la documentation...[/dim]")
                    chunks = retriever.retrieve(user_input)
                    if chunks:
                        context = retriever.format_context(chunks)
                        citations = retriever.get_citations(chunks)

            # Construire le prompt et générer si absent du cache
            if response is None:
                console.print("[dim]Génération...[/dim]")
                full_prompt = build_prompt(
                    user_input, config, context=context, history=history[:-1]
                )
                response = call_llama_cli(full_prompt, config)

                if retriever:
                    response_cache.set(
                        cache_query,
                        response,
                        citations,
                        embedder=cache_embedder,
                    )

            history.append({"role": "assistant", "content": response})

            # Afficher la réponse
            console.print("\n[bold blue]RustSensei[/bold blue]:")
            console.print(Markdown(response))

            # Afficher les citations
            if citations:
                console.print("\n[dim]Sources :[/dim]")
                for citation in citations:
                    console.print(f"  [cyan]{citation}[/cyan]")

        except KeyboardInterrupt:
            console.print("\n[dim]À bientôt ![/dim]")
            break


def main():
    """Point d'entrée."""
    import argparse

    parser = argparse.ArgumentParser(description="Chat RustSensei")
    parser.add_argument("--rag", action="store_true", help="Activer le mode RAG")
    args = parser.parse_args()

    chat_loop(use_rag=args.rag)


if __name__ == "__main__":
    main()
