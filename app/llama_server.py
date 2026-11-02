"""
Gestion de llama-server pour l'UI (streaming).

Mode persistant (par defaut) : un llama-server est lance au demarrage de l'API
et reutilise pour toutes les requetes ; il n'est relance que si le modele ou la
taille de contexte changent dans la configuration, ou s'il s'est arrete.
Mode "par requete" (server.persistent: false) : un llama-server est lance puis
arrete pour chaque requete (comportement historique, plus lent).
"""

import asyncio
import socket
import subprocess
import time
from pathlib import Path

import httpx

from .inference import chat_ctx_size

PROJECT_ROOT = Path(__file__).parent.parent
LLAMA_SERVER_BIN = PROJECT_ROOT / "vendor" / "llama.cpp" / "build" / "bin" / "llama-server"
STARTUP_TIMEOUT_S = 180.0


def find_free_port() -> int:
    """Retourne un port TCP libre."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def is_persistent(config: dict) -> bool:
    """Mode persistant (defaut) ou un serveur par requete."""
    return bool((config.get("server") or {}).get("persistent", True))


def model_path(config: dict) -> str:
    """Chemin absolu du GGUF configure."""
    return str((PROJECT_ROOT / config["paths"]["model"]).resolve())


def server_args(config: dict, port: int) -> list[str]:
    """Ligne de commande de llama-server pour la configuration donnee."""
    return [
        str(LLAMA_SERVER_BIN),
        "-m",
        model_path(config),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        # Contexte de conversation (historique compris) ; un seul emplacement de
        # requete pour qu'elle dispose de tout ce contexte.
        "-c",
        str(chat_ctx_size(config)),
        "--parallel",
        "1",
    ]


def start_process(config: dict, port: int) -> subprocess.Popen:
    """Lance llama-server (sorties ignorees)."""
    return subprocess.Popen(
        server_args(config, port),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def stop_process(proc: subprocess.Popen | None) -> None:
    """Arrete proprement un llama-server."""
    if proc is None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


async def wait_healthy(port: int, proc: subprocess.Popen, timeout: float = STARTUP_TIMEOUT_S) -> None:
    """Attend que llama-server reponde sur /health (modele charge)."""
    deadline = time.monotonic() + timeout
    async with httpx.AsyncClient(timeout=5.0) as client:
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise RuntimeError("llama-server s'est arrete pendant le demarrage")
            try:
                health = await client.get(f"http://127.0.0.1:{port}/health")
                if health.status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(0.25)
    raise RuntimeError("llama-server did not start in time")


class LlamaServerManager:
    """Un llama-server persistant, relance seulement si la configuration change."""

    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._port: int | None = None
        self._key: tuple[str, int] | None = None
        self._lock = asyncio.Lock()
        self.last_load_seconds: float | None = None
        self.loads = 0

    @staticmethod
    def _key_for(config: dict) -> tuple[str, int]:
        return model_path(config), chat_ctx_size(config)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._port}"

    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    async def ensure(self, config: dict) -> str:
        """URL d'un llama-server pret pour cette configuration (le lance au besoin)."""
        key = self._key_for(config)
        async with self._lock:
            if self.is_running() and self._key == key:
                return self.base_url

            self.stop()
            port = find_free_port()
            proc = start_process(config, port)
            started = time.monotonic()
            try:
                await wait_healthy(port, proc)
            except Exception:
                stop_process(proc)
                raise
            self._proc, self._port, self._key = proc, port, key
            self.last_load_seconds = round(time.monotonic() - started, 2)
            self.loads += 1
            return self.base_url

    def stop(self) -> None:
        """Arrete le serveur courant (s'il y en a un)."""
        stop_process(self._proc)
        self._proc, self._port, self._key = None, None, None

    def status(self) -> dict:
        """Etat pour /health."""
        return {
            "running": self.is_running(),
            "model": Path(self._key[0]).name if self._key else None,
            "ctx": self._key[1] if self._key else None,
            "last_load_seconds": self.last_load_seconds,
            "loads": self.loads,
        }


server_manager = LlamaServerManager()
