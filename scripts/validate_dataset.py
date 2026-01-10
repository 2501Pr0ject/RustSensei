#!/usr/bin/env python3
"""
Validation du dataset d'entraînement pour RustSensei.

Vérifie le format, la qualité et la cohérence du dataset.
"""

import json
import re
import sys
from pathlib import Path

import yaml
from rich.console import Console

console = Console()

PROJECT_ROOT = Path(__file__).parent.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"
DATA_SAMPLES_DIR = PROJECT_ROOT / "data_samples"


def load_config():
    """Charge la configuration du dataset."""
    config_path = CONFIGS_DIR / "dataset_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_dataset(path: Path) -> list[dict]:
    """Charge un dataset JSONL."""
    items = []
    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                console.print(f"[red]Erreur JSON ligne {line_num}: {e}[/red]")
    return items


# =============================================================================
# Validateurs
# =============================================================================


def validate_json_structure(item: dict, idx: int) -> list[str]:
    """Vérifie la structure JSON de base."""
    errors = []

    if "messages" not in item:
        errors.append(f"[{idx}] Champ 'messages' manquant")
        return errors

    messages = item["messages"]
    if not isinstance(messages, list):
        errors.append(f"[{idx}] 'messages' doit être une liste")
        return errors

    if len(messages) < 2:
        errors.append(f"[{idx}] Au moins 2 messages requis (user + assistant)")

    roles_expected = ["system", "user", "assistant"]
    for i, msg in enumerate(messages):
        if "role" not in msg:
            errors.append(f"[{idx}] Message {i}: 'role' manquant")
        elif msg["role"] not in roles_expected:
            errors.append(f"[{idx}] Message {i}: rôle invalide '{msg['role']}'")

        if "content" not in msg:
            errors.append(f"[{idx}] Message {i}: 'content' manquant")
        elif not isinstance(msg["content"], str):
            errors.append(f"[{idx}] Message {i}: 'content' doit être une string")

    return errors


def validate_message_roles(item: dict, idx: int) -> list[str]:
    """Vérifie l'ordre des rôles dans les messages."""
    errors = []
    messages = item.get("messages", [])

    if not messages:
        return errors

    # Premier message doit être system
    if messages[0].get("role") != "system":
        errors.append(f"[{idx}] Premier message doit être 'system'")

    # Vérifier alternance user/assistant après system
    for i, msg in enumerate(messages[1:], 1):
        expected = "user" if i % 2 == 1 else "assistant"
        if msg.get("role") != expected:
            errors.append(f"[{idx}] Message {i}: attendu '{expected}', trouvé '{msg.get('role')}'")

    return errors


def validate_content_length(item: dict, idx: int, config: dict) -> list[str]:
    """Vérifie la longueur du contenu."""
    errors = []
    warnings = []
    quality = config.get("quality", {})

    min_tokens = quality.get("min_response_tokens", 50)
    max_tokens = quality.get("max_response_tokens", 800)

    messages = item.get("messages", [])
    for msg in messages:
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            # Estimation tokens ≈ mots
            word_count = len(content.split())

            if word_count < min_tokens:
                warnings.append(f"[{idx}] Réponse trop courte ({word_count} mots < {min_tokens})")
            if word_count > max_tokens:
                warnings.append(f"[{idx}] Réponse trop longue ({word_count} mots > {max_tokens})")

    return errors, warnings


def validate_french(item: dict, idx: int, config: dict) -> list[str]:
    """Vérifie que le contenu est en français."""
    errors = []
    quality = config.get("quality", {})

    if not quality.get("require_french", True):
        return errors

    french_words = [
        "le", "la", "les", "de", "du", "des", "un", "une", "et", "est",
        "en", "que", "qui", "pour", "dans", "ce", "il", "ne", "sur", "se",
        "pas", "plus", "par", "je", "avec", "tout", "faire", "son", "mais",
        "nous", "comme", "ou", "si", "leur", "bien", "où", "cette", "sans",
        "fonction", "variable", "valeur", "type", "code", "erreur", "exemple",
        "tu", "te", "ta", "tes", "ton", "voici", "aussi", "donc", "car",
        "peut", "sont", "être", "avoir", "fait", "sur", "quand", "comment",
        "utilise", "permet", "retourne", "prend", "doit", "veut", "donne",
    ]

    messages = item.get("messages", [])
    for msg in messages:
        if msg.get("role") == "assistant":
            content = msg.get("content", "").lower()

            # Exclure les blocs de code de l'analyse
            content_no_code = re.sub(r'```[\s\S]*?```', '', content)
            content_no_code = re.sub(r'`[^`]+`', '', content_no_code)

            words = re.findall(r'\b[a-zàâäéèêëïîôùûüç]+\b', content_no_code)

            if len(words) < 20:  # Pas assez de texte hors code
                continue

            french_count = sum(1 for w in words if w in french_words)
            ratio = french_count / len(words) if words else 0

            threshold = quality.get("check_french_ratio", 0.08)
            if ratio < threshold:
                errors.append(f"[{idx}] Contenu pas assez français ({ratio:.0%} < {threshold:.0%})")

    return errors


