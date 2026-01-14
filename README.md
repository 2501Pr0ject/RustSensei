# RustSensei

Un assistant local pour apprendre le Rust en francais.

## Quick Start (< 2 min)

```bash
# 1. Cloner
git clone https://github.com/2501Pr0ject/RustSensei.git
cd RustSensei

# 2. Installer (Python + llama.cpp + modele)
make install-all

# 3. Lancer
make chat
```

**Prerequis**: Python 3.11+, [uv](https://github.com/astral-sh/uv), macOS Apple Silicon recommande

## Fonctionnalites

- **100% local** - Fonctionne sans connexion internet
- **Inference rapide** - llama.cpp optimise Metal/MPS
- **RAG** - Reponses enrichies avec la documentation Rust officielle
- **87% compilation** - Le code genere compile
- **Francais** - Reponses pedagogiques en francais

## Metriques

| Metrique | Valeur |
|----------|--------|
| Score global | 3.07/5 |
| Langue FR | 95% |
| Compilation | 87% |
| RAG boost | +10% |

## Utilisation

```bash
# Chat interactif
make chat

# Chat avec RAG (documentation Rust)
make chat-rag

# Evaluation
make eval

# Verification compilation
make compile-check
```

### Exemple

```
> Pourquoi ce code ne compile pas ?
> let s = String::from("hello");
> let s2 = s;
> println!("{}", s);

## TL;DR
La variable s a ete deplacee vers s2, elle n'est plus utilisable.

## Solution
let s2 = s.clone();  // ou let s2 = &s;
...
```

## Structure

```
RustSensei/
├── app/           # CLI et RAG (chat.py, rag.py)
├── scripts/       # Evaluation, training, export
├── configs/       # Configuration modele, RAG, training
├── data/          # Dataset d'entrainement
├── eval/          # Prompts d'evaluation
├── models/        # Modeles GGUF et adaptateurs LoRA
├── rag/           # Index de documentation
├── reports/       # Resultats et metriques
└── vendor/        # llama.cpp
```

## Documentation

- [MODEL_CARD.md](MODEL_CARD.md) - Specifications du modele
- [EVALUATION.md](EVALUATION.md) - Systeme d'evaluation

## Roadmap

- [x] **M0** : Structure du projet
- [x] **M1** : Baseline llama.cpp + CLI (3.00/5)
- [x] **M2** : RAG v0 (+10%)
- [x] **M3** : Dataset v0 (49 exemples)
- [x] **M4** : Fine-tune LoRA
- [x] **M5** : Verification compilation (87%)
- [x] **M6** : Packaging
- [ ] **M7** : RAG avance (rerank, chunking ameliore)

## Installation detaillee

```bash
# Etape par etape
make setup           # Dependances Python
make install-llama   # Compiler llama.cpp
make download-model  # Telecharger le modele GGUF
make build-index     # Construire l'index RAG

# Verifier
make check
```

## Licence

MIT License

## Auteur

**Abdel TOUATI**
