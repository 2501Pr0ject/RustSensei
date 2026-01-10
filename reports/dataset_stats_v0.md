# Dataset Stats v0 — RustSensei

**Date** : 2026-01-09
**Version** : v0 (M3)

## Statistiques globales

| Métrique | Valeur |
|----------|--------|
| Total exemples | 49 |
| Format | Chat JSONL |
| Langue | Français |

## Distribution par catégorie

| Catégorie | Count | % | Cible |
|-----------|-------|---|-------|
| debug | 19 | 39% | 40% |
| concepts | 18 | 37% | 40% |
| exercises | 12 | 24% | 20% |

## Distribution par difficulté

| Difficulté | Count | % |
|------------|-------|---|
| debutant | 23 | 47% |
| intermediaire | 20 | 41% |
| avance | 6 | 12% |

## Distribution par topic

| Topic | Count |
|-------|-------|
| ownership | 5 |
| error_handling | 5 |
| traits | 5 |
| generics | 4 |
| borrowing | 3 |
| lifetimes | 3 |
| pattern_matching | 3 |
| iterators | 3 |
| structs | 3 |
| enums | 3 |
| modules | 3 |
| closures | 3 |
| testing | 3 |
| unsafe | 2 |
| async | 1 |

## Format des réponses

Toutes les réponses suivent le format structuré :
- `## TL;DR` — résumé en une phrase
- `## Problème` — description du problème
- `## Solution` — code et explications
- `## Explication` — détails supplémentaires
- `## À retenir` — points clés

---

## 10 Exemples Golden

### 1. Debug — Ownership (débutant)

**User** :
```
Pourquoi ce code ne compile pas ?

fn main() {
    let s = String::from("hello");
    let s2 = s;
    println!("{}", s);
}
```

**Assistant** :
```
## TL;DR
La variable `s` a été *déplacée* (move) vers `s2`, donc `s` n'est plus utilisable.

## Problème
Quand tu écris `let s2 = s;`, la propriété (ownership) de la String est transférée
de `s` vers `s2`. Après ce transfert, `s` n'est plus valide et le compilateur
refuse de l'utiliser.

## Solution
Trois options selon ton besoin :

**1. Cloner la valeur** (crée une copie indépendante) :
let s2 = s.clone();
println!("{}", s);  // OK, s est toujours valide

**2. Utiliser une référence** (emprunter sans transférer) :
let s2 = &s;
println!("{}", s);  // OK

## Explication
En Rust, chaque valeur a **exactement un propriétaire**. L'assignation transfère
la propriété. C'est le système d'ownership qui évite les bugs mémoire.

## À retenir
- Une valeur = un propriétaire
- L'assignation transfère la propriété (move)
- Utilise `.clone()` pour copier, `&` pour emprunter
```

---

### 2. Concepts — Borrowing (débutant)

**User** :
```
C'est quoi le borrowing en Rust ? Explique simplement.
```

**Assistant** :
```
## TL;DR
Le borrowing (emprunt) permet de prêter une valeur temporairement sans transférer
la propriété.

## Problème
Comment passer une valeur à une fonction sans la perdre (move) ?

## Solution
Utiliser des références :

**Référence immuable** (`&T`) — lecture seule
let s = String::from("hello");
let r = &s;  // Emprunt immuable
println!("{}", r);  // OK: lecture

**Référence mutable** (`&mut T`) — lecture et écriture
let mut s = String::from("hello");
let r = &mut s;
r.push_str(" world");  // OK: modification

## Explication
Règles du borrow checker :
- Plusieurs références immuables OK
- Une seule référence mutable OK
- Les deux en même temps NON

## À retenir
- `&T` pour lire, `&mut T` pour modifier
- Plusieurs lecteurs OU un seul écrivain
- Le propriétaire garde le contrôle
```

---

### 3. Debug — Lifetimes (avancé)

**User** :
```
Comment corriger cette erreur de lifetime ?

fn longest(x: &str, y: &str) -> &str {
    if x.len() > y.len() { x } else { y }
}
```

**Assistant** :
```
## TL;DR
Ajoute un paramètre de lifetime `<'a>` pour lier les références d'entrée et de sortie.

## Problème
La fonction retourne une référence, mais Rust ne sait pas si elle vient de `x` ou `y`.

## Solution
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

## Explication
- `<'a>` déclare un paramètre de lifetime
- `&'a str` = "référence qui vit au moins aussi longtemps que 'a"
- Le retour a la même lifetime que les entrées

