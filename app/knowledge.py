"""
Graphe de concepts Rust pour l'expansion de requête (recherche lexicale).

Concepts cures avec aliases (FR/EN) et relations : permet d'elargir les
requetes qui couvrent plusieurs domaines (ex. "Rc entre threads" ->
Send/Sync/Arc) et de detecter les concepts presentes dans une question.
"""

import re
import unicodedata
from pathlib import Path

import yaml

from .config import PROJECT_ROOT

DEFAULT_KNOWLEDGE_PATH = "configs/knowledge_graph.yaml"


def normalize_text(text: str) -> str:
    """Minuscules sans accents, pour la detection insensible a la casse."""
    decomposed = unicodedata.normalize("NFD", text or "")
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return without_marks.casefold().strip()


class Concept:
    """Noeud du graphe : un concept Rust avec ses aliases et relations."""

    def __init__(self, id: str, name: str, aliases: list, related: list):
        self.id = id
        self.name = name
        self.aliases = [alias for alias in aliases if alias]
        self.related = [rid for rid in related if rid]


class KnowledgeGraph:
    """Graphe de concepts Rust : detection dans une question + expansion."""

    def __init__(self, concepts: list):
        self.concepts = concepts
        self._by_id = {concept.id: concept for concept in concepts if concept.id}
        self._patterns = []
        for concept in concepts:
            for alias in concept.aliases:
                normalized = normalize_text(alias)
                suffix = "s?" if not normalized.endswith("s") else ""
                pattern = re.compile(r"\b" + re.escape(normalized) + suffix + r"\b")
                self._patterns.append((concept.id, pattern))

    @classmethod
    def load(cls, path: Path = None) -> "KnowledgeGraph":
        """Charge le graphe depuis YAML (graphe vide si fichier absent/invalide)."""
        path = path or PROJECT_ROOT / DEFAULT_KNOWLEDGE_PATH

        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            return cls([])

        nodes = []
        if isinstance(raw, dict) and isinstance(raw.get("nodes"), list):
            for node in raw["nodes"]:
                if not isinstance(node, dict) or not node.get("id"):
                    continue
                nodes.append(
                    Concept(
                        id=str(node["id"]),
                        name=str(node.get("name", node["id"])),
                        aliases=list(node.get("aliases") or []),
                        related=list(node.get("related") or []),
                    )
                )
        return cls(nodes)

    @property
    def is_empty(self) -> bool:
        return not self.concepts

    def detect(self, query: str) -> list:
        """Retourne les concepts presents dans la question (ordre du graphe)."""
        normalized = normalize_text(query)
        matched = []
        for concept_id, pattern in self._patterns:
            if pattern.search(normalized):
                concept = self._by_id.get(concept_id)
                if concept is not None and concept not in matched:
                    matched.append(concept)
        return matched

    def related(self, detected: list) -> list:
        """Concepts lies aux concepts detectes, dedupliques, hors deja detectes."""
        result = []
        for concept in detected:
            for related_id in concept.related:
                node = self._by_id.get(related_id)
                if node is None or node in detected or node in result:
                    continue
                result.append(node)
        return result

    def expand(self, query: str, max_expansions: int = 3) -> list:
        """
        Termes d'expansion : aliases des concepts relies a la question.

        Args:
            query: Question de l'utilisateur.
            max_expansions: Nombre maximal de concepts lies utilises.

        Returns:
            Liste de chaines ("Send and Sync send sync ...") ou [].
        """
        detected = self.detect(query)
        if not detected:
            return []

        related = self.related(detected)
        expansions = []
        for node in related[: max(0, max_expansions)]:
            terms = [node.name, *node.aliases[:2]]
            expansions.append(" ".join(word for word in terms if word))
        return expansions
