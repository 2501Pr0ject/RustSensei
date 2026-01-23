#!/usr/bin/env python3
"""
Construction de l'index RAG pour RustSensei.

Chunking par sections markdown avec métadonnées riches.
"""

import pickle
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml
from rich.console import Console
from rich.progress import track

console = Console()

PROJECT_ROOT = Path(__file__).parent.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"
RAG_DIR = PROJECT_ROOT / "rag"


@dataclass
class Chunk:
    """Un chunk avec ses métadonnées."""
    text: str
    source: str           # book, rbe, reference
    source_name: str      # Rust Book, Rust by Example, etc.
    path: str             # chemin du fichier
    heading: str          # titre de section (H1 > H2 > H3)
    anchor: str           # ancre URL si disponible
    token_count: int      # nombre approximatif de tokens
    base_url: str = ""    # URL de base pour citations (M7)


def load_config():
    """Charge la configuration RAG."""
    config_path = CONFIGS_DIR / "rag_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def estimate_tokens(text: str) -> int:
    """Estime le nombre de tokens (approximation simple)."""
    # Approximation: 1 token ≈ 4 caractères pour l'anglais
    return len(text) // 4


def slugify(text: str) -> str:
    """Convertit un texte en ancre URL."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text.strip('-')


def parse_markdown_sections(content: str, file_path: str, source_id: str, source_name: str) -> list[dict]:
    """
    Parse un fichier markdown et extrait les sections.

    Retourne une liste de sections avec leur contenu et métadonnées.
    """
    sections = []

    # Pattern pour les headers markdown
    header_pattern = re.compile(r'^(#{1,3})\s+(.+)$', re.MULTILINE)

    # Trouver tous les headers
    headers = list(header_pattern.finditer(content))

    if not headers:
        # Pas de headers, traiter tout le fichier comme une section
        sections.append({
            "content": content.strip(),
            "heading": Path(file_path).stem.replace('-', ' ').replace('_', ' ').title(),
            "level": 1,
            "anchor": slugify(Path(file_path).stem),
        })
        return sections

    # Stack pour construire le heading hiérarchique
    heading_stack = []

    for i, match in enumerate(headers):
        level = len(match.group(1))  # Nombre de #
        title = match.group(2).strip()
        start = match.end()

        # Fin = début du prochain header ou fin du fichier
        end = headers[i + 1].start() if i + 1 < len(headers) else len(content)
        section_content = content[start:end].strip()

        # Mettre à jour le stack des headings
        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()
        heading_stack.append((level, title))

        # Construire le heading hiérarchique
        heading_parts = [h[1] for h in heading_stack]
        full_heading = " > ".join(heading_parts)

        if section_content:
            sections.append({
                "content": section_content,
                "heading": full_heading,
                "level": level,
                "anchor": slugify(title),
            })

    return sections


def parse_rust_file(content: str, file_path: str, source_id: str, source_name: str) -> list[dict]:
    """
    Parse un fichier Rust et extrait les commentaires et le code comme documentation.

    Utilise pour Rustlings - extrait les exercices avec leurs explications.
    """
    sections = []

    # Extraire le nom de l'exercice du chemin
    path_parts = Path(file_path).parts
    exercise_name = Path(file_path).stem

    # Trouver la categorie (dossier parent)
    category = path_parts[-2] if len(path_parts) > 1 else "general"
    heading = f"{category.replace('_', ' ').title()} > {exercise_name.replace('_', ' ').title()}"

    # Extraire les commentaires de documentation (// ou ///)
    doc_lines = []
    code_lines = []
    in_multiline_comment = False

    for line in content.split('\n'):
        stripped = line.strip()

        # Commentaires multilignes
        if '/*' in stripped:
            in_multiline_comment = True
        if '*/' in stripped:
            in_multiline_comment = False
            continue

        if in_multiline_comment:
            doc_lines.append(stripped.lstrip('* '))
        elif stripped.startswith('///') or stripped.startswith('//!'):
            # Doc comments
            doc_lines.append(stripped[3:].strip())
        elif stripped.startswith('//'):
            # Regular comments (souvent des explications dans Rustlings)
            comment = stripped[2:].strip()
            if comment and not comment.startswith('TODO') and not comment.startswith('FIXME'):
                doc_lines.append(comment)
        else:
            code_lines.append(line)

    # Construire le contenu: commentaires + code
    doc_text = '\n'.join(doc_lines).strip()
    code_text = '\n'.join(code_lines).strip()

    # Filtrer le code pour garder uniquement les parties pertinentes
    if code_text:
        # Garder le code comme exemple
        formatted_content = ""
        if doc_text:
            formatted_content = f"{doc_text}\n\n"
        formatted_content += f"```rust\n{code_text}\n```"

        sections.append({
            "content": formatted_content,
            "heading": heading,
            "level": 2,
            "anchor": slugify(exercise_name),
        })

    return sections


def chunk_section(section: dict, config: dict, source_id: str, source_name: str, file_path: str, base_url: str = "") -> list[Chunk]:
    """
    Découpe une section en chunks si nécessaire.

    - Si section < min_tokens: sera mergée avec la suivante (géré par l'appelant)
    - Si section > max_tokens: split en sous-chunks avec overlap
    - Sinon: garde tel quel
    """
    chunks = []
    content = section["content"]
    token_count = estimate_tokens(content)
    max_tokens = config.get("max_tokens", 800)
    overlap_tokens = config.get("overlap_tokens", 50)

    if token_count <= max_tokens:
        # Section de taille acceptable
        chunks.append(Chunk(
            text=content,
            source=source_id,
            source_name=source_name,
            path=file_path,
            heading=section["heading"],
            anchor=section["anchor"],
            token_count=token_count,
            base_url=base_url,
        ))
    else:
        # Section trop longue, split par paragraphes avec overlap
        paragraphs = content.split('\n\n')
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        overlap_buffer = []  # Buffer pour l'overlap

        for para in paragraphs:
            para_tokens = estimate_tokens(para)

            if current_tokens + para_tokens > max_tokens and current_chunk:
                # Sauvegarder le chunk actuel
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(Chunk(
                    text=chunk_text,
                    source=source_id,
                    source_name=source_name,
                    path=file_path,
                    heading=f"{section['heading']} (part {chunk_index + 1})",
                    anchor=f"{section['anchor']}-{chunk_index}",
                    token_count=estimate_tokens(chunk_text),
                    base_url=base_url,
                ))

                # Garder les derniers paragraphes pour l'overlap
                overlap_buffer = []
                overlap_size = 0
                for p in reversed(current_chunk):
                    p_tokens = estimate_tokens(p)
                    if overlap_size + p_tokens <= overlap_tokens:
                        overlap_buffer.insert(0, p)
                        overlap_size += p_tokens
                    else:
                        break

                current_chunk = overlap_buffer.copy()
                current_tokens = overlap_size
                chunk_index += 1

            current_chunk.append(para)
            current_tokens += para_tokens

        # Dernier chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            suffix = f" (part {chunk_index + 1})" if chunk_index > 0 else ""
            chunks.append(Chunk(
                text=chunk_text,
                source=source_id,
                source_name=source_name,
                path=file_path,
                heading=f"{section['heading']}{suffix}",
                anchor=f"{section['anchor']}-{chunk_index}" if chunk_index > 0 else section['anchor'],
                token_count=estimate_tokens(chunk_text),
                base_url=base_url,
            ))

    return chunks


def merge_small_chunks(chunks: list[Chunk], min_tokens: int) -> list[Chunk]:
    """Fusionne les chunks trop petits avec le suivant."""
    if not chunks:
        return chunks

    merged = []
    buffer = None

    for chunk in chunks:
        if buffer is None:
            if chunk.token_count < min_tokens:
                buffer = chunk
            else:
                merged.append(chunk)
        else:
            # Fusionner le buffer avec ce chunk
            merged_text = f"{buffer.text}\n\n{chunk.text}"
            merged_chunk = Chunk(
                text=merged_text,
                source=chunk.source,
                source_name=chunk.source_name,
                path=buffer.path if buffer.path == chunk.path else f"{buffer.path}, {chunk.path}",
                heading=buffer.heading,  # Garder le heading du premier
                anchor=buffer.anchor,
                token_count=estimate_tokens(merged_text),
                base_url=buffer.base_url,  # Garder l'URL du premier
            )

            if merged_chunk.token_count < min_tokens:
                buffer = merged_chunk
            else:
                merged.append(merged_chunk)
                buffer = None

    # Ajouter le buffer restant
    if buffer:
        merged.append(buffer)

    return merged


def process_source(source_config: dict, chunking_config: dict) -> list[Chunk]:
    """Traite une source de documents."""
    source_path = PROJECT_ROOT / source_config["path"]
    source_id = source_config["id"]
    source_name = source_config["name"]
    base_url = source_config.get("base_url", "")
    source_type = source_config.get("type", "markdown")

    if not source_path.exists():
        console.print(f"  [yellow]Source non trouvée: {source_path}[/yellow]")
        return []

    all_chunks = []

    # Determiner les extensions selon le type
    if source_type == "rust":
        files = list(source_path.rglob("*.rs"))
        parser = parse_rust_file
    else:
        files = list(source_path.rglob("*.md"))
        parser = parse_markdown_sections

    for file in track(files, description=f"  {source_name}"):
        try:
            with open(file, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            console.print(f"  [red]Erreur lecture {file}: {e}[/red]")
            continue

        # Skip les fichiers vides ou très courts
        if len(content) < 100:
            continue

        rel_path = str(file.relative_to(source_path))

        # Parser les sections selon le type
        sections = parser(content, rel_path, source_id, source_name)

        # Chunker chaque section
        for section in sections:
            chunks = chunk_section(section, chunking_config, source_id, source_name, rel_path, base_url)
            all_chunks.extend(chunks)

    # Merger les chunks trop petits
    min_tokens = chunking_config.get("min_tokens", 100)
    all_chunks = merge_small_chunks(all_chunks, min_tokens)

    return all_chunks


def create_embeddings(chunks: list[Chunk], config: dict):
    """Crée les embeddings pour les chunks."""
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError:
        console.print("[red]sentence-transformers non installé.[/red]")
        return None

    console.print(f"Modèle: {config['model']}")
    model = SentenceTransformer(config["model"], device=config.get("device", "cpu"))

    texts = [chunk.text for chunk in chunks]
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


def save_index(index, chunks: list[Chunk], config: dict):
    """Sauvegarde l'index, les métadonnées et le manifest."""
    import json
    from collections import Counter
    from datetime import datetime

    import faiss

    index_dir = RAG_DIR / "index"
    index_path = index_dir / "rustsensei.faiss"
    metadata_path = index_dir / "metadata.pkl"
    manifest_path = index_dir / "manifest.json"

    index_dir.mkdir(parents=True, exist_ok=True)

    # 1. Index FAISS
    faiss.write_index(index, str(index_path))
    console.print(f"Index: {index_path}")

    # 2. Métadonnées chunks
    metadata = [asdict(chunk) for chunk in chunks]
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata, f)
    console.print(f"Metadata: {metadata_path}")

    # 3. Manifest de build
    source_counts = Counter(c.source for c in chunks)
    total_tokens = sum(c.token_count for c in chunks)

    manifest = {
        "build_timestamp": datetime.now().isoformat(),
        "sources": {
            src["id"]: {
                "name": src["name"],
                "path": src["path"],
                "chunks": source_counts.get(src["id"], 0),
            }
            for src in config["sources"]
            if src.get("enabled", False)
        },
        "total_chunks": len(chunks),
        "total_tokens": total_tokens,
        "avg_tokens_per_chunk": total_tokens // len(chunks) if chunks else 0,
        "chunking": config["chunking"],
        "embeddings": {
            "model": config["embeddings"]["model"],
            "dimension": config["embeddings"]["dimension"],
            "normalize": config["embeddings"].get("normalize", True),
        },
        "index": {
            "type": config["index"]["type"],
            "vectors": index.ntotal,
        },
        "versions": {
            "faiss": faiss.__version__,
        },
    }

    # Ajouter version sentence-transformers si disponible
    try:
        import sentence_transformers
        manifest["versions"]["sentence_transformers"] = sentence_transformers.__version__
    except (ImportError, AttributeError):
        pass

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    console.print(f"Manifest: {manifest_path}")


