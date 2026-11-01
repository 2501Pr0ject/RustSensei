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
- **Compilation : 61%** - Évaluation auto sur 50 prompts
- **Français** - Réponses pédagogiques en français (100%)

## Métriques

| Métrique | Valeur |
|----------|--------|
| Score global | 3.10/5 |
| Langue FR | 100% |
| Compilation | 61% |
| Dataset | 221 exemples |

*Évaluation : 50 prompts, 5 critères, RAG activé*

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
- Mode sombre

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