## À retenir
- Les lifetimes décrivent les relations entre références
- Elles ne changent pas la durée de vie réelle
- Le compilateur les infère souvent automatiquement
```

---

### 4. Concepts — Pattern Matching (débutant)

**User** :
```
Comment fonctionne le pattern matching avec `match` en Rust ?
```

**Assistant** :
```
## TL;DR
`match` compare une valeur contre plusieurs motifs et exécute le code du premier
qui correspond. Il doit être exhaustif.

## Problème
Les chaînes de `if/else` sont verbeuses et risquent d'oublier des cas.

## Solution
match nombre {
    1 => println!("Un"),
    2 => println!("Deux"),
    3 => println!("Trois"),
    _ => println!("Autre chose"),  // catch-all
}

Avec enums :
match msg {
    Message::Quit => println!("Quit"),
    Message::Write(text) => println!("{}", text),
    Message::Move { x, y } => println!("({}, {})", x, y),
}

## Explication
Patterns avancés :
- `1 | 2` pour OU
- `3..=5` pour ranges
- `n if n > 10` pour guards

## À retenir
- `match` doit couvrir tous les cas (exhaustif)
- `_` capture tout ce qui reste
- Préfère `match` aux chaînes `if/else` pour les enums
```

---

### 5. Exercises — Ownership (débutant)

**User** :
```
Donne-moi un exercice pour pratiquer l'ownership en Rust.
```

**Assistant** :
```
## TL;DR
Exercice pratique : compléter des fonctions en utilisant références et ownership.

## Problème
Tu dois manipuler une String sans perdre la propriété.

## Solution
**Exercice** : Complète les fonctions

fn main() {
    let nom = String::from("Alice");
    afficher_majuscules(/* ??? */);
    let nouveau_nom = ajouter_titre(/* ??? */);
    println!("Original: {}", nom);  // Doit marcher !
}

**Solution** :
fn afficher_majuscules(nom: &String) {
    println!("{}", nom.to_uppercase());
}

fn ajouter_titre(nom: &String) -> String {
    format!("Mme {}", nom)
}

## Explication
- `&nom` passe une référence (emprunt immuable)
- `nom` reste valide après l'appel
- `format!` crée une nouvelle String owned

## À retenir
- Référence `&T` pour lire sans consommer
- `format!` pour créer une nouvelle String
```

---

### 6. Debug — Traits (intermédiaire)

**User** :
```
Mon code ne compile pas, il dit que `Debug` n'est pas implémenté :

struct Point { x: f64, y: f64 }
fn main() {
    let p = Point { x: 1.0, y: 2.0 };
    println!("{:?}", p);
}
```

**Assistant** :
```
## TL;DR
Ajoute `#[derive(Debug)]` au-dessus de ta struct.

## Problème
`{:?}` utilise le trait `Debug`. Ta struct ne l'implémente pas par défaut.

## Solution
#[derive(Debug)]
struct Point {
    x: f64,
    y: f64,
}

fn main() {
    let p = Point { x: 1.0, y: 2.0 };
    println!("{:?}", p);   // Point { x: 1.0, y: 2.0 }
}

## Explication
`#[derive(...)]` génère automatiquement l'implémentation des traits standard.

Traits dérivables courants :
- `Debug` : affichage avec `{:?}`
- `Clone` : méthode `.clone()`
- `PartialEq` : comparaison avec `==`

## À retenir
- `#[derive(Debug)]` est quasi-systématique sur les structs
- Combine : `#[derive(Debug, Clone, PartialEq)]`
```

---

### 7. Concepts — Error Handling (débutant)

**User** :
```
Comment gérer les erreurs proprement en Rust ?
```

**Assistant** :
```
## TL;DR
Rust utilise `Result<T, E>` et `Option<T>` au lieu des exceptions.
L'opérateur `?` propage les erreurs élégamment.

## Problème
Les exceptions peuvent surgir n'importe où. Rust force la gestion explicite.

## Solution
**Result** pour les opérations qui peuvent échouer :
match File::open("config.txt") {
    Ok(f) => println!("Ouvert !"),
    Err(e) => println!("Erreur: {}", e),
}

**L'opérateur `?`** — propagation rapide :
fn read_config() -> Result<String, io::Error> {
    let content = fs::read_to_string("config.txt")?;
    Ok(content)
}

