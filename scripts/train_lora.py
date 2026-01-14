#!/usr/bin/env python3
"""
Fine-tuning LoRA avec mlx-lm pour RustSensei.

Usage:
    python scripts/train_lora.py
    python scripts/train_lora.py --prepare-only
    python scripts/train_lora.py --fuse-only
"""

import json
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
TRAIN_CONFIG = PROJECT_ROOT / "configs" / "train.yaml"
LORA_CONFIG = PROJECT_ROOT / "configs" / "lora_config.yaml"


def load_config(config_path: Path) -> dict:
    """Charge la configuration."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def prepare_dataset() -> Path:
    """
    Prepare le dataset pour mlx-lm.
    mlx-lm attend train.jsonl et valid.jsonl avec 'messages' array.
    """
    config = load_config(TRAIN_CONFIG)
    input_path = PROJECT_ROOT / config["data"]["train_file"]
    output_dir = PROJECT_ROOT / "data" / "mlx_train"
    output_dir.mkdir(parents=True, exist_ok=True)

    train_path = output_dir / "train.jsonl"
    valid_path = output_dir / "valid.jsonl"

    # Lire et splitter le dataset (90% train, 10% valid)
    with open(input_path) as f:
        examples = [json.loads(line) for line in f]

    # Extraire seulement les messages (mlx-lm format)
    formatted = []
    for ex in examples:
        formatted.append({"messages": ex["messages"]})

    split_idx = int(len(formatted) * 0.9)
    train_data = formatted[:split_idx]
    valid_data = formatted[split_idx:]

    # Sauvegarder
    with open(train_path, "w") as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(valid_path, "w") as f:
        for item in valid_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Dataset prepare: {len(train_data)} train, {len(valid_data)} valid")
    print(f"Output: {output_dir}")
    return output_dir


def run_training() -> Path:
    """Lance le fine-tuning LoRA avec mlx-lm."""
    config = load_config(LORA_CONFIG)
    adapter_dir = PROJECT_ROOT / config["adapter_path"]
    adapter_dir.mkdir(parents=True, exist_ok=True)

    # Utiliser mlx_lm lora avec le fichier de config
    cmd = [
        sys.executable, "-m", "mlx_lm", "lora",
        "--config", str(LORA_CONFIG),
        "--train",
    ]

    print("\nLancement training LoRA...")
    print(f"Config: {LORA_CONFIG}")
    print(f"Commande: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode != 0:
        print(f"Erreur training (code {result.returncode})")
        sys.exit(1)

    print(f"\nAdaptateurs sauvegardes dans: {adapter_dir}")
    return adapter_dir


def fuse_model() -> Path:
    """Fusionne les adaptateurs LoRA avec le modele de base."""
    config = load_config(LORA_CONFIG)
    train_config = load_config(TRAIN_CONFIG)

    adapter_dir = PROJECT_ROOT / config["adapter_path"]
    merged_dir = PROJECT_ROOT / train_config["output"]["merged_dir"]
    merged_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "mlx_lm", "fuse",
        "--model", config["model"],
        "--adapter-path", str(adapter_dir),
        "--save-path", str(merged_dir),
    ]

    print("\nFusion modele + adaptateurs...")
    print(f"Commande: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode != 0:
        print(f"Erreur fusion (code {result.returncode})")
        sys.exit(1)

    print(f"\nModele fusionne dans: {merged_dir}")
    return merged_dir


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fine-tuning LoRA RustSensei")
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Preparer le dataset sans lancer le training"
    )
    parser.add_argument(
        "--fuse-only",
        action="store_true",
        help="Fusionner les adaptateurs existants"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("RustSensei - Fine-tuning LoRA")
    print("=" * 60)

    config = load_config(LORA_CONFIG)
    print(f"Modele: {config['model']}")
    print(f"LoRA rank: {config['lora_parameters']['rank']}")
    print(f"Iterations: {config['iters']}")

    if args.fuse_only:
        adapter_dir = PROJECT_ROOT / config["adapter_path"]
        if not adapter_dir.exists():
            print(f"Erreur: adaptateurs non trouves dans {adapter_dir}")
            sys.exit(1)
        fuse_model()
        return

    # Preparer le dataset
    prepare_dataset()

    if args.prepare_only:
        print("\nDataset prepare. Relancez sans --prepare-only pour entrainer.")
        return

    # Lancer le training
    run_training()

    # Fusionner
    print("\n" + "=" * 60)
    fuse_model()

    print("\n" + "=" * 60)
    print("Training termine!")
    train_config = load_config(TRAIN_CONFIG)
    print(f"Adaptateurs: {PROJECT_ROOT / config['adapter_path']}")
    print(f"Modele fusionne: {PROJECT_ROOT / train_config['output']['merged_dir']}")
    print("\nProchaine etape: make export-gguf")


if __name__ == "__main__":
    main()
