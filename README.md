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
                              Qwen2.5-Coder-1.5B-Instruct, Q4_K_M
CLI et évaluation ─────────► llama-completion (même modèle, mêmes réglages)
```

- **UI** : réponses en streaming, sources cliquables, saisie multi-ligne pour
  coller du code, bouton Stop, copie des blocs de code, conversation sur 3 échanges.
- **Sources RAG** : Rust Book, Reference, Rust by Example, Cookbook, Async Book,
  Rustonomicon, Edition Guide, Rustlings. Les exemples de code que mdBook inclut
  depuis d'autres fichiers (`{{#include}}`, `{{#rustdoc_include}}`) sont résolus
  à la construction de l'index, et l'italique autour des noms de fichiers est
  retiré. Si le meilleur extrait reste sous un cosinus de 0,42 (salutation,
  question hors Rust), aucune documentation n'est injectée.
- **Format des réponses** : cinq sections (TL;DR, Problème, Solution, Explication,
  À retenir) pour une question de code ou une erreur de compilation ; réponse
  simple et directe pour une salutation ou une question générale.
- **Cache** : une réponse n'est resservie que si le modèle, le prompt système,
  l'échantillonnage, l'index et les réglages du RAG sont identiques (empreinte
  dans la clé).
- **Configuration unique** (`configs/model_config.yaml`) : l'UI, le CLI et
  l'évaluation lisent le même échantillonnage, avec des réglages par modèle
  (`sampling_by_model`). Changer de modèle tient en une ligne (`paths.model`).

## Démarrage rapide

Prérequis : macOS Apple Silicon (16 Go recommandés), Python 3.11+,
[uv](https://github.com/astral-sh/uv), Node.js, Xcode Command Line Tools ;
`rustc` pour la vérification de compilation.

```bash
make install-all     # dépendances Python, compilation de llama.cpp, modèle (1 Go)
make build-index     # téléchargement de la documentation et index RAG
make chat-rag        # chat en terminal avec la documentation
make api             # API sur http://localhost:8000 (charge le modèle au démarrage)
make web             # interface sur http://localhost:5173 (installe le front au besoin)
make install-dev && make test   # tests (146)
```

## Méthode d'évaluation

- **91 questions** en français, 19 catégories, du débutant à l'avancé
  (`eval/prompts_fr.jsonl`). 27 recoupent les données d'entraînement LoRA ;
  les 64 autres forment le sous-ensemble **hors entraînement**.
- **3 graines** (42, 1, 2), RAG activé, mêmes réglages pour tous les modèles
  (température 0,7, top-k 40, top-p 0,9, min-p 0,05, 1024 tokens au plus).
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

> Chiffres mesurés avant les changements du 2 novembre (prompt système
> conditionnel, seuil de pertinence, index sans directives mdBook ni italiques) ;
> l'évaluation finale du 1.5B et du 4B sur la configuration actuelle les remplacera.

| Modèle | Score /5 | Écart au 1.5B (IC95) | Format 5 sections | Premier mot | Réponse complète | Licence |
|--------|----------|----------------------|-------------------|-------------|------------------|---------|
| **Qwen2.5-Coder-1.5B** (démo) | **3,00** | — | 13 % | 3,2 s | 7,9 s | Apache 2.0 |
| Qwen3-4B-Instruct-2507 | 3,99 | +0,99 [+0,83 ; +1,16] | 100 % | 11,2 s | 52,3 s | Apache 2.0 |
| Qwen2.5-Coder-3B | 3,57 | +0,52 [+0,39 ; +0,67] ¹ | 92 % | — | — | qwen-research |
| LoRA correctif du 1.5B | 2,63 | −0,45 [−0,72 ; −0,16] ¹ ² | 5 % | — | — | — |

¹ Mesuré face au 1.5B sous llama.cpp b4823 (version antérieure) ; ² graine 42 seule.
Latences mesurées dans l'UI (4 questions avec RAG, médianes, serveur persistant).

- Sur les 64 questions hors entraînement, le 4B fait +1,07 [+0,86 ; +1,27].
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
- **4B meilleur, mais pas pour la démo.** +1,0 point, format suivi à 100 %, mais
  environ 5 fois plus lent sur M2 : 3,5 × au premier mot (11,2 s contre 3,2 s),
  6,6 × sur la réponse complète (52 s contre 8 s, réponses aussi plus longues).
  **La démo reste sur le 1.5B pour la réactivité.** Le 4B se sélectionne en une
  ligne (`paths.model`) ; ses réglages (recommandés par Qwen, 1536 tokens) sont
  déjà dans `sampling_by_model`. Son GGUF vient de bartowski : Qwen n'en publie pas.
- **llama.cpp b12032** (requis pour Qwen3) : effet mesuré sur le 1.5B de −0,05
  (IC95 [−0,10 ; −0,01]), 17 réponses sur 91 modifiées à graine égale.

## Limites connues

- **Qualité du 1.5B** : 3,00/5 ; catégories faibles : borrowing 2,26,
  smart pointers 2,28, lifetimes 2,51, closures 2,56.
- **Format** : la structure en 5 sections (TL;DR, Problème, Solution, Explication,
  À retenir) n'est suivie que dans 13 % des réponses.
- **Code** : 50 % des blocs compilent ; 47 % des réponses contenant du code
  compilent entièrement.
- **Réponses coupées** : 13 sur 273 atteignent 1024 tokens, dont 9 bouclent
  sur elles-mêmes. Les coupures sont signalées dans l'UI.
- **Questions générales** : sans documentation pertinente, le 1.5B invente
  (« Rust développé par Microsoft en 2013 ») et applique souvent la structure en
  5 sections là où une réponse simple est demandée ; le 4B suit la consigne.
- **Latence** : le délai avant le premier mot vient surtout du traitement du
  prompt (environ 1 700 tokens avec la documentation ; la recherche prend 0,5 s).
- **Évaluation** : notation automatique (mots-clés, compilation), sans relecture
  humaine ni juge ; elle ne mesure pas l'exactitude technique, et des erreurs de
  fond subsistent, y compris chez le 4B.
- **Conversation** : contexte de 8192 tokens (au-delà, erreur 413 explicite) ;
  historique limité à 6 messages, chacun tronqué à 666 caractères.
- **Plateforme** : testé uniquement sur Mac Apple Silicon (M2 16 Go) ; pas d'image Docker.

## Licence

Code sous licence MIT. Modèle Qwen2.5-Coder-1.5B-Instruct sous licence Apache 2.0
(Alibaba Cloud), comme Qwen3-4B-Instruct-2507.

Auteur : **Abdel TOUATI**