def print_stats(chunks: list[Chunk]):
    """Affiche les statistiques des chunks."""
    from collections import Counter

    source_counts = Counter(c.source for c in chunks)
    total_tokens = sum(c.token_count for c in chunks)
    avg_tokens = total_tokens // len(chunks) if chunks else 0

    console.print("\n[bold]Statistiques[/bold]")
    for source, count in source_counts.items():
        console.print(f"  {source}: {count} chunks")
    console.print(f"  Total: {len(chunks)} chunks")
    console.print(f"  Tokens: ~{total_tokens:,} (avg: {avg_tokens})")


def main():
    """Point d'entrée."""
    console.print("[bold blue]Construction index RAG[/bold blue]\n")

    config = load_config()

    # 1. Charger et chunker les documents
    console.print("[bold]1. Chunking par sections markdown[/bold]")
    all_chunks = []
    for source in config["sources"]:
        if source.get("enabled", False):
            chunks = process_source(source, config["chunking"])
            all_chunks.extend(chunks)
            console.print(f"  → {len(chunks)} chunks\n")

    if not all_chunks:
        console.print("[yellow]Aucun chunk. Lancez 'make download-docs' d'abord.[/yellow]")
        return

    print_stats(all_chunks)

    # 2. Embeddings
    console.print("\n[bold]2. Embeddings[/bold]")
    embeddings = create_embeddings(all_chunks, config["embeddings"])
    if embeddings is None:
        return

    # 3. Index FAISS
    console.print("\n[bold]3. Index FAISS[/bold]")
    index = build_faiss_index(embeddings, config["index"])
    if index is None:
        return

    # 4. Sauvegarder
    console.print("\n[bold]4. Sauvegarde[/bold]")
    save_index(index, all_chunks, config)

    console.print("\n[bold green]Index RAG construit avec succès[/bold green]")


if __name__ == "__main__":
    main()
