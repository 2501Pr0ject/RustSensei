"""
Cache pour RustSensei (CAG - Cache Augmented Generation).

Mémorise les réponses générées pour éviter de relancer le modèle
sur des questions déjà traitées (cache de réponse).
"""

import time
from typing import Optional

from .config import get_rag_config

DEFAULT_TTL_SECONDS = 7 * 24 * 3600  # 7 jours


class ResponseCache:
    """Cache simple en mémoire des réponses par question normalisée."""

    def __init__(self, ttl_seconds: float = DEFAULT_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self._entries: dict[str, dict] = {}

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
            return None

        key = self.normalize_key(query)
        entry = self._entries.get(key)
        if entry is None:
            return None

        timestamp = entry["timestamp"]
        current = now if now is not None else time.monotonic()
        if current - timestamp > self.ttl_seconds:
            del self._entries[key]
            return None

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
            "timestamp": timestamp if timestamp is not None else time.monotonic(),
        }

    def clear(self) -> None:
        """Vide le cache."""
        self._entries.clear()


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


response_cache = ResponseCache(ttl_seconds=_default_ttl_seconds())
