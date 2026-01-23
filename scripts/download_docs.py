#!/usr/bin/env python3
"""
Télécharge les sources de documentation Rust pour le RAG.

Sources :
- Rust Book (https://github.com/rust-lang/book)
- Rust by Example (https://github.com/rust-lang/rust-by-example)
- Rust Reference (https://github.com/rust-lang/reference)
- Rust Cookbook (https://github.com/rust-lang-nursery/rust-cookbook)
- Async Book (https://github.com/rust-lang/async-book)
- Rustlings (https://github.com/rust-lang/rustlings)
- Nomicon (https://github.com/rust-lang/nomicon)
- Edition Guide (https://github.com/rust-lang/edition-guide)
"""

import shutil
import subprocess
from pathlib import Path

from rich.console import Console

console = Console()

PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "rag" / "docs"

# Sources avec leur config
SOURCES = {
    "book": {
        "repo": "https://github.com/rust-lang/book.git",
        "branch": "main",
        "src_dir": "src",
        "name": "Rust Book",
    },
    "rbe": {
        "repo": "https://github.com/rust-lang/rust-by-example.git",
        "branch": "master",
        "src_dir": "src",
        "name": "Rust by Example",
    },
    "reference": {
        "repo": "https://github.com/rust-lang/reference.git",
        "branch": "master",
        "src_dir": "src",
        "name": "Rust Reference",
    },
    "cookbook": {
        "repo": "https://github.com/rust-lang-nursery/rust-cookbook.git",
        "branch": "master",
        "src_dir": "src",
        "name": "Rust Cookbook",
    },
    "async-book": {
        "repo": "https://github.com/rust-lang/async-book.git",
        "branch": "master",
        "src_dir": "src",
        "name": "Async Book",
    },
    "rustlings": {
        "repo": "https://github.com/rust-lang/rustlings.git",
        "branch": "main",
        "src_dir": "exercises",
        "name": "Rustlings",
    },
    "nomicon": {
        "repo": "https://github.com/rust-lang/nomicon.git",
        "branch": "master",
        "src_dir": "src",
        "name": "Rustonomicon",
    },
    "edition-guide": {
        "repo": "https://github.com/rust-lang/edition-guide.git",
        "branch": "master",
        "src_dir": "src",
        "name": "Edition Guide",
    },
}


def clone_or_update(source_id: str, config: dict) -> Path:
    """Clone ou met à jour un repo source."""
    target_dir = DOCS_DIR / source_id

    if target_dir.exists():
        console.print(f"  [dim]Mise à jour {config['name']}...[/dim]")
        try:
            subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=target_dir,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            console.print("  [yellow]Pull failed, re-cloning...[/yellow]")
            shutil.rmtree(target_dir)
            return clone_or_update(source_id, config)
    else:
        console.print(f"  [dim]Clonage {config['name']}...[/dim]")
        subprocess.run(
            [
                "git", "clone",
                "--depth", "1",
                "--branch", config["branch"],
                config["repo"],
                str(target_dir),
            ],
            capture_output=True,
            check=True,
        )

    return target_dir


def count_markdown_files(source_dir: Path) -> int:
    """Compte les fichiers markdown dans un répertoire."""
    return len(list(source_dir.rglob("*.md")))


def main():
    """Point d'entrée."""
    console.print("[bold blue]Téléchargement des sources RAG[/bold blue]\n")

    # Créer le dossier docs si nécessaire
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    stats = {}

    for source_id, config in SOURCES.items():
        console.print(f"[cyan]{config['name']}[/cyan]")

        try:
            target_dir = clone_or_update(source_id, config)
            src_path = target_dir / config["src_dir"]

            if src_path.exists():
                md_count = count_markdown_files(src_path)
                stats[source_id] = md_count
                console.print(f"  [green]✓[/green] {md_count} fichiers markdown\n")
            else:
                console.print("  [red]✗[/red] Dossier src/ non trouvé\n")
                stats[source_id] = 0

        except subprocess.CalledProcessError as e:
            console.print(f"  [red]✗[/red] Erreur: {e}\n")
            stats[source_id] = 0

    # Résumé
    console.print("[bold]Résumé[/bold]")
    total = sum(stats.values())
    for source_id, count in stats.items():
        name = SOURCES[source_id]["name"]
        console.print(f"  {name}: {count} fichiers")
    console.print(f"  [bold]Total: {total} fichiers markdown[/bold]")

    console.print(f"\n[green]Sources téléchargées dans {DOCS_DIR}[/green]")
    console.print("[dim]Lancez 'make build-index' pour construire l'index RAG[/dim]")


if __name__ == "__main__":
    main()
