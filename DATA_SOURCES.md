# DATA_SOURCES.md — Sources de données RustSensei

Ce document décrit les sources de données utilisées pour le projet RustSensei, leurs licences et les méthodes d'acquisition.

## Principe général

**Aucun contenu externe n'est directement inclus dans ce repository.** Seuls sont committés :
- Les scripts de reconstruction (`scripts/`)
- Les échantillons de dataset curés (`data_samples/`)
- Les configurations (`configs/`)

Les données volumineuses (documentation, index) sont reconstruites à la demande via les scripts.

---

## Sources RAG (M2)

### 1. The Rust Programming Language (Book)

| Champ | Valeur |
|-------|--------|
| Source | https://github.com/rust-lang/book |
| Licence | [MIT/Apache 2.0](https://github.com/rust-lang/book/blob/main/COPYRIGHT) |
| Type | Markdown |
| Acquisition | `git clone --depth 1` via `scripts/download_docs.py` |
| Stockage | `rag/docs/book/` (gitignored) |
| Contenu | ~60 chapitres, concepts fondamentaux Rust |

### 2. Rust by Example

| Champ | Valeur |
|-------|--------|
| Source | https://github.com/rust-lang/rust-by-example |
| Licence | [MIT/Apache 2.0](https://github.com/rust-lang/rust-by-example/blob/master/LICENSE-MIT) |
| Type | Markdown |
| Acquisition | `git clone --depth 1` via `scripts/download_docs.py` |
| Stockage | `rag/docs/rbe/` (gitignored) |
| Contenu | Exemples de code annotés par concept |

### 3. The Rust Reference

| Champ | Valeur |
|-------|--------|
| Source | https://github.com/rust-lang/reference |
| Licence | [MIT/Apache 2.0](https://github.com/rust-lang/reference/blob/master/LICENSE-MIT) |
| Type | Markdown |
| Acquisition | `git clone --depth 1` via `scripts/download_docs.py` |
| Stockage | `rag/docs/reference/` (gitignored) |
| Contenu | Spécification détaillée du langage |

---

## Dataset d'entraînement (M3)

### Exemples curés

| Champ | Valeur |
|-------|--------|
| Source | Création originale |
| Licence | MIT (ce projet) |
| Type | Chat JSONL |
| Fichier | `data_samples/dataset_sample.jsonl` |
| Contenu | ~25-50 exemples qualité |

**Catégories** :
- `debug` (40%) : Correction de bugs, erreurs de compilation
- `concepts` (40%) : Explications de concepts Rust
- `exercises` (20%) : Exercices guidés avec hints

**Format** :
```json
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "metadata": {
    "category": "debug|concepts|exercises",
    "topic": "ownership|borrowing|...",
    "difficulty": "debutant|intermediaire|avance"
  }
}
```

### Sources futures (M3+)

- **Rustlings** : Exercices progressifs (MIT)
- **Exercism Rust Track** : Exercices communautaires (MIT)
- **Stack Overflow** : Q&A publiques (CC BY-SA 4.0)

---

## Reconstruction des données

### RAG Index

```bash
# 1. Télécharger les sources
make download-docs

# 2. Construire l'index
make build-index
```

**Résultat** :
- `rag/index/rustsensei.faiss` (index vecteur)
- `rag/index/metadata.pkl` (métadonnées chunks)
- `rag/index/manifest.json` (info de build)

### Dataset

```bash
# Générer le dataset
make build-dataset

# Valider le format
make validate-dataset
```

---

## Licences compatibles

Toutes les sources utilisées sont sous licences permissives compatibles avec un usage open-source :

| Licence | Usage commercial | Modification | Attribution |
|---------|------------------|--------------|-------------|
| MIT | ✅ | ✅ | ✅ Requise |
| Apache 2.0 | ✅ | ✅ | ✅ Requise |
| CC BY-SA 4.0 | ✅ | ✅ | ✅ Requise + ShareAlike |

---

## Ce qui n'est PAS inclus

- ❌ Dumps complets de documentation
- ❌ Datasets propriétaires
- ❌ Contenu sous copyright restrictif
- ❌ Code généré sans vérification de licence
