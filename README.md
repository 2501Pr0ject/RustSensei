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

**Prérequis** : Python 3.11+, [uv](https://github.com/astral-sh/uv), macOS Apple Silicon recommandé

## Fonctionnalités

- **100% local** - Fonctionne sans connexion internet (après installation)
- **Inférence rapide** - llama.cpp optimisé Metal/MPS
- **RAG** - 8 sources officielles (Book, Reference, Cookbook, Async, Nomicon...)
- **Retrieval hybride** - Dense (FAISS) + lexical (BM25), fusion RRF, graphe de connaissances et rerank multilingue
- **Sources cliquables** - Citations RAG affichées en liens dans l'interface
- **Cache (CAG)** - Réponses mémorisées sur disque, exactes ou sémantiquement proches
- **Conversation multi-tours** - Historique (3 derniers échanges) envoyé au modèle contextuel
- **Compilation : 49%** des blocs de code - Évaluation auto sur 91 prompts, 3 graines
- **Français** - Réponses pédagogiques en français (100%)

## Métriques

Référence actuelle : Qwen2.5-Coder-1.5B-Instruct (GGUF officiel Qwen, Q4_K_M),
RAG activé (retrieval hybride dense + BM25, graphe de connaissances, reranker
multilingue).

| Métrique | Valeur |
|----------|--------|
| Score global | 3.05/5 (graines 42, 1, 2 : 3.08 / 3.10 / 2.98) |
| Langue FR | 99% |
| Compilation (blocs) | 49% (173/351) |
| Format en 5 sections | 14% des réponses |
| Dataset | 221 exemples |

*Évaluation : 91 prompts (`eval/prompts_fr.jsonl`), 3 graines, notation v2 :
mots-clés avec alternatives, casse et accents normalisés, frontière de mot à
gauche (`SCORER_VERSION` dans `scripts/evaluate.py`, enregistré dans chaque
rapport). 27 prompts recoupent les données d'entraînement LoRA
(`"in_lora_train": true`) ; les 64 autres forment le sous-ensemble « hors
entraînement » (`--held-out`).*

**Anciens chiffres recalculés.** Les évaluations de janvier et du 1er novembre
(50 prompts) ont été renotées avec la notation v2 à partir des réponses
stockées (`scripts/rescore_reports.py`, marqueur `[end of text]` retiré des
réponses de janvier), sans régénération ; les copies renotées sont dans
`reports/rescored/`. Sur les prompts 1-50 : janvier 3.10/5, novembre 3.19/5
(3 graines), écart +0.09, IC95 [-0.14, +0.33], non significatif. Le nouveau
retrieval cite en revanche moins souvent des sources hors sujet (Rustonomicon,
Async Book ou Edition Guide pour une question qui n'y touche pas : 26 citations
au lieu de 42).

### Modèles évalués

| Modèle | Score | Écart à la référence (IC95) | FR | 5 sections | Compilation |
|--------|-------|-----------------------------|----|------------|-------------|
| Qwen2.5-Coder-1.5B (référence, 3 graines) | 3.05 | — | 99% | 14% | 49% |
| Qwen2.5-Coder-3B (GGUF officiel, 3 graines) | 3.57 | +0.52 [+0.39, +0.67] | 100% | 92% | 53% |
| LoRA correctif de janvier (graine 42) | 2.63 | -0.45 [-0.72, -0.16] (vs graine 42) | 80% | 5% | 34% |

- **3B** : l'écart est significatif sur tous les sous-ensembles — prompts 1-50
  +0.34, prompts 51-91 +0.74, hors entraînement +0.55 [+0.37, +0.74]. Coût :
  fichier de 2.1 Go, environ 34 s par réponse en évaluation contre 14 s pour le
  1.5B (réponses plus longues, médiane 293 mots contre 184). Licence
  `qwen-research` (le 1.5B est sous Apache 2.0) : à vérifier avant adoption.
- **LoRA correctif** : résultat rapporté pour information uniquement. Il a été
  entraîné avec un autre prompt système, sans contexte RAG, et quantifié par un
  pipeline local différent du GGUF officiel : il n'est pas représentatif d'un
  futur LoRA v2.

Reproduire :

```bash
uv run python scripts/evaluate.py --rag --seeds 42,1,2 [--model models/<fichier>.gguf]
uv run python scripts/rescore_reports.py reports/eval_rag_*.json   # après un changement de notation
uv run python scripts/compare_evals.py --ref <rapports référence> --new <rapports candidat> [--held-out] [--ids 1-50]
```

## Cache et retrieval hybride

Le cache de réponses (CAG) mémorise les réponses par question normalisée et les
persiste dans `data/cache.json` : une question déjà posée est servie
instantanément, même après un redémarrage. Le TTL (7 jours par défaut) se règle
dans `configs/rag_config.yaml` (section `cache`).

La recherche est d'abord exacte, puis sémantique : si une question proche a déjà
été posée, son embedding (modèle RAG) est comparé par similarité cosinus et la
réponse est réutilisée au-delà du seuil `cache.semantic.threshold` (0.85 par
défaut). Les reformulations du type « Comment créer un thread ? » / « Comment on
crée un thread ? » touchent ainsi le cache sans génération.

Les réponses RAG affichent leurs sources dans l'interface : le backend transmet
les citations via le header `X-Citations` (base64/UTF-8) et l'UI les rend sous
forme de liens vers la documentation officielle. Les réponses issues du cache
sont signalées par un badge (header `X-Cache` dans `/chat/stream`), ainsi que par
`GET /cache/stats`.

Le retrieval (KAG) combine deux canaux : recherche dense FAISS et recherche
lexicale BM25, fusionnées par Reciprocal Rank Fusion, puis réordonnées par un
cross-encoder multilingue. Les termes exacts (noms d'API, types) sont ainsi
mieux couverts que par la recherche dense seule.

Le graphe de connaissances relie les concepts Rust (ownership, Send/Sync, Rc,
lifetimes, Result...) avec leurs alias FR/EN (`configs/knowledge_graph.yaml`).
Une question qui croise plusieurs domaines fait remonter les pages des concepts
voisins via un canal lexical supplémentaire : « Pourquoi RefCell ne peut pas
être partagé entre threads ? » récupère aussi les pages Send/Sync.

Statistiques du cache :

```bash
curl http://localhost:8000/cache/stats
# {"entries": 4, "hits": 3, "misses": 1, "hit_rate": 0.75,
#  "semantic_enabled": true, "semantic_threshold": 0.85, ...}
```

### Conversation multi-tours

L'historique des échanges est transmis au backend (`/chat`, `/chat/stream` avec
le champ `history` de type `{role, content}`, rôles `user`/`assistant` uniquement,
plafonné à 6 messages ; chaque message est tronqué à 666 caractères pour rester
dans un budget de 4 000 caractères). Le prompt est construit avec le format
`Conversation précédente :` juste avant la question courante, puis le contexte RAG.

La clé de cache est composite (historique normalisé + question) : une réponse est
servie depuis le cache uniquement si l'historique et la question correspondent
exactement. Le matching sémantique (similarité) est désactivé en multi-tours.

L'historique est persisté dans le navigateur (`localStorage`, clé
`rustsensei_history`, 6 derniers messages) et restauré au chargement de la page.
Le bouton « Effacer » repart d'une conversation vide.