def validate_code_blocks(item: dict, idx: int, config: dict) -> list[str]:
    """Vérifie la présence de blocs de code si requis."""
    warnings = []
    quality = config.get("quality", {})
    metadata = item.get("metadata", {})

    category = metadata.get("category", "")

    # Code requis pour debug et exercises
    if category in ["debug", "exercises"] and quality.get("require_code_block", True):
        messages = item.get("messages", [])
        for msg in messages:
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                if "```" not in content:
                    warnings.append(f"[{idx}] Catégorie '{category}' sans bloc de code")

    return warnings


def validate_banned_phrases(item: dict, idx: int, config: dict) -> list[str]:
    """Vérifie l'absence de phrases interdites."""
    errors = []
    quality = config.get("quality", {})
    banned = quality.get("banned_phrases", [])

    messages = item.get("messages", [])
    for msg in messages:
        content = msg.get("content", "").lower()
        for phrase in banned:
            if phrase.lower() in content:
                errors.append(f"[{idx}] Phrase interdite détectée: '{phrase}'")

    return errors


def validate_metadata(item: dict, idx: int) -> list[str]:
    """Vérifie les métadonnées."""
    warnings = []
    metadata = item.get("metadata", {})

    if not metadata:
        warnings.append(f"[{idx}] Métadonnées manquantes")
        return warnings

    required_fields = ["category", "topic", "difficulty"]
    for field in required_fields:
        if field not in metadata:
            warnings.append(f"[{idx}] Métadonnée '{field}' manquante")

    valid_categories = ["debug", "concepts", "exercises"]
    if metadata.get("category") not in valid_categories:
        warnings.append(f"[{idx}] Catégorie invalide: {metadata.get('category')}")

    valid_difficulties = ["debutant", "intermediaire", "avance"]
    if metadata.get("difficulty") not in valid_difficulties:
        warnings.append(f"[{idx}] Difficulté invalide: {metadata.get('difficulty')}")

    return warnings


# =============================================================================
# Main
# =============================================================================


def validate_dataset(dataset: list[dict], config: dict) -> dict:
    """Valide le dataset complet."""
    all_errors = []
    all_warnings = []

    for idx, item in enumerate(dataset):
        # Structure
        errors = validate_json_structure(item, idx)
        all_errors.extend(errors)
        if errors:
            continue  # Skip autres validations si structure invalide

        # Rôles
        errors = validate_message_roles(item, idx)
        all_errors.extend(errors)

        # Longueur
        errors, warnings = validate_content_length(item, idx, config)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

        # Français
        errors = validate_french(item, idx, config)
        all_errors.extend(errors)

        # Blocs de code
        warnings = validate_code_blocks(item, idx, config)
        all_warnings.extend(warnings)

        # Phrases interdites
        errors = validate_banned_phrases(item, idx, config)
        all_errors.extend(errors)

        # Métadonnées
        warnings = validate_metadata(item, idx)
        all_warnings.extend(warnings)

    return {
        "total": len(dataset),
        "errors": all_errors,
        "warnings": all_warnings,
        "valid": len(all_errors) == 0,
    }


def print_report(results: dict):
    """Affiche le rapport de validation."""
    console.print("\n[bold]Rapport de validation[/bold]")
    console.print(f"  Total exemples: {results['total']}")

    if results["errors"]:
        console.print(f"\n[red]Erreurs ({len(results['errors'])}):[/red]")
        for err in results["errors"][:20]:  # Limiter affichage
            console.print(f"  {err}")
        if len(results["errors"]) > 20:
            console.print(f"  ... et {len(results['errors']) - 20} autres erreurs")

    if results["warnings"]:
        console.print(f"\n[yellow]Avertissements ({len(results['warnings'])}):[/yellow]")
        for warn in results["warnings"][:10]:
            console.print(f"  {warn}")
        if len(results["warnings"]) > 10:
            console.print(f"  ... et {len(results['warnings']) - 10} autres avertissements")

    if results["valid"]:
        console.print("\n[green]✓ Dataset valide[/green]")
    else:
        console.print("\n[red]✗ Dataset invalide[/red]")


def main():
    """Point d'entrée."""
    import argparse

    parser = argparse.ArgumentParser(description="Validation dataset RustSensei")
    parser.add_argument("--file", type=str, default=None, help="Fichier à valider")
    args = parser.parse_args()

    console.print("[bold blue]Validation du dataset RustSensei[/bold blue]\n")

    config = load_config()

    # Déterminer le fichier à valider
    if args.file:
        dataset_path = Path(args.file)
    else:
        dataset_path = DATA_SAMPLES_DIR / config["paths"]["sample_file"]

    if not dataset_path.exists():
        console.print(f"[red]Fichier non trouvé: {dataset_path}[/red]")
        console.print("[yellow]Lancez d'abord: make build-dataset[/yellow]")
        sys.exit(1)

    console.print(f"Fichier: {dataset_path}")

    # Charger et valider
    dataset = load_dataset(dataset_path)
    results = validate_dataset(dataset, config)

    print_report(results)

    sys.exit(0 if results["valid"] else 1)


if __name__ == "__main__":
    main()
