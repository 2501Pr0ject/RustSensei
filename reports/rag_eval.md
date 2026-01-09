# Évaluation RAG v0 — Comparaison Baseline vs RAG

**Date** : 2026-01-09
**Modèle** : Qwen2.5-Coder-1.5B-Instruct (Q4_K_M)
**Prompts** : 20

## Résumé

| Mode     | Score global | Language | Code blocks | Response length |
|----------|--------------|----------|-------------|-----------------|
| Baseline | 3.05/5       | 95%      | 70%         | 70%             |
| **RAG**  | **3.35/5**   | **100%** | **80%**     | **80%**         |

**Amélioration** : +10% sur le score global

## Scores par catégorie

| Catégorie | Baseline | RAG      | Δ       |
|-----------|----------|----------|---------|
| basics    | 3.00/5   | 3.40/5   | +13%    |
| borrowing | 3.22/5   | 2.89/5   | -10%    |
| enums     | 4.28/5   | 4.06/5   | -5%     |
| lifetimes | 1.33/5   | 2.89/5   | **+117%** |
| ownership | 2.33/5   | 3.33/5   | +43%    |
| structs   | 4.17/5   | 3.50/5   | -16%    |

## Observations

### Points positifs du RAG

1. **Lifetimes** : Amélioration majeure (+117%), le contexte aide le modèle à mieux expliquer ce concept difficile
2. **Ownership** : +43%, les exemples de la documentation enrichissent les réponses
3. **Basics** : +13%, réponses plus complètes avec exemples de code
4. **Language check** : 100% en français (vs 95% baseline)
5. **Citations** : Chaque réponse inclut 2-4 sources traçables

### Points à améliorer

1. **Borrowing/Structs** : Légère régression, potentiellement dû au bruit dans le contexte récupéré
2. **Enums** : Baseline déjà bon, RAG n'apporte pas d'amélioration significative
3. **Format** : Les sections structurées (TL;DR, Problème, Solution) ne sont toujours pas respectées

## Configuration RAG

- **Embedding** : sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384 dim)
- **Index** : FAISS IndexFlatIP (cosine similarity)
- **Sources** : Rust Book (514 chunks) + Rust by Example (265 chunks) + Rust Reference (707 chunks)
- **Total chunks** : 1486
- **Retrieval** : top_k=5, threshold=0.3
- **Context** : max 1500 tokens

## Exemple de réponse avec citations

**Question** : "Comment déclarer une variable mutable en Rust ?"

**Réponse RAG** (extraits) :
> Pour déclarer une variable mutable en Rust, utilisez la syntaxe suivante :
> ```rust
> let mut variable_name = initial_value;
> ```
> Dans cette ligne de code : `mut` signifie que `variable_name` est mutable...

**Citations** :
- [Rust Book — Data Types]
- [Rust Book — How to Write Tests > Structuring Test Functions]

## Fichiers de résultats

- `reports/eval_baseline_20.json` — Résultats baseline
- `reports/eval_rag_20.json` — Résultats RAG

## Conclusion

Le RAG v0 apporte une amélioration globale de **+10%** et une amélioration significative sur les concepts difficiles comme les **lifetimes** (+117%). Les citations permettent de tracer l'origine des informations.

Prochaines étapes :
- Affiner le retrieval (reranking, filtering par source)
- Améliorer le prompt template pour forcer le format structuré
- Ajouter les docs std lib (M2.1)
