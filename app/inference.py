"""
Parametres d'inference partages (source unique : configs/model_config.yaml).

Les chemins de generation (CLI et /chat via llama-completion, UI via llama-server,
evaluation) lisent l'echantillonnage ici, pour que l'UI tourne avec les reglages
mesures par l'evaluation.
"""

import hashlib
import json
import re
from pathlib import Path

# Cles d'echantillonnage de la section `inference`, surchargeables par modele.
SAMPLING_KEYS = ("temp", "top_k", "top_p", "min_p", "repeat_penalty", "n_predict")

DEFAULT_SAMPLING = {
    "temp": 0.7,
    "top_k": 40,
    "top_p": 0.9,
    "min_p": 0.05,
    "repeat_penalty": 1.1,
    "n_predict": 1024,
}

DEFAULT_CHAT_CTX = 8192


LENGTH_LIMIT_NOTE = (
    "\n\n*[Réponse interrompue : limite de longueur atteinte "
    "(nombre maximal de tokens ou contexte du modèle plein).]*"
)


class ContextOverflowError(Exception):
    """La requete (question + historique + contexte RAG) depasse le contexte du modele."""


def overflow_message(llama_error: str = "") -> str:
    """
    Message clair a partir d'une erreur de llama.cpp sur la taille du contexte.

    Reconnait "prompt is too long (N tokens, max M)" (llama-completion) et
    "request (N tokens) exceeds the available context size (M tokens)" ou
    "input (N tokens) is larger than the max context size (M tokens)" (llama-server).
    """
    numbers = re.findall(r"(\d+) tokens?", llama_error or "")
    max_match = re.search(r"max (\d+)", llama_error or "")
    detail = ""
    if numbers:
        total = numbers[0]
        limit = max_match.group(1) if max_match else (numbers[1] if len(numbers) > 1 else None)
        detail = f" ({total} tokens" + (f" pour un maximum de {limit}" if limit else "") + ")"
    return (
        "La question, l'historique et la documentation dépassent le contexte du modèle"
        f"{detail}. Effacez la conversation ou raccourcissez la question."
    )


def sampling_params(config: dict, model_path: str | None = None) -> dict:
    """
    Echantillonnage effectif pour un modele.

    Valeurs de `inference`, surchargees par `sampling_by_model[<fichier GGUF>]`
    si le modele y figure.

    Args:
        config: Configuration du modele (model_config.yaml).
        model_path: Chemin du GGUF (defaut : paths.model).

    Raises:
        ValueError: si une surcharge contient une cle inconnue (faute de frappe).
    """
    inference = config.get("inference") or {}
    params = {key: inference.get(key, DEFAULT_SAMPLING[key]) for key in SAMPLING_KEYS}

    name = Path(model_path or config["paths"]["model"]).name
    overrides = (config.get("sampling_by_model") or {}).get(name) or {}
    unknown = set(overrides) - set(SAMPLING_KEYS)
    if unknown:
        raise ValueError(
            f"Cles d'echantillonnage inconnues pour {name} : {sorted(unknown)} "
            f"(attendues : {list(SAMPLING_KEYS)})"
        )
    params.update(overrides)
    return params


def model_name(config: dict) -> str:
    """Nom du fichier GGUF utilise (identifie le modele, par exemple pour le cache)."""
    return Path(config["paths"]["model"]).name


RAG_MANIFEST = Path(__file__).parent.parent / "rag" / "index" / "manifest.json"


def rag_index_id(manifest_path: Path = RAG_MANIFEST) -> str | None:
    """Identifiant de l'index RAG (date de construction et nombre d'extraits)."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return f"{manifest.get('build_timestamp')}|{manifest.get('total_chunks')}"


def generation_signature(config: dict, manifest_path: Path = RAG_MANIFEST) -> str:
    """
    Empreinte de tout ce qui determine une reponse, hors question et historique.

    Modele, prompt systeme, gabarit, echantillonnage effectif et index RAG : une
    reponse en cache n'est resservie que si cette empreinte est identique.
    """
    prompt = config.get("prompt") or {}
    payload = {
        "model": model_name(config),
        "system": prompt.get("system"),
        "template": prompt.get("template"),
        "sampling": sampling_params(config),
        "rag_index": rag_index_id(manifest_path),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]
    return f"{model_name(config)}@{digest}"


def chat_ctx_size(config: dict) -> int:
    """Taille de contexte des chemins conversationnels (UI, /chat, CLI)."""
    return int((config.get("inference") or {}).get("n_ctx_chat", DEFAULT_CHAT_CTX))


def server_payload_sampling(params: dict) -> dict:
    """Parametres d'echantillonnage au format de l'API chat de llama-server."""
    return {
        "temperature": params["temp"],
        "top_k": params["top_k"],
        "top_p": params["top_p"],
        "min_p": params["min_p"],
        "repeat_penalty": params["repeat_penalty"],
        "max_tokens": params["n_predict"],
    }


def cli_sampling_args(params: dict) -> list[str]:
    """Parametres d'echantillonnage au format de llama-completion."""
    return [
        "-n", str(params["n_predict"]),
        "--temp", str(params["temp"]),
        "--top-k", str(params["top_k"]),
        "--top-p", str(params["top_p"]),
        "--min-p", str(params["min_p"]),
        "--repeat-penalty", str(params["repeat_penalty"]),
    ]
