# Model Card — RustSensei

## Informations generales

| Champ | Valeur |
|-------|--------|
| Nom | RustSensei |
| Version | 0.1.0 |
| Modele de base | Qwen2.5-Coder-1.5B-Instruct |
| Quantization | Q4_K_M |
| Taille | 940 MB (GGUF) |
| Langue | Francais |
| Licence | MIT |

## Description

RustSensei est un assistant pedagogique specialise dans l'enseignement du langage Rust en francais. Il fonctionne 100% en local sans connexion internet.

### Capacites

- Explication des concepts Rust (ownership, borrowing, lifetimes, traits, etc.)
- Correction de code avec explications detaillees
- Generation d'exercices guides
- Reponses structurees (TL;DR, Probleme, Solution, Explication, A retenir)

### Cas d'usage

- Apprentissage du Rust en francais
- Debug de code Rust avec explications pedagogiques
- Comprehension des erreurs du compilateur
- Preparation aux concepts avances (lifetimes, traits, generics)

## Specifications techniques

### Inference

| Parametre | Valeur |
|-----------|--------|
| Runtime | llama.cpp |
| Context | 4096 tokens |
| GPU | Metal/MPS (Apple Silicon) |
| Threads CPU | 8 |

### Parametres de generation

| Parametre | Valeur |
|-----------|--------|
| Temperature | 0.7 |
| Top-p | 0.9 |
| Top-k | 40 |
| Repeat penalty | 1.1 |

## Metriques

### Evaluation (20 prompts)

| Metrique | Valeur |
|----------|--------|
| Score global | 3.07/5 |
| Langue francaise | 95% |
| Blocs de code | 70% |
| Taux de compilation | 87% |

### Avec RAG

| Metrique | Baseline | RAG |
|----------|----------|-----|
| Score | 3.05/5 | 3.35/5 |
| Amelioration | - | +10% |

### Par categorie

| Categorie | Score |
|-----------|-------|
| enums | 4.24/5 |
| structs | 4.02/5 |
| borrowing | 3.39/5 |
| basics | 3.02/5 |
| ownership | 2.54/5 |
| lifetimes | 1.25/5 |

## Limitations

### Connues

1. **Lifetimes** - Score faible (1.25/5), difficulte avec les cas complexes
2. **Contexte limite** - 4096 tokens, pas adapte aux tres longs codes
3. **Pas de multi-fichiers** - Ne gere pas les projets Cargo complets
4. **Francais uniquement** - Reponses en francais, prompts en francais recommandes

### Biais potentiels

- Entraine principalement sur des exemples debutant/intermediaire
- Peut manquer de precision sur les cas avances (unsafe, async, macros)
- Dataset d'entrainement limite (49 exemples)

## Utilisation

### Installation rapide

```bash
git clone https://github.com/2501Pr0ject/RustSensei.git
cd RustSensei
make install-all
make chat
```

### Exemple de prompt

```
Pourquoi ce code ne compile pas ?

fn main() {
    let s = String::from("hello");
    let s2 = s;
    println!("{}", s);
}
```

### Format de reponse attendu

```
## TL;DR
La variable s a ete deplacee vers s2.

## Probleme
[Description du probleme]

## Solution
[Code corrige]

## Explication
[Details pedagogiques]

## A retenir
[Points cles]
```

## Entrainement

### Dataset

| Metrique | Valeur |
|----------|--------|
| Exemples | 49 |
| Categories | debug (39%), concepts (37%), exercises (24%) |
| Difficulte | debutant (47%), intermediaire (41%), avance (12%) |

### Fine-tuning LoRA

| Parametre | Valeur |
|-----------|--------|
| Methode | LoRA (mlx-lm) |
| Rank | 8 |
| Iterations | 50 (interrompu a 100) |
| Val loss | 1.572 -> 0.703 |

## Hardware recommande

| Composant | Minimum | Recommande |
|-----------|---------|------------|
| RAM | 8 GB | 16 GB |
| Stockage | 2 GB | 5 GB |
| GPU | - | Apple Silicon / CUDA |

## Citation

```
@software{rustsensei,
  title = {RustSensei},
  author = {Abdel TOUATI},
  year = {2026},
  url = {https://github.com/2501Pr0ject/RustSensei}
}
```

## Contact

- GitHub: https://github.com/2501Pr0ject/RustSensei
- Issues: https://github.com/2501Pr0ject/RustSensei/issues
