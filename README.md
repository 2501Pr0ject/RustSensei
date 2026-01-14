# RustSensei

Un assistant local pour apprendre le Rust en français.

## Objectif

RustSensei est un outil pédagogique spécialisé dans l'enseignement du langage Rust. Il fournit des explications claires, corrige les erreurs courantes et guide les apprenants avec des réponses structurées.

**Fonctionne 100% en local, sans connexion internet.**

## Caractéristiques

- **Inférence locale** : llama.cpp (optimisé Apple Silicon)
- **RAG** : Réponses enrichies avec la documentation Rust officielle
- **Langue** : Français
- **Open source** : MIT License

## Structure du projet

```
RustSenseï/
├── app/               # CLI et interface utilisateur
├── scripts/           # Scripts d'évaluation et de traitement
├── configs/           # Configurations (modèle, RAG)
├── data/              # Données (raw, processed)
├── eval/              # Prompts d'évaluation et métriques
├── rag/               # Documents et index pour le RAG
├── reports/           # Résultats d'évaluation
└── tests/             # Tests unitaires
```

## Prérequis

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- macOS Apple Silicon (M1/M2) recommandé

## Installation

```bash
git clone https://github.com/2501Pr0ject/RustSensei.git
cd RustSenseï

# Installation complète (Python + llama.cpp + modèle)
make install-all

# Ou étape par étape :
make setup           # Dépendances Python
make install-llama   # Compiler llama.cpp (Metal/MPS)
make download-model  # Télécharger le modèle GGUF

# Vérifier l'installation
make check
```

## Utilisation

```bash
# Chat interactif
make chat

# Évaluation
make eval
```

## Roadmap

- [x] **M0** : Structure du projet, prompts d'evaluation
- [x] **M1** : Baseline llama.cpp + CLI + eval (score: 3.00/5)
- [x] **M2** : RAG v0 (score: 3.35/5, +10%)
- [x] **M3** : Dataset v0 (49 exemples structures)
- [x] **M4** : Fine-tune LoRA (pipeline mlx-lm)
- [ ] **M5** : Evaluation Rust automatique (compilation)
- [ ] **M6** : Packaging et distribution

## Licence

MIT License - voir [LICENSE](LICENSE)

## Auteur

**Abdel TOUATI**
