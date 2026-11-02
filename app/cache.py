"""
Cache sémantique de réponses pour RustSensei (réponses exactes ou proches réutilisées).

Mémorise les réponses générées pour éviter de relancer le modèle
sur des questions déjà traitées (cache de réponse).

Le cache peut être persisté sur disque pour survivre aux redémarrages.
"""

import json
import math
import os
import time
from pathlib import Path
from typing import Callable, Optional

from .config import PROJECT_ROOT, get_rag_config

DEFAULT_TTL_SECONDS = 7 * 24 * 3600  # 7 jours
DEFAULT_CACHE_PATH = "data/cache.json"
DEFAULT_SEMANTIC_THRESHOLD = 0.85

Embedder = Callable[[str], list[float]]


class ResponseCache:
    """Cache des réponses par question normalisée (mémoire + disque optionnel)."""

    def __init__(
        self,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        path: Optional[Path] = None,
        semantic_enabled: bool = False,
        semantic_threshold: float = DEFAULT_SEMANTIC_THRESHOLD,
    ):
        self.ttl_seconds = ttl_seconds
        self.path = path
        self.semantic_enabled = semantic_enabled
        self.semantic_threshold = semantic_threshold
        self._entries: dict[str, dict] = {}
        self.hits = 0
        self.misses = 0
        self._load()

    @staticmethod
    def normalize_key(query: str) -> str:
        """Normalise une question pour la clé de cache (minuscules, espaces simples)."""
        return " ".join((query or "").strip().lower().split())

    @staticmethod
    def composite_key(history: list, query: str) -> str:
        """
        Construit une clé de cache incluant l'historique de la conversation.

        Args:
            history: Messages precedents ({role, content}), None a un seul tour.
            query: Question courante.

        Returns:
            Question normalisee si history vide, sinon historique + question.
        """
        normalized = ResponseCache.normalize_key(query)
        turns = [
            turn
            for turn in (history or [])
            if turn.get("role") in ("user", "assistant")
            and (turn.get("content") or "").strip()
        ]
        if not turns:
            return normalized

        prefix = " | ".join(
            f"{turn['role']}:{ResponseCache.normalize_key(turn['content'])}"
            for turn in turns
        )
        return f"{prefix} >> {normalized}"

    def get(
        self,
        query: str,
        now: Optional[float] = None,
        embedder: Optional[Embedder] = None,
        signature: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Récupère une réponse mise en cache.

        La correspondance exacte (question normalisée) est toujours tentée en
        premier. Si elle échoue et que le cache sémantique est actif, la
        question la plus proche est recherchée par similarité cosinus.

        Args:
            query: Question de l'utilisateur.
            now: Horloge injectable (tests).
            embedder: Fonction texte -> vecteur (cache sémantique).
            signature: Empreinte de génération (modèle, prompt système, échantillonnage,
                index RAG) ; seules les réponses produites avec la même empreinte sont servies.

        Returns:
            Dictionnaire {response, citations, timestamp} ou None si absent ou expiré.
        """
        if self.ttl_seconds <= 0:
            self.misses += 1
            return None

        current = now if now is not None else time.time()

        key = self.normalize_key(query)
        entry = self._entries.get(key)
        if entry is not None and self._is_expired(entry, current):
            del self._entries[key]
            self._save()
        elif entry is not None and self._same_signature(entry, signature):
            self.hits += 1
            return entry

        entry = self._semantic_get(query, current, embedder, signature)
        if entry is not None:
            self.hits += 1
            return entry

        self.misses += 1
        return None

    def set(
        self,
        query: str,
        response: str,
        citations: Optional[list] = None,
        timestamp: Optional[float] = None,
        embedder: Optional[Embedder] = None,
        signature: Optional[str] = None,
    ) -> None:
        """Met en cache une réponse générée (avec son embedding et son empreinte)."""
        if self.ttl_seconds <= 0:
            return

        key = self.normalize_key(query)
        entry = {
            "response": response,
            "citations": citations or [],
            "timestamp": timestamp if timestamp is not None else time.time(),
        }
        if signature is not None:
            entry["signature"] = signature

        embedding = self._embed(query, embedder)
        if embedding is not None:
            entry["embedding"] = embedding

        self._entries[key] = entry
        self._save()

    def clear(self) -> None:
        """Vide le cache."""
        self._entries.clear()
        self._save()

    def stats(self) -> dict:
        """Retourne les statistiques d'utilisation du cache (depuis le démarrage)."""
        total = self.hits + self.misses
        return {
            "entries": len(self._entries),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total else 0.0,
            "ttl_seconds": self.ttl_seconds,
            "semantic_enabled": self.semantic_enabled,
            "semantic_threshold": self.semantic_threshold,
            "path": str(self.path) if self.path is not None else None,
        }

    @staticmethod
    def _same_signature(entry: dict, signature: Optional[str]) -> bool:
        """
        Une réponse n'est resservie qu'avec la même empreinte de génération.

        Sans empreinte demandée (tests), toute entrée convient. Les entrées sans
        empreinte (antérieures) ne sont pas servies : leurs conditions de
        génération sont inconnues.
        """
        return signature is None or entry.get("signature") == signature

    def _is_expired(self, entry: dict, now: float) -> bool:
        """Indique si une entrée a dépassé le TTL."""
        return now - entry.get("timestamp", 0.0) > self.ttl_seconds

    def _semantic_get(
        self,
        query: str,
        now: float,
        embedder: Optional[Embedder],
        signature: Optional[str] = None,
    ) -> Optional[dict]:
        """Retourne l'entrée la plus proche si sa similarité dépasse le seuil."""
        if not self.semantic_enabled or embedder is None:
            return None

        query_embedding = self._embed(query, embedder)
        if not query_embedding:
            return None

        best_entry = None
        best_score = -1.0
        expired_keys = []

        for key, entry in self._entries.items():
            if self._is_expired(entry, now):
                expired_keys.append(key)
                continue

            embedding = entry.get("embedding")
            if not embedding or not self._same_signature(entry, signature):
                continue

            score = self._cosine_similarity(query_embedding, embedding)
            if score > best_score:
                best_score = score
                best_entry = entry

        if expired_keys:
            for key in expired_keys:
                del self._entries[key]
            self._save()

        if best_entry is not None and best_score >= self.semantic_threshold:
            return best_entry
        return None

    def _embed(self, query: str, embedder: Optional[Embedder]) -> Optional[list]:
        """Calcule un embedding normalisé, ou None si indisponible."""
        if not self.semantic_enabled or embedder is None:
            return None

        try:
            vector = embedder(query)
        except Exception:
            return None

        return self._normalize_vector(vector)

    @staticmethod
    def _normalize_vector(vector) -> list:
        """Normalise un vecteur (L2) pour que le produit scalaire soit un cosinus."""
        values = [float(value) for value in vector]
        norm = math.sqrt(sum(value * value for value in values))
        if not norm:
            return []
        return [round(value / norm, 6) for value in values]

    @staticmethod
    def _cosine_similarity(first, second) -> float:
        """Similarité cosinus entre deux vecteurs déjà normalisés."""
        if not first or not second or len(first) != len(second):
            return 0.0
        return sum(a * b for a, b in zip(first, second))

    def _load(self) -> None:
        """Charge le cache depuis le disque (silencieux si absent ou corrompu)."""
        if self.path is None or not self.path.exists():
            return

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        if isinstance(data, dict):
            self._entries = data

    def _save(self) -> None:
        """Écrit le cache sur le disque de manière atomique."""
        if self.path is None:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_name(f"{self.path.name}.tmp")
        content = json.dumps(self._entries, ensure_ascii=False)
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.replace(self.path)


def _default_ttl_seconds() -> float:
    """
    Retourne le TTL par défaut du cache depuis la configuration.

    La variable d'environnement RUSTSENSEI_CACHE_TTL le surcharge (0 désactive
    le cache, par exemple pour mesurer la latence de génération).
    """
    env_ttl = os.environ.get("RUSTSENSEI_CACHE_TTL")
    if env_ttl is not None:
        try:
            return float(env_ttl)
        except ValueError:
            pass
    try:
        config = get_rag_config()
        cache_config = config.get("cache") or {}
        ttl_seconds = cache_config.get("ttl_seconds")
        if ttl_seconds is None:
            return DEFAULT_TTL_SECONDS
        return float(ttl_seconds)
    except Exception:
        return DEFAULT_TTL_SECONDS


def _default_semantic_settings() -> tuple[bool, float]:
    """Retourne (actif, seuil) du cache sémantique depuis la configuration."""
    try:
        config = get_rag_config()
        semantic_config = (config.get("cache") or {}).get("semantic") or {}
        enabled = bool(semantic_config.get("enabled", False))
        threshold = float(
            semantic_config.get("threshold", DEFAULT_SEMANTIC_THRESHOLD)
        )
        return enabled, threshold
    except Exception:
        return False, DEFAULT_SEMANTIC_THRESHOLD


def _default_cache_path() -> Path:
    """Retourne le chemin du fichier de cache depuis la configuration."""
    try:
        config = get_rag_config()
        cache_config = config.get("cache") or {}
        path_value = cache_config.get("path")
        if not path_value:
            return PROJECT_ROOT / DEFAULT_CACHE_PATH

        path = Path(path_value)
        return path if path.is_absolute() else PROJECT_ROOT / path
    except Exception:
        return PROJECT_ROOT / DEFAULT_CACHE_PATH


_semantic_enabled, _semantic_threshold = _default_semantic_settings()

response_cache = ResponseCache(
    ttl_seconds=_default_ttl_seconds(),
    path=_default_cache_path(),
    semantic_enabled=_semantic_enabled,
    semantic_threshold=_semantic_threshold,
)
