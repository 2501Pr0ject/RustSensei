# RustSensei

Assistant local pour apprendre le Rust en français : il explique les concepts et
les erreurs du compilateur en s'appuyant sur la documentation officielle, sans
connexion internet, sur un Mac Apple Silicon.

## Démo vidéo

<!-- VIDÉO : insérer ici le lien ou le lecteur de la démo -->
> Vidéo à venir.

## Problème

La documentation Rust est en anglais et les erreurs du compilateur (ownership,
emprunts, lifetimes) déroutent les débutants. RustSensei est un tuteur en
français qui **tourne entièrement sur la machine** : le code et les questions ne
la quittent jamais, et il ne dépend d'aucun service (ni compte, ni clé d'API, ni
connexion une fois installé, ni coût à l'usage). Ses réponses s'appuient sur la
documentation officielle, dont il affiche les sources. Contrainte matérielle :
MacBook M2 16 Go, budget nul.

## Architecture

```
UI React (Vite) ──► API FastAPI ──► cache des réponses (exact + sémantique)
                        │
                        ├──► RAG : 8 sources officielles, 2 764 extraits
                        │     dense (FAISS, MiniLM multilingue) + BM25 → fusion RRF
                        │     + graphe de connaissances FR/EN → reranker multilingue
                        │     (aucun contexte si la question est hors documentation)
                        │
                        └──► llama-server persistant (llama.cpp b12032, Metal)
                              Qwen3-4B-Instruct-2507 (défaut)
                              ou Qwen2.5-Coder-1.5B-Instruct (mode rapide), Q4_K_M
CLI et évaluation ─────────► llama-completion (même modèle, mêmes réglages)
```

- **UI** : réponses en streaming, sources cliquables, saisie multi-ligne pour
  coller du code, bouton Stop, copie des blocs de code, conversation sur 3 échanges.
- **RAG, CAG, KAG** : RustSensei fait du **RAG** hybride (recherche dense et
  lexicale, reranker) avec un seuil de pertinence. Un **graphe de 35 concepts
  Rust** avec synonymes FR/EN élargit la requête d'un canal lexical : c'est une
  première brique vers une approche **KAG**, sans graphe tiré des documents ni
  raisonnement, et sa contribution seule n'a pas été mesurée. Le **CAG**
  (charger toute la base de connaissances dans le contexte du modèle) est écarté :
  la documentation dépasse largement les 8 192 tokens de contexte. Le cache des
  réponses est un cache sémantique distinct, sans rapport avec le CAG.
- **Sources RAG** : Rust Book, Reference, Rust by Example, Cookbook, Async Book,
  Rustonomicon, Edition Guide, Rustlings. Les exemples de code que mdBook inclut
  depuis d'autres fichiers (`{{#include}}`, `{{#rustdoc_include}}`) sont résolus
  à la construction de l'index, et l'italique autour des noms de fichiers est
  retiré. Si le meilleur extrait reste sous un cosinus de 0,42 (salutation,
  question hors Rust), aucune documentation n'est injectée.
- **Réponses** : en français, au tutoiement, sans emoji ; cinq sections
  (TL;DR, Problème, Solution, Explication, À retenir) pour une question de code
  ou une erreur de compilation, réponse simple et directe sinon.
- **Cache** : une réponse n'est resservie que si le modèle, le prompt système,
  l'échantillonnage, l'index et les réglages du RAG sont identiques (empreinte
  dans la clé).
- **Démarrage** : l'API charge le modèle et préchauffe le RAG au lancement, pour
  que la première question n'attende pas.
- **Configuration unique** (`configs/model_config.yaml`) : l'UI, le CLI et
  l'évaluation lisent le même échantillonnage, avec des réglages par modèle
  (`sampling_by_model`). Changer de modèle tient en une ligne (`paths.model`).

## Démarrage rapide

