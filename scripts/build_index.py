#!/usr/bin/env python3
"""
Construction de l'index RAG pour RustSensei.
"""

import pickle
from pathlib import Path

import yaml
from rich.console import Console
from rich.progress import track

console = Console()

PROJECT_ROOT = Path(__file__).parent.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"
RAG_DIR = PROJECT_ROOT / "rag"


def load_config():
    """Charge la configuration RAG."""
    config_path = CONFIGS_DIR / "rag_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_documents(source_config: dict) -> list[dict]:
    """Charge les documents depuis une source."""
    source_path = RAG_DIR / "docs" / source_config["path"].split("/")[-1]
    documents = []

    if not source_path.exists():
        console.print(f"[yellow]Source non trouvée: {source_path}[/yellow]")
        return documents

    if source_config["type"] == "markdown":
        for md_file in source_path.glob("**/*.md"):
            with open(md_file, encoding="utf-8") as f:
                content = f.read()
            documents.append({
                "content": content,
                "source": source_config["name"],
                "file": str(md_file.relative_to(source_path)),
                "type": "markdown",
            })

    elif source_config["type"] == "jsonl":
        import json
        jsonl_path = Path(source_config["path"])
        if jsonl_path.exists():
            with open(jsonl_path, encoding="utf-8") as f:
                for line in f:
                    doc = json.loads(line)
                    documents.append({
                        "content": doc.get("content", ""),
                        "source": source_config["name"],
                        **doc,
                    })

    console.print(f"  Chargé {len(documents)} documents depuis {source_config['name']}")
    return documents


def chunk_documents(documents: list[dict], config: dict) -> list[dict]:
    """Découpe les documents en chunks."""
    chunks = []
    chunk_size = config["chunk_size"]
    overlap = config["chunk_overlap"]

    for doc in track(documents, description="Chunking..."):
        content = doc["content"]
        words = content.split()

        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i : i + chunk_size]
            if len(chunk_words) < 50:
                continue

            chunk_text = " ".join(chunk_words)
            chunks.append({
                "text": chunk_text,
                "source": doc["source"],
                "file": doc.get("file", ""),
                "chunk_index": len(chunks),
            })

    return chunks


def create_embeddings(chunks: list[dict], config: dict):
    """Crée les embeddings pour les chunks."""
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError:
        console.print("[red]sentence-transformers non installé.[/red]")
        return None

    console.print(f"Modèle: {config['model']}")
    model = SentenceTransformer(config["model"], device=config.get("device", "cpu"))

    texts = [chunk["text"] for chunk in chunks]
    console.print(f"Création embeddings pour {len(texts)} chunks...")

    embeddings = model.encode(
        texts,
        batch_size=config.get("batch_size", 32),
        show_progress_bar=True,
        normalize_embeddings=config.get("normalize", True),
    )

    return np.array(embeddings)


def build_faiss_index(embeddings, config: dict):
    """Construit l'index FAISS."""
    try:
        import faiss
    except ImportError:
        console.print("[red]faiss-cpu non installé.[/red]")
        return None

    dimension = embeddings.shape[1]
    console.print(f"Construction index (dim={dimension})...")

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    console.print(f"Index: {index.ntotal} vecteurs")

    return index


def save_index(index, chunks: list[dict]):
    """Sauvegarde l'index et les métadonnées."""
    import faiss

    index_path = RAG_DIR / "index" / "rustsensei.faiss"
    metadata_path = RAG_DIR / "index" / "metadata.pkl"

    index_path.parent.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(index_path))
    console.print(f"Index: {index_path}")

    with open(metadata_path, "wb") as f:
        pickle.dump(chunks, f)
    console.print(f"Metadata: {metadata_path}")


def main():
    """Point d'entrée."""
    console.print("[bold blue]Construction index RAG[/bold blue]\n")

    config = load_config()

    # 1. Charger les documents
    console.print("[bold]1. Documents[/bold]")
    all_documents = []
    for source in config["sources"]:
        if source.get("enabled", False):
            docs = load_documents(source)
            all_documents.extend(docs)

    if not all_documents:
        console.print("[yellow]Aucun document. Ajoutez des fichiers dans rag/docs/[/yellow]")
        return

    console.print(f"Total: {len(all_documents)} documents\n")

    # 2. Chunker
    console.print("[bold]2. Chunking[/bold]")
    chunks = chunk_documents(all_documents, config["chunking"])
    console.print(f"Total: {len(chunks)} chunks\n")

    # 3. Embeddings
    console.print("[bold]3. Embeddings[/bold]")
    embeddings = create_embeddings(chunks, config["embeddings"])
    if embeddings is None:
        return

    # 4. Index FAISS
    console.print("\n[bold]4. Index FAISS[/bold]")
    index = build_faiss_index(embeddings, config["index"])
    if index is None:
        return

    # 5. Sauvegarder
    console.print("\n[bold]5. Sauvegarde[/bold]")
    save_index(index, chunks)

    console.print("\n[bold green]Done[/bold green]")


if __name__ == "__main__":
    main()