## Explication
Méthodes utiles :
- `r.unwrap()` : valeur ou panic
- `r.expect("msg")` : valeur ou panic avec message
- `r.unwrap_or(0)` : valeur ou défaut

## À retenir
- `?` dans les fonctions qui retournent Result
- Évite `unwrap()` en production
- Pas d'exceptions = pas de surprises
```

---

### 8. Debug — Generics (intermédiaire)

**User** :
```
J'ai cette erreur : "binary operation `>` cannot be applied to type `T`"

fn largest<T>(list: &[T]) -> &T {
    let mut largest = &list[0];
    for item in list {
        if item > largest { largest = item; }
    }
    largest
}
```

**Assistant** :
```
## TL;DR
Ajoute une contrainte `T: PartialOrd` pour indiquer que `T` supporte la comparaison.

## Problème
`T` est un type générique sans contrainte. Le compilateur ne sait pas si tous
les types `T` supportent `>`.

## Solution
fn largest<T: PartialOrd>(list: &[T]) -> &T {
    let mut largest = &list[0];
    for item in list {
        if item > largest { largest = item; }
    }
    largest
}

Syntaxe alternative avec `where` :
fn largest<T>(list: &[T]) -> &T
where T: PartialOrd { ... }

## Explication
- `T: PartialOrd` = "T doit implémenter PartialOrd"
- `PartialOrd` fournit `<`, `>`, `<=`, `>=`

## À retenir
- Generics sans contrainte = fonctionnalités minimales
- Trait bounds débloquent les opérations
- `where` pour lisibilité avec plusieurs contraintes
```

---

### 9. Concepts — Testing (débutant)

**User** :
```
Comment écrire des tests en Rust ?
```

**Assistant** :
```
## TL;DR
Utilise `#[test]` pour marquer une fonction de test et `assert_eq!` pour vérifier.

## Problème
Comment vérifier que ton code fonctionne correctement ?

## Solution
fn add(a: i32, b: i32) -> i32 { a + b }

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        assert_eq!(add(2, 2), 4);
    }

    #[test]
    #[should_panic]
    fn test_panic() {
        panic!("This should panic");
    }
}

Lancer : `cargo test`

## Explication
Macros d'assertion :
- `assert!(condition)` : vérifie true
- `assert_eq!(left, right)` : vérifie égalité
- `assert_ne!(left, right)` : vérifie différence

## À retenir
- `#[test]` + `assert_eq!` pour le cas de base
- `#[should_panic]` pour tester les panics
- `cargo test` pour lancer
```

---

### 10. Exercises — Iterators (intermédiaire)

**User** :
```
Un exercice sur les itérateurs en Rust.
```

**Assistant** :
```
## TL;DR
Exercice : implémenter des fonctions d'analyse de texte avec uniquement des itérateurs.

## Problème
Tu dois compter les mots, trouver le plus long, calculer les fréquences —
sans boucles `for` classiques.

## Solution
**Exercice** :
fn count_words(text: &str) -> usize { todo!() }
fn longest_word(text: &str) -> Option<&str> { todo!() }
fn word_frequency(text: &str) -> HashMap<String, usize> { todo!() }

**Solution** :
fn count_words(text: &str) -> usize {
    text.split_whitespace().count()
}

fn longest_word(text: &str) -> Option<&str> {
    text.split_whitespace()
        .max_by_key(|w| w.len())
}

fn word_frequency(text: &str) -> HashMap<String, usize> {
    text.split_whitespace()
        .map(|w| w.to_lowercase())
        .fold(HashMap::new(), |mut acc, word| {
            *acc.entry(word).or_insert(0) += 1;
            acc
        })
}

## Explication
- `split_whitespace()` : itère sur les mots
- `max_by_key()` : trouve le max selon un critère
- `fold()` : accumule dans un HashMap

## À retenir
- Chaîne d'itérateurs = pipeline de transformation
- `fold()` pour les accumulations complexes
- Plus lisible et sûr que les boucles avec indices
```

---

## Fichiers générés

- `data_samples/dataset_sample.jsonl` — 49 exemples (committé)
- `data/processed/dataset_v0.jsonl` — même contenu (gitignored, pour training)

## Validation

```bash
make validate-dataset
# ✓ Dataset valide
# - 0 erreurs
# - 0 warnings
```

## Prochaines étapes

1. Atteindre 100+ exemples pour M4 (fine-tuning)
2. Ajouter plus d'exemples `unsafe` et `async`
3. Augmentation de données avec variations
