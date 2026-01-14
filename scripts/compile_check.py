#!/usr/bin/env python3
"""
Verification de compilation du code Rust extrait des reponses.

Usage:
    python scripts/compile_check.py --response "## Solution\n```rust\nfn main() {}\n```"
    python scripts/compile_check.py --file reports/eval_baseline.json
"""

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CompileResult:
    """Resultat de compilation d'un bloc de code."""
    success: bool
    code: str
    error: str | None = None
    is_complete: bool = True  # True si le code semble complet (a un main ou est un snippet)


def extract_rust_blocks(text: str) -> list[str]:
    """Extrait tous les blocs de code Rust d'un texte."""
    # Pattern pour ```rust ... ``` ou ``` ... ``` (sans langage specifie)
    pattern = r"```(?:rust)?\s*\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    return [m.strip() for m in matches if m.strip()]


def is_complete_program(code: str) -> bool:
    """Verifie si le code est un programme complet (avec fn main)."""
    return "fn main" in code


def wrap_in_main(code: str) -> str:
    """Enveloppe le code dans une fonction main si necessaire."""
    if is_complete_program(code):
        return code
    # Ajouter les imports communs si necessaire
    imports = ""
    if "HashMap" in code and "use std::collections::HashMap" not in code:
        imports += "use std::collections::HashMap;\n"
    if "Vec" in code and "use std::vec::Vec" not in code:
        # Vec est dans le prelude, pas besoin d'import
        pass
    return f"{imports}fn main() {{\n{code}\n}}"


def compile_rust_code(code: str, timeout: int = 10) -> CompileResult:
    """Compile un bloc de code Rust et retourne le resultat."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = Path(tmpdir) / "main.rs"
        out_path = Path(tmpdir) / "main"

        # Ecrire le code source
        src_path.write_text(code)

        try:
            result = subprocess.run(
                ["rustc", str(src_path), "-o", str(out_path), "--edition", "2021"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode == 0:
                return CompileResult(success=True, code=code)
            else:
                return CompileResult(
                    success=False,
                    code=code,
                    error=result.stderr[:500] if result.stderr else "Unknown error"
                )
        except subprocess.TimeoutExpired:
            return CompileResult(success=False, code=code, error="Compilation timeout")
        except Exception as e:
            return CompileResult(success=False, code=code, error=str(e))


def check_response(response: str) -> dict:
    """Verifie tous les blocs de code d'une reponse."""
    blocks = extract_rust_blocks(response)

    if not blocks:
        return {
            "has_code": False,
            "blocks_count": 0,
            "compiled": 0,
            "failed": 0,
            "compilation_rate": None,
            "errors": []
        }

    results = []
    compiled = 0
    errors = []

    for i, block in enumerate(blocks):
        # Essayer de compiler tel quel
        result = compile_rust_code(block)

        # Si echec et pas de main, essayer avec wrapper
        if not result.success and not is_complete_program(block):
            wrapped = wrap_in_main(block)
            result = compile_rust_code(wrapped)
            result.is_complete = False

        if result.success:
            compiled += 1
        else:
            errors.append({
                "block": i + 1,
                "code_preview": block[:100] + "..." if len(block) > 100 else block,
                "error": result.error
            })

        results.append(result)

    return {
        "has_code": True,
        "blocks_count": len(blocks),
        "compiled": compiled,
        "failed": len(blocks) - compiled,
        "compilation_rate": compiled / len(blocks) if blocks else 0,
        "errors": errors
    }


def check_eval_file(filepath: Path) -> dict:
    """Analyse un fichier de resultats d'evaluation."""
    with open(filepath) as f:
        data = json.load(f)

    results = []
    total_blocks = 0
    total_compiled = 0
    responses_with_code = 0

    for item in data.get("results", []):
        response = item.get("response", "")
        check = check_response(response)

        if check["has_code"]:
            responses_with_code += 1
            total_blocks += check["blocks_count"]
            total_compiled += check["compiled"]

        results.append({
            "prompt_id": item.get("prompt_id"),
            "category": item.get("category"),
            **check
        })

    return {
        "file": str(filepath),
        "total_responses": len(data.get("results", [])),
        "responses_with_code": responses_with_code,
        "total_blocks": total_blocks,
        "total_compiled": total_compiled,
        "overall_compilation_rate": total_compiled / total_blocks if total_blocks > 0 else 0,
        "details": results
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Verification compilation Rust")
    parser.add_argument("--response", type=str, help="Texte de reponse a verifier")
    parser.add_argument("--file", type=Path, help="Fichier JSON d'evaluation")
    parser.add_argument("--output", type=Path, help="Fichier de sortie JSON")
    args = parser.parse_args()

    if args.response:
        result = check_response(args.response)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.file:
        result = check_eval_file(args.file)

        print(f"\nResultats compilation pour {args.file.name}")
        print("=" * 50)
        print(f"Reponses avec code: {result['responses_with_code']}/{result['total_responses']}")
        print(f"Blocs de code: {result['total_blocks']}")
        print(f"Compiles OK: {result['total_compiled']}")
        print(f"Taux de compilation: {result['overall_compilation_rate']:.1%}")

        # Afficher les erreurs
        errors_count = sum(len(d["errors"]) for d in result["details"])
        if errors_count > 0:
            print(f"\nErreurs ({errors_count}):")
            for detail in result["details"]:
                for err in detail["errors"]:
                    print(f"  - {detail['prompt_id']}: {err['error'][:80]}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nResultats sauvegardes: {args.output}")

    else:
        # Demo
        demo = """
## Solution
```rust
fn main() {
    let x = 5;
    println!("{}", x);
}
```
"""
        result = check_response(demo)
        print("Demo:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
