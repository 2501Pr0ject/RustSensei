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
git clone https://github.com/votre-username/RustSensei.git
cd RustSenseï

# Installer les dépendances
make setup

# Télécharger le modèle
make download-model
```

## Utilisation

```bash
# Chat interactif
make chat

# Évaluation
make eval
```

## Roadmap

- [x] **M0** : Structure du projet, prompts d'évaluation
- [ ] **M1** : Baseline llama.cpp + CLI + éval
- [ ] **M2** : RAG v0 (fiabilité)
- [ ] **M3** : Dataset v0 (qualité)
- [ ] **M4** : Fine-tune LoRA

## Licence

MIT License - voir [LICENSE](LICENSE)

## Auteur

**Abdel TOUATI**
