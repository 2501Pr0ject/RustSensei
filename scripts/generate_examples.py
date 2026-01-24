#!/usr/bin/env python3
"""
Generation automatique d'exemples pour le dataset RustSensei.

Utilise le LLM pour generer des exemples instruction/reponse
et valide la compilation du code Rust.
"""

import json
import random
import re
import subprocess
import tempfile
from pathlib import Path

import yaml
from rich.console import Console
from rich.progress import track

console = Console()

PROJECT_ROOT = Path(__file__).parent.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"

# Topics a renforcer (points faibles identifies)
PRIORITY_TOPICS = {
    "lifetimes": {
        "weight": 3,
        "prompts": [
            "Explique les lifetimes en Rust avec un exemple pratique.",
            "Comment annoter les lifetimes dans une fonction qui retourne une reference ?",
            "Pourquoi ce code ne compile pas ? fn longest(x: &str, y: &str) -> &str { if x.len() > y.len() { x } else { y } }",
            "Comment utiliser les lifetimes avec des structs ?",
            "Quelle est la difference entre 'static et une lifetime generique ?",
            "Explique l'elision des lifetimes en Rust.",
            "Comment gerer les lifetimes dans les closures ?",
            "Corrige cette erreur: missing lifetime specifier",
        ],
    },
    "borrowing": {
        "weight": 3,
        "prompts": [
            "Explique le borrowing en Rust avec des exemples.",
            "Quelle est la difference entre &T et &mut T ?",
            "Pourquoi ne peut-on pas avoir plusieurs references mutables ?",
            "Comment fonctionne le borrow checker ?",
            "Corrige: cannot borrow as mutable because it is also borrowed as immutable",
            "Comment eviter les conflits de borrow dans une boucle ?",
            "Explique le pattern reborrow en Rust.",
            "Comment utiliser les references avec des structs ?",
        ],
    },
    "async": {
        "weight": 2,
        "prompts": [
            "Explique async/await en Rust.",
            "Comment creer une fonction async ?",
            "Quelle est la difference entre async et threads ?",
            "Comment gerer les erreurs dans du code async ?",
            "Explique les Futures en Rust.",
            "Comment utiliser tokio pour l'async ?",
            "Comment faire des requetes HTTP async ?",
        ],
    },
    "ownership": {
        "weight": 1,
        "prompts": [
            "Explique le concept de move en Rust.",
            "Quand utiliser clone() vs une reference ?",
            "Comment fonctionne drop() ?",
            "Explique le trait Copy vs Clone.",
        ],
    },
    "error_handling": {
        "weight": 1,
        "prompts": [
            "Comment creer un type d'erreur personnalise ?",
            "Explique thiserror et anyhow.",
            "Comment combiner plusieurs types d'erreurs ?",
            "Quand utiliser panic! vs Result ?",
        ],
    },
    "traits": {
        "weight": 1,
        "prompts": [
            "Comment implementer un trait pour un type externe ?",
            "Explique les trait bounds avances.",
            "Comment utiliser les associated types ?",
            "Explique la difference entre dyn Trait et impl Trait.",
        ],
    },
    "generics": {
        "weight": 1,
        "prompts": [
            "Comment ecrire une fonction generique avec contraintes ?",
            "Explique where clauses en Rust.",
            "Comment utiliser les generics avec des lifetimes ?",
        ],
    },
    "smart_pointers": {
        "weight": 1,
        "prompts": [
            "Explique Box, Rc et Arc.",
            "Quand utiliser RefCell ?",
            "Comment eviter les cycles de references avec Weak ?",
        ],
    },
    "concurrency": {
        "weight": 1,
        "prompts": [
            "Comment partager des donnees entre threads ?",
            "Explique Mutex et RwLock.",
            "Comment utiliser les channels pour la communication ?",
        ],
    },
}


