# Metriques d'entrainement — RustSensei

## Resume

| Metrique | Valeur |
|----------|--------|
| Modele de base | Qwen2.5-Coder-1.5B-Instruct |
| Quantization | Q4_K_M |
| Methode | LoRA (mlx-lm) |
| Taille dataset | 49 exemples |
| Hardware | MacBook M2 16GB |

---

## Dataset

### Distribution par categorie

| Categorie | Nombre | % |
|-----------|--------|---|
| debug | 19 | 39% |
| concepts | 18 | 37% |
| exercises | 12 | 24% |

### Distribution par difficulte

| Niveau | Nombre | % |
|--------|--------|---|
| debutant | 23 | 47% |
| intermediaire | 20 | 41% |
| avance | 6 | 12% |

### Topics couverts

ownership, borrowing, lifetimes, traits, generics, error_handling, pattern_matching, iterators, structs, enums, modules, closures, testing, unsafe, async

---

## Entrainement LoRA

### Configuration

```yaml
model: Qwen/Qwen2.5-Coder-1.5B-Instruct
lora_parameters:
  rank: 8
  dropout: 0.0
  scale: 20.0
num_layers: 16
batch_size: 1
learning_rate: 1.0e-5
max_seq_length: 2048
```

### Progression de l'entrainement

| Iteration | Train Loss | Val Loss | Statut |
|-----------|------------|----------|--------|
| 1 | - | 1.572 | Debut |
| 10 | 1.696 | - | |
| 20 | 1.502 | - | |
| 30 | 1.248 | - | |
| 40 | 0.947 | - | |
| 50 | 0.866 | 0.703 | Checkpoint sauvegarde |
| 60 | 0.701 | - | |
| 70 | 0.732 | - | |
| 80 | 0.757 | - | |
| 90 | 0.788 | - | |
| 100 | - | 0.606 | Crash Metal GPU |

### Statistiques d'entrainement

| Metrique | Valeur |
|----------|--------|
| Parametres entraines | 5.276M (0.342%) |
| Parametres totaux | 1543.714M |
| Memoire max | 5.725 GB |
| Tokens/sec | ~100 |
| Duree | ~10 min (interrompu) |

### Artefacts generes

| Fichier | Taille | Description |
|---------|--------|-------------|
| `models/lora_adapters/adapters.safetensors` | 21 MB | Poids LoRA |
| `models/merged/` | 3.0 GB | Modele fusionne (safetensors) |
| `models/rustsensei-1.5b-q4_k_m.gguf` | 940 MB | Modele final quantize |

---

## Resultats d'evaluation

### Avant vs Apres fine-tuning

| Metrique | Baseline | Fine-tune | Delta |
|----------|----------|-----------|-------|
| Score | 3.05/5 | 3.05/5 | 0% |
| Langue FR | 95% | 95% | 0% |
| Blocs de code | 70% | 70% | 0% |

### Avec verification de compilation (M5)

| Metrique | Valeur |
|----------|--------|
| Score | 3.07/5 |
| Langue FR | 95% |
| Blocs de code | 70% |
| Longueur reponse | 70% |
| **Taux de compilation** | **87%** |

### Details compilation

| Metrique | Valeur |
|----------|--------|
| Reponses avec code | 14/20 |
| Blocs de code totaux | 23 |
| Compiles avec succes | 20 |
| Echecs | 3 |

### Score par categorie

| Categorie | Score |
|-----------|-------|
| basics | 3.02/5 |
| borrowing | 3.39/5 |
| enums | 4.24/5 |
| lifetimes | 1.25/5 |
| ownership | 2.54/5 |
| structs | 4.02/5 |

---

## Comparaison RAG

| Metrique | Baseline | RAG | Delta |
|----------|----------|-----|-------|
| Score | 3.05/5 | 3.35/5 | +10% |
| Langue | 95% | 100% | +5% |
| Lifetimes | 1.33/5 | 2.89/5 | +117% |

---

## Conclusions

### Ce qui fonctionne

1. **RAG** - +10% d'amelioration avec le contexte de documentation
2. **Verification compilation** - 87% du code genere compile
3. **Langue francaise** - 95% des reponses en francais
4. **Pipeline mlx-lm** - Entrainement fonctionnel sur Apple Silicon

### Limitations

1. **Dataset trop petit** - 49 exemples insuffisants pour une amelioration mesurable
2. **Entrainement interrompu** - Crash Metal GPU a l'iteration 100
3. **Lifetimes** - Score le plus bas (1.25/5), necessite plus d'exemples

### Recommandations

1. Etendre le dataset a 200+ exemples
2. Ajouter plus d'exemples sur lifetimes/borrowing
3. Reprendre l'entrainement avec gradient checkpointing
4. Filtrer les donnees d'entrainement par compilation