```bash
curl -s -X POST http://localhost:8000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"Puis je le partager entre deux threads ?", "use_rag": true, "history": [{"role":"user","content":"Qu est ce qu un Rc ?"}]}'
```

## Utilisation

```bash
# Chat interactif
make chat

# Chat avec RAG (documentation Rust)
make chat-rag

# Évaluation
make eval

# Vérification compilation
make compile-check

# Interface web (deux terminaux)
make api   # API FastAPI sur http://localhost:8000
make web   # UI sur http://localhost:5173
```

Dans l'interface web, Entrée envoie la question et Maj+Entrée insère un saut de
ligne : on peut coller un extrait de code Rust sur plusieurs lignes. Sur écran
tactile, Entrée insère un saut de ligne et l'envoi se fait avec le bouton.

L'interface affiche aussi :
- l'état de l'API dans l'en-tête, avec une nouvelle tentative automatique quand
  elle est hors ligne (`GET /health`, qui indique aussi si l'index RAG est
  disponible : `{"status": "ok", "rag_available": true, "rag_error": null}`) ;
- un bouton **Stop** pendant la génération : la réponse partielle est conservée
  et la génération est arrêtée côté serveur ;
- un bouton **Copier** et le langage sur chaque bloc de code ;
- des exemples de questions cliquables quand la conversation est vide.

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
├── app/           # CLI, API et RAG (chat.py, rag.py, cache.py, knowledge.py)
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

### v1.0 (terminé)

- [x] **M0-M7** : CLI + RAG + Fine-tune + Packaging

### v2.0 (planifié)

- [ ] **M8** : Web UI (React + TypeScript + Tailwind)
- [x] **M9** : Dataset étendu (221 exemples, LoRA en pause)
- [x] **M10** : RAG étendu (Cookbook, Async, Nomicon, Rustlings, Edition Guide)
- [ ] **M11** : Docker
- [ ] **M12** : Qualité (reranker, éval humaine)

Details : voir [Roadmap v2.0](#roadmap-v20)

## Installation détaillée

```bash
# Étape par étape
make setup           # Dépendances Python
make install-llama   # Compiler llama.cpp
make download-model  # Télécharger le modèle GGUF
make build-index     # Construire l'index RAG

# Vérifier
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

Fonctionnalités :
- Chat interface avec historique
- Toggle RAG on/off
- Citations avec liens vers docs
- Syntax highlighting Rust
- Saisie multi-ligne pour coller du code
- Bouton Stop, copie des blocs de code, état de l'API

### M9 — Dataset étendu (terminé)

**Résultats :**
| Métrique | Avant | Après |
|----------|-------|-------|
| Exemples | 49 | 221 (+351%) |
| Lifetimes | 3 | 34 |
| Borrowing | 3 | 26 |
| Async | 1 | 21 |

**Ce qui a fonctionné :**
- Extension du dataset avec focus sur les catégories faibles
- Prompt simplifié pour 100% français
- Validation compilation automatique des exemples

**Ce qui n'a pas fonctionné :**
- Fine-tuning LoRA sur MacBook M2 16GB : crashes répétitifs (Metal GPU timeout)
- Les adaptateurs LoRA amélioraient certains topics (+67% lifetimes) mais en dégradaient d'autres (catastrophic forgetting)

**Décision :** Utiliser le modèle baseline (Qwen2.5-Coder-1.5B) sans LoRA pour garantir la stabilité. Le dataset étendu reste disponible pour un futur fine-tuning sur hardware plus robuste.

### M10 — RAG étendu (terminé)

Sources ajoutées :
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

### M12 — Qualité

- Reranker multilingue (mmarco)
- Évaluation humaine
- Support multi-fichiers (projets Cargo)
- Modèle 7B (optionnel)