Prérequis : macOS Apple Silicon (16 Go recommandés), Python 3.11+,
[uv](https://github.com/astral-sh/uv), Node.js, Xcode Command Line Tools ;
`rustc` pour la vérification de compilation.

```bash
make install-all     # dépendances Python, compilation de llama.cpp, modèle 4B (2,5 Go)
make build-index     # téléchargement de la documentation et index RAG
make chat-rag        # chat en terminal avec la documentation
make api             # API sur http://localhost:8000 (charge le modèle au démarrage)
make web             # interface sur http://localhost:5173 (installe le front au besoin)
make install-dev && make test   # tests (161)
```

**Mode rapide** (environ 5 fois plus réactif, moins juste) : télécharger le 1.5B,
puis pointer `paths.model` vers lui dans `configs/model_config.yaml`.

```bash
make download-model MODEL_REPO=Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF \
                    MODEL_FILE=qwen2.5-coder-1.5b-instruct-q4_k_m.gguf
```

## Méthode d'évaluation

- **91 questions** en français, 19 catégories, du débutant à l'avancé
  (`eval/prompts_fr.jsonl`). 27 recoupent les données d'entraînement LoRA ;
  les 64 autres forment le sous-ensemble **hors entraînement**.
- **Choix des modèles** : 3 graines (42, 1, 2), RAG activé, réglages communs à
  tous (température 0,7, top-k 40, top-p 0,9, min-p 0,05, 1024 tokens au plus).
  **Configuration finale** : graine 42, avec les réglages propres à chaque modèle.
- **Score automatique sur 5** : réponse en français (20 %), présence de code (15 %),
  mots-clés attendus (35 %, avec alternatives, casse et accents normalisés),
  longueur de 100 à 800 mots (15 %), compilation des blocs par `rustc` (15 %).
- **Comparaisons appariées** par question, avec intervalle de confiance à 95 %
  par bootstrap. Chaque rapport enregistre le modèle, la version de llama.cpp,
  l'échantillonnage et la version de la notation ; un changement de notation
  se renote à partir des réponses stockées, sans régénérer.

```bash
uv run python scripts/evaluate.py --rag --seeds 42,1,2 [--model models/<fichier>.gguf]
uv run python scripts/compare_evals.py --ref <rapports> --new <rapports> [--held-out] [--ids 1-50]
uv run python scripts/rescore_reports.py reports/eval_rag_*.json
```

## Résultats

**Configuration finale** (2 novembre, graine 42, llama.cpp b12032) :

| Modèle | Score /5 | Écart au 1.5B (IC95) | Format 5 sections | Blocs qui compilent | Réponses coupées | Premier mot | Réponse complète |
|--------|----------|----------------------|-------------------|---------------------|------------------|-------------|------------------|
| **Qwen3-4B-Instruct-2507** (défaut) | **4,02** | +0,69 [+0,48 ; +0,90] | 89 % | 58 % | 0 / 91 | 11,2 s | 52 s |
| Qwen2.5-Coder-1.5B (mode rapide) | 3,34 | — | 87 % | 54 % | 2 / 91 | 3,2 s | 8 s |

Latences : médianes dans l'UI (4 questions avec RAG, serveur persistant), mesurées
le 1er novembre avec la limite de 1024 tokens.

- Le 4B devance le 1.5B sur tous les sous-ensembles : +0,76 [+0,52 ; +1,00] hors
  entraînement, +0,65 sur les questions 1-50, +0,73 sur les questions 51-91.
- Les changements du 2 novembre (prompt système conditionnel, seuil de
  pertinence, code des exemples dans l'index) font progresser le 1.5B de +0,31
  [+0,08 ; +0,55] ; le 4B de +0,10 [−0,05 ; +0,24], non significatif, mais ses
  réponses ne sont plus coupées (0 contre 9 à 1024 tokens).

**Choix des modèles** (1er novembre, 3 graines, réglages communs, ancienne configuration) :

| Modèle | Score /5 | Écart au 1.5B (IC95) | Licence |
|--------|----------|----------------------|---------|
| Qwen3-4B-Instruct-2507 | 3,99 | +0,99 [+0,83 ; +1,16] | Apache 2.0 |
| Qwen2.5-Coder-3B | 3,57 | +0,52 [+0,39 ; +0,67] ¹ | qwen-research |
| Qwen2.5-Coder-1.5B | 3,00 | — | Apache 2.0 |
| LoRA correctif du 1.5B | 2,63 | −0,45 [−0,72 ; −0,16] ¹ ² | — |

¹ Mesuré face au 1.5B sous llama.cpp b4823 (version antérieure) ; ² graine 42 seule.

- Le retrieval hybride n'améliore pas le score de façon mesurable face au
  retrieval dense de janvier (+0,09, IC95 [−0,14 ; +0,33]) mais cite moins de
  sources hors sujet (26 au lieu de 42).
- Le serveur persistant fait gagner 1,7 s (1.5B) à 8 s (4B) avant le premier
  mot, par rapport à un serveur lancé à chaque requête.

Rapports complets dans `reports/` ; copies renotées dans `reports/rescored/`.

## Décisions

- **LoRA abandonné.** Entraînements instables sur M2 (plantages Metal), régressions
  sur d'autres catégories, et le seul LoRA disponible fait −0,45 : changer de
  modèle de base rapporte bien plus.
- **3B écarté** : licence `qwen-research`, non commerciale.
- **4B par défaut, et pour la vidéo.** Il est le plus juste (+0,69 sur la
  configuration finale, +0,99 sur 3 graines), suit le format et la consigne de
  langue, et ses réponses ne sont plus coupées. Son GGUF vient de bartowski :
  Qwen n'en publie pas.
- **1.5B en mode rapide.** Environ 5 fois plus réactif sur M2 : 3,5 × au premier
  mot (3,2 s contre 11,2 s), 6,6 × sur la réponse complète (8 s contre 52 s),
  au prix de réponses moins justes. Il se sélectionne en une ligne (`paths.model`).
- **llama.cpp b12032** (requis pour Qwen3) : effet mesuré sur le 1.5B de −0,05
  (IC95 [−0,10 ; −0,01]), 17 réponses sur 91 modifiées à graine égale.

## Limites connues

- **Justesse** : score de 4,02/5 pour le 4B et 3,34/5 pour le 1.5B. Catégories
  les plus faibles : ownership 3,43, borrowing 3,58 et generics 3,62 pour le 4B ;
  smart pointers 2,47, async 2,76 et borrowing 2,76 pour le 1.5B.
- **Code** : 58 % des blocs compilent avec le 4B (54 % avec le 1.5B) ; 60 % des
  réponses contenant du code compilent entièrement (53 %).
- **Questions générales** : sans documentation pertinente, le 1.5B invente
  (« Rust développé par Microsoft en 2013 ») et applique la structure en 5
  sections là où une réponse simple est demandée ; le 4B suit la consigne.
- **Emojis** : malgré la consigne, le 4B place encore des symboles (⚠, ✅) dans
  13 réponses sur 91 ; le 1.5B, aucun.
- **Latence du 4B** : environ 11 s avant le premier mot et 50 s pour une réponse
  complète sur M2 16 Go. Elle dépend de la mémoire libre : quand le système
  utilise le swap, la recherche RAG passe de 0,6 s à 30 s et la génération
  ralentit de moitié. Fermer les autres applications avant une démonstration.
- **Évaluation** : notation automatique (mots-clés, compilation), sans relecture
  humaine ni juge ; elle ne mesure pas l'exactitude technique, et des erreurs de
  fond subsistent, y compris chez le 4B. La configuration finale n'est évaluée
  que sur une graine.
- **Conversation** : contexte de 8192 tokens (au-delà, erreur 413 explicite) ;
  historique limité à 6 messages, chacun tronqué à 666 caractères.
- **Plateforme** : testé uniquement sur Mac Apple Silicon (M2 16 Go) ; pas d'image Docker.

## Licence

Code sous licence MIT. Modèles Qwen3-4B-Instruct-2507 et
Qwen2.5-Coder-1.5B-Instruct sous licence Apache 2.0 (Alibaba Cloud).

Auteur : **Abdel TOUATI**
