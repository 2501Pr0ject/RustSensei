#!/usr/bin/env python3
"""
Construction du dataset d'entraînement pour RustSensei.

Génère un dataset au format chat JSONL à partir d'exemples curés.
"""

import json
from pathlib import Path

import yaml
from rich.console import Console

console = Console()

PROJECT_ROOT = Path(__file__).parent.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"
DATA_SAMPLES_DIR = PROJECT_ROOT / "data_samples"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def load_config():
    """Charge la configuration du dataset."""
    config_path = CONFIGS_DIR / "dataset_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# =============================================================================
# Exemples curés par catégorie
# =============================================================================

SEED_EXAMPLES = {
    "debug": [
        {
            "topic": "ownership",
            "difficulty": "debutant",
            "user": """Pourquoi ce code ne compile pas ?

```rust
fn main() {
    let s = String::from("hello");
    let s2 = s;
    println!("{}", s);
}
```""",
            "assistant": """## TL;DR
La variable `s` a été *déplacée* (move) vers `s2`, donc `s` n'est plus utilisable.

## Problème
Quand tu écris `let s2 = s;`, la propriété (ownership) de la String est transférée de `s` vers `s2`. Après ce transfert, `s` n'est plus valide et le compilateur refuse de l'utiliser.

**Erreur** :
```
error[E0382]: borrow of moved value: `s`
```

## Solution
Trois options selon ton besoin :

**1. Cloner la valeur** (crée une copie indépendante) :
```rust
let s2 = s.clone();
println!("{}", s);  // OK, s est toujours valide
```

**2. Utiliser une référence** (emprunter sans transférer) :
```rust
let s2 = &s;
println!("{}", s);  // OK
```

**3. Utiliser s2 au lieu de s** :
```rust
let s2 = s;
println!("{}", s2);  // OK, on utilise le nouveau propriétaire
```

## Explication
En Rust, chaque valeur a **exactement un propriétaire**. L'assignation `let s2 = s` ne copie pas la String — elle transfère la propriété. C'est le système d'ownership qui évite les bugs mémoire (double free, use after free).

Les types simples comme `i32`, `bool`, `char` implémentent le trait `Copy` et sont copiés automatiquement au lieu d'être déplacés.

## À retenir
- Une valeur = un propriétaire
- L'assignation transfère la propriété (move)
- Utilise `.clone()` pour copier, `&` pour emprunter""",
        },
        {
            "topic": "borrowing",
            "difficulty": "intermediaire",
            "user": """J'ai cette erreur : "cannot borrow `v` as mutable because it is also borrowed as immutable". Voici mon code :

```rust
fn main() {
    let mut v = vec![1, 2, 3];
    let first = &v[0];
    v.push(4);
    println!("first: {}", first);
}
```""",
            "assistant": """## TL;DR
Tu ne peux pas modifier un vecteur pendant qu'une référence vers un de ses éléments existe.

## Problème
Tu as une référence immuable `first` vers un élément du vecteur, et tu essaies ensuite de modifier le vecteur avec `push()`. C'est interdit car :
- `push()` peut réallouer le vecteur en mémoire
- Si ça arrive, `first` pointerait vers de la mémoire invalide

**Les règles d'emprunt** :
- Tu peux avoir plusieurs références immuables (`&T`) **OU** une seule référence mutable (`&mut T`)
- Jamais les deux en même temps

## Solution
Trois options selon ton besoin :

**1. Utiliser first avant la modification** :
```rust
let mut v = vec![1, 2, 3];
let first = &v[0];
println!("first: {}", first);  // Utilisation terminée
v.push(4);  // OK maintenant
```

**2. Copier la valeur** (si le type implémente Copy) :
```rust
let mut v = vec![1, 2, 3];
let first = v[0];  // Copie, pas une référence
v.push(4);
println!("first: {}", first);
```

**3. Récupérer l'élément après la modification** :
```rust
let mut v = vec![1, 2, 3];
v.push(4);
let first = &v[0];
println!("first: {}", first);
```

## Explication
Le borrow checker te protège contre les bugs mémoire. Quand tu fais `&v[0]`, tu empruntes une partie du vecteur. Pendant cet emprunt, Rust interdit toute modification qui pourrait invalider ta référence.

## À retenir
- Référence active = pas de modification
- Limite la portée des références
- Copie les valeurs simples si tu dois modifier ensuite""",
        },
        {
            "topic": "lifetimes",
            "difficulty": "avance",
            "user": """Comment corriger cette erreur de lifetime ?

```rust
fn longest(x: &str, y: &str) -> &str {
    if x.len() > y.len() {
        x
    } else {
        y
    }
}
```""",
            "assistant": """## TL;DR
Ajoute un paramètre de lifetime `<'a>` pour lier les références d'entrée et de sortie.

## Problème
La fonction retourne une référence, mais Rust ne sait pas si elle vient de `x` ou `y`. Il a besoin de cette info pour garantir que la référence retournée reste valide.

## Solution
Ajouter un paramètre de lifetime explicite :

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() {
        x
    } else {
        y
    }
}
```

## Explication
- `<'a>` déclare un paramètre de lifetime nommé `'a`
- `&'a str` signifie "une référence qui vit au moins aussi longtemps que `'a`"
- Le retour `-> &'a str` indique que la référence retournée a la même lifetime

En pratique, cela signifie que la référence retournée sera valide tant que les **deux** arguments le sont :

```rust
fn main() {
    let s1 = String::from("longue chaîne");
    let result;
    {
        let s2 = String::from("court");
        result = longest(&s1, &s2);
        println!("{}", result);  // OK ici
    }
    // println!("{}", result);  // ERREUR : s2 n'existe plus
}
```

## À retenir
- Les lifetimes décrivent les relations entre références
- Elles ne changent pas la durée de vie réelle
- Le compilateur les infère souvent automatiquement""",
        },
        {
            "topic": "error_handling",
            "difficulty": "intermediaire",
            "user": """Pourquoi `unwrap()` est déconseillé et comment le remplacer ?

```rust
let content = std::fs::read_to_string("config.txt").unwrap();
```""",
            "assistant": """## TL;DR
`unwrap()` fait paniquer le programme si l'opération échoue. Utilise `?` ou `expect()` à la place.

## Problème
`unwrap()` est risqué en production :
- Si le fichier n'existe pas → panic et crash
- Pas de message d'erreur clair pour l'utilisateur
- Impossible de récupérer gracieusement

## Solution
Plusieurs alternatives selon le contexte :

**1. `expect()` pour le debug** (meilleur message) :
```rust
let content = std::fs::read_to_string("config.txt")
    .expect("Impossible de lire config.txt");
```

**2. `match` pour gérer l'erreur** :
```rust
let content = match std::fs::read_to_string("config.txt") {
    Ok(c) => c,
    Err(e) => {
        eprintln!("Erreur: {}", e);
        return;
    }
};
```

**3. `?` pour propager l'erreur** (recommandé) :
```rust
fn load_config() -> Result<String, std::io::Error> {
    let content = std::fs::read_to_string("config.txt")?;
    Ok(content)
}
```

**4. `unwrap_or_default()` pour une valeur par défaut** :
```rust
let content = std::fs::read_to_string("config.txt")
    .unwrap_or_default();  // String vide si erreur
```

## Explication
`Result<T, E>` force la gestion explicite des erreurs. `unwrap()` court-circuite cette protection. L'opérateur `?` propage l'erreur de manière élégante tout en permettant au code appelant de décider quoi faire.

## À retenir
- `?` dans les fonctions qui retournent Result
- `expect("message")` pour les cas "impossibles"
- Jamais `unwrap()` sur des I/O en production""",
        },
        {
            "topic": "traits",
            "difficulty": "intermediaire",
            "user": """Mon code ne compile pas, il dit que `Debug` n'est pas implémenté :

```rust
struct Point {
    x: f64,
    y: f64,
}

fn main() {
    let p = Point { x: 1.0, y: 2.0 };
    println!("{:?}", p);
}
```""",
            "assistant": """## TL;DR
Ajoute `#[derive(Debug)]` au-dessus de ta struct pour activer l'affichage avec `{:?}`.

## Problème
`{:?}` utilise le trait `std::fmt::Debug` pour formater la valeur. Ta struct `Point` ne l'implémente pas par défaut — contrairement aux types primitifs.

## Solution
Utiliser `#[derive(Debug)]` :

```rust
#[derive(Debug)]
struct Point {
    x: f64,
    y: f64,
}

fn main() {
    let p = Point { x: 1.0, y: 2.0 };
    println!("{:?}", p);   // Point { x: 1.0, y: 2.0 }
    println!("{:#?}", p);  // Affichage formaté sur plusieurs lignes
}
```

Si tu veux personnaliser l'affichage :

```rust
use std::fmt;

impl fmt::Debug for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Point({}, {})", self.x, self.y)
    }
}
```

## Explication
`#[derive(...)]` génère automatiquement l'implémentation des traits standard. C'est de la métaprogrammation à la compilation — zéro coût runtime.

**Traits dérivables courants** :
- `Debug` : affichage avec `{:?}`
- `Clone` : méthode `.clone()`
- `PartialEq` : comparaison avec `==`
- `Default` : valeur par défaut

## À retenir
- `#[derive(Debug)]` est quasi-systématique sur les structs
- Combine plusieurs traits : `#[derive(Debug, Clone, PartialEq)]`
- Implémentation manuelle pour un format personnalisé""",
        },
    ],
    "concepts": [
        {
            "topic": "ownership",
            "difficulty": "debutant",
            "user": "Explique-moi le concept d'ownership en Rust comme si j'étais débutant.",
            "assistant": """## TL;DR
Chaque valeur en Rust a un seul propriétaire. Quand il sort du scope, la valeur est libérée automatiquement.

## Problème
Sans ownership, les langages ont soit un garbage collector (lent), soit des bugs mémoire (dangereux). Rust propose une troisième voie.

## Solution
Les 3 règles de l'ownership :

**1. Chaque valeur a exactement un propriétaire**
```rust
let s = String::from("hello");  // s est propriétaire de "hello"
```

**2. Quand le propriétaire sort du scope, la valeur est libérée**
```rust
{
    let s = String::from("hello");
}  // s sort du scope → mémoire libérée automatiquement
```

**3. L'assignation transfère la propriété (move)**
```rust
let s1 = String::from("hello");
let s2 = s1;  // s1 "donne" la propriété à s2
// s1 n'est plus utilisable !
```

## Explication
Imagine un livre : tu peux le donner à quelqu'un (move), le prêter temporairement (borrow avec `&`), mais il ne peut appartenir qu'à une personne à la fois.

Les types simples (nombres, bool) implémentent `Copy` et sont copiés au lieu d'être déplacés :
```rust
let x = 5;
let y = x;  // x est copié, pas déplacé
println!("{} {}", x, y);  // OK !
```

## À retenir
- Une valeur = un propriétaire
- Fin de scope = libération mémoire
- Move par défaut, `.clone()` pour copier
- Zéro coût runtime, tout vérifié à la compilation""",
        },
        {
            "topic": "pattern_matching",
            "difficulty": "debutant",
            "user": "Comment fonctionne le pattern matching avec `match` en Rust ?",
            "assistant": """## TL;DR
`match` compare une valeur contre plusieurs motifs et exécute le code du premier qui correspond. Il doit être exhaustif.

## Problème
Les chaînes de `if/else` sont verbeuses et risquent d'oublier des cas. Rust propose `match` pour un contrôle de flux plus sûr.

## Solution
Syntaxe de base :
```rust
let nombre = 3;

match nombre {
    1 => println!("Un"),
    2 => println!("Deux"),
    3 => println!("Trois"),
    _ => println!("Autre chose"),  // _ = catch-all
}
```

Avec des enums (cas le plus courant) :
```rust
enum Message {
    Quit,
    Write(String),
    Move { x: i32, y: i32 },
}

match msg {
    Message::Quit => println!("Quit"),
    Message::Write(text) => println!("Texte: {}", text),
    Message::Move { x, y } => println!("Move to ({}, {})", x, y),
}
```

Avec `Option<T>` :
```rust
match valeur {
    Some(n) => println!("Valeur: {}", n),
    None => println!("Pas de valeur"),
}
```

## Explication
Patterns avancés :
```rust
match x {
    1 | 2 => println!("1 ou 2"),      // OU
    3..=5 => println!("3 à 5"),        // Range inclusive
    n if n > 10 => println!("> 10"),   // Guard
    _ => println!("autre"),
}
```

Raccourci `if let` pour un seul cas :
```rust
if let Some(n) = opt {
    println!("Valeur: {}", n);
}
```

## À retenir
- `match` doit couvrir tous les cas (exhaustif)
- `_` capture tout ce qui reste
- Les patterns extraient les valeurs automatiquement
- Préfère `match` aux chaînes `if/else` pour les enums""",
        },
        {
            "topic": "traits",
            "difficulty": "intermediaire",
            "user": "C'est quoi un trait en Rust et comment ça se compare aux interfaces ?",
            "assistant": """## TL;DR
Un trait définit un comportement partagé (comme une interface), mais peut avoir des implémentations par défaut et s'ajouter à des types existants.

## Problème
Comment partager du comportement entre types différents sans héritage classique ?

## Solution
Définir un trait :
```rust
trait Saluer {
    fn dire_bonjour(&self) -> String;

    // Méthode avec implémentation par défaut
    fn dire_au_revoir(&self) -> String {
        String::from("Au revoir !")
    }
}
```

Implémenter pour un type :
```rust
struct Francais { nom: String }

impl Saluer for Francais {
    fn dire_bonjour(&self) -> String {
        format!("Bonjour, je suis {}", self.nom)
    }
}
```

Utiliser comme contrainte :
```rust
fn accueillir(personne: &impl Saluer) {
    println!("{}", personne.dire_bonjour());
}
```

## Explication
**Traits standard importants** :
- `Clone`, `Debug`, `PartialEq`, `Default` (dérivables)
- `Display` : affichage avec `{}`
- `Iterator` : pour les boucles `for`
- `From`/`Into` : conversions

**Différences avec les interfaces** :
- Implémentations par défaut ✅
- Ajout à types existants ✅
- Dispatch statique par défaut (meilleures perfs)

**Trait objects** pour le dispatch dynamique :
```rust
fn traiter(items: &[&dyn Saluer]) { ... }
```

## À retenir
- Traits = comportement partagé
- `impl Trait for Type` pour implémenter
- Préfère le dispatch statique pour les performances
- `dyn Trait` pour le polymorphisme runtime""",
        },
        {
            "topic": "iterators",
            "difficulty": "intermediaire",
            "user": "Comment fonctionnent les itérateurs en Rust ?",
            "assistant": """## TL;DR
Les itérateurs traitent des séquences élément par élément. Ils sont paresseux (lazy) et aussi performants que les boucles manuelles.

## Problème
Les boucles avec indices sont verbeuses et risquent des erreurs (off-by-one). Les itérateurs offrent une abstraction plus sûre.

## Solution
Créer un itérateur :
```rust
let v = vec![1, 2, 3];

v.iter()       // Itère sur &T (références)
v.iter_mut()   // Itère sur &mut T
v.into_iter()  // Consomme v, itère sur T
```

Chaîner des adaptateurs :
```rust
let result: Vec<_> = v.iter()
    .filter(|x| *x % 2 == 0)
    .map(|x| x * 10)
    .collect();
// [20, 40]
```

Consommateurs (produisent une valeur finale) :
```rust
v.iter().sum::<i32>();           // 15
v.iter().count();                // 5
v.iter().max();                  // Some(&5)
v.iter().find(|&&x| x > 3);      // Some(&4)
```

## Explication
Les adaptateurs sont **paresseux** — rien ne s'exécute tant qu'on n'appelle pas un consommateur :
```rust
// Rien ne se passe ici
let iter = v.iter().map(|x| x * 2);

// C'est seulement ici que le travail est fait
let result: Vec<_> = iter.collect();
```

Grâce aux optimisations du compilateur (zero-cost abstractions), les itérateurs sont aussi rapides que les boucles manuelles.

## À retenir
- `iter()` pour emprunter, `into_iter()` pour consommer
- Les adaptateurs (`map`, `filter`) sont lazy
- Toujours terminer par un consommateur (`collect`, `sum`, `for_each`)
- Plus idiomatique et sûr que les boucles avec indices""",
        },
    ],
    "exercises": [
        {
            "topic": "ownership",
            "difficulty": "debutant",
            "user": "Donne-moi un exercice pour pratiquer l'ownership en Rust.",
            "assistant": """## TL;DR
Exercice pratique : compléter des fonctions en utilisant références et ownership correctement.

## Problème
Tu dois manipuler une String sans perdre la propriété, puis créer une nouvelle valeur à partir d'elle.

## Solution
**Exercice : Gestionnaire de noms**

Complète les fonctions pour que le code compile :

```rust
fn main() {
    let nom = String::from("Alice");

    // 1. Affiche le nom en majuscules SANS perdre la propriété
    afficher_majuscules(/* ??? */);

    // 2. Crée un nouveau nom à partir de l'ancien
    let nouveau_nom = ajouter_titre(/* ??? */);

    // 3. Ces deux lignes doivent fonctionner
    println!("Original: {}", nom);
    println!("Nouveau: {}", nouveau_nom);
}

fn afficher_majuscules(/* paramètre ? */) { todo!() }
fn ajouter_titre(/* paramètre ? */) -> String { todo!() }
```

**Indices** :
- Pour lire sans prendre : utilise `&`
- `format!` crée une nouvelle String

**Solution** :
```rust
fn afficher_majuscules(nom: &String) {
    println!("{}", nom.to_uppercase());
}

fn ajouter_titre(nom: &String) -> String {
    format!("Mme {}", nom)
}
```

## Explication
- `&nom` passe une référence (emprunt immuable)
- `nom` reste valide après l'appel car on ne l'a pas consommé
- `format!` crée une nouvelle String owned

## À retenir
- Référence `&T` pour lire sans consommer
- `format!` pour créer une nouvelle String
- Bonus : préfère `&str` à `&String` pour plus de flexibilité""",
        },
        {
            "topic": "error_handling",
            "difficulty": "intermediaire",
            "user": "Un exercice sur la gestion d'erreurs avec Result, s'il te plaît.",
            "assistant": """## TL;DR
Exercice : implémenter un parseur de configuration avec gestion d'erreurs typée.

## Problème
Tu dois lire des valeurs depuis un HashMap et les convertir en types appropriés, en gérant les cas d'erreur (clé absente, parse impossible).

## Solution
**Exercice : Parseur de configuration**

```rust
use std::collections::HashMap;

#[derive(Debug)]
enum ConfigError {
    KeyNotFound(String),
    ParseError(String),
}

struct Config {
    data: HashMap<String, String>,
}

impl Config {
    fn get_string(&self, key: &str) -> Result<String, ConfigError> {
        todo!()
    }

    fn get_int(&self, key: &str) -> Result<i32, ConfigError> {
        todo!()
    }
}
```

**Indices** :
- `HashMap::get()` retourne `Option<&V>`
- `ok_or_else()` convertit `Option` en `Result`
- `?` propage les erreurs

**Solution** :
```rust
fn get_string(&self, key: &str) -> Result<String, ConfigError> {
    self.data
        .get(key)
        .cloned()
        .ok_or_else(|| ConfigError::KeyNotFound(key.to_string()))
}

fn get_int(&self, key: &str) -> Result<i32, ConfigError> {
    let value = self.get_string(key)?;
    value.parse::<i32>()
        .map_err(|_| ConfigError::ParseError(
            format!("'{}' n'est pas un entier", value)
        ))
}
```

## Explication
- `ok_or_else` : convertit `None` en `Err`
- `?` : propage l'erreur si `Err`, déballe si `Ok`
- `map_err` : transforme le type d'erreur
- `cloned()` : évite les problèmes de lifetime (&String → String)

## À retenir
- `Option` → `Result` avec `ok_or` / `ok_or_else`
- `?` pour la propagation élégante
- Types d'erreur personnalisés pour des messages clairs""",
        },
    ],
}


