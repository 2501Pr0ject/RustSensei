"""
Cache pour RustSensei (CAG - Cache Augmented Generation).

Mémorise les réponses générées pour éviter de relancer le modèle
sur des questions déjà traitées (cache de réponse).

Le cache peut être persisté sur disque pour survivre aux redémarrages.
"""

import json
import time
from pathlib import Path
from typing import Optional

from .config import PROJECT_ROOT, get_rag_config

DEFAULT_TTL_SECONDS = 7 * 24 * 3600  # 7 jours
DEFAULT_CACHE_PATH = "data/cache.json"


class ResponseCache:
    """Cache des réponses par question normalisée (mémoire + disque optionnel)."""

    def __init__(
        self,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        path: Optional[Path] = None,
    ):
        self.ttl_seconds = ttl_seconds
        self.path = path
        self._entries: dict[str, dict] = {}
        self.hits = 0
        self.misses = 0
        self._load()

    @staticmethod
    def normalize_key(query: str) -> str:
        """Normalise une question pour la clé de cache (minuscules, espaces simples)."""
        return " ".join((query or "").strip().lower().split())

    def get(self, query: str, now: Optional[float] = None) -> Optional[dict]:
        """
        Récupère une réponse mise en cache.

        Args:
            query: Question de l'utilisateur.
            now: Horloge injectable (tests).

        Returns:
            Dictionnaire {response, citations, timestamp} ou None si absent ou expiré.
        """
        if self.ttl_seconds <= 0:
            self.misses += 1
            return None

        key = self.normalize_key(query)
        entry = self._entries.get(key)
        if entry is None:
            self.misses += 1
            return None

        timestamp = entry["timestamp"]
        current = now if now is not None else time.time()
        if current - timestamp > self.ttl_seconds:
            del self._entries[key]
            self._save()
            self.misses += 1
            return None

        self.hits += 1
        return entry

    def set(
        self,
        query: str,
        response: str,
        citations: Optional[list] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        """Met en cache une réponse générée."""
        if self.ttl_seconds <= 0:
            return

        key = self.normalize_key(query)
        self._entries[key] = {
            "response": response,
            "citations": citations or [],
            "timestamp": timestamp if timestamp is not None else time.time(),
        }
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
            "path": str(self.path) if self.path is not None else None,
        }

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
    """Retourne le TTL par défaut du cache depuis la configuration."""
    try:
        config = get_rag_config()
        cache_config = config.get("cache") or {}
        ttl_seconds = cache_config.get("ttl_seconds")
        if ttl_seconds is None:
            return DEFAULT_TTL_SECONDS
        return float(ttl_seconds)
    except Exception:
        return DEFAULT_TTL_SECONDS


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


response_cache = ResponseCache(
    ttl_seconds=_default_ttl_seconds(),
    path=_default_cache_path(),
)
