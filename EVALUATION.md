# Évaluation — RustSensei

Ce document décrit le système d'évaluation de RustSensei.

## Lancer l'évaluation

```bash
# Évaluation complète (50 prompts)
make eval

# Smoke test rapide (5 prompts)
make eval-smoke

# Évaluation avec limite personnalisée
uv run python scripts/evaluate.py --limit 10

# Spécifier un fichier de sortie
uv run python scripts/evaluate.py --output reports/mon_eval.json
```

## Prompts d'évaluation

Les prompts sont stockés dans `eval/prompts_fr.jsonl` (format JSON Lines).

### Catégories

| Catégorie | Description | Difficulté |
|-----------|-------------|------------|
| basics | Variables, types, fonctions | débutant |
| ownership | Propriété, move, drop | intermédiaire |
| borrowing | Références, lifetimes | intermédiaire |
| structs | Structures, impl, traits | intermédiaire |
| errors | Result, Option, ? | intermédiaire |
| collections | Vec, HashMap, iterators | intermédiaire |
| concurrency | Threads, channels, Arc/Mutex | avancé |
| macros | Déclaratif, procédural | avancé |

### Format d'un prompt

```json
{
  "id": 1,
  "category": "basics",
  "difficulty": "debutant",
  "prompt": "Comment déclarer une variable mutable en Rust ?",
  "expected_topics": ["let", "mut", "variable"]
}
```

## Grille d'évaluation

La grille est définie dans `eval/rubric.json`.

### Critères automatiques

| Critère | Poids | Description |
|---------|-------|-------------|
| language | 20% | Réponse en français (détection mots-clés) |
| code_blocks | 20% | Présence de blocs ```rust |
| expected_topics | 40% | Couverture des topics attendus |
| response_length | 20% | Longueur entre 100-800 mots |

### Score format (bonus)

Vérifie la présence des sections structurées :
- `## TL;DR`
- `## Problème`
- `## Solution`
- `## Explication`
- `## À retenir`

## Résultats

Les résultats sont sauvegardés dans `reports/` au format JSON.

### Structure du rapport

```json
{
  "timestamp": "2025-01-09T14:18:07.715907",
  "model": {
    "name": "Qwen2.5-Coder-1.5B-Instruct",
    "repo": "Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF",
    "file": "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
    "quantization": "Q4_K_M"
  },
  "inference_params": {
    "n_ctx": 4096,
    "n_predict": 1024,
    "threads": 8,
    "n_gpu_layers": 99,
    "temp": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "seed": 42
  },
  "llama_cpp_rev": "b4823",
  "total_prompts": 10,
  "results": [...]
}
```

### Reproductibilité

Pour reproduire exactement les mêmes résultats :

1. Utiliser le même modèle GGUF (`qwen2.5-coder-1.5b-instruct-q4_k_m.gguf`)
2. Utiliser la même révision llama.cpp (`b4823`)
3. Utiliser le même seed (`42`)
4. Garder les mêmes paramètres d'inférence

## Baseline M1

| Métrique | Valeur |
|----------|--------|
| Score global | 2.87/5 |
| Langue FR | 90% |
| Code blocks | 70% |
| Longueur OK | 60% |
| Format structuré | 0% |

Voir `reports/baseline_examples.md` pour 10 exemples annotés.

## Comparaisons futures

| Version | Score | Notes |
|---------|-------|-------|
| M1 Baseline | 2.87/5 | Sans RAG ni fine-tune |
| M2 + RAG | TBD | Avec contexte documentation |
| M4 + LoRA | TBD | Après fine-tuning |

## Ajouter des prompts

1. Éditer `eval/prompts_fr.jsonl`
2. Ajouter une ligne JSON avec les champs requis
3. Lancer `make eval-smoke` pour valider
