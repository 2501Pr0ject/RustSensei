"""
Gestion de la configuration pour RustSensei.
"""

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"


def load_config(config_name: str) -> dict[str, Any]:
    """Charge un fichier de configuration YAML.

    Args:
        config_name: Nom du fichier (sans extension) ou chemin complet.

    Returns:
        Dictionnaire de configuration.

    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
    """
    if not config_name.endswith(".yaml"):
        config_path = CONFIGS_DIR / f"{config_name}.yaml"
    else:
        config_path = Path(config_name)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration non trouvée: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_model_config() -> dict[str, Any]:
    """Charge la configuration du modèle."""
    return load_config("model_config")


def get_rag_config() -> dict[str, Any]:
    """Charge la configuration RAG."""
    return load_config("rag_config")


# Chemins utiles
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"
RAG_DIR = PROJECT_ROOT / "rag"
EVAL_DIR = PROJECT_ROOT / "eval"
