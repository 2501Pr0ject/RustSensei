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
- **RAG** - 8 sources officielles (Book, Reference, Cookbook, Async, Nomicon...)
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

### v1.0 (termine)

- [x] **M0-M7** : CLI + RAG + Fine-tune + Packaging

### v2.0 (planifie)

- [ ] **M8** : Web UI (React + TypeScript + Tailwind)
- [ ] **M9** : Dataset etendu (200+ exemples)
- [x] **M10** : RAG etendu (Cookbook, Async, Nomicon, Rustlings, Edition Guide)
- [ ] **M11** : Docker
- [ ] **M12** : Qualite (reranker, eval humaine)

Details : voir [Roadmap v2.0](#roadmap-v20)

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

---

## Roadmap v2.0

### M8 — Web UI

| Composant | Techno |
|-----------|--------|
| Frontend | React + TypeScript + Tailwind |
| Backend | FastAPI |
| Build | Vite |

Fonctionnalites :
- Chat interface avec historique
- Toggle RAG on/off
- Citations avec liens vers docs
- Syntax highlighting Rust
- Mode sombre

### M9 — Dataset etendu

- 200+ exemples (vs 49 actuels)
- Focus lifetimes/borrowing (categories faibles)
- Validation compilation automatique
- Fine-tune LoRA v2

### M10 — RAG etendu (termine)

Sources ajoutees :
| Source | Chunks | Description |
|--------|--------|-------------|
| Rust Cookbook | 200 | Recettes pratiques |
| Async Book | 156 | Async/await |
| Rustlings | 70 | Exercices |
| Rustonomicon | 180 | Unsafe Rust |
| Edition Guide | 175 | Editions Rust |
| **Total** | **2,378** | +49% vs v1.0 |

### M11 — Docker

- Image Docker tout-en-un
- docker-compose (API + UI)
- Installation one-click
- Support GPU optionnel

### M12 — Qualite

- Reranker multilingue (mmarco)
- Evaluation humaine
- Support multi-fichiers (projets Cargo)
- Modele 7B (optionnel)
