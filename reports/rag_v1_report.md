# Rapport M7 — RAG avance

## Resume

| Metrique | Baseline | RAG v1 | Delta |
|----------|----------|--------|-------|
| Score | 3.12/5 | 3.22/5 | **+3%** |
| Langue FR | 98% | 98% | 0% |
| Code blocks | 76% | 80% | +5% |
| Compilation | 76% | 63% | -17% |
| Index chunks | 1486 | 1595 | +7% |

## Ameliorations implementees

### 1. Chunking ameliore

| Parametre | Avant | Apres |
|-----------|-------|-------|
| max_tokens | 1000 | 800 |
| target_tokens | 500 | 400 |
| overlap_tokens | 0 | 50 |

L'overlap de 50 tokens entre chunks ameliore la continuite du contexte.

### 2. Reranking (desactive)

Modele teste : `cross-encoder/ms-marco-MiniLM-L-6-v2`

Resultats :
- Score avec rerank : 3.01/5 (-3% vs baseline)
- Score sans rerank : 3.22/5 (+3% vs baseline)

Le cross-encoder anglais degrade les resultats sur des requetes francaises.

### 3. Citations avec URLs

Format : `[Source — Heading](URL)`

Exemple :
```
[Rust Book — Ownership](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html)
```

## Scores par categorie (RAG v1 vs Baseline)

| Categorie | Baseline | RAG v1 | Delta |
|-----------|----------|--------|-------|
| basics | 3.02 | 4.01 | +33% |
| enums | 4.24 | 4.40 | +4% |
| structs | 4.02 | 4.15 | +3% |
| lifetimes | 1.25 | 2.75 | +120% |
| concurrency | 2.50 | 3.46 | +38% |
| generics | 2.33 | 2.98 | +28% |
| borrowing | 3.39 | 2.00 | -41% |
| ownership | 2.54 | 2.04 | -20% |

## Conclusions

### Ce qui fonctionne

1. **Chunking ameliore** : +3% score global
2. **Lifetimes** : forte amelioration (+120%)
3. **Citations avec URLs** : meilleure tracabilite

### Limitations

1. **Rerank cross-encoder** : degrade les resultats (modele anglais)
2. **Compilation rate** : baisse de 76% a 63% (plus de code genere mais moins precis)
3. **Borrowing/Ownership** : regression sur certaines categories

### Recommandations futures

1. Tester un reranker multilingue (ex: mmarco)
2. Filtrer le contexte RAG pour eviter la confusion
3. Ajuster le prompt system pour mieux integrer le contexte

## Fichiers modifies

- `configs/rag_config.yaml` : nouvelle config chunking + rerank
- `scripts/build_index.py` : overlap entre chunks
- `app/rag.py` : reranking + citations avec URLs
- `DECISIONS.md` : D-0011