def build_message(example: dict, config: dict) -> dict:
    """Construit un exemple au format chat JSONL."""
    return {
        "messages": [
            {"role": "system", "content": config["format"]["system_prompt"].strip()},
            {"role": "user", "content": example["user"]},
            {"role": "assistant", "content": example["assistant"]},
        ],
        "metadata": {
            "category": example.get("category", "unknown"),
            "topic": example.get("topic", "unknown"),
            "difficulty": example.get("difficulty", "unknown"),
        },
    }


def generate_dataset(config: dict) -> list[dict]:
    """Génère le dataset à partir des exemples curés."""
    dataset = []

    # Exemples de base
    for category, examples in SEED_EXAMPLES.items():
        for example in examples:
            example["category"] = category
            message = build_message(example, config)
            dataset.append(message)

    # Exemples additionnels
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from data.seed_examples import ALL_ADDITIONAL_EXAMPLES

        for category, examples in ALL_ADDITIONAL_EXAMPLES.items():
            for example in examples:
                example["category"] = category
                message = build_message(example, config)
                dataset.append(message)
    except ImportError:
        console.print("[yellow]Exemples additionnels non trouvés[/yellow]")

    return dataset


def save_dataset(dataset: list[dict], output_path: Path):
    """Sauvegarde le dataset au format JSONL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def print_stats(dataset: list[dict]):
    """Affiche les statistiques du dataset."""
    from collections import Counter

    categories = Counter(item["metadata"]["category"] for item in dataset)
    difficulties = Counter(item["metadata"]["difficulty"] for item in dataset)
    topics = Counter(item["metadata"]["topic"] for item in dataset)

    console.print("\n[bold]Statistiques du dataset[/bold]")
    console.print(f"  Total: {len(dataset)} exemples\n")

    console.print("  [cyan]Par catégorie:[/cyan]")
    for cat, count in categories.most_common():
        pct = count / len(dataset) * 100
        console.print(f"    {cat}: {count} ({pct:.0f}%)")

    console.print("\n  [cyan]Par difficulté:[/cyan]")
    for diff, count in difficulties.most_common():
        console.print(f"    {diff}: {count}")

    console.print("\n  [cyan]Par topic:[/cyan]")
    for topic, count in topics.most_common():
        console.print(f"    {topic}: {count}")


def main():
    """Point d'entrée."""
    console.print("[bold blue]Construction du dataset RustSensei[/bold blue]\n")

    config = load_config()

    # Générer le dataset
    console.print("Génération des exemples...")
    dataset = generate_dataset(config)

    print_stats(dataset)

    # Sauvegarder le sample (committé)
    sample_path = DATA_SAMPLES_DIR / config["paths"]["sample_file"]
    save_dataset(dataset, sample_path)
    console.print(f"\n[green]Sample sauvegardé: {sample_path}[/green]")

    # Sauvegarder aussi dans data/processed/ (gitignored, pour training)
    processed_path = DATA_PROCESSED_DIR / "dataset_v0.jsonl"
    save_dataset(dataset, processed_path)
    console.print(f"[green]Dataset processed sauvegardé: {processed_path}[/green]")

    console.print(f"[dim]Total exemples: {len(dataset)}[/dim]")


if __name__ == "__main__":
    main()
