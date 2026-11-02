"""
Resolution des directives mdBook {{#include ...}} et {{#rustdoc_include ...}}.

Les livres mdBook (Rust Book, Cookbook, Async Book) n'ecrivent pas le code de
leurs exemples dans le markdown : ils l'incluent depuis des fichiers (dossier
listings/ du Rust Book). Sans resolution, l'index RAG contient la directive au
lieu du code.

Formes gerees (semantique mdBook, lignes numerotees a partir de 1) :
    chemin            fichier entier
    chemin:ancre      lignes entre "ANCHOR: ancre" et "ANCHOR_END: ancre"
    chemin:N          ligne N
    chemin:N:M        lignes N a M
    chemin:N:         de la ligne N a la fin
    chemin::M         des lignes 1 a M
Pour rustdoc_include, seule la partie visible du livre est gardee (l'ancre si
elle est donnee, sinon le fichier entier). Les lignes de marqueurs ANCHOR sont
toujours retirees.
"""

import re
from pathlib import Path

MAX_DEPTH = 5  # inclusions imbriquees (un fichier inclus qui en inclut un autre)

DIRECTIVE = re.compile(r"\{\{#(rustdoc_include|include)\s+([^}]+?)\}\}")
ANCHOR_LINE = re.compile(r"ANCHOR(_END)?:\s*([\w-]+)")


def _select_lines(lines: list[str], spec: list[str]) -> list[str] | None:
    """Selection par ancre ou par plage de lignes ; None si l'ancre est absente."""
    if not spec:
        return lines
    if len(spec) == 1 and spec[0] and not spec[0].isdigit():
        anchor = spec[0]
        selected, inside, found = [], False, False
        for line in lines:
            marker = ANCHOR_LINE.search(line)
            if marker and marker.group(2) == anchor:
                found = True
                inside = marker.group(1) is None
                continue
            if inside:
                selected.append(line)
        return selected if found else None
    start = int(spec[0]) if spec[0] else 1
    if len(spec) == 1:
        return lines[start - 1 : start]
    end = int(spec[1]) if spec[1] else len(lines)
    return lines[start - 1 : end]


def resolve_directive(kind: str, argument: str, base_dir: Path, depth: int = 0) -> str | None:
    """Contenu a inserer pour une directive, ou None si elle ne peut pas etre resolue."""
    path_part, *spec = argument.strip().split(":")
    target = (base_dir / path_part).resolve()
    if not target.is_file():
        return None
    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    selected = _select_lines(lines, spec)
    if selected is None:
        return None
    visible = [line for line in selected if not ANCHOR_LINE.search(line)]
    text = "\n".join(visible).strip("\n")
    if depth < MAX_DEPTH and DIRECTIVE.search(text):
        text, _, _ = resolve_includes(text, target.parent, depth + 1)
    return text


def resolve_includes(content: str, base_dir: Path, depth: int = 0) -> tuple[str, int, int]:
    """
    Remplace les directives d'inclusion d'un fichier markdown.

    Args:
        content: Texte markdown.
        base_dir: Dossier du fichier markdown (les chemins sont relatifs a lui).

    Returns:
        (texte resolu, directives resolues, directives non resolues). Une
        directive non resolue est laissee telle quelle.
    """
    resolved = unresolved = 0

    def replace(match: re.Match) -> str:
        nonlocal resolved, unresolved
        text = resolve_directive(match.group(1), match.group(2), base_dir, depth)
        if text is None:
            unresolved += 1
            return match.group(0)
        resolved += 1
        return text

    return DIRECTIVE.sub(replace, content), resolved, unresolved


# Noms de fichiers mis en italique par le Rust Book (_Cargo.toml_, *src/main.rs*) :
# le modele recopie ces marqueurs tels quels dans ses reponses.
_FILE = r"(?:Cargo\.toml|Cargo\.lock|src(?:/[\w./-]+)?|[\w-]+\.rs|[\w/-]+\.toml)"
FILENAME_EMPHASIS = re.compile(
    r"(?<![\w*])_(" + _FILE + r")_(?!\w)" + r"|(?<![\w*])\*(" + _FILE + r")\*(?![\w*])"
)


def strip_filename_emphasis(text: str) -> tuple[str, int]:
    """Retire l'italique autour des noms de fichiers ; renvoie (texte, nombre de retraits)."""
    count = 0

    def replace(match: re.Match) -> str:
        nonlocal count
        count += 1
        return match.group(1) or match.group(2)

    return FILENAME_EMPHASIS.sub(replace, text), count
