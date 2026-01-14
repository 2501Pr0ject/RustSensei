#!/usr/bin/env python3
"""
Export du modele fine-tune vers GGUF pour llama.cpp.

Usage:
    python scripts/export_gguf.py
    python scripts/export_gguf.py --quantize q4_k_m
"""

import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
LLAMA_CPP_DIR = PROJECT_ROOT / "vendor" / "llama.cpp"
CONVERT_SCRIPT = LLAMA_CPP_DIR / "convert_hf_to_gguf.py"


def load_config() -> dict:
    """Charge la configuration."""
    config_path = PROJECT_ROOT / "configs" / "train.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def convert_to_gguf(merged_dir: Path, output_path: Path) -> bool:
    """Convertit le modele HF/safetensors en GGUF."""
    if not CONVERT_SCRIPT.exists():
        print(f"Erreur: {CONVERT_SCRIPT} non trouve")
        print("Assurez-vous que llama.cpp est installe (make install-llama)")
        return False

    cmd = [
        sys.executable,
        str(CONVERT_SCRIPT),
        str(merged_dir),
        "--outfile", str(output_path),
        "--outtype", "f16",  # D'abord en f16, puis quantize
    ]

    print(f"Conversion en GGUF...")
    print(f"Commande: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode == 0


def quantize_gguf(input_path: Path, output_path: Path, quant_type: str = "q4_k_m") -> bool:
    """Quantize le modele GGUF."""
    llama_quantize = LLAMA_CPP_DIR / "build" / "bin" / "llama-quantize"

    if not llama_quantize.exists():
        print(f"Erreur: {llama_quantize} non trouve")
        return False

    cmd = [
        str(llama_quantize),
        str(input_path),
        str(output_path),
        quant_type.upper(),
    ]

    print(f"\nQuantization {quant_type}...")
    print(f"Commande: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode == 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Export GGUF RustSensei")
    parser.add_argument(
        "--quantize",
        type=str,
        default="q4_k_m",
        help="Type de quantization (q4_k_m, q8_0, f16)"
    )
    parser.add_argument(
        "--skip-convert",
        action="store_true",
        help="Skip conversion, quantize only"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("RustSensei - Export GGUF")
    print("=" * 60)

    config = load_config()
    merged_dir = PROJECT_ROOT / config["output"]["merged_dir"]
    models_dir = PROJECT_ROOT / "models"
    models_dir.mkdir(exist_ok=True)

    # Fichiers intermediaires et final
    f16_path = models_dir / "rustsensei-1.5b-f16.gguf"
    final_path = PROJECT_ROOT / config["output"]["gguf_file"]

    if not merged_dir.exists():
        print(f"Erreur: modele fusionne non trouve dans {merged_dir}")
        print("Lancez d'abord: python scripts/train_lora.py")
        sys.exit(1)

    # Conversion
    if not args.skip_convert:
        if not convert_to_gguf(merged_dir, f16_path):
            print("Erreur lors de la conversion")
            sys.exit(1)
        print(f"Modele F16 cree: {f16_path}")

    # Quantization
    if args.quantize.lower() != "f16":
        if not f16_path.exists():
            print(f"Erreur: {f16_path} non trouve pour quantization")
            sys.exit(1)

        if not quantize_gguf(f16_path, final_path, args.quantize):
            print("Erreur lors de la quantization")
            sys.exit(1)

        # Nettoyer le fichier F16 intermediaire
        f16_path.unlink()
        print(f"\nModele quantize cree: {final_path}")
    else:
        # Pas de quantization, renommer f16 en final
        f16_path.rename(final_path)
        print(f"\nModele F16 cree: {final_path}")

    print("\n" + "=" * 60)
    print("Export termine!")
    print(f"Modele final: {final_path}")
    print("\nPour tester:")
    print(f"  MODEL_PATH={final_path} make chat")


if __name__ == "__main__":
    main()