def load_config():
    """Charge la configuration du modele."""
    config_path = CONFIGS_DIR / "model_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_dataset_config():
    """Charge la configuration du dataset."""
    config_path = CONFIGS_DIR / "dataset_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def call_llm(prompt: str, config: dict, max_tokens: int = 1024) -> str:
    """Appelle le LLM pour generer une reponse."""
    llama_cli = PROJECT_ROOT / config["paths"]["llama_cli"]
    model_path = PROJECT_ROOT / config["paths"]["model"]

    system_prompt = """Tu es RustSensei, un expert Rust pedagogique.
Genere une reponse educative en francais avec cette structure:

## TL;DR
[Resume en 1-2 phrases]

## Probleme
[Description du probleme]

## Solution
[Code Rust et explications]

## Explication
[Details pedagogiques]

## A retenir
[Points cles]

IMPORTANT: Inclus du code Rust fonctionnel et compilable."""

    full_prompt = f"""<|im_start|>system
{system_prompt}
<|im_end|>
<|im_start|>user
{prompt}
<|im_end|>
<|im_start|>assistant
"""

    inf = config["inference"]
    cmd = [
        str(llama_cli),
        "-m", str(model_path),
        "-p", full_prompt,
        "-n", str(max_tokens),
        "-c", str(inf.get("n_ctx", 4096)),
        "-t", str(inf.get("threads", 8)),
        "-ngl", str(inf.get("n_gpu_layers", 99)),
        "--temp", "0.8",
        "--top-p", "0.9",
        "-s", str(random.randint(1, 100000)),
        "--no-display-prompt",
        "-no-cnv",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""
    except Exception as e:
        console.print(f"[red]Erreur LLM: {e}[/red]")
        return ""


def extract_rust_code(response: str) -> list[str]:
    """Extrait les blocs de code Rust d'une reponse."""
    pattern = r"```rust\n(.*?)```"
    matches = re.findall(pattern, response, re.DOTALL)
    return [m.strip() for m in matches if m.strip()]


def validate_rust_code(code: str) -> tuple[bool, str]:
    """Valide qu'un bloc de code Rust compile."""
    # Ajouter main() si absent
    if "fn main()" not in code:
        code = f"fn main() {{\n{code}\n}}"

    # Ajouter imports communs si necessaire
    if "HashMap" in code and "use std::collections::HashMap" not in code:
        code = "use std::collections::HashMap;\n" + code
    if "Result<" in code and "std::io" in code:
        code = "use std::io;\n" + code

    with tempfile.TemporaryDirectory() as tmpdir:
        src_file = Path(tmpdir) / "check.rs"
        src_file.write_text(code)

        try:
            result = subprocess.run(
                ["rustc", "--edition", "2021", "--emit", "metadata", str(src_file)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=tmpdir,
            )
            if result.returncode == 0:
                return True, ""
            return False, result.stderr
        except Exception as e:
            return False, str(e)


def validate_response(response: str, prompt: str) -> tuple[bool, dict]:
    """Valide une reponse generee."""
    if not response or len(response) < 100:
        return False, {"error": "Reponse trop courte"}

    # Verifier la structure
    required_sections = ["## TL;DR", "## Solution"]
    sections_found = sum(1 for s in required_sections if s in response)
    if sections_found < 1:
        return False, {"error": "Structure manquante"}

    # Verifier le code Rust
    code_blocks = extract_rust_code(response)
    if not code_blocks:
        return False, {"error": "Pas de code Rust"}

    # Valider la compilation
    compiled = 0
    errors = []
    for code in code_blocks:
        valid, err = validate_rust_code(code)
        if valid:
            compiled += 1
        else:
            errors.append(err[:200])

    compilation_rate = compiled / len(code_blocks) if code_blocks else 0

    if compilation_rate < 0.5:
        return False, {"error": "Code ne compile pas", "details": errors}

    return True, {
        "code_blocks": len(code_blocks),
        "compiled": compiled,
        "rate": compilation_rate,
    }


def generate_example(topic: str, prompt: str, config: dict, dataset_config: dict) -> dict | None:
    """Genere un exemple complet."""
    response = call_llm(prompt, config)

    valid, info = validate_response(response, prompt)
    if not valid:
        return None

    # Determiner la difficulte
    difficulty = "intermediaire"
    if any(k in topic for k in ["lifetimes", "async", "unsafe"]):
        difficulty = "avance"
    elif any(k in topic for k in ["ownership", "borrowing"]):
        difficulty = random.choice(["debutant", "intermediaire"])

    # Determiner la categorie
    if "corrige" in prompt.lower() or "erreur" in prompt.lower():
        category = "debug"
    elif "exercice" in prompt.lower():
        category = "exercises"
    else:
        category = "concepts"

    return {
        "messages": [
            {"role": "system", "content": dataset_config["format"]["system_prompt"].strip()},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response},
        ],
        "metadata": {
            "category": category,
            "topic": topic,
            "difficulty": difficulty,
            "auto_generated": True,
            "compilation_rate": info.get("rate", 0),
        },
    }


def generate_dataset(target_count: int = 150):
    """Genere un dataset avec le nombre d'exemples cible."""
    config = load_config()
    dataset_config = load_dataset_config()

    # Construire la liste des prompts ponderes
    weighted_prompts = []
    for topic, data in PRIORITY_TOPICS.items():
        for prompt in data["prompts"]:
            for _ in range(data["weight"]):
                weighted_prompts.append((topic, prompt))

    random.shuffle(weighted_prompts)

    generated = []
    attempts = 0
    max_attempts = target_count * 3

    console.print(f"[bold]Generation de {target_count} exemples[/bold]\n")

    for topic, prompt in track(weighted_prompts[:max_attempts], description="Generation..."):
        if len(generated) >= target_count:
            break

        example = generate_example(topic, prompt, config, dataset_config)
        if example:
            generated.append(example)
            console.print(f"  [green]+[/green] {topic}: {prompt[:40]}...")
        else:
            console.print(f"  [red]-[/red] {topic}: echec")

        attempts += 1

    # Sauvegarder
    output_path = DATA_DIR / "generated" / "examples_auto.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for ex in generated:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    console.print(f"\n[bold green]Genere: {len(generated)}/{target_count}[/bold green]")
    console.print(f"[dim]Sauvegarde: {output_path}[/dim]")

    # Stats
    from collections import Counter
    topics = Counter(ex["metadata"]["topic"] for ex in generated)
    console.print("\n[bold]Par topic:[/bold]")
    for topic, count in topics.most_common():
        console.print(f"  {topic}: {count}")

    return generated


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=150, help="Nombre d'exemples a generer")
    args = parser.parse_args()

    generate_dataset(args.count)


if __name__ == "__main__":
    main()
