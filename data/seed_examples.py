"""
Exemples curés additionnels pour le dataset RustSensei.

Ces exemples sont importés par build_dataset.py pour générer le dataset d'entraînement.
"""

ADDITIONAL_DEBUG_EXAMPLES = [
    {
        "topic": "structs",
        "difficulty": "debutant",
        "user": """Mon code ne compile pas. Pourquoi ?

```rust
struct User {
    name: String,
    age: u32,
}

fn main() {
    let user = User {
        name: "Alice",
        age: 30,
    };
}
```""",
        "assistant": """## TL;DR
Tu passes une `&str` (chaîne littérale) alors que la struct attend une `String`. Utilise `String::from()`.

## Problème
**Erreur du compilateur** :
```
error[E0308]: mismatched types
expected `String`, found `&str`
```

Les chaînes littérales (`"Alice"`) sont de type `&str`, pas `String`.

## Solution
Convertir en String :
```rust
let user = User {
    name: String::from("Alice"),  // ou "Alice".to_string()
    age: 30,
};
```

Ou changer le type dans la struct (si tu n'as pas besoin de propriété) :
```rust
struct User<'a> {
    name: &'a str,  // Référence avec lifetime
    age: u32,
}
```

## Explication
- `String` : chaîne owned, allouée sur le heap, modifiable
- `&str` : référence vers une chaîne, pas de propriété

Une struct qui stocke des données devrait généralement utiliser `String` pour posséder ses données.

## À retenir
- Littéral `"hello"` = `&str`
- Struct avec données owned = `String`
- Conversion : `String::from()` ou `.to_string()`""",
    },
    {
        "topic": "enums",
        "difficulty": "debutant",
        "user": """Pourquoi j'ai "pattern `None` not covered" ?

```rust
fn main() {
    let x: Option<i32> = Some(5);

    match x {
        Some(n) => println!("Valeur: {}", n),
    }
}
```""",
        "assistant": """## TL;DR
Le `match` doit couvrir tous les cas. `Option` a deux variants (`Some` et `None`), tu n'en gères qu'un.

## Problème
`Option<T>` a deux variants : `Some(T)` et `None`. Le compilateur exige que tous soient gérés.

## Solution
**Option 1** : Gérer `None` explicitement
```rust
match x {
    Some(n) => println!("Valeur: {}", n),
    None => println!("Pas de valeur"),
}
```

**Option 2** : Utiliser `_` pour ignorer
```rust
match x {
    Some(n) => println!("Valeur: {}", n),
    _ => {}
}
```

**Option 3** : Utiliser `if let` pour un seul cas
```rust
if let Some(n) = x {
    println!("Valeur: {}", n);
}
```

## Explication
Le compilateur vérifie que tu n'oublies aucun cas. C'est une protection contre les bugs — imagine oublier de gérer une erreur en production !

## À retenir
- `match` doit être exhaustif
- `_` capture tous les cas restants
- `if let` pour ne gérer qu'un seul cas""",
    },
    {
        "topic": "modules",
        "difficulty": "intermediaire",
        "user": """J'ai "function `helper` is private". Comment rendre ma fonction publique ?

```rust
// src/utils.rs
fn helper() -> i32 {
    42
}

// src/main.rs
mod utils;

fn main() {
    let x = utils::helper();  // Erreur!
}
```""",
        "assistant": """## TL;DR
Ajoute `pub` devant la fonction. Par défaut, tout est privé en Rust.

## Problème
Sans `pub`, les fonctions ne sont accessibles que dans leur module.

## Solution
```rust
// src/utils.rs
pub fn helper() -> i32 {  // Ajout de `pub`
    42
}
```

**Niveaux de visibilité** :
- `pub` : visible partout
- `pub(crate)` : visible dans le crate seulement
- `pub(super)` : visible dans le module parent
- *(rien)* : privé au module

**Pour les structs** (attention aux champs) :
```rust
pub struct User {
    pub name: String,  // Champ public
    age: u32,          // Champ privé !
}
```

## Explication
Même si la struct est `pub`, les champs restent privés par défaut. Pattern courant : constructeur public avec champs privés.

```rust
impl User {
    pub fn new(name: String, age: u32) -> Self {
        User { name, age }
    }
}
```

## À retenir
- Par défaut = privé
- `pub` à chaque niveau (module, fonction, struct, champs)
- `pub(crate)` pour limiter à ton crate""",
    },
    {
        "topic": "generics",
        "difficulty": "intermediaire",
        "user": """J'ai cette erreur : "binary operation `>` cannot be applied to type `T`"

```rust
fn largest<T>(list: &[T]) -> &T {
    let mut largest = &list[0];
    for item in list {
        if item > largest {
            largest = item;
        }
    }
    largest
}
```""",
        "assistant": """## TL;DR
Ajoute une contrainte `T: PartialOrd` pour indiquer que `T` supporte la comparaison.

## Problème
`T` est un type générique sans contrainte. Le compilateur ne sait pas si tous les types `T` possibles supportent `>`.

## Solution
Ajouter un trait bound :
```rust
fn largest<T: PartialOrd>(list: &[T]) -> &T {
    let mut largest = &list[0];
    for item in list {
        if item > largest {
            largest = item;
        }
    }
    largest
}
```

Syntaxe alternative avec `where` :
```rust
fn largest<T>(list: &[T]) -> &T
where
    T: PartialOrd,
{
    // ...
}
```

## Explication
- `T: PartialOrd` = "T doit implémenter PartialOrd"
- `PartialOrd` fournit `<`, `>`, `<=`, `>=`

Contraintes multiples :
```rust
fn process<T: Clone + Debug>(item: T) { ... }
```

## À retenir
- Generics sans contrainte = fonctionnalités minimales
- Trait bounds débloquent les opérations
- `where` pour lisibilité avec plusieurs contraintes""",
    },
    {
        "topic": "closures",
        "difficulty": "intermediaire",
        "user": """Pourquoi ce code ne compile pas ? J'essaie de capturer une variable dans une closure.

```rust
fn main() {
    let x = vec![1, 2, 3];

    let print_x = || {
        println!("{:?}", x);
    };

    let consume_x = || {
        drop(x);
    };

    print_x();
    consume_x();
}
```""",
        "assistant": """## TL;DR
Deux closures capturent `x` de manières incompatibles : une veut lire, l'autre veut consommer.

## Problème
- `print_x` capture `x` par référence (`&x`)
- `consume_x` capture `x` par valeur (move pour `drop`)
- Une valeur ne peut pas être empruntée ET déplacée

## Solution
**Option 1** : Cloner pour avoir deux valeurs
```rust
let x_clone = x.clone();
let print_x = move || println!("{:?}", x_clone);
let consume_x = move || drop(x);
```

**Option 2** : Réorganiser l'ordre
```rust
let print_x = || println!("{:?}", x);
print_x();  // Utiliser d'abord
drop(x);    // Puis consommer
```

## Explication
Les 3 modes de capture des closures :
- `Fn` : emprunte par référence immuable (`&T`)
- `FnMut` : emprunte par référence mutable (`&mut T`)
- `FnOnce` : prend ownership (move)

Rust infère le mode le plus permissif possible. `move` force la prise de propriété.

## À retenir
- Closures capturent automatiquement l'environnement
- `move` force la prise de propriété
- Clone si tu dois utiliser la valeur plusieurs fois""",
    },
    {
        "topic": "async",
        "difficulty": "avance",
        "user": """J'ai "future cannot be sent between threads safely". Voici mon code :

```rust
use std::rc::Rc;

async fn process(data: Rc<String>) {
    println!("{}", data);
}

#[tokio::main]
async fn main() {
    let data = Rc::new(String::from("hello"));
    tokio::spawn(process(data));
}
```""",
        "assistant": """## TL;DR
`Rc` n'est pas thread-safe. Utilise `Arc` (Atomic Reference Counted) pour le code async.

## Problème
`tokio::spawn` peut exécuter la tâche sur n'importe quel thread, mais `Rc` utilise un compteur non-atomique → data race potentielle.

## Solution
Remplacer `Rc` par `Arc` :
```rust
use std::sync::Arc;

async fn process(data: Arc<String>) {
    println!("{}", data);
}

#[tokio::main]
async fn main() {
    let data = Arc::new(String::from("hello"));
    tokio::spawn(process(data));
}
```

Avec mutation, ajouter un `Mutex` :
```rust
use std::sync::{Arc, Mutex};
let data = Arc::new(Mutex::new(String::from("hello")));
```

## Explication
| Type | Thread-safe | Performance |
|------|-------------|-------------|
| `Rc` | ❌ Non | Plus rapide |
| `Arc` | ✅ Oui | Légèrement plus lent |

Les futures dans `tokio::spawn` doivent implémenter `Send`.

## À retenir
- Un seul thread → `Rc`
- Multi-thread / async → `Arc`
- Mutation partagée → `Arc<Mutex<T>>`""",
    },
]

ADDITIONAL_CONCEPTS_EXAMPLES = [
    {
        "topic": "borrowing",
        "difficulty": "debutant",
        "user": "C'est quoi le borrowing en Rust ? Explique simplement.",
        "assistant": """## TL;DR
Le borrowing (emprunt) permet de prêter une valeur temporairement sans transférer la propriété.

## Problème
Comment passer une valeur à une fonction sans la perdre (move) ?

## Solution
Utiliser des références :

**Référence immuable** (`&T`) — lecture seule
```rust
let s = String::from("hello");
let r = &s;  // Emprunt immuable
println!("{}", r);  // OK: lecture
println!("{}", s);  // OK: s toujours valide
```

**Référence mutable** (`&mut T`) — lecture et écriture
```rust
let mut s = String::from("hello");
let r = &mut s;
r.push_str(" world");  // OK: modification
```

## Explication
Règles du borrow checker :
- Plusieurs références immuables ✅
- Une seule référence mutable ✅
- Les deux en même temps ❌

```rust
let mut s = String::from("hello");
let r1 = &s;     // OK
let r2 = &s;     // OK
// let r3 = &mut s; // ERREUR pendant que r1/r2 existent

println!("{} {}", r1, r2);  // r1, r2 plus utilisés après
let r3 = &mut s;  // OK maintenant
```

Cela évite les data races à la compilation, sans coût runtime.

## À retenir
- `&T` pour lire, `&mut T` pour modifier
- Plusieurs lecteurs OU un seul écrivain
- Le propriétaire garde le contrôle""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "intermediaire",
        "user": "Les lifetimes en Rust, ça sert à quoi concrètement ?",
        "assistant": """## TL;DR
Les lifetimes garantissent que les références restent valides pendant toute leur utilisation.

## Problème
Sans vérification, on pourrait avoir des "dangling references" :
```rust
let r;
{
    let x = 5;
    r = &x;      // r pointe vers x
}                // x détruit !
println!("{}", r);  // ERREUR: r invalide
```

## Solution
Rust vérifie automatiquement que `r` ne vit pas plus longtemps que `x`.

Quand tu dois écrire les lifetimes :

**Fonctions retournant des références** :
```rust
fn first_word<'a>(s: &'a str) -> &'a str {
    &s[..s.find(' ').unwrap_or(s.len())]
}
```

**Structs contenant des références** :
```rust
struct Excerpt<'a> {
    text: &'a str,
}
```

## Explication
- `'a` est un paramètre de lifetime (comme `T` pour les generics)
- `&'a str` = "référence qui vit au moins aussi longtemps que 'a"

**Lifetime elision** : Rust infère souvent automatiquement :
```rust
fn first(s: &str) -> &str { ... }
// Équivalent à :
fn first<'a>(s: &'a str) -> &'a str { ... }
```

## À retenir
- Les lifetimes décrivent, ne modifient pas les durées de vie
- Souvent inférées automatiquement
- Nécessaires pour structs avec références""",
    },
    {
        "topic": "error_handling",
        "difficulty": "debutant",
        "user": "Comment gérer les erreurs proprement en Rust ?",
        "assistant": """## TL;DR
Rust utilise `Result<T, E>` et `Option<T>` au lieu des exceptions. L'opérateur `?` propage les erreurs élégamment.

## Problème
Les exceptions peuvent surgir n'importe où et sont faciles à oublier. Rust force la gestion explicite.

## Solution
**Result** pour les opérations qui peuvent échouer :
```rust
let file = File::open("config.txt");
match file {
    Ok(f) => println!("Ouvert !"),
    Err(e) => println!("Erreur: {}", e),
}
```

**L'opérateur `?`** — propagation rapide :
```rust
fn read_config() -> Result<String, std::io::Error> {
    let content = std::fs::read_to_string("config.txt")?;
    Ok(content)
}
```

**Option** pour les valeurs optionnelles :
```rust
let first: Option<&i32> = v.first();
match first {
    Some(n) => println!("Premier: {}", n),
    None => println!("Vide"),
}
```

## Explication
Méthodes utiles :
```rust
r.unwrap();         // valeur ou panic
r.expect("msg");    // valeur ou panic avec message
r.unwrap_or(0);     // valeur ou défaut
r.map(|x| x * 2);   // transformer la valeur
```

## À retenir
- `?` dans les fonctions qui retournent Result
- `expect()` pour les cas "impossibles"
- Évite `unwrap()` en production
- Pas d'exceptions = pas de surprises""",
    },
    {
        "topic": "structs",
        "difficulty": "debutant",
        "user": "Comment créer et utiliser des structs en Rust ?",
        "assistant": """## TL;DR
Les structs regroupent des données liées. `impl` ajoute des méthodes.

## Problème
Comment créer des types personnalisés avec plusieurs champs ?

## Solution
**Définir et instancier** :
```rust
struct User {
    username: String,
    email: String,
    active: bool,
}

let user = User {
    username: String::from("alice"),
    email: String::from("alice@ex.com"),
    active: true,
};
```

**Raccourcis pratiques** :
```rust
// Field init shorthand
fn create_user(email: String, username: String) -> User {
    User { email, username, active: true }
}

// Struct update syntax
let user2 = User {
    email: String::from("bob@ex.com"),
    ..user  // Autres champs de user
};
```

**Ajouter des méthodes** :
```rust
impl User {
    fn new(username: String, email: String) -> Self {
        User { username, email, active: true }
    }

    fn is_active(&self) -> bool {
        self.active
    }
}
```

## Explication
Variantes de structs :
- **Tuple struct** : `struct Point(f64, f64);`
- **Unit struct** : `struct Marker;`

Accès aux champs : `user.username`, `point.0`

## À retenir
- `struct` pour les types personnalisés
- `impl` pour les méthodes
- `Self` = le type en cours
- `&self` pour les méthodes qui lisent""",
    },
    {
        "topic": "enums",
        "difficulty": "debutant",
        "user": "Explique les enums en Rust avec des exemples.",
        "assistant": """## TL;DR
Les enums Rust peuvent contenir des données différentes par variant. C'est bien plus puissant que dans d'autres langages.

## Problème
Comment représenter une valeur qui peut être de plusieurs types différents ?

## Solution
**Enum simple** :
```rust
enum Direction { Nord, Sud, Est, Ouest }
let dir = Direction::Nord;
```

**Enum avec données** :
```rust
enum Message {
    Quit,                       // Pas de données
    Move { x: i32, y: i32 },    // Struct anonyme
    Write(String),              // Tuple
}
```

**Pattern matching** :
```rust
match msg {
    Message::Quit => println!("Quit"),
    Message::Move { x, y } => println!("({}, {})", x, y),
    Message::Write(text) => println!("{}", text),
}
```

## Explication
Enums standard importants :

**Option<T>** — valeur optionnelle :
```rust
let x: Option<i32> = Some(5);
if let Some(n) = x { println!("{}", n); }
```

**Result<T, E>** — succès ou erreur :
```rust
let r: Result<i32, &str> = Ok(42);
```

Méthodes sur enum avec `impl` :
```rust
impl Coin {
    fn value(&self) -> u32 {
        match self { Coin::Penny => 1, ... }
    }
}
```

## À retenir
- Enums = "types somme" (un seul variant à la fois)
- Chaque variant peut avoir des données différentes
- `match` pour traiter tous les cas
- `Option` et `Result` sont des enums""",
    },
    {
        "topic": "modules",
        "difficulty": "debutant",
        "user": "Comment organiser son code avec les modules en Rust ?",
        "assistant": """## TL;DR
Les modules organisent le code en namespaces. `mod` déclare, `use` importe, `pub` expose.

## Problème
Comment structurer un projet Rust avec plusieurs fichiers ?

## Solution
**Module inline** :
```rust
mod math {
    pub fn add(a: i32, b: i32) -> i32 { a + b }
    fn private_helper() { }  // Privé !
}

fn main() {
    let sum = math::add(2, 3);
}
```

**Module dans un fichier séparé** :
```
src/
├── main.rs
└── math.rs
```

```rust
// src/math.rs
pub fn add(a: i32, b: i32) -> i32 { a + b }

// src/main.rs
mod math;
fn main() { math::add(2, 3); }
```

**use** pour simplifier :
```rust
use std::collections::HashMap;
use math::add;
```

## Explication
Structure avec sous-modules :
```
src/math/
├── mod.rs
├── basic.rs
└── advanced.rs
```

Niveaux de visibilité :
- `pub` : visible partout
- `pub(crate)` : dans le crate
- `pub(super)` : dans le parent
- *(rien)* : privé

Re-export :
```rust
pub use internal::ImportantStruct;
```

## À retenir
- `mod nom;` charge `nom.rs` ou `nom/mod.rs`
- Par défaut tout est privé
- `use` crée des raccourcis
- `pub use` pour exposer une API propre""",
    },
]

ADDITIONAL_EXERCISES_EXAMPLES = [
    {
        "topic": "pattern_matching",
        "difficulty": "debutant",
        "user": "Un exercice sur le pattern matching avec match.",
        "assistant": """## TL;DR
Exercice : implémenter une calculatrice avec `match` et guards.

## Problème
Tu dois créer une fonction qui calcule le résultat d'une opération, en gérant la division par zéro.

## Solution
**Exercice : Calculatrice simple**

```rust
enum Operation {
    Add(f64, f64),
    Subtract(f64, f64),
    Multiply(f64, f64),
    Divide(f64, f64),
}

enum CalcResult {
    Success(f64),
    Error(String),
}

fn calculate(op: Operation) -> CalcResult {
    todo!()
}
```

**Indices** :
- Utilise `match` pour extraire les valeurs
- Guard `if b == 0.0` pour la division par zéro

**Solution** :
```rust
fn calculate(op: Operation) -> CalcResult {
    match op {
        Operation::Add(a, b) => CalcResult::Success(a + b),
        Operation::Subtract(a, b) => CalcResult::Success(a - b),
        Operation::Multiply(a, b) => CalcResult::Success(a * b),
        Operation::Divide(_, b) if b == 0.0 => {
            CalcResult::Error(String::from("Division par zéro"))
        }
        Operation::Divide(a, b) => CalcResult::Success(a / b),
    }
}
```

## Explication
- Chaque variant extrait ses données avec `(a, b)`
- Le guard `if condition` ajoute une condition au pattern
- L'ordre compte : le guard doit être avant le cas général

## À retenir
- `match` sur enum extrait les données
- Guards pour des conditions supplémentaires
- Ordre des branches important avec guards""",
    },
    {
        "topic": "iterators",
        "difficulty": "intermediaire",
        "user": "Un exercice sur les itérateurs en Rust.",
        "assistant": """## TL;DR
Exercice : implémenter des fonctions d'analyse de texte avec uniquement des itérateurs.

## Problème
Tu dois compter les mots, trouver le plus long, et calculer les fréquences — sans boucles `for` classiques.

## Solution
**Exercice : Analyse de texte**

```rust
fn count_words(text: &str) -> usize { todo!() }
fn longest_word(text: &str) -> Option<&str> { todo!() }
fn word_frequency(text: &str) -> HashMap<String, usize> { todo!() }
```

**Indices** :
- `split_whitespace()` pour itérer sur les mots
- `max_by_key()` pour trouver le max
- `fold()` pour accumuler dans un HashMap

**Solution** :
```rust
fn count_words(text: &str) -> usize {
    text.split_whitespace().count()
}

fn longest_word(text: &str) -> Option<&str> {
    text.split_whitespace()
        .map(|w| w.trim_matches(|c: char| !c.is_alphabetic()))
        .filter(|w| !w.is_empty())
        .max_by_key(|w| w.len())
}

fn word_frequency(text: &str) -> HashMap<String, usize> {
    text.split_whitespace()
        .map(|w| w.trim_matches(|c: char| !c.is_alphabetic()).to_lowercase())
        .fold(HashMap::new(), |mut acc, word| {
            *acc.entry(word).or_insert(0) += 1;
            acc
        })
}
```

## Explication
- `split_whitespace()` : itère sur les mots
- `trim_matches()` : enlève la ponctuation
- `max_by_key()` : trouve le max selon un critère
- `entry().or_insert()` : pattern idiomatique pour compteurs

## À retenir
- Chaîne d'itérateurs = pipeline de transformation
- `fold()` pour les accumulations complexes
- Plus lisible et sûr que les boucles avec indices""",
    },
    {
        "topic": "traits",
        "difficulty": "intermediaire",
        "user": "Donne-moi un exercice pour pratiquer les traits en Rust.",
        "assistant": """## TL;DR
Exercice : créer un système de formes géométriques avec un trait `Shape`.

## Problème
Tu dois définir un trait avec méthodes, l'implémenter pour plusieurs types, et utiliser le polymorphisme.

## Solution
**Exercice : Système de formes**

```rust
trait Shape {
    fn area(&self) -> f64;
    fn perimeter(&self) -> f64;
    fn name(&self) -> &str { "Shape" }  // défaut
}

struct Rectangle { width: f64, height: f64 }
struct Circle { radius: f64 }
struct Triangle { a: f64, b: f64, c: f64 }

fn print_info(shape: &impl Shape) { todo!() }
```

**Indices** :
- Aire du triangle (Héron) : `sqrt(s*(s-a)*(s-b)*(s-c))` où `s = (a+b+c)/2`
- `&impl Shape` pour le polymorphisme statique

**Solution** :
```rust
impl Shape for Rectangle {
    fn area(&self) -> f64 { self.width * self.height }
    fn perimeter(&self) -> f64 { 2.0 * (self.width + self.height) }
    fn name(&self) -> &str { "Rectangle" }
}

impl Shape for Circle {
    fn area(&self) -> f64 { PI * self.radius * self.radius }
    fn perimeter(&self) -> f64 { 2.0 * PI * self.radius }
    fn name(&self) -> &str { "Circle" }
}

fn print_info(shape: &impl Shape) {
    println!("{}: aire={:.2}", shape.name(), shape.area());
}
```

## Explication
- Méthode par défaut dans le trait (`name`)
- `impl Trait for Type` pour implémenter
- `&impl Shape` = generics statiques
- `Box<dyn Shape>` = trait objects (dynamique)

## À retenir
- Traits = comportement partagé
- Implémentation par défaut possible
- Choisir entre statique (`impl`) et dynamique (`dyn`)""",
    },
]

# ============================================================================
# Exemples supplémentaires pour atteindre 50
# ============================================================================

MORE_DEBUG_EXAMPLES = [
    {
        "topic": "testing",
        "difficulty": "debutant",
        "user": """Pourquoi mon test ne compile pas ?

```rust
fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[test]
fn test_add() {
    assert_eq!(add(2, 2), 4);
}
```

J'ai l'erreur "cannot find function `add`".""",
        "assistant": """## TL;DR
Le test est probablement dans un module séparé et n'a pas accès à la fonction. Ajoute `#[cfg(test)]` et `mod tests`.

## Problème
Les tests dans un fichier séparé ou mal structurés ne voient pas les fonctions du module principal.

## Solution
Structure standard pour les tests unitaires :
```rust
fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[cfg(test)]
mod tests {
    use super::*;  // Importe tout du module parent

    #[test]
    fn test_add() {
        assert_eq!(add(2, 2), 4);
    }
}
```

## Explication
- `#[cfg(test)]` : le module n'est compilé que pour les tests
- `mod tests` : crée un sous-module pour les tests
- `use super::*` : importe les fonctions du module parent

Lancer les tests : `cargo test`

## À retenir
- Tests dans un module `#[cfg(test)] mod tests`
- `use super::*` pour accéder aux fonctions
- `#[test]` sur chaque fonction de test""",
    },
    {
        "topic": "ownership",
        "difficulty": "intermediaire",
        "user": """Pourquoi je ne peux pas retourner une référence vers une variable locale ?

```rust
fn create_string() -> &str {
    let s = String::from("hello");
    &s
}
```""",
        "assistant": """## TL;DR
La variable locale `s` est détruite à la fin de la fonction. La référence retournée pointerait vers de la mémoire libérée.

## Problème
```
error[E0515]: cannot return reference to local variable `s`
```

`s` est créée dans la fonction et détruite quand la fonction termine. Une référence vers `s` serait invalide après le retour.

## Solution
Retourner la valeur owned au lieu d'une référence :
```rust
fn create_string() -> String {
    let s = String::from("hello");
    s  // Ownership transféré à l'appelant
}
```

Ou si tu veux une `&str`, utilise une constante statique :
```rust
fn get_greeting() -> &'static str {
    "hello"  // Littéral avec lifetime 'static
}
```

## Explication
En Rust, les références doivent toujours pointer vers des données valides. Une variable locale n'existe que pendant l'exécution de la fonction.

## À retenir
- Jamais de référence vers une variable locale
- Retourne la valeur owned ou utilise `'static`
- Le compilateur te protège des dangling references""",
    },
    {
        "topic": "unsafe",
        "difficulty": "avance",
        "user": """J'ai besoin d'utiliser `unsafe` pour du FFI. Quelles sont les règles ?

```rust
extern "C" {
    fn strlen(s: *const i8) -> usize;
}

fn main() {
    let s = "hello";
    let len = strlen(s.as_ptr() as *const i8);  // Erreur!
}
```""",
        "assistant": """## TL;DR
Les appels FFI doivent être dans un bloc `unsafe`. Tu dois garantir les invariants toi-même.

## Problème
Les fonctions `extern` sont intrinsèquement unsafe car Rust ne peut pas vérifier leur comportement.

## Solution
```rust
extern "C" {
    fn strlen(s: *const i8) -> usize;
}

fn main() {
    let s = std::ffi::CString::new("hello").unwrap();
    let len = unsafe { strlen(s.as_ptr()) };
    println!("Length: {}", len);
}
```

## Explication
**Pourquoi `unsafe`** :
- Rust ne peut pas vérifier le code C
- Tu dois garantir : pointeur valide, null-terminated, bon encoding

**CString** pour les chaînes C :
```rust
use std::ffi::CString;
let c_str = CString::new("hello").unwrap();  // Ajoute \0
let ptr = c_str.as_ptr();  // *const c_char
```

**Les 5 super-pouvoirs de `unsafe`** :
1. Déréférencer des raw pointers
2. Appeler des fonctions unsafe
3. Accéder/modifier des variables mutables statiques
4. Implémenter des traits unsafe
5. Accéder aux champs d'unions

## À retenir
- `unsafe` = "je garantis la sécurité moi-même"
- Utilise `CString` pour le FFI avec des chaînes
- Minimise le code unsafe, encapsule-le""",
    },
    {
        "topic": "generics",
        "difficulty": "debutant",
        "user": """Pourquoi ce code ne compile pas ?

```rust
fn print_twice<T>(value: T) {
    println!("{}", value);
    println!("{}", value);
}
```""",
        "assistant": """## TL;DR
`T` n'implémente pas forcément `Display` (nécessaire pour `{}`). Ajoute une contrainte.

## Problème
```
error[E0277]: `T` doesn't implement `std::fmt::Display`
```

Le compilateur ne sait pas si tous les types `T` peuvent être affichés avec `{}`.

## Solution
Ajouter une contrainte de trait :
```rust
use std::fmt::Display;

fn print_twice<T: Display>(value: T) {
    println!("{}", value);
    println!("{}", value);
}
```

Ou avec `Debug` si tu veux `{:?}` :
```rust
fn print_twice<T: std::fmt::Debug>(value: T) {
    println!("{:?}", value);
    println!("{:?}", value);
}
```

## Explication
- `Display` : formatage user-friendly (`{}`)
- `Debug` : formatage debug (`{:?}`)

Les types primitifs implémentent les deux. Tes structs personnalisées peuvent dériver `Debug` mais doivent implémenter `Display` manuellement.

## À retenir
- `{}` requiert `Display`
- `{:?}` requiert `Debug`
- Ajoute les trait bounds nécessaires""",
    },
    {
        "topic": "closures",
        "difficulty": "debutant",
        "user": """Quelle est la différence entre `|x| x + 1` et `fn add_one(x: i32) -> i32` ?""",
        "assistant": """## TL;DR
Les closures peuvent capturer l'environnement, les fonctions non. Les closures ont des types anonymes.

## Problème
Quand utiliser une closure vs une fonction ?

## Solution
**Closure** — peut capturer des variables :
```rust
let multiplier = 3;
let multiply = |x| x * multiplier;  // Capture `multiplier`
println!("{}", multiply(4));  // 12
```

**Fonction** — pas de capture :
```rust
fn add_one(x: i32) -> i32 {
    x + 1
    // Ne peut pas accéder à des variables externes
}
```

## Explication
| Aspect | Closure | Fonction |
|--------|---------|----------|
| Capture environnement | ✅ | ❌ |
| Type nommable | ❌ (anonyme) | ✅ |
| Peut être générique | ✅ (inféré) | ✅ (explicite) |
| Stockable dans struct | Via trait (`Fn`) | Direct |

Les closures implémentent des traits :
- `Fn` : emprunte immuablement
- `FnMut` : emprunte mutablement
- `FnOnce` : consomme

```rust
fn apply<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 {
    f(x)
}
```

## À retenir
- Closure pour capturer l'environnement
- Fonction pour du code réutilisable sans contexte
- Les deux peuvent être passées en paramètre via traits""",
    },
]

MORE_CONCEPTS_EXAMPLES = [
    {
        "topic": "testing",
        "difficulty": "debutant",
        "user": "Comment écrire des tests en Rust ?",
        "assistant": """## TL;DR
Utilise `#[test]` pour marquer une fonction de test et `assert!`/`assert_eq!` pour les vérifications.

## Problème
Comment vérifier que ton code fonctionne correctement ?

## Solution
**Test basique** :
```rust
fn add(a: i32, b: i32) -> i32 { a + b }

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        assert_eq!(add(2, 2), 4);
    }

    #[test]
    fn test_add_negative() {
        assert_eq!(add(-1, 1), 0);
    }
}
```

**Macros d'assertion** :
```rust
assert!(condition);              // Vérifie true
assert_eq!(left, right);         // Vérifie égalité
assert_ne!(left, right);         // Vérifie différence
assert!(result.is_ok());         // Pour Result
```

## Explication
Lancer les tests :
```bash
cargo test              # Tous les tests
cargo test test_add     # Tests contenant "test_add"
cargo test -- --nocapture  # Voir les println
```

**Test qui doit paniquer** :
```rust
#[test]
#[should_panic(expected = "division by zero")]
fn test_panic() {
    divide(1, 0);
}
```

**Test avec Result** :
```rust
#[test]
fn test_result() -> Result<(), String> {
    let result = parse_number("42")?;
    assert_eq!(result, 42);
    Ok(())
}
```

## À retenir
- `#[test]` + `assert_eq!` pour le cas de base
- `#[should_panic]` pour tester les panics
- `cargo test` pour lancer""",
    },
    {
        "topic": "unsafe",
        "difficulty": "avance",
        "user": "Quand et pourquoi utiliser `unsafe` en Rust ?",
        "assistant": """## TL;DR
`unsafe` désactive certaines vérifications du compilateur. Utilise-le uniquement quand nécessaire (FFI, optimisations critiques).

## Problème
Parfois Rust ne peut pas prouver qu'une opération est sûre, même si elle l'est.

## Solution
Les 5 opérations nécessitant `unsafe` :

**1. Déréférencer un raw pointer** :
```rust
let x = 42;
let ptr = &x as *const i32;
let value = unsafe { *ptr };
```

**2. Appeler une fonction unsafe** :
```rust
unsafe fn dangerous() { }
unsafe { dangerous(); }
```

**3. Accéder à une variable mutable statique** :
```rust
static mut COUNTER: i32 = 0;
unsafe { COUNTER += 1; }
```

**4. Implémenter un trait unsafe** :
```rust
unsafe trait MyTrait { }
unsafe impl MyTrait for MyType { }
```

**5. Accéder aux champs d'une union** :
```rust
union MyUnion { i: i32, f: f32 }
let u = MyUnion { i: 42 };
let i = unsafe { u.i };
```

## Explication
**Quand c'est justifié** :
- FFI (appel de code C/C++)
- Abstractions bas niveau (allocateurs)
- Optimisations critiques prouvées correctes

**Bonnes pratiques** :
- Encapsuler `unsafe` dans des fonctions safe
- Documenter les invariants
- Minimiser la surface unsafe

## À retenir
- `unsafe` ≠ "dangereux", = "je garantis la sécurité"
- 5 super-pouvoirs spécifiques
- Encapsule et minimise""",
    },
    {
        "topic": "generics",
        "difficulty": "intermediaire",
        "user": "Comment utiliser les génériques avec plusieurs types ?",
        "assistant": """## TL;DR
Déclare plusieurs paramètres de type `<T, U>` et ajoute des contraintes si nécessaire.

## Problème
Comment créer une fonction ou struct qui fonctionne avec plusieurs types différents ?

## Solution
**Fonction avec plusieurs types** :
```rust
fn make_pair<T, U>(first: T, second: U) -> (T, U) {
    (first, second)
}

let pair = make_pair("hello", 42);  // (&str, i32)
```

**Struct générique** :
```rust
struct Pair<T, U> {
    first: T,
    second: U,
}

impl<T, U> Pair<T, U> {
    fn new(first: T, second: U) -> Self {
        Pair { first, second }
    }
}
```

**Avec contraintes** :
```rust
fn compare<T: PartialOrd, U: Display>(a: T, b: T, label: U) {
    if a > b {
        println!("{}: a > b", label);
    }
}
```

## Explication
Syntaxe `where` pour plusieurs contraintes :
```rust
fn complex<T, U>(t: T, u: U)
where
    T: Clone + Debug,
    U: Display + Default,
{
    // ...
}
```

**Impl conditionnelle** :
```rust
impl<T: Display> Pair<T, T> {
    fn print_both(&self) {
        println!("{} {}", self.first, self.second);
    }
}
// Disponible seulement si T implémente Display
```

## À retenir
- `<T, U, V>` pour plusieurs types
- `where` pour les contraintes complexes
- Impl conditionnelle pour des méthodes spécifiques""",
    },
    {
        "topic": "closures",
        "difficulty": "intermediaire",
        "user": "Comment stocker une closure dans une struct ?",
        "assistant": """## TL;DR
Utilise un paramètre générique avec un trait bound (`Fn`, `FnMut`, ou `FnOnce`), ou `Box<dyn Fn()>` pour le polymorphisme.

## Problème
Les closures ont des types anonymes. Comment les stocker ?

## Solution
**Option 1 : Générique** (plus performant)
```rust
struct Handler<F: Fn(i32) -> i32> {
    callback: F,
}

impl<F: Fn(i32) -> i32> Handler<F> {
    fn new(callback: F) -> Self {
        Handler { callback }
    }

    fn call(&self, x: i32) -> i32 {
        (self.callback)(x)
    }
}
```

**Option 2 : Box<dyn>** (polymorphisme)
```rust
struct Handler {
    callback: Box<dyn Fn(i32) -> i32>,
}

impl Handler {
    fn new<F: Fn(i32) -> i32 + 'static>(callback: F) -> Self {
        Handler { callback: Box::new(callback) }
    }
}
```

## Explication
- **Générique** : monomorphisation, taille connue, pas d'indirection
- **Box<dyn>** : dispatch dynamique, peut stocker différentes closures

Les trois traits de closure :
- `Fn` : peut être appelée plusieurs fois, emprunte `&self`
- `FnMut` : peut modifier ses captures, emprunte `&mut self`
- `FnOnce` : consomme ses captures, prend `self`

## À retenir
- Générique pour performance
- `Box<dyn Fn>` pour flexibilité
- `'static` requis pour `Box<dyn>`""",
    },
    {
        "topic": "traits",
        "difficulty": "avance",
        "user": "C'est quoi un trait object (`dyn Trait`) et quand l'utiliser ?",
        "assistant": """## TL;DR
Un trait object (`dyn Trait`) permet le polymorphisme à l'exécution. Utilise-le quand tu as besoin de stocker des types différents dans une même collection.

## Problème
Comment avoir une liste d'objets de types différents qui implémentent le même trait ?

## Solution
```rust
trait Animal {
    fn speak(&self) -> String;
}

struct Dog;
struct Cat;

impl Animal for Dog {
    fn speak(&self) -> String { "Woof!".into() }
}
impl Animal for Cat {
    fn speak(&self) -> String { "Meow!".into() }
}

// Collection de types différents
let animals: Vec<Box<dyn Animal>> = vec![
    Box::new(Dog),
    Box::new(Cat),
];

for animal in &animals {
    println!("{}", animal.speak());
}
```

## Explication
**Dispatch statique vs dynamique** :
```rust
// Statique (monomorphisation) - plus rapide
fn greet_static(animal: &impl Animal) { ... }

// Dynamique (vtable) - plus flexible
fn greet_dynamic(animal: &dyn Animal) { ... }
```

**Object safety** — un trait est object-safe si :
- Pas de méthodes avec `Self` en retour
- Pas de paramètres génériques sur les méthodes

```rust
// NOT object-safe
trait Clone {
    fn clone(&self) -> Self;  // Self en retour
}
```

## À retenir
- `&dyn Trait` ou `Box<dyn Trait>`
- Coût runtime (vtable)
- Object safety requis""",
    },
]

MORE_EXERCISES_EXAMPLES = [
    {
        "topic": "testing",
        "difficulty": "debutant",
        "user": "Un exercice sur les tests unitaires en Rust.",
        "assistant": """## TL;DR
Exercice : écrire des tests pour une fonction de validation d'email.

## Problème
Tu dois tester une fonction qui vérifie si un email est valide.

## Solution
**Exercice : Tests de validation**

```rust
fn is_valid_email(email: &str) -> bool {
    email.contains('@') && email.contains('.')
}

#[cfg(test)]
mod tests {
    use super::*;

    // TODO: Écris les tests suivants
    // 1. test_valid_email - email valide
    // 2. test_missing_at - email sans @
    // 3. test_missing_dot - email sans .
    // 4. test_empty_email - chaîne vide
}
```

**Solution** :
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_email() {
        assert!(is_valid_email("user@example.com"));
    }

    #[test]
    fn test_missing_at() {
        assert!(!is_valid_email("userexample.com"));
    }

    #[test]
    fn test_missing_dot() {
        assert!(!is_valid_email("user@examplecom"));
    }

    #[test]
    fn test_empty_email() {
        assert!(!is_valid_email(""));
    }
}
```

## Explication
- `assert!(bool)` : vérifie que c'est vrai
- `assert!(!bool)` : vérifie que c'est faux
- Un test par cas = lisibilité

## À retenir
- Nommer les tests clairement
- Tester les cas limites
- `cargo test` pour lancer""",
    },
    {
        "topic": "generics",
        "difficulty": "intermediaire",
        "user": "Un exercice sur les génériques en Rust.",
        "assistant": """## TL;DR
Exercice : implémenter une stack générique.

## Problème
Crée une structure de pile (LIFO) qui fonctionne avec n'importe quel type.

## Solution
**Exercice : Stack générique**

```rust
struct Stack<T> {
    items: Vec<T>,
}

impl<T> Stack<T> {
    fn new() -> Self { todo!() }
    fn push(&mut self, item: T) { todo!() }
    fn pop(&mut self) -> Option<T> { todo!() }
    fn peek(&self) -> Option<&T> { todo!() }
    fn is_empty(&self) -> bool { todo!() }
}
```

**Tests à faire passer** :
```rust
let mut stack: Stack<i32> = Stack::new();
assert!(stack.is_empty());
stack.push(1);
stack.push(2);
assert_eq!(stack.peek(), Some(&2));
assert_eq!(stack.pop(), Some(2));
assert_eq!(stack.pop(), Some(1));
assert!(stack.is_empty());
```

**Solution** :
```rust
impl<T> Stack<T> {
    fn new() -> Self {
        Stack { items: Vec::new() }
    }

    fn push(&mut self, item: T) {
        self.items.push(item);
    }

    fn pop(&mut self) -> Option<T> {
        self.items.pop()
    }

    fn peek(&self) -> Option<&T> {
        self.items.last()
    }

    fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
}
```

## Explication
- `<T>` rend la struct générique
- `Vec<T>` gère le stockage
- `Option<T>` pour les cas où la pile est vide

## À retenir
- `impl<T> Struct<T>` pour les méthodes
- Délègue à `Vec` quand possible
- `Option` pour les accès potentiellement vides""",
    },
    {
        "topic": "borrowing",
        "difficulty": "intermediaire",
        "user": "Un exercice sur les références et le borrowing.",
        "assistant": """## TL;DR
Exercice : manipuler une liste sans en prendre la propriété.

## Problème
Tu dois écrire des fonctions qui travaillent sur des vecteurs sans les consommer.

## Solution
**Exercice : Statistiques sur liste**

```rust
// TODO: Implémente ces fonctions
fn sum(numbers: /* ??? */) -> i32 { todo!() }
fn average(numbers: /* ??? */) -> f64 { todo!() }
fn max(numbers: /* ??? */) -> Option<&i32> { todo!() }

fn main() {
    let nums = vec![1, 2, 3, 4, 5];

    // Toutes ces lignes doivent fonctionner
    println!("Sum: {}", sum(&nums));
    println!("Avg: {}", average(&nums));
    println!("Max: {:?}", max(&nums));

    // nums doit toujours être utilisable
    println!("Original: {:?}", nums);
}
```

**Solution** :
```rust
fn sum(numbers: &[i32]) -> i32 {
    numbers.iter().sum()
}

fn average(numbers: &[i32]) -> f64 {
    if numbers.is_empty() {
        return 0.0;
    }
    sum(numbers) as f64 / numbers.len() as f64
}

fn max(numbers: &[i32]) -> Option<&i32> {
    numbers.iter().max()
}
```

## Explication
- `&[i32]` (slice) accepte `&Vec<i32>` et `&[i32; N]`
- `iter()` emprunte les éléments
- `max()` retourne `Option<&i32>` (référence vers l'élément)

## À retenir
- `&[T]` plus flexible que `&Vec<T>`
- Les itérateurs empruntent par défaut
- Retourner des références quand possible""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "avance",
        "user": "Un exercice avancé sur les lifetimes.",
        "assistant": """## TL;DR
Exercice : créer un itérateur qui retourne des références.

## Problème
Tu dois implémenter une struct qui retourne des références vers ses éléments.

## Solution
**Exercice : Itérateur de mots**

```rust
struct Words<'a> {
    text: &'a str,
    position: usize,
}

impl<'a> Words<'a> {
    fn new(text: &'a str) -> Self { todo!() }
}

impl<'a> Iterator for Words<'a> {
    type Item = &'a str;

    fn next(&mut self) -> Option<Self::Item> {
        todo!()
    }
}

// Usage
let text = "Hello World Rust";
for word in Words::new(text) {
    println!("{}", word);
}
```

**Solution** :
```rust
impl<'a> Words<'a> {
    fn new(text: &'a str) -> Self {
        Words { text, position: 0 }
    }
}

impl<'a> Iterator for Words<'a> {
    type Item = &'a str;

    fn next(&mut self) -> Option<Self::Item> {
        // Skip whitespace
        let start = self.text[self.position..]
            .find(|c: char| !c.is_whitespace())?;
        let start = self.position + start;

        // Find end of word
        let end = self.text[start..]
            .find(char::is_whitespace)
            .map(|i| start + i)
            .unwrap_or(self.text.len());

        self.position = end;
        Some(&self.text[start..end])
    }
}
```

## Explication
- `'a` lie la lifetime de `Words` à celle de `text`
- `Item = &'a str` : l'itérateur produit des références
- La struct ne peut pas survivre au texte source

## À retenir
- Iterator avec références = lifetimes explicites
- `type Item` peut contenir des lifetimes
- La struct emprunte, ne possède pas""",
    },
]

# ============================================================================
# 10 exemples supplémentaires pour atteindre 50
# ============================================================================

FINAL_DEBUG_EXAMPLES = [
    {
        "topic": "traits",
        "difficulty": "debutant",
        "user": """Pourquoi j'ai "the trait `Copy` is not implemented" ?

```rust
#[derive(Clone)]
struct Data {
    value: String,
}

fn main() {
    let d = Data { value: "hello".into() };
    let d2 = d;
    println!("{}", d.value);  // Erreur!
}
```""",
        "assistant": """## TL;DR
`String` n'implémente pas `Copy`, donc ta struct ne peut pas non plus. L'assignation `let d2 = d` fait un move.

## Problème
Le trait `Copy` permet la copie implicite au lieu du move. Mais `Copy` requiert que tous les champs soient eux-mêmes `Copy`.

`String` n'est pas `Copy` car elle gère de la mémoire sur le heap.

## Solution
**Option 1** : Clone explicitement
```rust
let d2 = d.clone();
println!("{}", d.value);  // OK
```

**Option 2** : Utilise une référence
```rust
let d2 = &d;
println!("{}", d.value);  // OK
```

**Option 3** : Si tu veux vraiment `Copy`, utilise `&str`
```rust
#[derive(Clone, Copy)]
struct Data<'a> {
    value: &'a str,  // Référence, pas String
}
```

## Explication
Types `Copy` : `i32`, `f64`, `bool`, `char`, `&T`, tuples de types `Copy`.
Pas `Copy` : `String`, `Vec<T>`, `Box<T>` (tout ce qui possède du heap).

## À retenir
- `Copy` = copie bit-à-bit implicite
- Requiert que tous les champs soient `Copy`
- `String` → `Clone` explicite ou référence""",
    },
    {
        "topic": "error_handling",
        "difficulty": "debutant",
        "user": """Comment convertir une `Option` en `Result` ?

J'ai `None` mais je veux retourner une erreur avec un message.""",
        "assistant": """## TL;DR
Utilise `ok_or()` ou `ok_or_else()` pour transformer `None` en `Err`.

## Problème
`Option<T>` n'a pas de message d'erreur. Tu veux le convertir en `Result<T, E>`.

## Solution
```rust
fn find_user(id: u32) -> Option<User> { ... }

fn get_user(id: u32) -> Result<User, String> {
    find_user(id).ok_or(format!("User {} not found", id))
}
```

**`ok_or`** — erreur évaluée immédiatement :
```rust
let opt: Option<i32> = None;
let result = opt.ok_or("Missing value");  // Err("Missing value")
```

**`ok_or_else`** — erreur évaluée paresseusement :
```rust
let result = opt.ok_or_else(|| {
    expensive_error_computation()
});
```

## Explication
| Méthode | Input | Output |
|---------|-------|--------|
| `ok_or(err)` | `Some(v)` | `Ok(v)` |
| `ok_or(err)` | `None` | `Err(err)` |

Inverse : `Result` → `Option` avec `.ok()` ou `.err()`.

## À retenir
- `ok_or()` pour erreur simple
- `ok_or_else()` si l'erreur est coûteuse à créer
- Utile pour chaîner avec `?`""",
    },
    {
        "topic": "iterators",
        "difficulty": "debutant",
        "user": """C'est quoi la différence entre `iter()`, `iter_mut()` et `into_iter()` ?""",
        "assistant": """## TL;DR
- `iter()` : emprunte (`&T`)
- `iter_mut()` : emprunte mutablement (`&mut T`)
- `into_iter()` : consomme et prend ownership (`T`)

## Problème
Tu veux parcourir une collection mais tu ne sais pas quelle méthode utiliser.

## Solution
```rust
let mut v = vec![1, 2, 3];

// iter() - lecture seule, v reste utilisable
for x in v.iter() {
    println!("{}", x);  // x: &i32
}
println!("{:?}", v);  // OK

// iter_mut() - modification, v reste utilisable
for x in v.iter_mut() {
    *x *= 2;  // x: &mut i32
}
println!("{:?}", v);  // [2, 4, 6]

// into_iter() - consomme v
for x in v.into_iter() {
    println!("{}", x);  // x: i32
}
// println!("{:?}", v);  // ERREUR: v consumed
```

## Explication
| Méthode | Type de l'élément | Collection après |
|---------|-------------------|------------------|
| `iter()` | `&T` | Intacte |
| `iter_mut()` | `&mut T` | Intacte (modifiée) |
| `into_iter()` | `T` | Consommée |

La boucle `for` utilise `into_iter()` par défaut :
```rust
for x in v { }     // into_iter()
for x in &v { }    // iter()
for x in &mut v { } // iter_mut()
```

## À retenir
- Lecture : `iter()` ou `&collection`
- Modification : `iter_mut()` ou `&mut collection`
- Consommation : `into_iter()` ou `collection`""",
    },
]

FINAL_CONCEPTS_EXAMPLES = [
    {
        "topic": "ownership",
        "difficulty": "intermediaire",
        "user": "Explique les smart pointers `Box`, `Rc` et `Arc` en Rust.",
        "assistant": """## TL;DR
- `Box<T>` : allocation heap, un seul propriétaire
- `Rc<T>` : comptage de références, plusieurs propriétaires (single-thread)
- `Arc<T>` : comme `Rc` mais thread-safe

## Problème
Parfois tu as besoin de propriété partagée ou de données sur le heap.

## Solution
**Box** — allocation simple sur le heap :
```rust
let b = Box::new(5);
println!("{}", b);  // Déréférencement automatique
```

Utile pour : récursion (taille inconnue), gros objets.

**Rc** — plusieurs propriétaires (single-thread) :
```rust
use std::rc::Rc;

let a = Rc::new(String::from("hello"));
let b = Rc::clone(&a);  // Incrémente le compteur
let c = Rc::clone(&a);

println!("{}", Rc::strong_count(&a));  // 3
```

**Arc** — comme Rc mais thread-safe :
```rust
use std::sync::Arc;

let data = Arc::new(vec![1, 2, 3]);
let data_clone = Arc::clone(&data);

std::thread::spawn(move || {
    println!("{:?}", data_clone);
});
```

## Explication
| Type | Propriétaires | Thread-safe | Overhead |
|------|---------------|-------------|----------|
| `Box` | 1 | N/A | Minimal |
| `Rc` | N | ❌ | Compteur |
| `Arc` | N | ✅ | Atomique |

## À retenir
- `Box` pour le heap simple
- `Rc` pour partage single-thread
- `Arc` pour partage multi-thread""",
    },
    {
        "topic": "pattern_matching",
        "difficulty": "intermediaire",
        "user": "Comment utiliser `while let` et `let else` en Rust ?",
        "assistant": """## TL;DR
- `while let` : boucle tant qu'un pattern matche
- `let else` : unwrap avec early return si ça ne matche pas

## Problème
Tu veux des alternatives plus concises à `match` ou `if let` dans certains cas.

## Solution
**while let** — boucle sur un pattern :
```rust
let mut stack = vec![1, 2, 3];

while let Some(top) = stack.pop() {
    println!("{}", top);
}
// Affiche: 3, 2, 1
```

Équivalent à :
```rust
loop {
    match stack.pop() {
        Some(top) => println!("{}", top),
        None => break,
    }
}
```

**let else** — unwrap ou early return :
```rust
fn process(opt: Option<i32>) -> i32 {
    let Some(value) = opt else {
        return 0;  // Early return si None
    };
    value * 2
}
```

Équivalent à :
```rust
let value = match opt {
    Some(v) => v,
    None => return 0,
};
```

## Explication
Ces patterns rendent le code plus lisible :
- `while let` : évite les `loop { match { ... } }`
- `let else` : évite les `if let ... else { return }`

## À retenir
- `while let` pour itérer sur des `Option`/`Result`
- `let else` avec un bloc qui diverge (`return`, `break`, `panic!`)
- Plus idiomatique que les alternatives verbeuses""",
    },
    {
        "topic": "modules",
        "difficulty": "intermediaire",
        "user": "Comment créer une bibliothèque (lib) vs un binaire (bin) en Rust ?",
        "assistant": """## TL;DR
- `src/main.rs` → binaire exécutable
- `src/lib.rs` → bibliothèque importable
- Les deux peuvent coexister

## Problème
Tu veux organiser ton code en lib réutilisable et/ou binaire exécutable.

## Solution
**Structure avec les deux** :
```
my_project/
├── Cargo.toml
└── src/
    ├── lib.rs     # Bibliothèque
    └── main.rs    # Binaire
```

**lib.rs** — code réutilisable :
```rust
// src/lib.rs
pub fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}
```

**main.rs** — utilise la lib :
```rust
// src/main.rs
use my_project::greet;

fn main() {
    println!("{}", greet("World"));
}
```

## Explication
**Binaires multiples** :
```
src/
├── lib.rs
└── bin/
    ├── cli.rs
    └── server.rs
```

```bash
cargo run --bin cli
cargo run --bin server
```

**Cargo.toml** peut aussi définir :
```toml
[[bin]]
name = "my_cli"
path = "src/bin/cli.rs"
```

## À retenir
- `lib.rs` = point d'entrée de la bibliothèque
- `main.rs` = point d'entrée du binaire
- Le binaire importe la lib avec `use crate_name::...`""",
    },
]

FINAL_EXERCISES_EXAMPLES = [
    {
        "topic": "error_handling",
        "difficulty": "debutant",
        "user": "Un exercice simple sur Result et l'opérateur `?`.",
        "assistant": """## TL;DR
Exercice : lire un fichier et parser son contenu en nombre.

## Problème
Tu dois chaîner plusieurs opérations qui peuvent échouer.

## Solution
**Exercice : Lire un nombre depuis un fichier**

```rust
use std::fs;
use std::num::ParseIntError;
use std::io;

#[derive(Debug)]
enum ReadError {
    Io(io::Error),
    Parse(ParseIntError),
}

fn read_number(path: &str) -> Result<i32, ReadError> {
    todo!()
}

fn main() {
    match read_number("number.txt") {
        Ok(n) => println!("Number: {}", n),
        Err(e) => println!("Error: {:?}", e),
    }
}
```

**Solution** :
```rust
impl From<io::Error> for ReadError {
    fn from(e: io::Error) -> Self { ReadError::Io(e) }
}

impl From<ParseIntError> for ReadError {
    fn from(e: ParseIntError) -> Self { ReadError::Parse(e) }
}

fn read_number(path: &str) -> Result<i32, ReadError> {
    let content = fs::read_to_string(path)?;
    let number = content.trim().parse::<i32>()?;
    Ok(number)
}
```

## Explication
- `impl From<E>` permet à `?` de convertir automatiquement
- `?` propage et convertit les erreurs
- `trim()` enlève les whitespace/newlines

## À retenir
- `From` trait pour conversion d'erreur
- `?` convertit automatiquement si `From` est implémenté
- Une seule ligne par opération faillible""",
    },
    {
        "topic": "structs",
        "difficulty": "debutant",
        "user": "Un exercice sur la création de structs avec des méthodes.",
        "assistant": """## TL;DR
Exercice : créer une struct `Rectangle` avec des méthodes de calcul.

## Problème
Tu dois créer un type avec son comportement associé.

## Solution
**Exercice : Rectangle**

```rust
struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    // TODO: Constructeur
    fn new(width: u32, height: u32) -> Self { todo!() }

    // TODO: Calcule l'aire
    fn area(&self) -> u32 { todo!() }

    // TODO: Vérifie si c'est un carré
    fn is_square(&self) -> bool { todo!() }

    // TODO: Vérifie si self peut contenir other
    fn can_hold(&self, other: &Rectangle) -> bool { todo!() }
}
```

**Tests** :
```rust
let r1 = Rectangle::new(10, 5);
assert_eq!(r1.area(), 50);
assert!(!r1.is_square());

let r2 = Rectangle::new(5, 5);
assert!(r2.is_square());
assert!(r1.can_hold(&r2));
```

**Solution** :
```rust
impl Rectangle {
    fn new(width: u32, height: u32) -> Self {
        Rectangle { width, height }
    }

    fn area(&self) -> u32 {
        self.width * self.height
    }

    fn is_square(&self) -> bool {
        self.width == self.height
    }

    fn can_hold(&self, other: &Rectangle) -> bool {
        self.width >= other.width && self.height >= other.height
    }
}
```

## Explication
- `Self` = le type en cours (`Rectangle`)
- `&self` = référence immuable vers l'instance
- Les méthodes sans `self` sont des fonctions associées

## À retenir
- Constructeur = fonction associée retournant `Self`
- `&self` pour méthodes qui lisent
- `&mut self` pour méthodes qui modifient""",
    },
    {
        "topic": "enums",
        "difficulty": "debutant",
        "user": "Un exercice sur les enums avec données.",
        "assistant": """## TL;DR
Exercice : modéliser un système de messages avec un enum.

## Problème
Tu dois créer un type qui peut représenter différents types de messages.

## Solution
**Exercice : Système de messages**

```rust
enum Message {
    Text(String),
    Image { url: String, width: u32, height: u32 },
    File { name: String, size: u64 },
}

impl Message {
    // TODO: Retourne une description du message
    fn describe(&self) -> String { todo!() }

    // TODO: Retourne la taille en bytes (texte=len, image=width*height*3, file=size)
    fn size_bytes(&self) -> u64 { todo!() }
}
```

**Tests** :
```rust
let m1 = Message::Text("Hello".into());
assert_eq!(m1.describe(), "Text message: 5 chars");

let m2 = Message::Image { url: "img.png".into(), width: 100, height: 50 };
assert_eq!(m2.size_bytes(), 15000);
```

**Solution** :
```rust
impl Message {
    fn describe(&self) -> String {
        match self {
            Message::Text(s) => format!("Text message: {} chars", s.len()),
            Message::Image { url, .. } => format!("Image: {}", url),
            Message::File { name, size } => format!("File: {} ({} bytes)", name, size),
        }
    }

    fn size_bytes(&self) -> u64 {
        match self {
            Message::Text(s) => s.len() as u64,
            Message::Image { width, height, .. } => (*width as u64) * (*height as u64) * 3,
            Message::File { size, .. } => *size,
        }
    }
}
```

## Explication
- `..` ignore les champs non utilisés
- `*` pour déréférencer les références dans le pattern
- Chaque variant peut avoir une structure différente

## À retenir
- Enums avec données = types somme
- `match` pour extraire les données
- `..` pour ignorer des champs""",
    },
]

# ============================================================================
# M9: Exemples supplementaires pour lifetimes, borrowing, async
# ============================================================================

LIFETIMES_EXAMPLES = [
    {
        "topic": "lifetimes",
        "difficulty": "debutant",
        "user": "Pourquoi ce code ne compile pas ?\n\n```rust\nfn longest(x: &str, y: &str) -> &str {\n    if x.len() > y.len() { x } else { y }\n}\n```",
        "assistant": """## TL;DR
Le compilateur ne sait pas quelle reference (`x` ou `y`) sera retournee. Il faut annoter les lifetimes pour indiquer que le resultat vit aussi longtemps que les deux entrees.

## Probleme
```
error[E0106]: missing lifetime specifier
 --> src/main.rs:1:33
  |
1 | fn longest(x: &str, y: &str) -> &str {
  |                                 ^ expected named lifetime parameter
```

Rust doit savoir combien de temps la reference retournee sera valide.

## Solution
Ajouter un parametre de lifetime :
```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

## Explication
- `'a` est un parametre de lifetime (comme `T` pour les generics)
- `&'a str` signifie "reference qui vit au moins aussi longtemps que 'a"
- Le retour `&'a str` sera valide tant que `x` ET `y` sont valides

Utilisation :
```rust
let s1 = String::from("long string");
let s2 = String::from("short");
let result = longest(&s1, &s2);
println!("{}", result);  // OK: s1 et s2 toujours valides
```

## A retenir
- Le compilateur ne peut pas deviner quelle branche sera prise
- Les lifetimes lient la duree du retour aux entrees
- Syntaxe : `<'a>` apres le nom de fonction""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "debutant",
        "user": "C'est quoi la difference entre `'static` et une lifetime generique `'a` ?",
        "assistant": """## TL;DR
`'static` signifie "vit pour toute la duree du programme". Une lifetime generique `'a` peut etre plus courte.

## Probleme
Quand utiliser `'static` vs `'a` ?

## Solution
**`'static`** - donnees qui vivent eternellement :
```rust
// Litteraux de chaines sont 'static
let s: &'static str = "hello";

// Constantes
static GREETING: &str = "Hello";

// Donnees leakees intentionnellement
let leaked: &'static str = Box::leak(Box::new(String::from("leaked")));
```

**Lifetime generique** - duree variable :
```rust
fn first_word<'a>(s: &'a str) -> &'a str {
    &s[..s.find(' ').unwrap_or(s.len())]
}
```

## Explication
| Aspect | `'static` | `'a` |
|--------|-----------|------|
| Duree | Programme entier | Variable |
| Flexibilite | Rigide | Adaptable |
| Cas d'usage | Constantes, config | Fonctions, structs |

**Piege courant** :
```rust
// ERREUR: String n'est pas 'static
fn bad() -> &'static str {
    let s = String::from("hello");
    &s  // s sera detruite!
}
```

## A retenir
- `'static` = vit toujours (litteraux, constantes)
- `'a` = "au moins aussi longtemps que..."
- Ne pas confondre `'static` et owned data""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "intermediaire",
        "user": "Comment utiliser les lifetimes avec une struct qui contient des references ?",
        "assistant": """## TL;DR
La struct doit declarer un parametre de lifetime. Elle ne peut pas survivre aux donnees qu'elle reference.

## Probleme
Tu veux creer une struct qui emprunte des donnees au lieu de les posseder.

## Solution
```rust
struct Excerpt<'a> {
    text: &'a str,
}

impl<'a> Excerpt<'a> {
    fn new(text: &'a str) -> Self {
        Excerpt { text }
    }

    fn display(&self) {
        println!("{}", self.text);
    }
}

fn main() {
    let novel = String::from("Call me Ishmael...");
    let excerpt = Excerpt::new(&novel[..15]);
    excerpt.display();  // OK: novel toujours valide
}
```

## Explication
La lifetime `'a` garantit que :
- `Excerpt` ne peut pas survivre au texte source
- Pas de dangling reference possible

**Erreur typique** :
```rust
fn broken() -> Excerpt<'static> {
    let temp = String::from("temporary");
    Excerpt::new(&temp)  // ERREUR: temp detruite a la fin
}
```

**Struct avec plusieurs lifetimes** :
```rust
struct MultiRef<'a, 'b> {
    first: &'a str,
    second: &'b str,
}
```

## A retenir
- `struct Name<'a>` pour declarer la lifetime
- `impl<'a> Name<'a>` pour les methodes
- La struct emprunte, ne possede pas""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "intermediaire",
        "user": "Explique l'elision des lifetimes. Quand peut-on les omettre ?",
        "assistant": """## TL;DR
Rust infere les lifetimes dans des cas simples grace a 3 regles d'elision. Tu peux souvent les omettre.

## Probleme
Ecrire les lifetimes partout serait verbeux. Quand sont-elles optionnelles ?

## Solution
Ces deux fonctions sont equivalentes :
```rust
// Avec elision (prefere)
fn first_word(s: &str) -> &str {
    &s[..s.find(' ').unwrap_or(s.len())]
}

// Sans elision (explicite)
fn first_word<'a>(s: &'a str) -> &'a str {
    &s[..s.find(' ').unwrap_or(s.len())]
}
```

## Explication
**Les 3 regles d'elision** :

1. Chaque reference en entree recoit sa propre lifetime
```rust
fn f(x: &str, y: &str)
// devient
fn f<'a, 'b>(x: &'a str, y: &'b str)
```

2. S'il y a exactement une lifetime en entree, elle s'applique a toutes les sorties
```rust
fn f(x: &str) -> &str
// devient
fn f<'a>(x: &'a str) -> &'a str
```

3. Si une des entrees est `&self` ou `&mut self`, sa lifetime s'applique aux sorties
```rust
impl Foo {
    fn method(&self) -> &str
    // devient
    fn method<'a>(&'a self) -> &'a str
}
```

**Quand ca ne marche pas** :
```rust
// Deux entrees, pas de self -> explicite requis
fn longest(x: &str, y: &str) -> &str  // ERREUR
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str  // OK
```

## A retenir
- Elision = inference automatique des lifetimes
- Une entree -> sortie herite sa lifetime
- Methodes avec `&self` -> sortie herite de self
- Plusieurs entrees sans self -> explicite""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "avance",
        "user": "Comment gerer les lifetimes dans les closures qui capturent des references ?",
        "assistant": """## TL;DR
Les closures capturent leur environnement. Si elles capturent des references, elles heritent de leurs lifetimes.

## Probleme
Une closure qui capture une reference ne peut pas survivre a cette reference.

## Solution
**Closure qui emprunte** :
```rust
fn process_with_closure<'a>(data: &'a str) -> impl Fn() + 'a {
    move || {
        println!("{}", data);
    }
}

fn main() {
    let s = String::from("hello");
    let closure = process_with_closure(&s);
    closure();  // OK
    // s doit rester valide tant que closure existe
}
```

**HRTB (Higher-Ranked Trait Bounds)** pour plus de flexibilite :
```rust
fn apply_to_all<F>(items: &[String], f: F)
where
    F: for<'a> Fn(&'a str) -> &'a str,
{
    for item in items {
        println!("{}", f(item));
    }
}
```

## Explication
Le `for<'a>` signifie "pour toute lifetime 'a". C'est utile quand :
- La closure doit fonctionner avec des references de durees differentes
- Tu ne connais pas la lifetime a l'avance

**Piege courant** :
```rust
fn bad() -> impl Fn() {
    let local = String::from("hello");
    move || println!("{}", local)  // OK: move prend ownership
}

fn also_bad() -> impl Fn() {
    let local = String::from("hello");
    || println!("{}", local)  // ERREUR: emprunte local qui sera detruit
}
```

## A retenir
- `move` pour prendre ownership au lieu d'emprunter
- `impl Fn() + 'a` lie la closure a une lifetime
- `for<'a>` pour des lifetimes universellement quantifiees""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "avance",
        "user": "Corrige cette erreur: `lifetime may not live long enough`\n\n```rust\nstruct Parser<'a> {\n    input: &'a str,\n}\n\nimpl<'a> Parser<'a> {\n    fn parse(&mut self) -> &str {\n        &self.input[..5]\n    }\n}\n```",
        "assistant": """## TL;DR
Le retour doit avoir la lifetime `'a` de `input`, pas une lifetime anonyme liee a `&mut self`.

## Probleme
```
error: lifetime may not live long enough
  |
6 |     fn parse(&mut self) -> &str {
  |              - let's call the lifetime of this reference `'1`
7 |         &self.input[..5]
  |         ^^^^^^^^^^^^^^^^ method was supposed to return data with lifetime `'1` but it is returning data with lifetime `'a`
```

Le compilateur infere que le retour est lie a `&mut self`, mais tu retournes une partie de `input` (lifetime `'a`).

## Solution
Specifier explicitement que le retour a la lifetime `'a` :
```rust
impl<'a> Parser<'a> {
    fn parse(&mut self) -> &'a str {
        &self.input[..5]
    }
}
```

Ou si tu veux que le retour soit lie a self :
```rust
impl<'a> Parser<'a> {
    fn parse<'b>(&'b mut self) -> &'b str
    where
        'a: 'b,  // 'a outlives 'b
    {
        &self.input[..5]
    }
}
```

## Explication
Sans annotation, l'elision donne :
```rust
fn parse<'b>(&'b mut self) -> &'b str
```

Mais `self.input` a la lifetime `'a`, pas `'b`. Il faut soit :
- Retourner `&'a str` (le plus simple)
- Contraindre `'a: 'b` (plus flexible mais verbeux)

## A retenir
- L'elision lie le retour a `&self`, pas aux champs
- Annotez explicitement quand le retour vient d'un champ
- `'a: 'b` signifie "'a vit au moins aussi longtemps que 'b\"""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "intermediaire",
        "user": "Comment avoir deux structs qui se referencent mutuellement ?",
        "assistant": """## TL;DR
Les references mutuelles sont difficiles en Rust. Utilise `Rc<RefCell<T>>` ou des indices au lieu de references.

## Probleme
```rust
// IMPOSSIBLE avec des references simples
struct Node<'a> {
    value: i32,
    next: Option<&'a Node<'a>>,
    prev: Option<&'a Node<'a>>,  // Reference mutuelle!
}
```

## Solution
**Option 1 : Indices** (prefere pour les graphes)
```rust
struct Graph {
    nodes: Vec<Node>,
}

struct Node {
    value: i32,
    neighbors: Vec<usize>,  // Indices, pas references
}

impl Graph {
    fn get(&self, idx: usize) -> &Node {
        &self.nodes[idx]
    }
}
```

**Option 2 : Rc<RefCell<T>>** (ownership partagee)
```rust
use std::cell::RefCell;
use std::rc::{Rc, Weak};

struct Node {
    value: i32,
    next: Option<Rc<RefCell<Node>>>,
    prev: Option<Weak<RefCell<Node>>>,  // Weak evite les cycles
}
```

## Explication
Pourquoi les references ne marchent pas :
- A doit exister avant B (pour que B reference A)
- B doit exister avant A (pour que A reference B)
- Paradoxe!

Les solutions :
- **Indices** : pas de lifetime, acces via le conteneur
- **Rc/Weak** : comptage de references, Weak casse les cycles
- **Arena** : allocateur qui gere les lifetimes

## A retenir
- Eviter les references mutuelles directes
- Indices pour structures de donnees complexes
- `Weak` pour eviter les cycles memoire""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "debutant",
        "user": "Pourquoi le compilateur dit 'borrowed value does not live long enough' ?",
        "assistant": """## TL;DR
Tu essaies d'utiliser une reference apres que la valeur originale a ete detruite.

## Probleme
```rust
fn main() {
    let r;
    {
        let x = 5;
        r = &x;  // Emprunte x
    }  // x est detruite ici
    println!("{}", r);  // ERREUR: r pointe vers rien
}
```

## Solution
**Option 1** : Etendre la portee de la valeur
```rust
fn main() {
    let x = 5;  // x vit assez longtemps
    let r = &x;
    println!("{}", r);  // OK
}
```

**Option 2** : Retourner une valeur owned
```rust
fn create_value() -> String {
    String::from("hello")  // Ownership transfere
}

fn main() {
    let s = create_value();
    println!("{}", s);
}
```

**Option 3** : Clone si necessaire
```rust
fn main() {
    let owned: String;
    {
        let temp = String::from("hello");
        owned = temp.clone();  // Copie les donnees
    }
    println!("{}", owned);  // OK: owned possede sa propre copie
}
```

## Explication
Rust garantit a la compilation qu'aucune reference ne devient invalide. Une reference ne peut pas survivre a sa source.

## A retenir
- Les references ne peuvent pas depasser la vie de leur source
- Solutions : etendre la portee, clone, ou retourner owned
- Le compilateur te protege des bugs memoire""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "avance",
        "user": "Comment implementer un iterateur qui retourne des references vers les elements ?",
        "assistant": """## TL;DR
L'iterateur doit avoir un parametre de lifetime qui lie les references retournees a la source de donnees.

## Probleme
Creer un iterateur custom qui emprunte les donnees.

## Solution
```rust
struct Iter<'a, T> {
    data: &'a [T],
    index: usize,
}

impl<'a, T> Iter<'a, T> {
    fn new(data: &'a [T]) -> Self {
        Iter { data, index: 0 }
    }
}

impl<'a, T> Iterator for Iter<'a, T> {
    type Item = &'a T;

    fn next(&mut self) -> Option<Self::Item> {
        if self.index < self.data.len() {
            let item = &self.data[self.index];
            self.index += 1;
            Some(item)
        } else {
            None
        }
    }
}

fn main() {
    let v = vec![1, 2, 3];
    for item in Iter::new(&v) {
        println!("{}", item);
    }
}
```

## Explication
- `Iter<'a, T>` : l'iterateur vit au plus aussi longtemps que les donnees
- `type Item = &'a T` : chaque element est une reference avec la meme lifetime
- L'iterateur emprunte, il ne possede pas les donnees

**Pattern IntoIterator** :
```rust
impl<'a, T> IntoIterator for &'a MyCollection<T> {
    type Item = &'a T;
    type IntoIter = Iter<'a, T>;

    fn into_iter(self) -> Self::IntoIter {
        Iter::new(&self.items)
    }
}
```

## A retenir
- `type Item = &'a T` pour iterateurs de references
- La lifetime lie l'iterateur a sa source
- Implementer `IntoIterator` pour `for` loops""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "intermediaire",
        "user": "Comment utiliser les lifetimes avec des traits ?",
        "assistant": """## TL;DR
Les traits peuvent avoir des parametres de lifetime comme les structs. Utile pour les methodes qui retournent des references.

## Probleme
Definir un trait dont les methodes travaillent avec des references.

## Solution
**Trait avec lifetime** :
```rust
trait Parser<'a> {
    fn parse(&self, input: &'a str) -> &'a str;
}

struct JsonParser;

impl<'a> Parser<'a> for JsonParser {
    fn parse(&self, input: &'a str) -> &'a str {
        // Retourne une partie de l'input
        input.trim()
    }
}
```

**Trait avec associated lifetime** :
```rust
trait Container {
    type Item<'a> where Self: 'a;

    fn get<'a>(&'a self) -> Self::Item<'a>;
}

struct StringHolder(String);

impl Container for StringHolder {
    type Item<'a> = &'a str where Self: 'a;

    fn get<'a>(&'a self) -> &'a str {
        &self.0
    }
}
```

## Explication
Deux approches :
1. **Lifetime sur le trait** : `trait Foo<'a>` - la lifetime fait partie du type
2. **GAT (Generic Associated Types)** : `type Item<'a>` - plus flexible

**Trait object avec lifetime** :
```rust
fn process<'a>(parser: &dyn Parser<'a>, input: &'a str) -> &'a str {
    parser.parse(input)
}
```

## A retenir
- `trait Name<'a>` pour traits avec lifetimes
- GATs (`type Item<'a>`) pour plus de flexibilite
- Les trait objects doivent specifier leurs lifetimes""",
    },
]

BORROWING_EXAMPLES = [
    {
        "topic": "borrowing",
        "difficulty": "debutant",
        "user": "Pourquoi je ne peux pas modifier une variable pendant qu'elle est empruntee ?\n\n```rust\nlet mut v = vec![1, 2, 3];\nlet first = &v[0];\nv.push(4);\nprintln!(\"{}\", first);\n```",
        "assistant": """## TL;DR
`v.push()` pourrait reallouer le vecteur, invalidant la reference `first`. Rust l'interdit pour eviter les bugs memoire.

## Probleme
```
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
```

`first` emprunte `v` immuablement. `push` veut emprunter `v` mutablement. Les deux ne peuvent pas coexister.

## Solution
**Option 1** : Utiliser la reference avant de modifier
```rust
let mut v = vec![1, 2, 3];
let first = &v[0];
println!("{}", first);  // Utilise first ici
v.push(4);  // OK: first plus utilisee
```

**Option 2** : Copier la valeur
```rust
let mut v = vec![1, 2, 3];
let first = v[0];  // Copie (i32 est Copy)
v.push(4);
println!("{}", first);
```

**Option 3** : Clone si pas Copy
```rust
let mut v = vec![String::from("a")];
let first = v[0].clone();  // Clone la String
v.push(String::from("b"));
println!("{}", first);
```

## Explication
Pourquoi `push` est dangereux :
1. Le vecteur peut manquer de capacite
2. Il realloue un nouveau buffer
3. Les anciennes references pointent vers la memoire liberee

Rust detecte ce pattern et l'interdit.

## A retenir
- Pas de reference mutable + immuable simultanement
- `Vec::push` peut invalider les references
- Utiliser la reference avant de modifier, ou copier/cloner""",
    },
    {
        "topic": "borrowing",
        "difficulty": "intermediaire",
        "user": "Comment eviter les conflits de borrow dans une boucle qui modifie une collection ?",
        "assistant": """## TL;DR
Utilise des indices au lieu de references, ou collecte les modifications dans un vecteur separe.

## Probleme
```rust
let mut items = vec![1, 2, 3, 4, 5];
for item in &items {
    if *item % 2 == 0 {
        items.push(*item * 10);  // ERREUR: borrow conflict
    }
}
```

## Solution
**Option 1** : Indices
```rust
let mut items = vec![1, 2, 3, 4, 5];
let len = items.len();
for i in 0..len {
    if items[i] % 2 == 0 {
        items.push(items[i] * 10);
    }
}
```

**Option 2** : Collecter puis modifier
```rust
let mut items = vec![1, 2, 3, 4, 5];
let to_add: Vec<_> = items.iter()
    .filter(|&&x| x % 2 == 0)
    .map(|&x| x * 10)
    .collect();
items.extend(to_add);
```

**Option 3** : retain/drain pour filtrage
```rust
let mut items = vec![1, 2, 3, 4, 5];
items.retain(|&x| x % 2 != 0);  // Garde les impairs
```

## Explication
Le probleme : `for item in &items` emprunte `items` pour toute la boucle. `push` veut emprunter mutablement.

Solutions :
- Les indices n'empruntent pas le vecteur entier
- Collecter separe la lecture de l'ecriture
- `retain`/`drain` sont des methodes qui gerent cela internement

## A retenir
- Boucle + modification = utiliser des indices
- Ou separer lecture et ecriture
- `retain`, `drain` pour les cas courants""",
    },
    {
        "topic": "borrowing",
        "difficulty": "intermediaire",
        "user": "Explique la difference entre `&T`, `&mut T`, et `T` en parametre de fonction.",
        "assistant": """## TL;DR
- `T` : prend ownership (consomme)
- `&T` : emprunte en lecture seule
- `&mut T` : emprunte avec droit de modification

## Probleme
Choisir le bon type de parametre selon les besoins.

## Solution
**`T`** - ownership (move) :
```rust
fn consume(s: String) {
    println!("{}", s);
}  // s est detruite ici

let s = String::from("hello");
consume(s);
// println!("{}", s);  // ERREUR: s a ete moved
```

**`&T`** - lecture seule :
```rust
fn print_len(s: &String) {
    println!("Length: {}", s.len());
    // s.push('!');  // ERREUR: pas mutable
}

let s = String::from("hello");
print_len(&s);
println!("{}", s);  // OK: s toujours valide
```

**`&mut T`** - modification :
```rust
fn append_exclaim(s: &mut String) {
    s.push('!');
}

let mut s = String::from("hello");
append_exclaim(&mut s);
println!("{}", s);  // "hello!"
```

## Explication
| Parametre | Ownership | Peut lire | Peut modifier |
|-----------|-----------|-----------|---------------|
| `T` | Transfere | Oui | Oui |
| `&T` | Emprunte | Oui | Non |
| `&mut T` | Emprunte mut | Oui | Oui |

Regles :
- `&T` : plusieurs simultanes OK
- `&mut T` : une seule a la fois
- Jamais `&T` et `&mut T` simultanes

## A retenir
- `&T` par defaut pour la lecture
- `&mut T` si tu dois modifier
- `T` si tu veux consommer ou stocker""",
    },
    {
        "topic": "borrowing",
        "difficulty": "debutant",
        "user": "Corrige: `cannot borrow as mutable because it is also borrowed as immutable`",
        "assistant": """## TL;DR
Tu as une reference immuable active et tu essaies d'obtenir une reference mutable. Rust l'interdit.

## Probleme
```rust
let mut s = String::from("hello");
let r1 = &s;      // Emprunt immuable
let r2 = &mut s;  // ERREUR: emprunt mutable
println!("{}", r1);
```

## Solution
**S'assurer que les emprunts ne se chevauchent pas** :
```rust
let mut s = String::from("hello");

// Scope 1: lecture
let r1 = &s;
println!("{}", r1);
// r1 n'est plus utilisee apres cette ligne

// Scope 2: modification
let r2 = &mut s;
r2.push_str(" world");
println!("{}", r2);
```

**Ou separer explicitement** :
```rust
let mut s = String::from("hello");

{
    let r1 = &s;
    println!("{}", r1);
}  // r1 liberee

{
    let r2 = &mut s;
    r2.push_str(" world");
}
```

## Explication
Le borrow checker suit les "Non-Lexical Lifetimes" (NLL) :
- Une reference vit jusqu'a sa derniere utilisation
- Pas jusqu'a la fin du bloc

```rust
let mut s = String::from("hello");
let r1 = &s;
println!("{}", r1);  // Derniere utilisation de r1
let r2 = &mut s;     // OK: r1 n'est plus active
```

## A retenir
- Pas de `&mut` pendant qu'un `&` existe
- NLL permet plus de flexibilite qu'avant
- Utiliser les references, puis les liberer avant de modifier""",
    },
    {
        "topic": "borrowing",
        "difficulty": "avance",
        "user": "C'est quoi le pattern reborrow et quand l'utiliser ?",
        "assistant": """## TL;DR
Le reborrow cree une nouvelle reference a partir d'une existante, avec une portee plus limitee. Utile pour les methodes qui prennent `&mut self`.

## Probleme
Passer une reference mutable a plusieurs methodes successives.

## Solution
```rust
struct Data {
    value: i32,
}

impl Data {
    fn increment(&mut self) {
        self.value += 1;
    }

    fn get(&self) -> i32 {
        self.value
    }
}

fn process(data: &mut Data) {
    // Reborrow implicite a chaque appel
    data.increment();  // &mut *data
    data.increment();  // &mut *data
    println!("{}", data.get());  // &*data
}
```

**Reborrow explicite** :
```rust
fn explicit_reborrow(data: &mut Data) {
    let reborrowed: &mut Data = &mut *data;  // Reborrow explicite
    reborrowed.increment();
    // data peut etre reutilise apres que reborrowed n'est plus utilise
}
```

## Explication
Quand tu passes `&mut T` a une fonction :
- Sans reborrow : la fonction prend le `&mut` (move)
- Avec reborrow : la fonction emprunte temporairement

```rust
fn takes_mut(x: &mut i32) {}

let mut n = 5;
let r = &mut n;

// Reborrow implicite - r reste valide apres
takes_mut(r);
takes_mut(r);

// Move explicite - r invalide apres
takes_mut(r);  // OK
// r ne peut plus etre utilise si on avait fait un move
```

## A retenir
- Reborrow = creer une reference temporaire depuis une existante
- Rust fait souvent des reborrows implicites
- Permet de reutiliser `&mut` apres un appel de methode""",
    },
    {
        "topic": "borrowing",
        "difficulty": "intermediaire",
        "user": "Comment utiliser `RefCell` pour contourner les regles du borrow checker ?",
        "assistant": """## TL;DR
`RefCell<T>` deplace les verifications d'emprunt a l'execution. Utile pour la mutabilite interieure.

## Probleme
Parfois tu as besoin de modifier des donnees meme avec une reference immuable (pattern mutabilite interieure).

## Solution
```rust
use std::cell::RefCell;

struct Counter {
    value: RefCell<i32>,
}

impl Counter {
    fn new() -> Self {
        Counter { value: RefCell::new(0) }
    }

    // &self (immuable) mais peut modifier value!
    fn increment(&self) {
        *self.value.borrow_mut() += 1;
    }

    fn get(&self) -> i32 {
        *self.value.borrow()
    }
}

fn main() {
    let counter = Counter::new();  // Pas mut!
    counter.increment();
    counter.increment();
    println!("{}", counter.get());  // 2
}
```

## Explication
**Methodes de RefCell** :
- `borrow()` : retourne `Ref<T>` (lecture)
- `borrow_mut()` : retourne `RefMut<T>` (ecriture)

**Les memes regles s'appliquent, mais a l'execution** :
```rust
let cell = RefCell::new(5);
let r1 = cell.borrow();
let r2 = cell.borrow_mut();  // PANIC a l'execution!
```

**Cas d'usage** :
- Caches internes
- Compteurs de visite
- Graphes avec `Rc<RefCell<Node>>`

## A retenir
- `RefCell` = borrow checking a l'execution
- `borrow()` / `borrow_mut()` au lieu de `&` / `&mut`
- Panic si les regles sont violees
- Single-thread seulement (utiliser `Mutex` pour multi-thread)""",
    },
    {
        "topic": "borrowing",
        "difficulty": "debutant",
        "user": "Pourquoi `&[T]` (slice) est souvent prefere a `&Vec<T>` ?",
        "assistant": """## TL;DR
`&[T]` est plus generique : il accepte les `Vec`, les arrays, et les sous-parties. C'est le type de reference "universel" pour les sequences.

## Probleme
Quelle signature utiliser pour une fonction qui lit une sequence ?

## Solution
**Prefere `&[T]`** :
```rust
fn sum(numbers: &[i32]) -> i32 {
    numbers.iter().sum()
}

fn main() {
    let vec = vec![1, 2, 3];
    let array = [4, 5, 6];

    println!("{}", sum(&vec));       // Vec -> slice OK
    println!("{}", sum(&array));     // Array -> slice OK
    println!("{}", sum(&vec[1..]));  // Sous-slice OK
}
```

**Avec `&Vec<T>`** (moins flexible) :
```rust
fn sum_vec(numbers: &Vec<i32>) -> i32 {
    numbers.iter().sum()
}

// sum_vec(&array);  // ERREUR: array n'est pas un Vec
```

## Explication
`&[T]` est une "fat pointer" :
- Pointeur vers les donnees
- Longueur

Conversions automatiques :
- `&Vec<T>` -> `&[T]` (deref coercion)
- `&[T; N]` -> `&[T]`
- `&[T][a..b]` -> `&[T]`

| Parametre | Accepte |
|-----------|---------|
| `&Vec<T>` | Vec seulement |
| `&[T]` | Vec, array, slice |

## A retenir
- `&[T]` pour la lecture de sequences
- `&mut [T]` pour la modification
- Plus idiomatique et flexible que `&Vec<T>`""",
    },
]

ASYNC_EXAMPLES = [
    {
        "topic": "async",
        "difficulty": "debutant",
        "user": "Comment creer et executer une fonction async en Rust ?",
        "assistant": """## TL;DR
Declare avec `async fn`, execute avec un runtime comme `tokio`. Les fonctions async retournent des `Future` qui doivent etre `.await`ed.

## Probleme
Tu veux ecrire du code asynchrone en Rust.

## Solution
**Avec tokio** :
```rust
use tokio::time::{sleep, Duration};

async fn greet(name: &str) {
    sleep(Duration::from_secs(1)).await;
    println!("Hello, {}!", name);
}

#[tokio::main]
async fn main() {
    greet("World").await;
}
```

**Sans tokio (async-std)** :
```rust
use async_std::task;

async fn greet(name: &str) {
    task::sleep(std::time::Duration::from_secs(1)).await;
    println!("Hello, {}!", name);
}

#[async_std::main]
async fn main() {
    greet("World").await;
}
```

## Explication
- `async fn` transforme la fonction en generateur de `Future`
- `.await` suspend l'execution jusqu'a completion
- Un runtime (`tokio`, `async-std`) execute les futures

**Sans macro main** :
```rust
fn main() {
    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async {
        greet("World").await;
    });
}
```

## A retenir
- `async fn` retourne un `Future`
- `.await` pour attendre le resultat
- Besoin d'un runtime pour executer""",
    },
    {
        "topic": "async",
        "difficulty": "intermediaire",
        "user": "Comment executer plusieurs taches async en parallele ?",
        "assistant": """## TL;DR
Utilise `tokio::join!` pour attendre plusieurs futures, ou `tokio::spawn` pour les lancer en taches independantes.

## Probleme
Tu veux faire plusieurs operations I/O en meme temps.

## Solution
**`join!`** - attend plusieurs futures :
```rust
use tokio::time::{sleep, Duration};

async fn fetch_user() -> String {
    sleep(Duration::from_secs(1)).await;
    "User data".to_string()
}

async fn fetch_posts() -> Vec<String> {
    sleep(Duration::from_secs(1)).await;
    vec!["Post 1".to_string(), "Post 2".to_string()]
}

#[tokio::main]
async fn main() {
    // Execute en parallele, attend les deux
    let (user, posts) = tokio::join!(
        fetch_user(),
        fetch_posts()
    );
    println!("User: {}, Posts: {:?}", user, posts);
    // Total: ~1s, pas 2s
}
```

**`spawn`** - taches independantes :
```rust
#[tokio::main]
async fn main() {
    let handle1 = tokio::spawn(async {
        fetch_user().await
    });

    let handle2 = tokio::spawn(async {
        fetch_posts().await
    });

    let user = handle1.await.unwrap();
    let posts = handle2.await.unwrap();
}
```

## Explication
| Methode | Usage | Annulation |
|---------|-------|------------|
| `join!` | Futures liees | Si une panic, toutes annulees |
| `spawn` | Taches independantes | Continuent independamment |

**`select!`** pour le premier qui termine :
```rust
tokio::select! {
    result = fetch_user() => println!("User: {}", result),
    result = fetch_posts() => println!("Posts: {:?}", result),
}
```

## A retenir
- `join!` pour paralleliser des operations liees
- `spawn` pour des taches independantes
- `select!` pour le premier qui repond""",
    },
    {
        "topic": "async",
        "difficulty": "intermediaire",
        "user": "Comment gerer les erreurs dans du code async ?",
        "assistant": """## TL;DR
Utilise `Result` et l'operateur `?` comme en code synchrone. `tokio::spawn` retourne un `JoinHandle` qui peut aussi echouer.

## Probleme
Propager et gerer les erreurs dans des fonctions async.

## Solution
**`?` fonctionne normalement** :
```rust
use std::io;

async fn read_config() -> Result<String, io::Error> {
    let content = tokio::fs::read_to_string("config.txt").await?;
    Ok(content)
}

async fn process() -> Result<(), io::Error> {
    let config = read_config().await?;
    println!("Config: {}", config);
    Ok(())
}
```

**Avec `spawn`** - double Result :
```rust
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let handle = tokio::spawn(async {
        read_config().await
    });

    // JoinError si la tache panic
    // io::Error si read_config echoue
    let result = handle.await??;
    println!("Config: {}", result);
    Ok(())
}
```

**`try_join!`** pour plusieurs :
```rust
async fn fetch_all() -> Result<(String, Vec<String>), Error> {
    let (user, posts) = tokio::try_join!(
        fetch_user(),  // Result<String, Error>
        fetch_posts()  // Result<Vec<String>, Error>
    )?;  // Retourne a la premiere erreur
    Ok((user, posts))
}
```

## Explication
- `await?` combine attente et propagation d'erreur
- `spawn().await` retourne `Result<T, JoinError>`
- `try_join!` arrete au premier echec

## A retenir
- `?` fonctionne avec async
- `spawn` ajoute un niveau de Result (JoinError)
- `try_join!` pour propager la premiere erreur""",
    },
    {
        "topic": "async",
        "difficulty": "avance",
        "user": "Pourquoi j'ai 'future cannot be sent between threads safely' ?",
        "assistant": """## TL;DR
Ta future utilise un type non-`Send` (comme `Rc` ou `RefCell`). `tokio::spawn` requiert des futures `Send` car elles peuvent changer de thread.

## Probleme
```rust
use std::rc::Rc;

async fn process(data: Rc<String>) {
    println!("{}", data);
}

#[tokio::main]
async fn main() {
    let data = Rc::new(String::from("hello"));
    tokio::spawn(process(data));  // ERREUR!
}
```

## Solution
**Utilise `Arc` au lieu de `Rc`** :
```rust
use std::sync::Arc;

async fn process(data: Arc<String>) {
    println!("{}", data);
}

#[tokio::main]
async fn main() {
    let data = Arc::new(String::from("hello"));
    tokio::spawn(process(data));
}
```

**Ou `spawn_local` pour rester sur le meme thread** :
```rust
use tokio::task::LocalSet;

#[tokio::main]
async fn main() {
    let local = LocalSet::new();
    local.run_until(async {
        let data = Rc::new(String::from("hello"));
        tokio::task::spawn_local(async move {
            println!("{}", data);
        });
    }).await;
}
```

## Explication
| Type | Send? | Usage |
|------|-------|-------|
| `Rc<T>` | Non | Single-thread |
| `Arc<T>` | Oui | Multi-thread |
| `RefCell<T>` | Non | Single-thread |
| `Mutex<T>` | Oui | Multi-thread |

Une future est `Send` si tout ce qu'elle capture/utilise across `.await` est `Send`.

```rust
async fn bad() {
    let rc = Rc::new(5);
    some_async_fn().await;  // rc vit across await
    println!("{}", rc);     // donc future non-Send
}
```

## A retenir
- `spawn` requiert `Send` (peut changer de thread)
- `Rc` -> `Arc`, `RefCell` -> `Mutex`
- `spawn_local` si tu dois rester single-thread""",
    },
    {
        "topic": "async",
        "difficulty": "intermediaire",
        "user": "C'est quoi la difference entre `async` et les threads ?",
        "assistant": """## TL;DR
Les threads sont preemptifs et couteux, async est cooperatif et leger. Async est ideal pour l'I/O, threads pour le CPU.

## Probleme
Quand utiliser async vs threads ?

## Solution
**Async** - milliers de taches I/O :
```rust
#[tokio::main]
async fn main() {
    let mut handles = vec![];

    // 10000 "taches" legeres
    for i in 0..10000 {
        handles.push(tokio::spawn(async move {
            tokio::time::sleep(Duration::from_millis(100)).await;
            i
        }));
    }

    for handle in handles {
        let _ = handle.await;
    }
}
```

**Threads** - travail CPU intensif :
```rust
use std::thread;

fn main() {
    let handles: Vec<_> = (0..8)
        .map(|i| {
            thread::spawn(move || {
                heavy_computation(i)
            })
        })
        .collect();

    for handle in handles {
        let _ = handle.join();
    }
}
```

## Explication
| Aspect | Async | Threads |
|--------|-------|---------|
| Cout creation | ~few bytes | ~1MB stack |
| Switching | Cooperatif (.await) | Preemptif (OS) |
| Parallelisme CPU | Non* | Oui |
| Ideal pour | I/O (reseau, fichiers) | Calcul CPU |

*Async peut utiliser plusieurs threads via le runtime.

**Combiner les deux** :
```rust
#[tokio::main]
async fn main() {
    // Bloque le thread async -> mauvais
    // let result = heavy_computation();

    // Delegue a un thread dedie
    let result = tokio::task::spawn_blocking(|| {
        heavy_computation()
    }).await.unwrap();
}
```

## A retenir
- Async pour I/O-bound (reseau, fichiers)
- Threads pour CPU-bound (calculs)
- `spawn_blocking` pour mixer les deux""",
    },
    {
        "topic": "async",
        "difficulty": "debutant",
        "user": "Comment faire une requete HTTP async en Rust ?",
        "assistant": """## TL;DR
Utilise la crate `reqwest` qui fournit un client HTTP async simple.

## Probleme
Tu veux faire des requetes HTTP sans bloquer.

## Solution
```toml
# Cargo.toml
[dependencies]
tokio = { version = "1", features = ["full"] }
reqwest = { version = "0.11", features = ["json"] }
serde = { version = "1", features = ["derive"] }
```

```rust
use serde::Deserialize;

#[derive(Deserialize, Debug)]
struct User {
    login: String,
    id: u64,
}

#[tokio::main]
async fn main() -> Result<(), reqwest::Error> {
    // GET simple
    let body = reqwest::get("https://api.github.com/users/rust-lang")
        .await?
        .text()
        .await?;
    println!("Response: {}", body);

    // GET avec deserialization JSON
    let user: User = reqwest::get("https://api.github.com/users/rust-lang")
        .await?
        .json()
        .await?;
    println!("User: {:?}", user);

    // POST
    let client = reqwest::Client::new();
    let res = client.post("https://httpbin.org/post")
        .json(&serde_json::json!({"key": "value"}))
        .send()
        .await?;
    println!("Status: {}", res.status());

    Ok(())
}
```

## Explication
Chaque etape est async :
1. `get()` / `post()` : prepare la requete
2. `send().await` : envoie et attend la reponse
3. `text().await` / `json().await` : lit le body

**Avec timeout** :
```rust
let client = reqwest::Client::builder()
    .timeout(Duration::from_secs(10))
    .build()?;
```

## A retenir
- `reqwest` pour HTTP async
- Chaque `.await` est un point de suspension
- `json()` deserialise avec serde""",
    },
    {
        "topic": "async",
        "difficulty": "avance",
        "user": "Comment implementer un stream async custom ?",
        "assistant": """## TL;DR
Implemente le trait `Stream` de `futures` ou utilise `async_stream` pour une syntaxe plus simple.

## Probleme
Tu veux creer un iterateur asynchrone qui produit des valeurs au fil du temps.

## Solution
**Avec `async_stream`** (simple) :
```rust
use async_stream::stream;
use futures::StreamExt;
use tokio::time::{sleep, Duration};

fn countdown(from: u32) -> impl futures::Stream<Item = u32> {
    stream! {
        for i in (1..=from).rev() {
            sleep(Duration::from_secs(1)).await;
            yield i;
        }
    }
}

#[tokio::main]
async fn main() {
    let mut stream = std::pin::pin!(countdown(5));

    while let Some(n) = stream.next().await {
        println!("{}", n);
    }
}
```

**Implementation manuelle** :
```rust
use std::pin::Pin;
use std::task::{Context, Poll};
use futures::Stream;

struct Counter {
    count: u32,
    max: u32,
}

impl Stream for Counter {
    type Item = u32;

    fn poll_next(
        mut self: Pin<&mut Self>,
        _cx: &mut Context<'_>
    ) -> Poll<Option<Self::Item>> {
        self.count += 1;
        if self.count <= self.max {
            Poll::Ready(Some(self.count))
        } else {
            Poll::Ready(None)
        }
    }
}
```

## Explication
- `Stream` est l'equivalent async de `Iterator`
- `yield` dans `stream!` produit une valeur
- `poll_next` retourne `Poll::Ready(Some(x))`, `Poll::Ready(None)`, ou `Poll::Pending`

**Combinateurs utiles** :
```rust
stream
    .map(|x| x * 2)
    .filter(|x| futures::future::ready(*x > 5))
    .take(10)
    .collect::<Vec<_>>()
    .await
```

## A retenir
- `async_stream` pour la creation simple
- `StreamExt` pour les combinateurs
- Pin requis pour les streams""",
    },
]

# ============================================================================
# M9 Part 2: Exercices et exemples supplementaires
# ============================================================================

LIFETIMES_EXERCISES = [
    {
        "topic": "lifetimes",
        "difficulty": "debutant",
        "user": "Un exercice simple sur les lifetimes avec une fonction.",
        "assistant": """## TL;DR
Exercice : completer les annotations de lifetime pour une fonction qui retourne la plus courte de deux chaines.

## Probleme
Tu dois annoter correctement les lifetimes.

## Solution
**Exercice : Plus courte chaine**

```rust
// TODO: Ajoute les annotations de lifetime
fn shorter(s1: &str, s2: &str) -> &str {
    if s1.len() <= s2.len() { s1 } else { s2 }
}

fn main() {
    let s1 = String::from("hello");
    let s2 = String::from("hi");
    let result = shorter(&s1, &s2);
    println!("Shorter: {}", result);
}
```

**Solution** :
```rust
fn shorter<'a>(s1: &'a str, s2: &'a str) -> &'a str {
    if s1.len() <= s2.len() { s1 } else { s2 }
}

fn main() {
    let s1 = String::from("hello");
    let s2 = String::from("hi");
    let result = shorter(&s1, &s2);
    println!("Shorter: {}", result);  // "hi"
}
```

## Explication
- `'a` indique que les deux entrees et la sortie partagent la meme lifetime
- Le resultat sera valide tant que s1 ET s2 sont valides
- Sans annotation, le compilateur ne sait pas quelle reference sera retournee

## A retenir
- Annoter quand plusieurs references en entree et une en sortie
- `'a` lie la duree de la sortie aux entrees
- Syntaxe : `<'a>` apres le nom de fonction""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "intermediaire",
        "user": "Un exercice sur les lifetimes avec une struct.",
        "assistant": """## TL;DR
Exercice : creer une struct qui stocke une reference vers un texte et implementer une methode.

## Probleme
Tu dois creer une struct avec une reference et gerer les lifetimes correctement.

## Solution
**Exercice : Highlighter**

```rust
// TODO: Ajoute les lifetimes
struct Highlighter {
    text: &str,
    pattern: &str,
}

impl Highlighter {
    fn new(text: &str, pattern: &str) -> Self {
        Highlighter { text, pattern }
    }

    // Retourne le texte avec le pattern en majuscules
    fn highlight(&self) -> String {
        self.text.replace(self.pattern, &self.pattern.to_uppercase())
    }
}
```

**Solution** :
```rust
struct Highlighter<'a> {
    text: &'a str,
    pattern: &'a str,
}

impl<'a> Highlighter<'a> {
    fn new(text: &'a str, pattern: &'a str) -> Self {
        Highlighter { text, pattern }
    }

    fn highlight(&self) -> String {
        self.text.replace(self.pattern, &self.pattern.to_uppercase())
    }
}

fn main() {
    let text = "hello world, hello rust";
    let h = Highlighter::new(text, "hello");
    println!("{}", h.highlight());
    // "HELLO world, HELLO rust"
}
```

## Explication
- `Highlighter<'a>` : la struct a un parametre de lifetime
- `impl<'a> Highlighter<'a>` : les methodes heritent de la lifetime
- `highlight` retourne `String` (owned), pas besoin de lifetime en sortie

## A retenir
- Struct avec reference = lifetime obligatoire
- La struct ne peut pas survivre aux donnees referencees
- Retourner owned si possible pour simplifier""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "avance",
        "user": "Un exercice avance sur les lifetimes multiples.",
        "assistant": """## TL;DR
Exercice : une struct avec deux references de lifetimes differentes.

## Probleme
Parfois tu as besoin de lifetimes independantes.

## Solution
**Exercice : Context avec config et data**

```rust
// TODO: Cette struct a besoin de deux lifetimes
// car config et data peuvent avoir des durees differentes
struct Context {
    config: &str,   // Configuration longue duree
    data: &str,     // Donnees courte duree
}

impl Context {
    fn new(config: &str, data: &str) -> Self { todo!() }
    fn process(&self) -> String { todo!() }
}
```

**Solution** :
```rust
struct Context<'cfg, 'data> {
    config: &'cfg str,
    data: &'data str,
}

impl<'cfg, 'data> Context<'cfg, 'data> {
    fn new(config: &'cfg str, data: &'data str) -> Self {
        Context { config, data }
    }

    fn process(&self) -> String {
        format!("[{}] {}", self.config, self.data)
    }
}

fn main() {
    let config = String::from("DEBUG");

    for data in ["item1", "item2", "item3"] {
        let ctx = Context::new(&config, data);
        println!("{}", ctx.process());
    }
}
```

## Explication
Pourquoi deux lifetimes :
- `config` vit pour toute la boucle
- `data` change a chaque iteration

Avec une seule lifetime, on serait trop restrictif.

**Contrainte entre lifetimes** :
```rust
struct Bounded<'a, 'b: 'a> {  // 'b outlives 'a
    long: &'b str,
    short: &'a str,
}
```

## A retenir
- Plusieurs lifetimes si les durees sont independantes
- `'a: 'b` signifie 'a vit au moins aussi longtemps que 'b
- Plus de flexibilite mais plus de complexite""",
    },
]

BORROWING_EXERCISES = [
    {
        "topic": "borrowing",
        "difficulty": "debutant",
        "user": "Un exercice sur le borrowing immuable.",
        "assistant": """## TL;DR
Exercice : ecrire des fonctions qui empruntent des donnees sans les modifier.

## Probleme
Tu dois passer des donnees a des fonctions sans transferer l'ownership.

## Solution
**Exercice : Statistiques de liste**

```rust
// TODO: Implemente ces fonctions avec le bon type de parametre
fn len(/* ??? */) -> usize { todo!() }
fn first(/* ??? */) -> Option<&i32> { todo!() }
fn contains(/* ??? */, value: i32) -> bool { todo!() }

fn main() {
    let numbers = vec![10, 20, 30, 40, 50];

    println!("Length: {}", len(&numbers));
    println!("First: {:?}", first(&numbers));
    println!("Contains 30: {}", contains(&numbers, 30));

    // numbers doit toujours etre utilisable
    println!("Original: {:?}", numbers);
}
```

**Solution** :
```rust
fn len(list: &[i32]) -> usize {
    list.len()
}

fn first(list: &[i32]) -> Option<&i32> {
    list.first()
}

fn contains(list: &[i32], value: i32) -> bool {
    list.iter().any(|&x| x == value)
}

fn main() {
    let numbers = vec![10, 20, 30, 40, 50];
    println!("Length: {}", len(&numbers));        // 5
    println!("First: {:?}", first(&numbers));     // Some(10)
    println!("Contains 30: {}", contains(&numbers, 30));  // true
    println!("Original: {:?}", numbers);  // Toujours la!
}
```

## Explication
- `&[i32]` accepte `&Vec<i32>` et `&[i32]`
- Emprunt immuable = pas de modification
- La valeur originale reste intacte

## A retenir
- `&[T]` pour les fonctions de lecture
- Pas besoin de mutable si on ne modifie pas
- L'appelant garde l'ownership""",
    },
    {
        "topic": "borrowing",
        "difficulty": "intermediaire",
        "user": "Un exercice sur le borrowing mutable.",
        "assistant": """## TL;DR
Exercice : modifier des donnees via une reference mutable.

## Probleme
Tu dois modifier des donnees sans en prendre l'ownership.

## Solution
**Exercice : Operations sur vecteur**

```rust
// TODO: Implemente ces fonctions avec &mut
fn double_all(/* ??? */) { todo!() }
fn remove_negatives(/* ??? */) { todo!() }
fn sort_desc(/* ??? */) { todo!() }

fn main() {
    let mut numbers = vec![3, -1, 4, -1, 5, -9, 2, 6];

    double_all(&mut numbers);
    println!("Doubled: {:?}", numbers);

    remove_negatives(&mut numbers);
    println!("No negatives: {:?}", numbers);

    sort_desc(&mut numbers);
    println!("Sorted desc: {:?}", numbers);
}
```

**Solution** :
```rust
fn double_all(list: &mut [i32]) {
    for x in list.iter_mut() {
        *x *= 2;
    }
}

fn remove_negatives(list: &mut Vec<i32>) {
    list.retain(|&x| x >= 0);
}

fn sort_desc(list: &mut [i32]) {
    list.sort_by(|a, b| b.cmp(a));
}

fn main() {
    let mut numbers = vec![3, -1, 4, -1, 5, -9, 2, 6];

    double_all(&mut numbers);
    println!("Doubled: {:?}", numbers);  // [6, -2, 8, -2, 10, -18, 4, 12]

    remove_negatives(&mut numbers);
    println!("No negatives: {:?}", numbers);  // [6, 8, 10, 4, 12]

    sort_desc(&mut numbers);
    println!("Sorted desc: {:?}", numbers);  // [12, 10, 8, 6, 4]
}
```

## Explication
- `&mut [T]` permet de modifier les elements
- `&mut Vec<T>` permet aussi de changer la taille (push, remove)
- `iter_mut()` pour iterer avec modification

## A retenir
- `&mut [T]` pour modifier les elements
- `&mut Vec<T>` si besoin de resize
- Une seule reference mutable a la fois""",
    },
    {
        "topic": "borrowing",
        "difficulty": "avance",
        "user": "Un exercice sur le split borrowing.",
        "assistant": """## TL;DR
Exercice : emprunter differentes parties d'une structure simultanement.

## Probleme
Comment modifier deux champs d'une struct en meme temps ?

## Solution
**Exercice : Player avec stats**

```rust
struct Player {
    health: i32,
    mana: i32,
    name: String,
}

impl Player {
    // TODO: Retourne des references mutables vers health et mana
    // simultanement (split borrow)
    fn get_stats_mut(&mut self) -> (???, ???) {
        todo!()
    }
}

fn heal_and_restore(player: &mut Player) {
    // On veut modifier health ET mana en meme temps
    todo!()
}
```

**Solution** :
```rust
struct Player {
    health: i32,
    mana: i32,
    name: String,
}

impl Player {
    fn get_stats_mut(&mut self) -> (&mut i32, &mut i32) {
        (&mut self.health, &mut self.mana)
    }
}

fn heal_and_restore(player: &mut Player) {
    let (health, mana) = player.get_stats_mut();
    *health = (*health + 50).min(100);
    *mana = (*mana + 30).min(100);
}

fn main() {
    let mut player = Player {
        health: 30,
        mana: 20,
        name: String::from("Hero"),
    };

    heal_and_restore(&mut player);
    println!("Health: {}, Mana: {}", player.health, player.mana);
    // Health: 80, Mana: 50
}
```

## Explication
Rust autorise le "split borrowing" : emprunter differentes parties disjoint d'une structure.

```rust
let mut arr = [1, 2, 3, 4];
let (left, right) = arr.split_at_mut(2);
// left = &mut [1, 2], right = &mut [3, 4]
// Les deux sont des &mut disjoints
```

Le compilateur peut prouver que les emprunts ne se chevauchent pas.

## A retenir
- Split borrow = emprunts disjoints autorises
- `split_at_mut` pour les slices
- Champs differents d'une struct = OK""",
    },
]

CONCURRENCY_EXAMPLES = [
    {
        "topic": "concurrency",
        "difficulty": "intermediaire",
        "user": "Comment partager des donnees entre threads en Rust ?",
        "assistant": """## TL;DR
Utilise `Arc<Mutex<T>>` pour partager des donnees modifiables entre threads. `Arc` pour le partage, `Mutex` pour l'acces exclusif.

## Probleme
Les threads ont besoin d'acceder aux memes donnees de maniere sure.

## Solution
```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];

    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            let mut num = counter.lock().unwrap();
            *num += 1;
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Result: {}", *counter.lock().unwrap());  // 10
}
```

## Explication
**Arc** (Atomic Reference Counting) :
- Permet plusieurs propriétaires
- Thread-safe (compteur atomique)
- `Arc::clone` incremente le compteur

**Mutex** (Mutual Exclusion) :
- Un seul thread a l'acces a la fois
- `lock()` bloque jusqu'a disponibilite
- `MutexGuard` libere le lock automatiquement

**Pourquoi pas `Rc<RefCell<T>>` ?**
- `Rc` n'est pas thread-safe (compteur non-atomique)
- `RefCell` n'est pas thread-safe

## A retenir
- `Arc` pour partager entre threads
- `Mutex` pour modifier de maniere exclusive
- `Arc<Mutex<T>>` est le pattern standard""",
    },
    {
        "topic": "concurrency",
        "difficulty": "intermediaire",
        "user": "Comment utiliser les channels pour communiquer entre threads ?",
        "assistant": """## TL;DR
Les channels permettent d'envoyer des messages entre threads. `mpsc` = multiple producers, single consumer.

## Probleme
Tu veux que des threads communiquent sans partager de memoire.

## Solution
```rust
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    let (tx, rx) = mpsc::channel();

    // Thread producteur
    let tx1 = tx.clone();
    thread::spawn(move || {
        for i in 1..=5 {
            tx1.send(format!("Thread1: {}", i)).unwrap();
            thread::sleep(Duration::from_millis(100));
        }
    });

    // Autre producteur
    thread::spawn(move || {
        for i in 1..=5 {
            tx.send(format!("Thread2: {}", i)).unwrap();
            thread::sleep(Duration::from_millis(150));
        }
    });

    // Consommateur (thread principal)
    for received in rx {
        println!("Got: {}", received);
    }
}
```

## Explication
**Types de channels** :
- `mpsc::channel()` : capacite illimitee (peut bloquer sur send)
- `mpsc::sync_channel(n)` : buffer de taille n

**Methodes** :
```rust
tx.send(value)      // Envoie (erreur si rx dropped)
rx.recv()           // Bloque jusqu'a reception
rx.try_recv()       // Non-bloquant
rx.recv_timeout(d)  // Avec timeout
```

**Ownership** :
- `send` prend l'ownership de la valeur
- La valeur est transferee au receveur

## A retenir
- Channels pour communication par message
- `tx.clone()` pour plusieurs producteurs
- La boucle `for received in rx` termine quand tous les tx sont dropped""",
    },
    {
        "topic": "concurrency",
        "difficulty": "avance",
        "user": "Explique `RwLock` et quand l'utiliser au lieu de `Mutex`.",
        "assistant": """## TL;DR
`RwLock` permet plusieurs lecteurs OU un seul ecrivain. Plus performant que `Mutex` si tu as beaucoup de lectures.

## Probleme
Avec `Mutex`, meme les lectures sont exclusives. C'est inefficace si tu lis beaucoup plus que tu n'ecris.

## Solution
```rust
use std::sync::{Arc, RwLock};
use std::thread;

fn main() {
    let config = Arc::new(RwLock::new(vec!["setting1".to_string()]));

    let mut handles = vec![];

    // 5 lecteurs
    for i in 0..5 {
        let config = Arc::clone(&config);
        handles.push(thread::spawn(move || {
            let data = config.read().unwrap();
            println!("Reader {}: {:?}", i, *data);
        }));
    }

    // 1 ecrivain
    {
        let config = Arc::clone(&config);
        handles.push(thread::spawn(move || {
            let mut data = config.write().unwrap();
            data.push("setting2".to_string());
            println!("Writer added setting2");
        }));
    }

    for handle in handles {
        handle.join().unwrap();
    }
}
```

## Explication
| Operation | Mutex | RwLock |
|-----------|-------|--------|
| Lecture | Exclusive | Partagee |
| Ecriture | Exclusive | Exclusive |
| Plusieurs lecteurs | Non | Oui |

**Methodes RwLock** :
```rust
lock.read()   // RwLockReadGuard (plusieurs OK)
lock.write()  // RwLockWriteGuard (exclusif)
```

**Quand utiliser quoi** :
- `Mutex` : lectures et ecritures frequentes
- `RwLock` : beaucoup de lectures, peu d'ecritures
- Attention : `RwLock` peut causer starvation des ecrivains

## A retenir
- `RwLock` pour read-heavy workloads
- `read()` non-bloquant entre lecteurs
- `write()` attend que tous les lecteurs finissent""",
    },
]

SMART_POINTERS_EXAMPLES = [
    {
        "topic": "smart_pointers",
        "difficulty": "intermediaire",
        "user": "Comment eviter les cycles de references avec `Weak` ?",
        "assistant": """## TL;DR
`Weak<T>` est une reference qui ne compte pas dans le comptage. Utilise-le pour les back-references dans les structures cycliques.

## Probleme
`Rc<RefCell<T>>` avec des references mutuelles cree des memory leaks car le compteur ne tombe jamais a zero.

## Solution
```rust
use std::cell::RefCell;
use std::rc::{Rc, Weak};

struct Node {
    value: i32,
    parent: RefCell<Weak<Node>>,    // Weak pour le parent
    children: RefCell<Vec<Rc<Node>>>, // Rc pour les enfants
}

impl Node {
    fn new(value: i32) -> Rc<Self> {
        Rc::new(Node {
            value,
            parent: RefCell::new(Weak::new()),
            children: RefCell::new(vec![]),
        })
    }

    fn add_child(parent: &Rc<Node>, child: Rc<Node>) {
        *child.parent.borrow_mut() = Rc::downgrade(parent);
        parent.children.borrow_mut().push(child);
    }
}

fn main() {
    let root = Node::new(1);
    let child = Node::new(2);

    Node::add_child(&root, child.clone());

    // Acceder au parent depuis l'enfant
    if let Some(parent) = child.parent.borrow().upgrade() {
        println!("Parent value: {}", parent.value);
    }
}
```

## Explication
**Weak vs Rc** :
| Aspect | Rc | Weak |
|--------|-----|------|
| Compte dans strong_count | Oui | Non |
| Empeche la destruction | Oui | Non |
| Acces aux donnees | Direct | Via `upgrade()` |

**Methodes** :
```rust
Rc::downgrade(&rc)  // Rc -> Weak
weak.upgrade()      // Weak -> Option<Rc>
Rc::strong_count(&rc)
Rc::weak_count(&rc)
```

## A retenir
- `Weak` pour les back-references (parent, prev)
- `upgrade()` retourne `None` si la donnee est detruite
- Casse les cycles de references""",
    },
    {
        "topic": "smart_pointers",
        "difficulty": "intermediaire",
        "user": "Quand utiliser `Box<T>` vs juste `T` ?",
        "assistant": """## TL;DR
`Box<T>` alloue sur le heap. Utilise-le pour les types recursifs, les gros objets, ou le trait object.

## Probleme
Quand l'allocation heap est-elle necessaire ou benefique ?

## Solution
**1. Types recursifs** (taille inconnue a la compilation) :
```rust
// ERREUR: taille infinie
// enum List { Cons(i32, List), Nil }

// OK avec Box
enum List {
    Cons(i32, Box<List>),
    Nil,
}

fn main() {
    let list = List::Cons(1,
        Box::new(List::Cons(2,
            Box::new(List::Nil))));
}
```

**2. Gros objets** (eviter les copies stack) :
```rust
struct BigData {
    data: [u8; 1_000_000],  // 1MB
}

fn main() {
    // Sur le heap, pas la stack
    let big = Box::new(BigData { data: [0; 1_000_000] });
}
```

**3. Trait objects** (polymorphisme dynamique) :
```rust
trait Animal {
    fn speak(&self);
}

fn get_animal(dog: bool) -> Box<dyn Animal> {
    if dog {
        Box::new(Dog)
    } else {
        Box::new(Cat)
    }
}
```

## Explication
| Aspect | Stack (`T`) | Heap (`Box<T>`) |
|--------|-------------|-----------------|
| Allocation | Automatique | Explicite |
| Taille | Connue compile | Peut etre dynamique |
| Performance | Plus rapide | Indirection |

`Box` implemente `Deref` donc s'utilise comme la valeur directement.

## A retenir
- `Box` pour recursion et types de taille inconnue
- `Box<dyn Trait>` pour le polymorphisme dynamique
- Prefer stack quand possible (plus rapide)""",
    },
]

ERROR_HANDLING_EXAMPLES = [
    {
        "topic": "error_handling",
        "difficulty": "intermediaire",
        "user": "Comment creer un type d'erreur custom avec `thiserror` ?",
        "assistant": """## TL;DR
`thiserror` genere automatiquement les implementations de `Error` et `Display` via des macros derive.

## Probleme
Tu veux des erreurs personnalisees sans boilerplate.

## Solution
```toml
# Cargo.toml
[dependencies]
thiserror = "1.0"
```

```rust
use thiserror::Error;

#[derive(Error, Debug)]
enum AppError {
    #[error("Failed to read config file: {0}")]
    ConfigRead(#[from] std::io::Error),

    #[error("Invalid value '{value}' for field '{field}'")]
    InvalidValue { field: String, value: String },

    #[error("User not found: {0}")]
    UserNotFound(u64),

    #[error("Permission denied")]
    PermissionDenied,
}

fn load_config() -> Result<String, AppError> {
    let content = std::fs::read_to_string("config.txt")?;
    Ok(content)
}

fn validate(field: &str, value: &str) -> Result<(), AppError> {
    if value.is_empty() {
        return Err(AppError::InvalidValue {
            field: field.to_string(),
            value: value.to_string(),
        });
    }
    Ok(())
}
```

## Explication
**Attributs thiserror** :
- `#[error("...")]` : message d'affichage
- `#[from]` : impl `From<T>` pour conversion auto avec `?`
- `#[source]` : chaine d'erreur (cause)

**Avec source explicite** :
```rust
#[derive(Error, Debug)]
enum DbError {
    #[error("Connection failed")]
    Connection(#[source] std::io::Error),
}
```

## A retenir
- `thiserror` pour les bibliotheques
- `#[from]` pour convertir automatiquement avec `?`
- Messages clairs avec contexte""",
    },
    {
        "topic": "error_handling",
        "difficulty": "debutant",
        "user": "C'est quoi la difference entre `unwrap()`, `expect()`, et `?` ?",
        "assistant": """## TL;DR
- `unwrap()` : extrait la valeur ou panic
- `expect("msg")` : comme unwrap avec message custom
- `?` : propage l'erreur a l'appelant

## Probleme
Tu dois extraire une valeur de `Result` ou `Option`.

## Solution
**`unwrap()`** - panic si erreur :
```rust
let file = File::open("config.txt").unwrap();
// Panic avec message generique si erreur
```

**`expect()`** - panic avec message :
```rust
let file = File::open("config.txt")
    .expect("Failed to open config.txt");
// Panic avec ton message
```

**`?`** - propage l'erreur :
```rust
fn read_config() -> Result<String, io::Error> {
    let content = fs::read_to_string("config.txt")?;
    Ok(content)
}
// Retourne Err si ca echoue, continue sinon
```

## Explication
| Methode | Erreur | Succes |
|---------|--------|--------|
| `unwrap()` | Panic | Valeur |
| `expect()` | Panic + msg | Valeur |
| `?` | Return Err | Valeur |

**Quand utiliser quoi** :
```rust
// Tests, prototypes - unwrap OK
let result = parse("123").unwrap();

// Code de production - expect avec contexte
let config = load_config().expect("Config required");

// Fonctions faillibles - propager avec ?
fn process() -> Result<(), Error> {
    let data = fetch_data()?;
    Ok(())
}
```

## A retenir
- `unwrap` : tests/prototypes uniquement
- `expect` : cas "impossibles" documentes
- `?` : propagation propre en production""",
    },
]

TRAITS_EXAMPLES = [
    {
        "topic": "traits",
        "difficulty": "intermediaire",
        "user": "Comment implementer un trait pour un type externe (orphan rule) ?",
        "assistant": """## TL;DR
Tu ne peux pas implementer un trait externe pour un type externe. Cree un newtype wrapper.

## Probleme
```rust
// ERREUR: ni Vec ni Display ne sont definis dans ton crate
impl std::fmt::Display for Vec<String> {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "[{}]", self.join(", "))
    }
}
```

## Solution
**Newtype pattern** :
```rust
struct StringList(Vec<String>);

impl std::fmt::Display for StringList {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "[{}]", self.0.join(", "))
    }
}

impl std::ops::Deref for StringList {
    type Target = Vec<String>;
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

fn main() {
    let list = StringList(vec!["a".into(), "b".into()]);
    println!("{}", list);  // [a, b]
    println!("Len: {}", list.len());  // Deref vers Vec
}
```

## Explication
**Orphan rule** : Au moins un des deux (trait ou type) doit etre defini dans ton crate.

| Trait | Type | Autorise |
|-------|------|----------|
| Ton trait | Tout type | Oui |
| Tout trait | Ton type | Oui |
| Externe | Externe | Non |

**Newtype avantages** :
- Contourne l'orphan rule
- Zero-cost abstraction
- Peut ajouter des contraintes

**Deref** permet d'utiliser les methodes du type interne.

## A retenir
- Newtype = `struct Wrapper(Inner)`
- Implemente `Deref` pour l'ergonomie
- Zero overhead a l'execution""",
    },
    {
        "topic": "traits",
        "difficulty": "avance",
        "user": "Explique les associated types vs les generics sur un trait.",
        "assistant": """## TL;DR
Associated types : un seul type par implementation. Generics : plusieurs implementations possibles pour le meme type.

## Probleme
Quand utiliser `type Item` vs `trait Foo<T>` ?

## Solution
**Associated type** (un seul par impl) :
```rust
trait Iterator {
    type Item;  // Defini une fois par impl
    fn next(&mut self) -> Option<Self::Item>;
}

struct Counter;
impl Iterator for Counter {
    type Item = u32;
    fn next(&mut self) -> Option<u32> { Some(1) }
}
```

**Generic** (plusieurs impl possibles) :
```rust
trait From<T> {
    fn from(value: T) -> Self;
}

// String peut etre creee depuis plusieurs types
impl From<&str> for String { ... }
impl From<Vec<u8>> for String { ... }
```

## Explication
**Quand utiliser quoi** :

| Aspect | Associated Type | Generic |
|--------|-----------------|---------|
| Implementations | Une par type | Plusieurs |
| Syntaxe d'usage | `T::Item` | `T: From<X>` |
| Inference | Facile | Peut etre ambigue |

**Exemple combine** :
```rust
trait Graph {
    type Node;
    type Edge;

    fn edges(&self, node: &Self::Node) -> Vec<Self::Edge>;
}
```

Un Graph a UN type de Node et UN type de Edge, pas plusieurs.

**Generic sur associated type** (GATs) :
```rust
trait StreamingIterator {
    type Item<'a> where Self: 'a;
    fn next<'a>(&'a mut self) -> Option<Self::Item<'a>>;
}
```

## A retenir
- Associated type : "quel est LE type ?"
- Generic : "fonctionne avec PLUSIEURS types"
- Un type impl une fois avec associated, N fois avec generic""",
    },
]

ITERATORS_EXAMPLES = [
    {
        "topic": "iterators",
        "difficulty": "intermediaire",
        "user": "Comment implementer le trait `Iterator` pour un type custom ?",
        "assistant": """## TL;DR
Implemente `Iterator` avec `type Item` et `fn next()`. C'est tout ce qui est requis.

## Probleme
Tu veux creer ton propre iterateur.

## Solution
```rust
struct Range {
    current: i32,
    end: i32,
}

impl Range {
    fn new(start: i32, end: i32) -> Self {
        Range { current: start, end }
    }
}

impl Iterator for Range {
    type Item = i32;

    fn next(&mut self) -> Option<Self::Item> {
        if self.current < self.end {
            let value = self.current;
            self.current += 1;
            Some(value)
        } else {
            None
        }
    }
}

fn main() {
    let range = Range::new(1, 5);

    for n in range {
        println!("{}", n);  // 1, 2, 3, 4
    }

    // Ou avec les combinateurs
    let sum: i32 = Range::new(1, 5).sum();
    println!("Sum: {}", sum);  // 10
}
```

## Explication
**Minimum requis** :
- `type Item` : le type des elements
- `fn next()` : retourne `Some(item)` ou `None`

**Methodes gratuites** une fois `next` implemente :
```rust
.map(), .filter(), .fold(), .collect()
.sum(), .count(), .take(), .skip()
// ... et ~70 autres!
```

**Pour les references** :
```rust
impl<'a> Iterator for MyIter<'a> {
    type Item = &'a T;
    // ...
}
```

## A retenir
- Seul `next()` est requis
- Les autres methodes sont fournies par defaut
- `None` signale la fin de l'iteration""",
    },
    {
        "topic": "iterators",
        "difficulty": "avance",
        "user": "Explique `collect()` et comment ca marche avec les types de retour.",
        "assistant": """## TL;DR
`collect()` transforme un iterateur en collection. Le type de retour determine la collection creee via `FromIterator`.

## Probleme
Comment `collect()` sait-il quel type creer ?

## Solution
**Annotation de type** :
```rust
let v: Vec<i32> = (1..5).collect();
let s: String = ['a', 'b', 'c'].iter().collect();
let set: HashSet<i32> = vec![1, 2, 2, 3].into_iter().collect();
```

**Turbofish** :
```rust
let v = (1..5).collect::<Vec<_>>();
let s = ['a', 'b', 'c'].iter().collect::<String>();
```

**Collect en Result** :
```rust
let results: Vec<Result<i32, _>> = vec!["1", "2", "x"]
    .iter()
    .map(|s| s.parse::<i32>())
    .collect();
// [Ok(1), Ok(2), Err(...)]

// Ou inverser Result et Vec :
let result: Result<Vec<i32>, _> = vec!["1", "2", "3"]
    .iter()
    .map(|s| s.parse::<i32>())
    .collect();
// Ok([1, 2, 3])
```

## Explication
`collect()` utilise le trait `FromIterator` :
```rust
trait FromIterator<A> {
    fn from_iter<I: IntoIterator<Item = A>>(iter: I) -> Self;
}
```

Types implementant `FromIterator` :
- `Vec<T>`, `VecDeque<T>`
- `String` (depuis `char` ou `&str`)
- `HashMap<K, V>` (depuis tuples)
- `Result<Vec<T>, E>` (short-circuit sur erreur)

## A retenir
- Le type annote determine la collection
- `collect::<Type<_>>()` avec turbofish
- `Result<Collection, E>` collecte jusqu'a la premiere erreur""",
    },
]

# ============================================================================
# M9 Part 3: Plus d'exemples pour atteindre 200+
# ============================================================================

MORE_LIFETIMES = [
    {
        "topic": "lifetimes",
        "difficulty": "debutant",
        "user": "Pourquoi les litteraux de chaines ont la lifetime `'static` ?",
        "assistant": """## TL;DR
Les litteraux sont stockes dans le binaire du programme et existent pour toute son execution.

## Probleme
Comprendre d'ou vient `'static` pour `"hello"`.

## Solution
```rust
let s1: &'static str = "hello";  // Explicite
let s2 = "world";                 // Infere comme &'static str

fn get_greeting() -> &'static str {
    "Hello!"  // OK: vit pour toujours
}
```

## Explication
Le compilateur place les litteraux dans une section read-only du binaire :
- Ils existent avant `main()`
- Ils existent apres `main()`
- Pas d'allocation heap

```rust
// Equivalent conceptuel
static HELLO: &str = "hello";
```

**Attention** - `'static` ne veut pas dire "sur le heap" :
```rust
// Ceci n'est PAS 'static
fn bad() -> &'static str {
    let s = String::from("temp");
    &s  // ERREUR: s sera detruite
}
```

## A retenir
- Litteraux `"..."` = `&'static str`
- Stockes dans le binaire, pas le heap
- `'static` = duree de vie du programme""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "intermediaire",
        "user": "Comment retourner une reference conditionnellement depuis deux sources ?",
        "assistant": """## TL;DR
Utilise la meme lifetime pour les deux sources et le retour. Le retour sera valide tant que les deux sources sont valides.

## Probleme
Retourner une reference qui vient soit de A, soit de B selon une condition.

## Solution
```rust
fn choose<'a>(condition: bool, a: &'a str, b: &'a str) -> &'a str {
    if condition { a } else { b }
}

fn main() {
    let x = String::from("first");
    let y = String::from("second");

    let result = choose(true, &x, &y);
    println!("{}", result);
    // x et y doivent rester valides tant qu'on utilise result
}
```

**Avec des lifetimes differentes** (plus flexible) :
```rust
fn choose_flex<'a, 'b>(condition: bool, a: &'a str, b: &'b str) -> &'a str
where
    'b: 'a,  // b vit au moins aussi longtemps que a
{
    if condition { a } else { b }
}
```

## Explication
Quand le compilateur voit `&'a str` en retour et deux `&'a str` en entree :
- Il comprend que le retour peut etre l'un ou l'autre
- Il exige que les deux vivent assez longtemps

Le cas `'b: 'a` permet des lifetimes differentes tant que b >= a.

## A retenir
- Meme lifetime = le retour vit tant que les deux sont valides
- `'b: 'a` pour plus de flexibilite
- Le compilateur ne sait pas quelle branche sera prise""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "avance",
        "user": "Comment utiliser les Higher-Ranked Trait Bounds (HRTB) ?",
        "assistant": """## TL;DR
`for<'a>` signifie "pour toute lifetime 'a". Utilise-le quand une fonction doit fonctionner avec des references de durees arbitraires.

## Probleme
Tu veux passer une closure qui fonctionne avec n'importe quelle lifetime.

## Solution
```rust
fn apply_to_all<F>(items: &[String], f: F)
where
    F: for<'a> Fn(&'a str) -> &'a str,
{
    for item in items {
        println!("{}", f(item));
    }
}

fn main() {
    let items = vec![
        String::from("  hello  "),
        String::from("  world  "),
    ];

    apply_to_all(&items, |s| s.trim());
}
```

**Sans HRTB, ca ne compile pas** :
```rust
// ERREUR: la closure a une lifetime concrete
fn apply<'b, F>(items: &[String], f: F)
where
    F: Fn(&'b str) -> &'b str,
{
    // La lifetime 'b est fixee, pas flexible
}
```

## Explication
`for<'a> Fn(&'a str) -> &'a str` signifie :
- Pour TOUTE lifetime 'a choisie par l'appelant
- La fonction accepte `&'a str` et retourne `&'a str`

C'est comme un generic sur les lifetimes au niveau du trait bound.

**Cas d'usage** :
- Closures qui transforment des references
- Traits avec methodes parametrees par lifetime
- APIs generiques sur les emprunts

## A retenir
- `for<'a>` = "pour toute lifetime"
- Necessite pour closures avec refs en entree ET sortie
- Syntaxe avancee mais parfois indispensable""",
    },
]

MORE_BORROWING = [
    {
        "topic": "borrowing",
        "difficulty": "debutant",
        "user": "Pourquoi `String` et `&str` sont differents ? Quand utiliser lequel ?",
        "assistant": """## TL;DR
`String` possede ses donnees (heap), `&str` emprunte. Utilise `String` pour stocker, `&str` pour lire.

## Probleme
Comprendre la difference entre ces deux types de chaines.

## Solution
**`String`** - owned, modifiable :
```rust
let mut s = String::from("hello");
s.push_str(" world");  // OK: on possede les donnees
println!("{}", s);     // "hello world"
```

**`&str`** - emprunte, lecture seule :
```rust
let s: &str = "hello";  // Litterale
let greeting: &str = &String::from("hi");  // Emprunt
// s.push_str("!");  // ERREUR: pas mutable
```

**En parametre de fonction** :
```rust
// Prefere &str - accepte String et &str
fn greet(name: &str) {
    println!("Hello, {}!", name);
}

greet("world");              // &str
greet(&String::from("you")); // &String -> &str
```

## Explication
| Aspect | String | &str |
|--------|--------|------|
| Ownership | Possede | Emprunte |
| Allocation | Heap | Peut etre stack/heap/static |
| Modifiable | Oui | Non |
| Taille | Dynamique | Fixe (pour cette ref) |

**Conversions** :
```rust
let owned: String = "hello".to_string();
let borrowed: &str = &owned;
```

## A retenir
- `String` pour stocker des donnees
- `&str` pour lire/passer en parametre
- `&str` est plus generique""",
    },
    {
        "topic": "borrowing",
        "difficulty": "intermediaire",
        "user": "Comment fonctionne la deref coercion ?",
        "assistant": """## TL;DR
Rust convertit automatiquement `&T` en `&U` si `T: Deref<Target=U>`. C'est pourquoi `&String` devient `&str`.

## Probleme
Pourquoi peut-on passer `&String` a une fonction qui attend `&str` ?

## Solution
```rust
fn print_len(s: &str) {
    println!("Length: {}", s.len());
}

fn main() {
    let owned = String::from("hello");
    let boxed = Box::new(String::from("world"));

    print_len(&owned);   // &String -> &str
    print_len(&*boxed);  // Explicite
    print_len(&boxed);   // &Box<String> -> &String -> &str
}
```

## Explication
**Chaine de Deref** :
```
Box<String> --Deref--> String --Deref--> str
&Box<String> -> &String -> &str
```

**Implementations standard** :
```rust
impl Deref for String {
    type Target = str;
}

impl<T> Deref for Box<T> {
    type Target = T;
}

impl<T> Deref for Vec<T> {
    type Target = [T];
}
```

**Implique automatiquement** :
- `&String` -> `&str`
- `&Vec<T>` -> `&[T]`
- `&Box<T>` -> `&T`

## A retenir
- Deref coercion = conversion automatique de references
- Fonctionne pour `&` et `&mut`
- Permet des APIs flexibles avec `&str`, `&[T]`""",
    },
    {
        "topic": "borrowing",
        "difficulty": "avance",
        "user": "Comment utiliser `Cow` (Copy on Write) ?",
        "assistant": """## TL;DR
`Cow<T>` peut etre soit emprunte soit owned. Clone seulement si modification necessaire.

## Probleme
Tu veux eviter les clones inutiles quand tu pourrais juste emprunter.

## Solution
```rust
use std::borrow::Cow;

fn process_text(text: &str) -> Cow<str> {
    if text.contains("bad") {
        // Modification necessaire -> clone
        Cow::Owned(text.replace("bad", "good"))
    } else {
        // Pas de modif -> emprunt
        Cow::Borrowed(text)
    }
}

fn main() {
    let clean = "hello world";
    let dirty = "bad word";

    // Pas de clone
    let result1 = process_text(clean);
    println!("{}", result1);

    // Clone seulement ici
    let result2 = process_text(dirty);
    println!("{}", result2);
}
```

## Explication
`Cow<'a, T>` ou T: ToOwned :
- `Borrowed(&'a T)` - reference
- `Owned(<T as ToOwned>::Owned)` - possede

**Methodes utiles** :
```rust
cow.to_mut()      // &mut, clone si necessaire
cow.into_owned()  // Owned, clone si emprunte
cow.is_borrowed() // bool
cow.is_owned()    // bool
```

**Cas d'usage** :
- Parsing avec modifications optionnelles
- APIs qui retournent parfois les donnees originales
- Optimisation des allocations

## A retenir
- `Cow` = Clone On Write
- Emprunte par defaut, clone si modifie
- Bon pour les transformations conditionnelles""",
    },
]

MORE_ASYNC = [
    {
        "topic": "async",
        "difficulty": "debutant",
        "user": "C'est quoi un `Future` en Rust ?",
        "assistant": """## TL;DR
Un `Future` represente une valeur qui sera disponible plus tard. C'est ce que retournent les fonctions `async`.

## Probleme
Comprendre le fondement de l'async en Rust.

## Solution
```rust
use std::future::Future;

// async fn cree un Future
async fn fetch_data() -> String {
    "data".to_string()
}

// Equivalent manuel (conceptuel)
fn fetch_data_manual() -> impl Future<Output = String> {
    async {
        "data".to_string()
    }
}

#[tokio::main]
async fn main() {
    // Le Future n'execute rien tant qu'on ne l'await pas
    let future = fetch_data();  // Pas encore execute!
    let data = future.await;    // Execute maintenant
    println!("{}", data);
}
```

## Explication
**Trait Future** :
```rust
trait Future {
    type Output;
    fn poll(self: Pin<&mut Self>, cx: &mut Context) -> Poll<Self::Output>;
}

enum Poll<T> {
    Ready(T),   // Valeur disponible
    Pending,    // Pas encore pret
}
```

**Les Futures sont lazy** :
```rust
let f = async { println!("Hello"); };
// Rien ne s'affiche!
f.await;  // Maintenant "Hello" s'affiche
```

Le runtime (tokio, async-std) appelle `poll` jusqu'a `Ready`.

## A retenir
- Future = promesse de valeur future
- Lazy : ne s'execute qu'avec `.await`
- Le runtime gere le polling""",
    },
    {
        "topic": "async",
        "difficulty": "intermediaire",
        "user": "Comment faire des timeouts en async ?",
        "assistant": """## TL;DR
Utilise `tokio::time::timeout` pour limiter le temps d'attente d'une future.

## Probleme
Tu veux abandonner une operation si elle prend trop de temps.

## Solution
```rust
use tokio::time::{timeout, Duration};

async fn slow_operation() -> String {
    tokio::time::sleep(Duration::from_secs(10)).await;
    "Done".to_string()
}

#[tokio::main]
async fn main() {
    let result = timeout(
        Duration::from_secs(2),
        slow_operation()
    ).await;

    match result {
        Ok(value) => println!("Got: {}", value),
        Err(_) => println!("Timeout!"),
    }
}
```

**Avec select! pour plusieurs alternatives** :
```rust
use tokio::select;

async fn with_fallback() {
    select! {
        result = slow_operation() => {
            println!("Operation finished: {}", result);
        }
        _ = tokio::time::sleep(Duration::from_secs(2)) => {
            println!("Timeout, using fallback");
        }
    }
}
```

## Explication
**`timeout(duration, future)`** :
- Retourne `Result<T, Elapsed>`
- `Ok(T)` si la future finit a temps
- `Err(Elapsed)` si timeout

**Annulation** :
La future est dropped si le timeout expire. Cleanup automatique.

## A retenir
- `timeout()` pour limiter le temps
- `select!` pour le premier qui repond
- Les futures sont annulees proprement""",
    },
    {
        "topic": "async",
        "difficulty": "avance",
        "user": "Comment debugger du code async qui ne progresse pas ?",
        "assistant": """## TL;DR
Verifie : 1) `.await` manquant, 2) deadlock sur Mutex, 3) blocking code dans async, 4) `spawn` oublie.

## Probleme
Le programme semble bloque ou ne fait rien.

## Solution
**1. `.await` oublie** :
```rust
// MAUVAIS - la future n'est jamais executee
async fn bad() {
    fetch_data();  // Oubli de .await!
}

// BON
async fn good() {
    fetch_data().await;
}
```

**2. Deadlock avec Mutex** :
```rust
// MAUVAIS - garde le lock pendant await
async fn bad(data: Arc<Mutex<String>>) {
    let guard = data.lock().unwrap();
    some_async_op().await;  // Deadlock potentiel!
    println!("{}", guard);
}

// BON - libere avant await
async fn good(data: Arc<Mutex<String>>) {
    let value = {
        let guard = data.lock().unwrap();
        guard.clone()
    };  // Lock libere
    some_async_op().await;
    println!("{}", value);
}
```

**3. Blocking code** :
```rust
// MAUVAIS - bloque le runtime
async fn bad() {
    std::thread::sleep(Duration::from_secs(1));
}

// BON
async fn good() {
    tokio::time::sleep(Duration::from_secs(1)).await;
}

// Ou pour du CPU-bound
async fn also_good() {
    tokio::task::spawn_blocking(|| heavy_computation()).await;
}
```

## Explication
**Outils de debug** :
- `tokio-console` : visualise les taches
- `tracing` : logs structures
- Compiler warnings pour futures non-awaited

## A retenir
- Toujours `.await` les futures
- Liberer les locks avant `.await`
- Jamais de blocking dans async sans `spawn_blocking`""",
    },
]

MORE_CONCEPTS = [
    {
        "topic": "pattern_matching",
        "difficulty": "debutant",
        "user": "Comment utiliser les guards dans un match ?",
        "assistant": """## TL;DR
Les guards (`if condition`) ajoutent une condition supplementaire a un pattern.

## Probleme
Tu veux matcher un pattern ET verifier une condition.

## Solution
```rust
fn describe_number(n: i32) -> &'static str {
    match n {
        x if x < 0 => "negative",
        0 => "zero",
        x if x % 2 == 0 => "positive even",
        _ => "positive odd",
    }
}

fn main() {
    println!("{}", describe_number(-5));  // "negative"
    println!("{}", describe_number(0));   // "zero"
    println!("{}", describe_number(4));   // "positive even"
    println!("{}", describe_number(7));   // "positive odd"
}
```

**Avec des enums** :
```rust
enum Message {
    Text(String),
    Number(i32),
}

fn process(msg: Message) {
    match msg {
        Message::Text(s) if s.is_empty() => println!("Empty text"),
        Message::Text(s) => println!("Text: {}", s),
        Message::Number(n) if n > 100 => println!("Big number"),
        Message::Number(n) => println!("Number: {}", n),
    }
}
```

## Explication
- Le guard est evalue APRES que le pattern matche
- `x if condition =>` : x est lie, puis condition testee
- Ordre important : le premier match gagne

**Binding dans guard** :
```rust
match pair {
    (x, y) if x == y => println!("Equal"),
    (x, _) if x > 0 => println!("First positive"),
    _ => println!("Other"),
}
```

## A retenir
- `if condition` apres le pattern
- Permet des conditions complexes
- Le pattern bind d'abord, guard teste ensuite""",
    },
    {
        "topic": "ownership",
        "difficulty": "debutant",
        "user": "C'est quoi la difference entre `Copy` et `Clone` ?",
        "assistant": """## TL;DR
`Copy` = copie implicite bit-a-bit (stack). `Clone` = copie explicite potentiellement couteuse.

## Probleme
Comprendre quand les valeurs sont copiees automatiquement.

## Solution
**`Copy`** - implicite, gratuit :
```rust
let x = 5;
let y = x;  // Copie automatique
println!("{}", x);  // x toujours valide

// Types Copy : i32, f64, bool, char, tuples de Copy
```

**`Clone`** - explicite, peut etre couteux :
```rust
let s1 = String::from("hello");
let s2 = s1.clone();  // Explicite
println!("{} {}", s1, s2);  // Les deux valides

// Sans clone -> move
let s3 = s1;  // s1 invalide
```

## Explication
| Trait | Semantique | Types |
|-------|------------|-------|
| Copy | Copie stack implicite | Primitifs, refs |
| Clone | Clone explicite | Tout type |

**Regles** :
- `Copy` requiert que tous les champs soient `Copy`
- `Copy` implique `Clone`
- Pas de `Copy` si le type gere des ressources (heap, fichiers)

```rust
#[derive(Clone, Copy)]
struct Point { x: i32, y: i32 }  // OK: i32 est Copy

#[derive(Clone)]
struct Data { value: String }  // Pas Copy: String n'est pas Copy
```

## A retenir
- `Copy` : types simples, copie gratuite
- `Clone` : copie explicite avec `.clone()`
- Si pas Copy, c'est un move""",
    },
    {
        "topic": "ownership",
        "difficulty": "intermediaire",
        "user": "Comment `drop` fonctionne et quand l'utiliser explicitement ?",
        "assistant": """## TL;DR
`drop` est appele automatiquement a la fin de la portee. Appelle-le explicitement pour liberer des ressources plus tot.

## Probleme
Comprendre la destruction des valeurs en Rust.

## Solution
**Drop automatique** :
```rust
{
    let s = String::from("hello");
    // ... utilisation
}  // drop(s) appele automatiquement ici
```

**Drop explicite** :
```rust
use std::mem::drop;

fn main() {
    let data = String::from("important");

    // Libere maintenant, pas a la fin de main
    drop(data);

    // data n'est plus utilisable
    // println!("{}", data);  // ERREUR
}
```

**Implementer Drop** :
```rust
struct CustomResource {
    name: String,
}

impl Drop for CustomResource {
    fn drop(&mut self) {
        println!("Dropping {}", self.name);
    }
}

fn main() {
    let r = CustomResource { name: "test".into() };
}  // "Dropping test"
```

## Explication
**Ordre de drop** :
- Variables : inverse de declaration
- Champs de struct : ordre de declaration
- Elements de Vec : index croissant

**Cas d'usage de drop explicite** :
- Liberer un lock plus tot
- Fermer une connexion
- Liberer de la memoire pendant une longue operation

## A retenir
- `Drop` = destructeur automatique
- `drop(value)` pour liberation anticipee
- RAII : Resources Are Initialized In Acquisition""",
    },
    {
        "topic": "generics",
        "difficulty": "debutant",
        "user": "Comment ecrire une fonction generique basique ?",
        "assistant": """## TL;DR
Utilise `<T>` pour declarer un type generique. Ajoute des trait bounds pour utiliser des fonctionnalites.

## Probleme
Tu veux une fonction qui fonctionne avec plusieurs types.

## Solution
**Fonction generique basique** :
```rust
fn first<T>(list: &[T]) -> Option<&T> {
    list.first()
}

fn main() {
    let numbers = vec![1, 2, 3];
    let strings = vec!["a", "b", "c"];

    println!("{:?}", first(&numbers));  // Some(1)
    println!("{:?}", first(&strings));  // Some("a")
}
```

**Avec trait bounds** :
```rust
fn print_all<T: std::fmt::Display>(items: &[T]) {
    for item in items {
        println!("{}", item);
    }
}

// Syntaxe where (plus lisible pour contraintes multiples)
fn complex<T, U>(t: T, u: U)
where
    T: Clone + Debug,
    U: Display,
{
    println!("{:?} {}", t.clone(), u);
}
```

## Explication
Sans trait bound, `T` est un type inconnu :
- Pas d'operations dessus
- Peut seulement le stocker/deplacer

Avec trait bound `T: Trait` :
- Peut utiliser les methodes du trait
- Le compilateur verifie a l'appel

**Monomorphisation** : le compilateur genere du code specifique pour chaque type utilise.

## A retenir
- `<T>` declare le generique
- `T: Trait` pour les contraintes
- `where` pour la lisibilite""",
    },
    {
        "topic": "collections",
        "difficulty": "debutant",
        "user": "Quelles sont les principales collections en Rust et quand les utiliser ?",
        "assistant": """## TL;DR
`Vec` pour les listes, `HashMap` pour les cles-valeurs, `HashSet` pour les ensembles uniques.

## Probleme
Choisir la bonne structure de donnees.

## Solution
**`Vec<T>`** - liste ordonnee :
```rust
let mut v = vec![1, 2, 3];
v.push(4);
v.pop();
let first = &v[0];
```

**`HashMap<K, V>`** - dictionnaire :
```rust
use std::collections::HashMap;

let mut scores = HashMap::new();
scores.insert("Alice", 100);
scores.insert("Bob", 85);

if let Some(score) = scores.get("Alice") {
    println!("Alice: {}", score);
}
```

**`HashSet<T>`** - ensemble unique :
```rust
use std::collections::HashSet;

let mut set = HashSet::new();
set.insert(1);
set.insert(2);
set.insert(1);  // Ignore, deja present
println!("{}", set.len());  // 2
```

## Explication
| Collection | Acces | Insertion | Cas d'usage |
|------------|-------|-----------|-------------|
| Vec | O(1) index | O(1) push | Liste ordonnee |
| HashMap | O(1) key | O(1) | Lookup par cle |
| HashSet | O(1) | O(1) | Unicite |
| VecDeque | O(1) ends | O(1) ends | Queue/stack |
| BTreeMap | O(log n) | O(log n) | Cles ordonnees |

## A retenir
- `Vec` par defaut pour les listes
- `HashMap` pour les associations cle-valeur
- `HashSet` pour les ensembles sans doublons""",
    },
    {
        "topic": "macros",
        "difficulty": "intermediaire",
        "user": "C'est quoi la difference entre les macros `!` et les fonctions ?",
        "assistant": """## TL;DR
Les macros operent sur le code source (AST) et peuvent generer du code. Les fonctions operent sur les valeurs a l'execution.

## Probleme
Comprendre quand utiliser une macro vs une fonction.

## Solution
**Macro** - genere du code :
```rust
// vec! genere du code specifique
let v = vec![1, 2, 3];
// Equivalent a :
// let v = { let mut v = Vec::new(); v.push(1); v.push(2); v.push(3); v };

// Nombre variable d'arguments
println!("{} + {} = {}", 1, 2, 3);  // Impossible avec une fonction
```

**Fonction** - execute du code :
```rust
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

**Macro declarative basique** :
```rust
macro_rules! say_hello {
    () => {
        println!("Hello!");
    };
    ($name:expr) => {
        println!("Hello, {}!", $name);
    };
}

say_hello!();          // "Hello!"
say_hello!("World");   // "Hello, World!"
```

## Explication
| Aspect | Macro | Fonction |
|--------|-------|----------|
| Quand | Compilation | Execution |
| Arguments | Patterns sur tokens | Types fixes |
| Variadic | Oui | Non |
| Hygiene | Oui | N/A |

**Macros standard utiles** :
- `vec![]`, `println!()`, `format!()`
- `derive()`, `cfg!()`
- `assert!()`, `panic!()`

## A retenir
- Macros = metaprogrammation
- Utilise `!` pour les appeler
- Prefere les fonctions sauf besoin special""",
    },
]

MORE_DEBUG = [
    {
        "topic": "lifetimes",
        "difficulty": "debutant",
        "user": "Pourquoi j'ai 'missing lifetime specifier' sur cette struct ?\n\n```rust\nstruct Config {\n    name: &str,\n}\n```",
        "assistant": """## TL;DR
Une struct avec une reference doit declarer une lifetime. Ajoute `<'a>`.

## Probleme
```
error[E0106]: missing lifetime specifier
 --> src/main.rs:2:11
  |
2 |     name: &str,
  |           ^ expected named lifetime parameter
```

## Solution
```rust
struct Config<'a> {
    name: &'a str,
}

impl<'a> Config<'a> {
    fn new(name: &'a str) -> Self {
        Config { name }
    }
}

fn main() {
    let name = String::from("MyApp");
    let config = Config::new(&name);
    println!("Config: {}", config.name);
}
```

**Ou utilise `String` pour eviter les lifetimes** :
```rust
struct Config {
    name: String,  // Owned, pas de lifetime
}
```

## Explication
La struct contient une reference. Le compilateur doit savoir :
- Combien de temps la reference est valide
- Que la struct ne survit pas aux donnees referencees

`'a` lie la duree de vie de la struct a celle des donnees.

## A retenir
- Struct avec `&T` = lifetime obligatoire
- `<'a>` sur la struct et les champs references
- Alternative : utiliser des types owned (`String`)""",
    },
    {
        "topic": "borrowing",
        "difficulty": "intermediaire",
        "user": "Pourquoi 'cannot move out of borrowed content' ?\n\n```rust\nfn take_first(v: &Vec<String>) -> String {\n    v[0]\n}\n```",
        "assistant": """## TL;DR
Tu essaies de prendre ownership d'un element via une reference. Clone ou retourne une reference.

## Probleme
```
error[E0507]: cannot move out of `v[_]` which is behind a shared reference
```

`v` est emprunte (`&Vec`), tu ne peux pas en extraire un element par valeur.

## Solution
**Option 1 : Retourner une reference** :
```rust
fn get_first(v: &Vec<String>) -> Option<&String> {
    v.first()
}
```

**Option 2 : Cloner** :
```rust
fn take_first(v: &Vec<String>) -> String {
    v[0].clone()
}
```

**Option 3 : Prendre ownership du Vec** :
```rust
fn take_first(mut v: Vec<String>) -> String {
    v.remove(0)
}
```

**Option 4 : swap_remove (O(1) mais change l'ordre)** :
```rust
fn take_first(v: &mut Vec<String>) -> String {
    v.swap_remove(0)
}
```

## Explication
Une reference `&Vec` permet de lire mais pas de deplacer les elements. Deplacer un element le retirerait du Vec, ce qui le modifierait.

## A retenir
- `&T` = lecture seule, pas de move
- Clone si tu as besoin d'une copie
- `&mut` si tu veux vraiment retirer l'element""",
    },
    {
        "topic": "traits",
        "difficulty": "intermediaire",
        "user": "Pourquoi 'the trait bound is not satisfied' pour Debug ?\n\n```rust\nstruct Point { x: i32, y: i32 }\nfn main() {\n    let p = Point { x: 1, y: 2 };\n    println!(\"{:?}\", p);\n}\n```",
        "assistant": """## TL;DR
`Point` n'implemente pas `Debug`. Derive-le ou implemente-le.

## Probleme
```
error[E0277]: `Point` doesn't implement `Debug`
```

`{:?}` requiert le trait `Debug` qui n'est pas implemente par defaut.

## Solution
**Derive automatique** :
```rust
#[derive(Debug)]
struct Point { x: i32, y: i32 }

fn main() {
    let p = Point { x: 1, y: 2 };
    println!("{:?}", p);   // Point { x: 1, y: 2 }
    println!("{:#?}", p);  // Pretty print
}
```

**Implementation manuelle** :
```rust
use std::fmt;

struct Point { x: i32, y: i32 }

impl fmt::Debug for Point {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}
```

## Explication
- `{:?}` = `Debug` trait
- `{}` = `Display` trait
- `derive` genere l'implementation automatiquement

**Derives courants** :
```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct MyStruct { ... }
```

## A retenir
- `#[derive(Debug)]` pour le debug printing
- `Debug` pour les devs, `Display` pour les users
- Tous les champs doivent etre `Debug` pour derive""",
    },
    {
        "topic": "async",
        "difficulty": "intermediaire",
        "user": "Pourquoi 'this function must be `async`' ?\n\n```rust\nfn process() {\n    let data = fetch_data().await;\n}\n```",
        "assistant": """## TL;DR
`.await` ne peut etre utilise que dans une fonction `async`. Ajoute `async` ou utilise un runtime.

## Probleme
```
error[E0728]: `await` is only allowed inside `async` functions and blocks
```

## Solution
**Marquer la fonction async** :
```rust
async fn process() {
    let data = fetch_data().await;
}
```

**Ou utiliser un bloc async** :
```rust
fn process() {
    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async {
        let data = fetch_data().await;
    });
}
```

**Dans main** :
```rust
#[tokio::main]
async fn main() {
    let data = fetch_data().await;
}

// Ou manuellement
fn main() {
    tokio::runtime::Runtime::new()
        .unwrap()
        .block_on(async {
            fetch_data().await;
        });
}
```

## Explication
`.await` :
- Transforme la fonction en machine a etats
- Necessite le contexte async pour fonctionner
- Suspend l'execution jusqu'a completion

Sans `async`, le compilateur ne peut pas generer le code necessaire.

## A retenir
- `.await` requiert `async fn` ou `async {}`
- `#[tokio::main]` pour le point d'entree
- `block_on` pour appeler async depuis sync""",
    },
    {
        "topic": "generics",
        "difficulty": "debutant",
        "user": "Pourquoi 'the method exists for struct but not for trait bound' ?\n\n```rust\nfn process<T>(item: T) {\n    println!(\"{}\", item.len());\n}\n```",
        "assistant": """## TL;DR
Le type generique `T` n'a pas de contrainte. Ajoute un trait bound.

## Probleme
```
error[E0599]: no method named `len` found for type parameter `T`
```

`T` peut etre n'importe quel type. Le compilateur ne peut pas garantir que `.len()` existe.

## Solution
**Avec un trait qui a len()** :
```rust
fn process<T: AsRef<str>>(item: T) {
    println!("{}", item.as_ref().len());
}

// Ou avec ExactSizeIterator
fn count<T: ExactSizeIterator>(iter: T) {
    println!("{}", iter.len());
}
```

**Definir ton propre trait** :
```rust
trait HasLength {
    fn len(&self) -> usize;
}

impl HasLength for String {
    fn len(&self) -> usize { self.len() }
}

fn process<T: HasLength>(item: T) {
    println!("{}", item.len());
}
```

## Explication
Les generics sans contraintes :
- Peuvent seulement etre stockes/deplaces
- Pas d'operations specifiques

Avec trait bound :
- Acces aux methodes du trait
- Le compilateur verifie a l'appel

## A retenir
- `T` seul = type inconnu minimal
- `T: Trait` = type avec garanties
- Le compilateur applique les contraintes""",
    },
]

MORE_EXERCISES = [
    {
        "topic": "async",
        "difficulty": "intermediaire",
        "user": "Un exercice sur async/await avec des requetes paralleles.",
        "assistant": """## TL;DR
Exercice : telecharger plusieurs URLs en parallele et combiner les resultats.

## Probleme
Tu dois faire plusieurs requetes HTTP en parallele pour gagner du temps.

## Solution
**Exercice : Fetch parallele**

```rust
use tokio;

async fn fetch_url(url: &str) -> Result<String, reqwest::Error> {
    todo!()
}

async fn fetch_all(urls: Vec<&str>) -> Vec<Result<String, reqwest::Error>> {
    todo!()
}

#[tokio::main]
async fn main() {
    let urls = vec![
        "https://httpbin.org/get",
        "https://httpbin.org/ip",
    ];

    let results = fetch_all(urls).await;
    for result in results {
        match result {
            Ok(body) => println!("Got {} bytes", body.len()),
            Err(e) => println!("Error: {}", e),
        }
    }
}
```

**Solution** :
```rust
async fn fetch_url(url: &str) -> Result<String, reqwest::Error> {
    reqwest::get(url).await?.text().await
}

async fn fetch_all(urls: Vec<&str>) -> Vec<Result<String, reqwest::Error>> {
    let futures: Vec<_> = urls
        .into_iter()
        .map(|url| fetch_url(url))
        .collect();

    futures::future::join_all(futures).await
}
```

## Explication
- `join_all` attend toutes les futures en parallele
- Chaque requete s'execute independamment
- Les resultats sont dans le meme ordre que les URLs

**Alternative avec `try_join_all`** :
```rust
let results = futures::future::try_join_all(futures).await?;
// Retourne Err des qu'une echoue
```

## A retenir
- `join_all` pour paralleliser
- Les futures sont lazy, doivent etre attendues
- `try_join_all` pour short-circuit sur erreur""",
    },
    {
        "topic": "concurrency",
        "difficulty": "avance",
        "user": "Un exercice sur les threads et la synchronisation.",
        "assistant": """## TL;DR
Exercice : implementer un compteur thread-safe avec plusieurs threads qui incrementent.

## Probleme
Tu dois creer un compteur partage entre plusieurs threads.

## Solution
**Exercice : Compteur thread-safe**

```rust
use std::sync::{Arc, Mutex};
use std::thread;

struct Counter {
    // TODO: Quelle structure utiliser ?
}

impl Counter {
    fn new() -> Self { todo!() }
    fn increment(&self) { todo!() }
    fn get(&self) -> i32 { todo!() }
}

fn main() {
    let counter = Counter::new();

    let mut handles = vec![];
    for _ in 0..10 {
        // TODO: Lancer un thread qui incremente 100 fois
    }

    for handle in handles {
        handle.join().unwrap();
    }

    assert_eq!(counter.get(), 1000);
    println!("Final count: {}", counter.get());
}
```

**Solution** :
```rust
use std::sync::{Arc, Mutex};
use std::thread;

struct Counter {
    value: Arc<Mutex<i32>>,
}

impl Counter {
    fn new() -> Self {
        Counter { value: Arc::new(Mutex::new(0)) }
    }

    fn increment(&self) {
        let mut num = self.value.lock().unwrap();
        *num += 1;
    }

    fn get(&self) -> i32 {
        *self.value.lock().unwrap()
    }
}

impl Clone for Counter {
    fn clone(&self) -> Self {
        Counter { value: Arc::clone(&self.value) }
    }
}

fn main() {
    let counter = Counter::new();
    let mut handles = vec![];

    for _ in 0..10 {
        let c = counter.clone();
        handles.push(thread::spawn(move || {
            for _ in 0..100 {
                c.increment();
            }
        }));
    }

    for handle in handles {
        handle.join().unwrap();
    }

    assert_eq!(counter.get(), 1000);
}
```

## Explication
- `Arc` : partage entre threads
- `Mutex` : acces exclusif
- `Clone` pour envoyer aux threads

## A retenir
- `Arc<Mutex<T>>` pour partage mutable thread-safe
- Clone l'Arc, pas les donnees
- `lock()` pour acceder""",
    },
    {
        "topic": "traits",
        "difficulty": "intermediaire",
        "user": "Un exercice sur l'implementation de traits standard.",
        "assistant": """## TL;DR
Exercice : implementer `Display`, `FromStr` et `PartialEq` pour un type custom.

## Probleme
Tu dois rendre ton type utilisable avec les conventions Rust.

## Solution
**Exercice : Type Temperature**

```rust
use std::fmt;
use std::str::FromStr;

struct Temperature {
    celsius: f64,
}

// TODO: Implemente Display pour afficher "25.0C"
// TODO: Implemente FromStr pour parser "25.0C"
// TODO: Implemente PartialEq pour comparer

fn main() {
    let t1 = Temperature { celsius: 25.0 };
    let t2: Temperature = "25.0C".parse().unwrap();

    println!("{}", t1);  // "25.0C"
    assert_eq!(t1, t2);
}
```

**Solution** :
```rust
use std::fmt;
use std::str::FromStr;

#[derive(Debug)]
struct Temperature {
    celsius: f64,
}

impl fmt::Display for Temperature {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{:.1}C", self.celsius)
    }
}

#[derive(Debug)]
struct ParseTempError;

impl FromStr for Temperature {
    type Err = ParseTempError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let s = s.trim().trim_end_matches('C');
        let celsius = s.parse().map_err(|_| ParseTempError)?;
        Ok(Temperature { celsius })
    }
}

impl PartialEq for Temperature {
    fn eq(&self, other: &Self) -> bool {
        (self.celsius - other.celsius).abs() < 0.001
    }
}

fn main() {
    let t1 = Temperature { celsius: 25.0 };
    let t2: Temperature = "25.0C".parse().unwrap();
    println!("{}", t1);
    assert_eq!(t1, t2);
}
```

## Explication
- `Display` : formatage user-friendly
- `FromStr` : parsing depuis `&str`
- `PartialEq` : comparaison avec `==`

Pour les floats, comparer avec une tolerance.

## A retenir
- `Display` pour `{}`
- `FromStr` pour `.parse()`
- `PartialEq` pour `==`""",
    },
    {
        "topic": "error_handling",
        "difficulty": "intermediaire",
        "user": "Un exercice sur la creation d'un type d'erreur custom.",
        "assistant": """## TL;DR
Exercice : creer un type d'erreur avec plusieurs variants et conversions.

## Probleme
Tu dois creer une hierarchie d'erreurs pour une application.

## Solution
**Exercice : Erreurs de parsing de config**

```rust
use std::io;
use std::num::ParseIntError;

// TODO: Cree un enum d'erreur avec :
// - IoError (contient io::Error)
// - ParseError (contient ParseIntError)
// - MissingField (contient String)

fn read_config(path: &str) -> Result<i32, ???> {
    // Simule lecture de fichier
    let content = "port=abc";

    // Parse le port
    let port_str = content
        .strip_prefix("port=")
        .ok_or_else(|| ??? )?;

    let port = port_str.parse::<i32>()?;
    Ok(port)
}
```

**Solution** :
```rust
use std::io;
use std::num::ParseIntError;
use std::fmt;
use std::error::Error;

#[derive(Debug)]
enum ConfigError {
    Io(io::Error),
    Parse(ParseIntError),
    MissingField(String),
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            ConfigError::Io(e) => write!(f, "IO error: {}", e),
            ConfigError::Parse(e) => write!(f, "Parse error: {}", e),
            ConfigError::MissingField(s) => write!(f, "Missing field: {}", s),
        }
    }
}

impl Error for ConfigError {}

impl From<io::Error> for ConfigError {
    fn from(e: io::Error) -> Self { ConfigError::Io(e) }
}

impl From<ParseIntError> for ConfigError {
    fn from(e: ParseIntError) -> Self { ConfigError::Parse(e) }
}

fn read_config(path: &str) -> Result<i32, ConfigError> {
    let content = "port=abc";

    let port_str = content
        .strip_prefix("port=")
        .ok_or_else(|| ConfigError::MissingField("port".into()))?;

    let port = port_str.parse::<i32>()?;  // Conversion auto via From
    Ok(port)
}
```

## Explication
- `From<T>` permet la conversion avec `?`
- `Display` pour le message d'erreur
- `Error` pour la compatibilite avec `Box<dyn Error>`

## A retenir
- Enum pour plusieurs types d'erreur
- `From<T>` pour conversion automatique
- `thiserror` simplifie tout ca""",
    },
]

# ============================================================================
# M9 Part 4: Derniere serie pour atteindre 200+
# ============================================================================

EXTRA_LIFETIMES = [
    {
        "topic": "lifetimes",
        "difficulty": "debutant",
        "user": "Pourquoi je ne peux pas stocker une reference dans cette struct sans lifetime ?\n\n```rust\nstruct Cache {\n    data: &[u8],\n}\n```",
        "assistant": """## TL;DR
Une struct avec reference doit avoir un parametre de lifetime pour garantir que les donnees referencees vivent assez longtemps.

## Probleme
Sans lifetime, le compilateur ne peut pas verifier la validite des references.

## Solution
```rust
struct Cache<'a> {
    data: &'a [u8],
}

fn main() {
    let bytes = vec![1, 2, 3];
    let cache = Cache { data: &bytes };
    println!("{:?}", cache.data);
    // cache ne peut pas survivre a bytes
}
```

## Explication
La lifetime `'a` exprime : "Cache ne vit pas plus longtemps que les donnees pointees par data".

Alternative owned :
```rust
struct Cache {
    data: Vec<u8>,  // Possede les donnees
}
```

## A retenir
- Reference dans struct = lifetime obligatoire
- `<'a>` garantit la validite
- Alternative : types owned""",
    },
    {
        "topic": "lifetimes",
        "difficulty": "intermediaire",
        "user": "Comment fonctionne la variance des lifetimes ?",
        "assistant": """## TL;DR
La variance determine si on peut substituer une lifetime par une plus longue ou plus courte. `&'a T` est covariant en `'a`.

## Probleme
Comprendre pourquoi certaines substitutions de lifetime sont acceptees.

## Solution
```rust
fn covariance_demo<'long, 'short>(long_ref: &'long str)
where
    'long: 'short,  // 'long outlives 'short
{
    // OK: on peut utiliser une ref plus longue ou une plus courte est attendue
    let short_ref: &'short str = long_ref;
}

fn main() {
    let s = String::from("hello");
    // La lifetime de &s peut etre "raccourcie" selon le besoin
    covariance_demo(&s);
}
```

## Explication
**Covariance** (`&'a T`) : `'long` peut remplacer `'short`
```rust
&'static str -> &'a str  // OK
```

**Contravariance** (`fn(&'a T)`) : l'inverse
```rust
fn(&'a str) -> fn(&'static str)  // Plus restrictif accepte
```

**Invariance** (`&'a mut T`) : doit etre exact
```rust
&'a mut T ne peut pas devenir &'b mut T
```

## A retenir
- `&T` covariant : peut raccourcir
- `&mut T` invariant : doit matcher exactement
- Rarement un probleme en pratique""",
    },
]

EXTRA_BORROWING = [
    {
        "topic": "borrowing",
        "difficulty": "debutant",
        "user": "Comment passer une String a une fonction qui attend &str ?",
        "assistant": """## TL;DR
Utilise `&string` ou `&string[..]`. La conversion est automatique grace a Deref.

## Probleme
Tu as une `String` mais la fonction attend `&str`.

## Solution
```rust
fn greet(name: &str) {
    println!("Hello, {}!", name);
}

fn main() {
    let owned = String::from("World");

    // Toutes ces syntaxes fonctionnent
    greet(&owned);           // Deref coercion
    greet(&owned[..]);       // Slice explicite
    greet(owned.as_str());   // Methode explicite

    // owned est toujours utilisable
    println!("Still have: {}", owned);
}
```

## Explication
`String` implemente `Deref<Target = str>`, donc :
- `&String` se convertit automatiquement en `&str`
- C'est la "deref coercion"
- Zero cost a l'execution

## A retenir
- `&String` -> `&str` automatique
- Prefere `&str` en parametre (plus flexible)
- La String reste valide apres l'appel""",
    },
    {
        "topic": "borrowing",
        "difficulty": "debutant",
        "user": "Comment iterer sur un vecteur sans en prendre ownership ?",
        "assistant": """## TL;DR
Utilise `&vec` ou `vec.iter()` pour iterer par reference.

## Probleme
Tu veux parcourir un vecteur et le garder utilisable apres.

## Solution
```rust
fn main() {
    let numbers = vec![1, 2, 3, 4, 5];

    // Methode 1: reference dans for
    for n in &numbers {
        println!("{}", n);  // n est &i32
    }

    // Methode 2: iter() explicite
    for n in numbers.iter() {
        println!("{}", n);
    }

    // numbers toujours utilisable
    println!("Sum: {}", numbers.iter().sum::<i32>());
}
```

## Explication
| Syntaxe | Type element | Apres boucle |
|---------|--------------|--------------|
| `for x in vec` | `T` | vec consumed |
| `for x in &vec` | `&T` | vec intact |
| `for x in &mut vec` | `&mut T` | vec intact |

## A retenir
- `&vec` ou `.iter()` pour lecture
- `&mut vec` ou `.iter_mut()` pour modification
- Sans `&` = consumption du vecteur""",
    },
    {
        "topic": "borrowing",
        "difficulty": "intermediaire",
        "user": "Comment fonctionne le pattern entry() avec HashMap ?",
        "assistant": """## TL;DR
`entry()` donne acces a une entree pour insertion ou modification sans double lookup.

## Probleme
Inserer ou modifier une valeur dans une HashMap efficacement.

## Solution
```rust
use std::collections::HashMap;

fn main() {
    let mut scores = HashMap::new();

    // Insert si absent
    scores.entry("Alice").or_insert(0);

    // Insert avec calcul lazy
    scores.entry("Bob").or_insert_with(|| expensive_default());

    // Modifier l'existant
    *scores.entry("Alice").or_insert(0) += 10;

    // Pattern compteur de mots
    let text = "hello world hello rust world world";
    let mut word_count = HashMap::new();

    for word in text.split_whitespace() {
        *word_count.entry(word).or_insert(0) += 1;
    }

    println!("{:?}", word_count);
    // {"hello": 2, "world": 3, "rust": 1}
}

fn expensive_default() -> i32 { 42 }
```

## Explication
`entry()` retourne un `Entry` enum :
- `Occupied` : la cle existe
- `Vacant` : la cle n'existe pas

Methodes :
- `or_insert(v)` : insere v si vacant
- `or_insert_with(f)` : appelle f si vacant
- `or_default()` : utilise Default::default()
- `and_modify(f)` : modifie si present

## A retenir
- Un seul lookup au lieu de get+insert
- `or_insert` retourne une `&mut V`
- Pattern idiomatique pour les compteurs""",
    },
]

EXTRA_ASYNC = [
    {
        "topic": "async",
        "difficulty": "debutant",
        "user": "Comment faire un sleep async ?",
        "assistant": """## TL;DR
Utilise `tokio::time::sleep` ou `async_std::task::sleep`. Ne jamais utiliser `std::thread::sleep` dans du code async.

## Probleme
Tu veux attendre un certain temps sans bloquer le runtime.

## Solution
```rust
use tokio::time::{sleep, Duration};

#[tokio::main]
async fn main() {
    println!("Starting...");
    sleep(Duration::from_secs(2)).await;
    println!("2 seconds later!");
}
```

**MAUVAIS - bloque le runtime** :
```rust
async fn bad() {
    std::thread::sleep(Duration::from_secs(2));  // Bloque!
}
```

## Explication
| Methode | Comportement |
|---------|--------------|
| `tokio::time::sleep` | Suspend la tache, libere le thread |
| `std::thread::sleep` | Bloque le thread entier |

En async, bloquer un thread bloque potentiellement toutes les autres taches sur ce thread.

**Avec intervalle** :
```rust
use tokio::time::{interval, Duration};

async fn periodic() {
    let mut timer = interval(Duration::from_secs(1));
    loop {
        timer.tick().await;
        println!("Tick!");
    }
}
```

## A retenir
- `tokio::time::sleep` pour async
- Jamais `std::thread::sleep` dans async
- `interval` pour des actions periodiques""",
    },
    {
        "topic": "async",
        "difficulty": "intermediaire",
        "user": "Comment annuler une tache async ?",
        "assistant": """## TL;DR
Utilise `tokio::select!` avec un token d'annulation, ou simplement drop le `JoinHandle`.

## Probleme
Tu veux pouvoir arreter une tache en cours.

## Solution
**Avec select! et signal** :
```rust
use tokio::sync::oneshot;
use tokio::time::{sleep, Duration};

async fn cancellable_work(mut cancel: oneshot::Receiver<()>) {
    loop {
        tokio::select! {
            _ = &mut cancel => {
                println!("Cancelled!");
                return;
            }
            _ = sleep(Duration::from_secs(1)) => {
                println!("Working...");
            }
        }
    }
}

#[tokio::main]
async fn main() {
    let (tx, rx) = oneshot::channel();

    let handle = tokio::spawn(cancellable_work(rx));

    sleep(Duration::from_secs(3)).await;
    let _ = tx.send(());  // Signal d'annulation

    handle.await.unwrap();
}
```

**Avec abort()** :
```rust
let handle = tokio::spawn(async {
    loop { sleep(Duration::from_secs(1)).await; }
});

sleep(Duration::from_secs(3)).await;
handle.abort();  // Force l'arret
```

## Explication
- `select!` : verifie plusieurs conditions
- `oneshot` : channel a usage unique
- `abort()` : arret force, peut laisser des ressources

Prefere le pattern cooperatif (select!) pour un cleanup propre.

## A retenir
- `select!` pour annulation cooperative
- `abort()` pour arret force
- Les futures sont annulees proprement quand droppees""",
    },
]

EXTRA_OWNERSHIP = [
    {
        "topic": "ownership",
        "difficulty": "debutant",
        "user": "Pourquoi ma variable n'est plus utilisable apres l'avoir passee a une fonction ?",
        "assistant": """## TL;DR
C'est le "move" : la fonction a pris ownership. Utilise une reference ou clone.

## Probleme
```rust
fn process(s: String) {
    println!("{}", s);
}

fn main() {
    let s = String::from("hello");
    process(s);
    println!("{}", s);  // ERREUR!
}
```

## Solution
**Option 1 : Reference (emprunte)** :
```rust
fn process(s: &String) {
    println!("{}", s);
}

fn main() {
    let s = String::from("hello");
    process(&s);
    println!("{}", s);  // OK
}
```

**Option 2 : Clone (copie)** :
```rust
fn main() {
    let s = String::from("hello");
    process(s.clone());
    println!("{}", s);  // OK
}
```

**Option 3 : Retourner la valeur** :
```rust
fn process(s: String) -> String {
    println!("{}", s);
    s  // Retourne l'ownership
}

fn main() {
    let s = String::from("hello");
    let s = process(s);
    println!("{}", s);  // OK
}
```

## Explication
Rust a trois facons de passer des donnees :
1. Move : transfert d'ownership
2. Borrow : reference temporaire
3. Clone : copie des donnees

## A retenir
- Par defaut c'est un move
- `&` pour emprunter
- `.clone()` pour copier""",
    },
    {
        "topic": "ownership",
        "difficulty": "intermediaire",
        "user": "Comment fonctionne le shadowing et quelle est la difference avec mut ?",
        "assistant": """## TL;DR
Shadowing cree une nouvelle variable avec le meme nom. `mut` permet de modifier la meme variable.

## Probleme
Comprendre la difference entre redeclarer et modifier.

## Solution
**Shadowing** - nouvelle variable :
```rust
let x = 5;
let x = x + 1;     // Nouvelle variable x
let x = x * 2;     // Encore une nouvelle
println!("{}", x); // 12

// Peut changer de type!
let spaces = "   ";
let spaces = spaces.len();  // Maintenant un usize
```

**Mut** - modification en place :
```rust
let mut x = 5;
x = x + 1;  // Meme variable
x = x * 2;
println!("{}", x);  // 12

// Ne peut PAS changer de type
let mut spaces = "   ";
// spaces = spaces.len();  // ERREUR: type mismatch
```

## Explication
| Aspect | Shadowing | mut |
|--------|-----------|-----|
| Nouvelle variable | Oui | Non |
| Peut changer type | Oui | Non |
| Immutable apres | Oui | Non |
| Keyword | let | mut |

**Cas d'usage shadowing** :
- Transformation de donnees
- Parsing avec changement de type
- Raffiner une valeur

## A retenir
- Shadowing = `let x = ...` (nouvelle variable)
- Mut = `x = ...` (modifier l'existante)
- Shadowing permet le changement de type""",
    },
]

EXTRA_TRAITS = [
    {
        "topic": "traits",
        "difficulty": "debutant",
        "user": "Comment implementer Display pour mon type ?",
        "assistant": """## TL;DR
Implemente le trait `std::fmt::Display` avec une methode `fmt`.

## Probleme
Tu veux pouvoir utiliser `{}` avec ton type dans println!.

## Solution
```rust
use std::fmt;

struct Point {
    x: f64,
    y: f64,
}

impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}

fn main() {
    let p = Point { x: 1.5, y: 2.5 };
    println!("{}", p);  // "(1.5, 2.5)"

    // Formatage avec precision
    println!("{:.1}", p.x);  // "1.5"
}
```

## Explication
- `Display` = formatage user-friendly (`{}`)
- `Debug` = formatage debug (`{:?}`)

`write!` fonctionne comme `println!` mais ecrit dans le formatter.

**Avec formatage personnalise** :
```rust
impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        if f.alternate() {
            write!(f, "Point(x={}, y={})", self.x, self.y)
        } else {
            write!(f, "({}, {})", self.x, self.y)
        }
    }
}
// {:#} active le mode "alternate"
```

## A retenir
- `impl fmt::Display for Type`
- `write!` pour ecrire dans le formatter
- Retourne `fmt::Result`""",
    },
    {
        "topic": "traits",
        "difficulty": "intermediaire",
        "user": "Comment utiliser les default type parameters dans un trait ?",
        "assistant": """## TL;DR
Les parametres de type par defaut evitent de specifier le type a chaque implementation.

## Probleme
Tu veux un trait generique avec un type par defaut raisonnable.

## Solution
```rust
trait Add<Rhs = Self> {  // Rhs a un defaut: Self
    type Output;
    fn add(self, rhs: Rhs) -> Self::Output;
}

struct Point { x: i32, y: i32 }

// Impl avec le defaut (Rhs = Point)
impl Add for Point {
    type Output = Point;

    fn add(self, other: Point) -> Point {
        Point {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}

// Impl avec un type different
impl Add<(i32, i32)> for Point {
    type Output = Point;

    fn add(self, (dx, dy): (i32, i32)) -> Point {
        Point { x: self.x + dx, y: self.y + dy }
    }
}
```

## Explication
`trait Add<Rhs = Self>` signifie :
- Si on ecrit `impl Add for T`, Rhs = T
- On peut override avec `impl Add<Other> for T`

Cas d'usage :
- Operations mathematiques
- Conversions avec type cible par defaut
- Builder patterns

## A retenir
- `<T = Default>` pour type par defaut
- Reduit le boilerplate
- Peut etre override si besoin""",
    },
]

EXTRA_ERROR = [
    {
        "topic": "error_handling",
        "difficulty": "debutant",
        "user": "C'est quoi `anyhow` et quand l'utiliser ?",
        "assistant": """## TL;DR
`anyhow` simplifie la gestion d'erreurs dans les applications. Utilise-le dans `main()` et les binaires.

## Probleme
Gerer plusieurs types d'erreurs sans creer un type custom.

## Solution
```toml
# Cargo.toml
[dependencies]
anyhow = "1.0"
```

```rust
use anyhow::{Context, Result};

fn read_config() -> Result<String> {
    let content = std::fs::read_to_string("config.txt")
        .context("Failed to read config file")?;
    Ok(content)
}

fn parse_port(config: &str) -> Result<u16> {
    let port: u16 = config
        .parse()
        .context("Invalid port number")?;
    Ok(port)
}

fn main() -> Result<()> {
    let config = read_config()?;
    let port = parse_port(&config)?;
    println!("Port: {}", port);
    Ok(())
}
```

## Explication
| Crate | Usage | Quand |
|-------|-------|-------|
| anyhow | Applications | Binaires, main() |
| thiserror | Libraries | Crates publics |

**Fonctionnalites anyhow** :
- `Result<T>` = `Result<T, anyhow::Error>`
- `.context()` ajoute du contexte
- `bail!("error")` pour retourner une erreur
- `ensure!(condition, "msg")` comme assert mais Result

## A retenir
- `anyhow` pour les applications
- `thiserror` pour les libraries
- `.context()` pour des erreurs informatives""",
    },
    {
        "topic": "error_handling",
        "difficulty": "intermediaire",
        "user": "Comment chainer plusieurs erreurs avec leur contexte ?",
        "assistant": """## TL;DR
Utilise `.context()` de anyhow ou implemente la chaine source avec thiserror.

## Probleme
Tu veux voir toute la chaine d'erreurs pour le debug.

## Solution
**Avec anyhow** :
```rust
use anyhow::{Context, Result};

fn inner() -> Result<()> {
    std::fs::read_to_string("missing.txt")
        .context("Failed to read file")?;
    Ok(())
}

fn middle() -> Result<()> {
    inner().context("In middle function")?;
    Ok(())
}

fn outer() -> Result<()> {
    middle().context("In outer function")?;
    Ok(())
}

fn main() {
    if let Err(e) = outer() {
        // Affiche toute la chaine
        println!("Error: {:#}", e);
        // Error: In outer function
        //
        // Caused by:
        //     0: In middle function
        //     1: Failed to read file
        //     2: No such file or directory
    }
}
```

**Avec thiserror** :
```rust
use thiserror::Error;

#[derive(Error, Debug)]
enum AppError {
    #[error("Configuration error")]
    Config(#[source] ConfigError),

    #[error("Database error")]
    Database(#[from] DbError),
}

// #[source] cree la chaine d'erreurs
// #[from] implemente From et #[source]
```

## Explication
La chaine d'erreurs aide au debug :
- Chaque niveau ajoute du contexte
- `{:#}` affiche la chaine complete
- `.source()` accede a l'erreur sous-jacente

## A retenir
- `.context()` ajoute un niveau
- `{:#}` affiche la chaine complete
- `#[source]` avec thiserror""",
    },
]

EXTRA_STRUCTS = [
    {
        "topic": "structs",
        "difficulty": "debutant",
        "user": "C'est quoi la difference entre struct, tuple struct, et unit struct ?",
        "assistant": """## TL;DR
- Struct : champs nommes
- Tuple struct : champs par position
- Unit struct : pas de champs

## Probleme
Choisir le bon type de struct.

## Solution
**Struct classique** - champs nommes :
```rust
struct User {
    name: String,
    age: u32,
}

let user = User { name: "Alice".into(), age: 30 };
println!("{}", user.name);
```

**Tuple struct** - champs par index :
```rust
struct Point(f64, f64);
struct Color(u8, u8, u8);

let p = Point(1.0, 2.0);
println!("x={}, y={}", p.0, p.1);

// Utile pour le newtype pattern
struct Meters(f64);
struct Seconds(f64);
```

**Unit struct** - pas de donnees :
```rust
struct Marker;

// Utile pour les traits sans donnees
impl SomeTrait for Marker {
    fn do_something(&self) {}
}
```

## Explication
| Type | Syntaxe | Usage |
|------|---------|-------|
| Struct | `{ name: T }` | Donnees complexes |
| Tuple struct | `(T, U)` | Newtypes, petit tuple |
| Unit struct | `;` | Markers, implementations |

## A retenir
- Struct pour lisibilite (champs nommes)
- Tuple struct pour newtypes et wrappers
- Unit struct pour types sans donnees""",
    },
    {
        "topic": "structs",
        "difficulty": "intermediaire",
        "user": "Comment implementer le builder pattern en Rust ?",
        "assistant": """## TL;DR
Cree une struct Builder avec des methodes chainables qui consomment et retournent self.

## Probleme
Tu veux une API fluide pour construire des objets complexes.

## Solution
```rust
#[derive(Debug)]
struct Server {
    host: String,
    port: u16,
    max_connections: usize,
    timeout_ms: u64,
}

#[derive(Default)]
struct ServerBuilder {
    host: Option<String>,
    port: Option<u16>,
    max_connections: Option<usize>,
    timeout_ms: Option<u64>,
}

impl ServerBuilder {
    fn new() -> Self {
        Self::default()
    }

    fn host(mut self, host: impl Into<String>) -> Self {
        self.host = Some(host.into());
        self
    }

    fn port(mut self, port: u16) -> Self {
        self.port = Some(port);
        self
    }

    fn max_connections(mut self, n: usize) -> Self {
        self.max_connections = Some(n);
        self
    }

    fn timeout_ms(mut self, ms: u64) -> Self {
        self.timeout_ms = Some(ms);
        self
    }

    fn build(self) -> Result<Server, &'static str> {
        Ok(Server {
            host: self.host.ok_or("host required")?,
            port: self.port.unwrap_or(8080),
            max_connections: self.max_connections.unwrap_or(100),
            timeout_ms: self.timeout_ms.unwrap_or(5000),
        })
    }
}

fn main() {
    let server = ServerBuilder::new()
        .host("localhost")
        .port(3000)
        .max_connections(50)
        .build()
        .unwrap();

    println!("{:?}", server);
}
```

## Explication
- `mut self` : prend ownership, retourne modifie
- `impl Into<String>` : accepte &str et String
- `Option` pour les champs optionnels avec defauts

## A retenir
- `fn method(mut self, ...) -> Self`
- `build()` valide et construit
- Considere la crate `derive_builder` pour generer""",
    },
]

EXTRA_ENUMS = [
    {
        "topic": "enums",
        "difficulty": "debutant",
        "user": "Comment representer un etat avec plusieurs variantes possibles ?",
        "assistant": """## TL;DR
Utilise un enum avec des variants representant chaque etat, potentiellement avec des donnees.

## Probleme
Tu veux modeliser une machine a etats.

## Solution
```rust
enum ConnectionState {
    Disconnected,
    Connecting { attempt: u32 },
    Connected { peer_id: String },
    Error(String),
}

impl ConnectionState {
    fn description(&self) -> String {
        match self {
            ConnectionState::Disconnected =>
                "Not connected".to_string(),
            ConnectionState::Connecting { attempt } =>
                format!("Connecting (attempt {})", attempt),
            ConnectionState::Connected { peer_id } =>
                format!("Connected to {}", peer_id),
            ConnectionState::Error(msg) =>
                format!("Error: {}", msg),
        }
    }

    fn is_active(&self) -> bool {
        matches!(self, ConnectionState::Connected { .. })
    }
}

fn main() {
    let mut state = ConnectionState::Disconnected;
    println!("{}", state.description());

    state = ConnectionState::Connecting { attempt: 1 };
    println!("{}", state.description());

    state = ConnectionState::Connected { peer_id: "peer123".into() };
    println!("Active: {}", state.is_active());
}
```

## Explication
Chaque variant peut avoir :
- Rien : `Disconnected`
- Tuple : `Error(String)`
- Struct : `Connected { peer_id: String }`

`matches!` pour tester un pattern rapidement.

## A retenir
- Un enum = un etat a la fois
- `match` pour gerer tous les cas
- `matches!` pour test rapide""",
    },
]

EXTRA_MODULES = [
    {
        "topic": "modules",
        "difficulty": "debutant",
        "user": "Comment importer plusieurs choses d'un module ?",
        "assistant": """## TL;DR
Utilise `use module::{Item1, Item2}` ou `use module::*` pour tout.

## Probleme
Tu veux eviter de repeter `use` pour chaque item.

## Solution
```rust
// Import multiple items
use std::collections::{HashMap, HashSet, VecDeque};

// Import avec renommage
use std::io::{self, Read, Write};
// io = std::io, Read = std::io::Read, etc.

// Import avec alias
use std::collections::HashMap as Map;

// Import tout (a eviter sauf prelude)
use std::io::prelude::*;

fn main() {
    let mut map: HashMap<String, i32> = HashMap::new();
    let mut set: HashSet<i32> = HashSet::new();
}
```

## Explication
| Syntaxe | Signification |
|---------|---------------|
| `{A, B}` | Import A et B |
| `self` | Le module lui-meme |
| `*` | Tout (glob) |
| `as Name` | Renomme |

**Bonnes pratiques** :
- Evite `*` sauf pour les preludes
- Groupe les imports du meme module
- Ordre : std, external, crate

## A retenir
- `{}` pour grouper les imports
- `self` pour le module + ses items
- `as` pour eviter les conflits""",
    },
]

EXTRA_COLLECTIONS = [
    {
        "topic": "collections",
        "difficulty": "intermediaire",
        "user": "Comment choisir entre Vec, VecDeque, et LinkedList ?",
        "assistant": """## TL;DR
`Vec` par defaut, `VecDeque` pour queue/stack double, `LinkedList` rarement (cache-unfriendly).

## Probleme
Choisir la bonne structure pour ton cas d'usage.

## Solution
**Vec** - acces par index, push/pop a la fin :
```rust
let mut v = vec![1, 2, 3];
v.push(4);         // O(1) amorti
let last = v.pop(); // O(1)
let x = v[0];      // O(1)
```

**VecDeque** - push/pop aux deux bouts :
```rust
use std::collections::VecDeque;

let mut q = VecDeque::new();
q.push_back(1);    // O(1)
q.push_front(0);   // O(1)
let first = q.pop_front(); // O(1)
```

**LinkedList** - insertion milieu frequente (rare) :
```rust
use std::collections::LinkedList;

let mut list = LinkedList::new();
// Generalement moins performant que Vec
// a cause du cache
```

## Explication
| Operation | Vec | VecDeque | LinkedList |
|-----------|-----|----------|------------|
| Index | O(1) | O(1) | O(n) |
| push_back | O(1)* | O(1)* | O(1) |
| push_front | O(n) | O(1)* | O(1) |
| insert mid | O(n) | O(n) | O(1)** |

*amorti, **si tu as deja le curseur

## A retenir
- `Vec` dans 95% des cas
- `VecDeque` pour queues FIFO
- `LinkedList` presque jamais""",
    },
]

EXTRA_TESTING = [
    {
        "topic": "testing",
        "difficulty": "intermediaire",
        "user": "Comment tester du code async ?",
        "assistant": """## TL;DR
Utilise `#[tokio::test]` ou `#[async_std::test]` pour les tests async.

## Probleme
Tu veux tester des fonctions async.

## Solution
```rust
// src/lib.rs
async fn fetch_data(id: u32) -> Result<String, &'static str> {
    if id == 0 {
        Err("Invalid ID")
    } else {
        Ok(format!("Data for {}", id))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_fetch_success() {
        let result = fetch_data(1).await;
        assert_eq!(result, Ok("Data for 1".to_string()));
    }

    #[tokio::test]
    async fn test_fetch_error() {
        let result = fetch_data(0).await;
        assert!(result.is_err());
    }

    // Test avec timeout
    #[tokio::test]
    async fn test_with_timeout() {
        tokio::time::timeout(
            std::time::Duration::from_secs(5),
            fetch_data(1)
        )
        .await
        .expect("Test timed out")
        .expect("Fetch failed");
    }
}
```

## Explication
`#[tokio::test]` :
- Cree un runtime pour le test
- Permet d'utiliser `.await`
- Chaque test a son propre runtime

**Cargo.toml** :
```toml
[dev-dependencies]
tokio = { version = "1", features = ["test-util", "macros", "rt"] }
```

## A retenir
- `#[tokio::test]` pour tests async
- Chaque test est isole
- Ajoute `test-util` pour les helpers de test""",
    },
]

EXTRA_UNSAFE = [
    {
        "topic": "unsafe",
        "difficulty": "intermediaire",
        "user": "Comment utiliser correctement les raw pointers ?",
        "assistant": """## TL;DR
Cree des raw pointers avec `as *const T` ou `as *mut T`. Dereference uniquement dans un bloc `unsafe`.

## Probleme
Tu dois travailler avec des pointeurs pour FFI ou optimisation.

## Solution
```rust
fn main() {
    let x = 42;

    // Creer des raw pointers (safe)
    let ptr: *const i32 = &x as *const i32;
    let ptr2: *const i32 = &x;  // Coercion implicite

    // Dereference (unsafe)
    unsafe {
        println!("Value: {}", *ptr);
    }

    // Pointer mutable
    let mut y = 10;
    let ptr_mut: *mut i32 = &mut y;

    unsafe {
        *ptr_mut = 20;
        println!("Modified: {}", *ptr_mut);
    }

    // Pointer arithmetique
    let arr = [1, 2, 3, 4, 5];
    let ptr = arr.as_ptr();

    unsafe {
        println!("arr[2] = {}", *ptr.add(2));
    }
}
```

## Explication
**Regles de securite (tu dois garantir)** :
- Le pointeur est valide (pas null, pas dangling)
- La donnee pointee est initialisee
- Pas de data races
- Alignement correct

**Conversions** :
```rust
// Reference -> raw pointer (safe)
let ptr = &x as *const i32;

// Raw pointer -> reference (unsafe)
unsafe {
    let ref_back = &*ptr;
}
```

## A retenir
- Creation de ptr = safe
- Dereference = unsafe
- Tu es responsable de la validite""",
    },
]

# ============================================================================
# M9 Part 5: Dernieres series pour 200+
# ============================================================================

FINAL_LIFETIMES = [
    {"topic": "lifetimes", "difficulty": "debutant", "user": "Que signifie `'_` dans une signature de type ?", "assistant": """## TL;DR
`'_` est une lifetime anonyme/elisee. Le compilateur l'infere automatiquement.

## Solution
```rust
// Ces deux sont equivalents
fn first(s: &str) -> &str { &s[..1] }
fn first_explicit<'a>(s: &'a str) -> &'a str { &s[..1] }

// '_ indique "infere la lifetime"
struct Wrapper<'a>(&'a str);
fn wrap(s: &str) -> Wrapper<'_> {
    Wrapper(s)
}
```

## Explication
`'_` dit "je sais qu'il y a une lifetime ici, laisse le compilateur la determiner".

## A retenir
- `'_` = lifetime anonyme
- Utile pour reduire le bruit
- Le compilateur infere"""},
    {"topic": "lifetimes", "difficulty": "intermediaire", "user": "Comment utiliser les lifetimes avec des closures stockees ?", "assistant": """## TL;DR
Utilise `Box<dyn Fn() + 'a>` ou un generic avec bound.

## Solution
```rust
struct Handler<'a> {
    callback: Box<dyn Fn() + 'a>,
}

impl<'a> Handler<'a> {
    fn new<F: Fn() + 'a>(f: F) -> Self {
        Handler { callback: Box::new(f) }
    }

    fn call(&self) {
        (self.callback)();
    }
}

fn main() {
    let msg = String::from("Hello");
    let handler = Handler::new(|| println!("{}", msg));
    handler.call();
}
```

## A retenir
- `dyn Fn() + 'a` lie la closure aux captures
- `'static` si pas de captures
- Box pour le stockage dynamique"""},
    {"topic": "lifetimes", "difficulty": "avance", "user": "Explique le pattern 'self lifetime' pour les methodes qui retournent self.", "assistant": """## TL;DR
Retourner `&mut self` permet le chainage. La lifetime est implicite.

## Solution
```rust
struct Builder {
    value: i32,
}

impl Builder {
    fn new() -> Self { Builder { value: 0 } }

    fn add(&mut self, n: i32) -> &mut Self {
        self.value += n;
        self
    }

    fn multiply(&mut self, n: i32) -> &mut Self {
        self.value *= n;
        self
    }

    fn build(self) -> i32 { self.value }
}

fn main() {
    let result = Builder::new()
        .add(5)
        .multiply(2)
        .add(3)
        .build();
    println!("{}", result);  // 13
}
```

## Explication
L'elision donne `fn add<'a>(&'a mut self, n: i32) -> &'a mut Self`.

## A retenir
- Retourne `&mut Self` pour chainage
- Lifetime implicite sur self
- `build(self)` consomme a la fin"""},
]

FINAL_BORROWING = [
    {"topic": "borrowing", "difficulty": "debutant", "user": "Pourquoi `let x = &mut y; let z = &mut y;` ne compile pas ?", "assistant": """## TL;DR
Une seule reference mutable a la fois. C'est la regle fondamentale.

## Solution
```rust
let mut y = 5;

// Sequentiel - OK
{
    let x = &mut y;
    *x += 1;
}
let z = &mut y;  // OK: x n'existe plus

// Ou utiliser la premiere avant de creer la deuxieme
let mut y = 5;
let x = &mut y;
*x += 1;
// x plus utilisee apres
let z = &mut y;  // OK avec NLL
```

## A retenir
- Une seule `&mut` a la fois
- NLL permet plus de flexibilite
- Utilise des scopes explicites si besoin"""},
    {"topic": "borrowing", "difficulty": "intermediaire", "user": "Comment fonctionne le borrow splitting sur les tuples ?", "assistant": """## TL;DR
Tu peux emprunter differents elements d'un tuple separement.

## Solution
```rust
fn main() {
    let mut pair = (String::from("a"), String::from("b"));

    // Split borrow - OK
    let first = &mut pair.0;
    let second = &mut pair.1;

    first.push('!');
    second.push('?');

    println!("{:?}", pair);  // ("a!", "b?")
}
```

## Explication
Le compilateur peut prouver que `.0` et `.1` sont disjoints.

Meme principe avec structs :
```rust
struct Data { a: String, b: String }
let mut d = Data { ... };
let ra = &mut d.a;
let rb = &mut d.b;  // OK: champs disjoints
```

## A retenir
- Elements de tuple = emprunts disjoints
- Champs de struct aussi
- Le compilateur verifie la non-interference"""},
    {"topic": "borrowing", "difficulty": "intermediaire", "user": "Comment utiliser `mem::take` et `mem::replace` ?", "assistant": """## TL;DR
`take` remplace par defaut et retourne l'original. `replace` remplace par une valeur donnee.

## Solution
```rust
use std::mem;

fn main() {
    let mut s = String::from("hello");

    // take: remplace par Default, retourne l'original
    let taken = mem::take(&mut s);
    println!("Taken: {}, Remaining: '{}'", taken, s);
    // Taken: hello, Remaining: ''

    // replace: remplace par valeur donnee
    let mut v = vec![1, 2, 3];
    let old = mem::replace(&mut v, vec![4, 5]);
    println!("Old: {:?}, New: {:?}", old, v);
    // Old: [1, 2, 3], New: [4, 5]
}
```

## Explication
Utile quand tu veux extraire une valeur d'une `&mut` :
- `take`: laisse une valeur par defaut
- `replace`: tu fournis le remplacement
- `swap`: echange deux valeurs

## A retenir
- `take` pour extraire et laisser vide
- `replace` pour echanger avec une valeur
- Evite les clones inutiles"""},
]

FINAL_ASYNC = [
    {"topic": "async", "difficulty": "debutant", "user": "Comment lire un fichier de maniere async ?", "assistant": """## TL;DR
Utilise `tokio::fs` pour les operations fichier asynchrones.

## Solution
```rust
use tokio::fs;
use tokio::io::AsyncReadExt;

#[tokio::main]
async fn main() -> std::io::Result<()> {
    // Lire tout le fichier
    let content = fs::read_to_string("file.txt").await?;
    println!("{}", content);

    // Lire en bytes
    let bytes = fs::read("file.txt").await?;

    // Avec un buffer
    let mut file = fs::File::open("file.txt").await?;
    let mut buf = Vec::new();
    file.read_to_end(&mut buf).await?;

    Ok(())
}
```

## A retenir
- `tokio::fs` pour fichiers async
- `AsyncReadExt` pour les methodes read
- Ne bloque pas le runtime"""},
    {"topic": "async", "difficulty": "intermediaire", "user": "Comment implementer un retry avec backoff ?", "assistant": """## TL;DR
Boucle avec sleep croissant entre les tentatives.

## Solution
```rust
use tokio::time::{sleep, Duration};

async fn fetch_with_retry<T, E, F, Fut>(
    f: F,
    max_retries: u32,
) -> Result<T, E>
where
    F: Fn() -> Fut,
    Fut: std::future::Future<Output = Result<T, E>>,
{
    let mut attempts = 0;
    loop {
        match f().await {
            Ok(v) => return Ok(v),
            Err(e) if attempts < max_retries => {
                attempts += 1;
                let delay = Duration::from_millis(100 * 2u64.pow(attempts));
                println!("Retry {} after {:?}", attempts, delay);
                sleep(delay).await;
            }
            Err(e) => return Err(e),
        }
    }
}
```

## Explication
Backoff exponentiel : 200ms, 400ms, 800ms...
Evite de surcharger un service en difficulte.

## A retenir
- Backoff exponentiel pour les retries
- Cap le nombre de tentatives
- Peut ajouter du jitter (random)"""},
    {"topic": "async", "difficulty": "avance", "user": "Comment partager un etat mutable entre taches async ?", "assistant": """## TL;DR
Utilise `Arc<Mutex<T>>` ou `Arc<RwLock<T>>` avec tokio.

## Solution
```rust
use std::sync::Arc;
use tokio::sync::Mutex;

struct AppState {
    counter: i32,
    data: Vec<String>,
}

#[tokio::main]
async fn main() {
    let state = Arc::new(Mutex::new(AppState {
        counter: 0,
        data: vec![],
    }));

    let mut handles = vec![];
    for i in 0..5 {
        let state = Arc::clone(&state);
        handles.push(tokio::spawn(async move {
            let mut guard = state.lock().await;
            guard.counter += 1;
            guard.data.push(format!("Task {}", i));
        }));
    }

    for h in handles { h.await.unwrap(); }

    let state = state.lock().await;
    println!("Counter: {}, Data: {:?}", state.counter, state.data);
}
```

## Explication
`tokio::sync::Mutex` vs `std::sync::Mutex` :
- tokio : `.await` pendant le lock
- std : bloque le thread

## A retenir
- `tokio::sync::Mutex` pour async
- `Arc` pour partage multi-taches
- Garde les sections critiques courtes"""},
]

FINAL_TRAITS = [
    {"topic": "traits", "difficulty": "debutant", "user": "Comment deriver automatiquement des traits ?", "assistant": """## TL;DR
Utilise `#[derive(...)]` pour les traits standard.

## Solution
```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash, Default)]
struct User {
    name: String,
    age: u32,
}

fn main() {
    let u1 = User::default();  // Default
    let u2 = u1.clone();       // Clone
    println!("{:?}", u1);      // Debug
    assert_eq!(u1, u2);        // PartialEq

    use std::collections::HashSet;
    let mut set = HashSet::new();
    set.insert(u1);            // Hash + Eq
}
```

## Explication
Traits derivables :
- `Debug` : formatage {:?}
- `Clone` : .clone()
- `Copy` : copie implicite
- `PartialEq`, `Eq` : ==
- `PartialOrd`, `Ord` : <, >, etc.
- `Hash` : hachage
- `Default` : valeur par defaut

## A retenir
- `#[derive]` genere l'implementation
- Tous les champs doivent supporter le trait
- Rapide et sans erreur"""},
    {"topic": "traits", "difficulty": "intermediaire", "user": "Comment implementer Default pour une struct ?", "assistant": """## TL;DR
Implemente le trait `Default` avec une methode `default()`.

## Solution
```rust
struct Config {
    host: String,
    port: u16,
    debug: bool,
}

impl Default for Config {
    fn default() -> Self {
        Config {
            host: String::from("localhost"),
            port: 8080,
            debug: false,
        }
    }
}

fn main() {
    let config = Config::default();

    // Struct update syntax
    let custom = Config {
        port: 3000,
        ..Default::default()
    };
}
```

## Explication
`Default` permet :
- Valeurs par defaut sensees
- Struct update syntax `..Default::default()`
- Collections vides automatiques

## A retenir
- `impl Default for Type`
- Retourne `Self` avec valeurs sensees
- Utile avec builders et options"""},
    {"topic": "traits", "difficulty": "avance", "user": "Comment utiliser les supertraits ?", "assistant": """## TL;DR
Un supertrait est un trait qui en requiert un autre : `trait A: B`.

## Solution
```rust
use std::fmt::Debug;

// Printable requiert Debug
trait Printable: Debug {
    fn print(&self) {
        println!("{:?}", self);
    }
}

#[derive(Debug)]
struct Item { name: String }

impl Printable for Item {}

// Trait avec multiple supertraits
trait Serializable: Clone + Debug + Default {
    fn serialize(&self) -> String;
}
```

## Explication
`trait A: B + C` signifie :
- Pour implementer A, tu dois d'abord implementer B et C
- Les methodes de A peuvent utiliser B et C
- Les bounds se combinent

## A retenir
- `:` pour les supertraits
- `+` pour combiner
- Les impls des supertraits sont requises"""},
]

FINAL_GENERICS = [
    {"topic": "generics", "difficulty": "debutant", "user": "Comment ecrire une struct generique ?", "assistant": """## TL;DR
Declare le parametre de type apres le nom : `struct Name<T>`.

## Solution
```rust
struct Pair<T> {
    first: T,
    second: T,
}

struct Mixed<T, U> {
    key: T,
    value: U,
}

impl<T> Pair<T> {
    fn new(first: T, second: T) -> Self {
        Pair { first, second }
    }
}

// Impl seulement si T est Clone
impl<T: Clone> Pair<T> {
    fn swap(&self) -> Pair<T> {
        Pair {
            first: self.second.clone(),
            second: self.first.clone(),
        }
    }
}
```

## A retenir
- `<T>` apres le nom
- `impl<T>` pour les methodes
- Contraintes conditionnelles possibles"""},
    {"topic": "generics", "difficulty": "intermediaire", "user": "C'est quoi le turbofish `::<>` ?", "assistant": """## TL;DR
Le turbofish specifie les types generiques explicitement quand l'inference ne suffit pas.

## Solution
```rust
fn main() {
    // Le type ne peut pas etre infere
    let v = Vec::<i32>::new();

    // Collect a besoin de savoir le type cible
    let numbers: Vec<i32> = (1..5).collect();
    // Ou avec turbofish
    let numbers = (1..5).collect::<Vec<i32>>();
    let numbers = (1..5).collect::<Vec<_>>();  // _ = infere

    // Parse
    let n = "42".parse::<i32>().unwrap();
}
```

## Explication
- `name::<Type>` = turbofish
- Utilise quand le compilateur ne peut pas inferer
- `_` pour laisser le compilateur deviner

## A retenir
- Turbofish = `::<Type>`
- Surtout pour `collect`, `parse`, `into`
- `_` pour inference partielle"""},
]

FINAL_PATTERNS = [
    {"topic": "pattern_matching", "difficulty": "debutant", "user": "Comment deconstruire un tuple dans un let ?", "assistant": """## TL;DR
Utilise les parentheses dans le pattern : `let (a, b) = tuple;`.

## Solution
```rust
fn main() {
    let pair = (1, "hello");
    let (num, text) = pair;
    println!("{}: {}", num, text);

    // Ignorer des elements
    let triple = (1, 2, 3);
    let (first, _, third) = triple;

    // Dans une boucle
    let pairs = vec![(1, "a"), (2, "b")];
    for (n, s) in pairs {
        println!("{}: {}", n, s);
    }

    // Avec des structs
    struct Point { x: i32, y: i32 }
    let p = Point { x: 1, y: 2 };
    let Point { x, y } = p;
}
```

## A retenir
- `let (a, b) = tuple`
- `_` pour ignorer
- Fonctionne partout ou on peut mettre un pattern"""},
    {"topic": "pattern_matching", "difficulty": "intermediaire", "user": "Comment utiliser @ pour binder et matcher ?", "assistant": """## TL;DR
`name @ pattern` lie la valeur a `name` tout en verifiant `pattern`.

## Solution
```rust
fn main() {
    let x = 5;

    match x {
        n @ 1..=5 => println!("{} is in 1-5", n),
        n @ 6..=10 => println!("{} is in 6-10", n),
        n => println!("{} is out of range", n),
    }

    // Avec enums
    enum Message {
        Hello { id: i32 },
    }

    let msg = Message::Hello { id: 5 };
    match msg {
        Message::Hello { id: id @ 3..=7 } => {
            println!("Found id {} in range", id);
        }
        Message::Hello { id } => {
            println!("Other id: {}", id);
        }
    }
}
```

## A retenir
- `name @ pattern` bind + match
- Utile pour ranges et conditions
- Evite de re-matcher pour avoir la valeur"""},
]

FINAL_ERRORS = [
    {"topic": "error_handling", "difficulty": "debutant", "user": "Comment transformer un Option en Result ?", "assistant": """## TL;DR
Utilise `.ok_or()` ou `.ok_or_else()` pour convertir None en erreur.

## Solution
```rust
fn find_user(id: u32) -> Option<String> {
    if id == 1 { Some("Alice".into()) } else { None }
}

fn get_user(id: u32) -> Result<String, String> {
    find_user(id).ok_or_else(|| format!("User {} not found", id))
}

fn main() {
    match get_user(1) {
        Ok(name) => println!("Found: {}", name),
        Err(e) => println!("Error: {}", e),
    }
}
```

## Explication
- `ok_or(err)` : erreur evaluee immediatement
- `ok_or_else(|| err)` : erreur evaluee si None

## A retenir
- Option -> Result avec `ok_or`
- Result -> Option avec `.ok()` ou `.err()`
- Permet d'utiliser `?` ensuite"""},
    {"topic": "error_handling", "difficulty": "intermediaire", "user": "Comment utiliser map_err pour transformer les erreurs ?", "assistant": """## TL;DR
`map_err` transforme le type d'erreur sans toucher au succes.

## Solution
```rust
use std::num::ParseIntError;

#[derive(Debug)]
struct AppError(String);

fn parse_port(s: &str) -> Result<u16, AppError> {
    s.parse::<u16>()
        .map_err(|e| AppError(format!("Invalid port: {}", e)))
}

fn main() {
    match parse_port("abc") {
        Ok(port) => println!("Port: {}", port),
        Err(e) => println!("Error: {:?}", e),
    }
}
```

## Explication
Transformations sur Result :
- `map` : transforme Ok
- `map_err` : transforme Err
- `and_then` : chaine des operations

## A retenir
- `map_err(|e| ...)` pour convertir l'erreur
- Ne touche pas a la valeur Ok
- Utile avant `?` pour unifier les types"""},
]

FINAL_ITERATORS = [
    {"topic": "iterators", "difficulty": "debutant", "user": "Comment filtrer et transformer une liste en une seule passe ?", "assistant": """## TL;DR
Chaine `filter()` et `map()`, ou utilise `filter_map()`.

## Solution
```rust
fn main() {
    let numbers = vec![1, 2, 3, 4, 5, 6];

    // filter + map
    let evens_doubled: Vec<i32> = numbers.iter()
        .filter(|&&x| x % 2 == 0)
        .map(|&x| x * 2)
        .collect();
    // [4, 8, 12]

    // filter_map - combine les deux
    let parsed: Vec<i32> = vec!["1", "two", "3"]
        .iter()
        .filter_map(|s| s.parse().ok())
        .collect();
    // [1, 3]
}
```

## Explication
`filter_map` prend une closure qui retourne `Option`:
- `Some(x)` : garde x
- `None` : ignore

## A retenir
- Les iterateurs sont lazy
- Chaine les operations
- `collect()` a la fin"""},
    {"topic": "iterators", "difficulty": "intermediaire", "user": "Comment creer un iterateur infini ?", "assistant": """## TL;DR
Utilise `std::iter::repeat`, `from_fn`, ou `successors`.

## Solution
```rust
use std::iter;

fn main() {
    // Repete indefiniment
    let ones = iter::repeat(1);

    // Genere avec une fonction
    let mut n = 0;
    let counter = iter::from_fn(move || {
        n += 1;
        Some(n)
    });

    // Successeurs
    let powers = iter::successors(Some(1), |&n| Some(n * 2));

    // TOUJOURS limiter!
    let first_10: Vec<_> = powers.take(10).collect();
    println!("{:?}", first_10);
    // [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
}
```

## A retenir
- `repeat(v)` repete v
- `from_fn` avec closure mutable
- TOUJOURS `take(n)` ou `take_while`"""},
]

FINAL_EXERCISES = [
    {"topic": "lifetimes", "difficulty": "intermediaire", "user": "Un exercice sur les lifetimes avec des slices.", "assistant": """## TL;DR
Exercice : retourner le slice le plus court.

## Probleme
Ecrire une fonction qui retourne le plus court de deux slices.

## Solution
```rust
fn shortest<'a, T>(a: &'a [T], b: &'a [T]) -> &'a [T] {
    if a.len() <= b.len() { a } else { b }
}

fn main() {
    let arr1 = [1, 2, 3, 4, 5];
    let arr2 = [10, 20];
    let result = shortest(&arr1, &arr2);
    println!("{:?}", result);  // [10, 20]
}
```

## A retenir
- Meme lifetime pour entrees et sortie
- Le slice retourne vit tant que les deux existent"""},
    {"topic": "borrowing", "difficulty": "debutant", "user": "Un exercice pour comprendre les references.", "assistant": """## TL;DR
Exercice : incrementer un compteur via reference.

## Solution
```rust
fn increment(n: &mut i32) {
    *n += 1;
}

fn main() {
    let mut count = 0;

    increment(&mut count);
    increment(&mut count);
    increment(&mut count);

    assert_eq!(count, 3);
    println!("Count: {}", count);
}
```

## Explication
- `&mut i32` : reference mutable vers i32
- `*n` : dereference pour modifier

## A retenir
- `&mut` pour modifier via reference
- `*` pour dereference"""},
    {"topic": "async", "difficulty": "intermediaire", "user": "Un exercice sur la gestion d'erreurs async.", "assistant": """## TL;DR
Exercice : fetch avec retry et erreur typee.

## Solution
```rust
use tokio::time::{sleep, Duration};

#[derive(Debug)]
enum FetchError {
    NetworkError,
    Timeout,
    MaxRetries,
}

async fn fetch(url: &str) -> Result<String, FetchError> {
    // Simule un echec occasionnel
    if rand::random::<bool>() {
        Err(FetchError::NetworkError)
    } else {
        Ok(format!("Response from {}", url))
    }
}

async fn fetch_with_retry(url: &str, max: u32) -> Result<String, FetchError> {
    for attempt in 1..=max {
        match fetch(url).await {
            Ok(data) => return Ok(data),
            Err(_) if attempt < max => {
                sleep(Duration::from_millis(100 * attempt as u64)).await;
            }
            Err(e) => return Err(e),
        }
    }
    Err(FetchError::MaxRetries)
}
```

## A retenir
- Enum pour types d'erreur
- Boucle avec limite de retries
- Backoff entre tentatives"""},
    {"topic": "traits", "difficulty": "intermediaire", "user": "Un exercice sur l'implementation de From et Into.", "assistant": """## TL;DR
Exercice : convertir entre Celsius et Fahrenheit.

## Solution
```rust
struct Celsius(f64);
struct Fahrenheit(f64);

impl From<Celsius> for Fahrenheit {
    fn from(c: Celsius) -> Self {
        Fahrenheit(c.0 * 9.0 / 5.0 + 32.0)
    }
}

impl From<Fahrenheit> for Celsius {
    fn from(f: Fahrenheit) -> Self {
        Celsius((f.0 - 32.0) * 5.0 / 9.0)
    }
}

fn main() {
    let c = Celsius(100.0);
    let f: Fahrenheit = c.into();  // Into gratuit!
    println!("100C = {}F", f.0);   // 212

    let f = Fahrenheit(32.0);
    let c: Celsius = f.into();
    println!("32F = {}C", c.0);    // 0
}
```

## A retenir
- Impl `From<A> for B`
- `Into<B>` est automatique
- Permet `.into()` et `B::from(a)`"""},
    {"topic": "generics", "difficulty": "intermediaire", "user": "Un exercice sur les generics avec trait bounds.", "assistant": """## TL;DR
Exercice : fonction generique qui trouve le minimum.

## Solution
```rust
fn minimum<T: PartialOrd>(list: &[T]) -> Option<&T> {
    if list.is_empty() {
        return None;
    }

    let mut min = &list[0];
    for item in list.iter().skip(1) {
        if item < min {
            min = item;
        }
    }
    Some(min)
}

fn main() {
    let numbers = vec![3, 1, 4, 1, 5];
    assert_eq!(minimum(&numbers), Some(&1));

    let words = vec!["banana", "apple", "cherry"];
    assert_eq!(minimum(&words), Some(&"apple"));

    let empty: Vec<i32> = vec![];
    assert_eq!(minimum(&empty), None);
}
```

## A retenir
- `T: PartialOrd` pour `<`
- `Option` pour liste vide
- Fonctionne avec tout type comparable"""},
]

# ============================================================================
# M9 Part 6: Derniere serie pour 200+
# ============================================================================

LAST_BATCH = [
    {"topic": "lifetimes", "difficulty": "debutant", "user": "Comment savoir si j'ai besoin d'annoter les lifetimes ?", "assistant": """## TL;DR
Les lifetimes sont necessaires quand le compilateur ne peut pas inferer la relation entre references en entree et sortie.

## Solution
**Pas besoin** (elision) :
```rust
fn first(s: &str) -> &str { &s[..1] }  // Une entree -> sortie liee
```

**Necessaire** :
```rust
fn choose<'a>(a: &'a str, b: &'a str) -> &'a str {  // Plusieurs entrees
    if a.len() > b.len() { a } else { b }
}
```

## A retenir
- Une ref en entree, une en sortie -> elision
- Plusieurs refs ou struct -> annotation"""},
    {"topic": "borrowing", "difficulty": "debutant", "user": "C'est quoi la difference entre `ref` et `&` dans les patterns ?", "assistant": """## TL;DR
`ref` dans un pattern cree une reference. `&` dans un pattern matche une reference existante.

## Solution
```rust
let x = 5;

// ref cree une reference
let ref r = x;  // r: &i32

// equivalent a
let r = &x;

// & matche une reference
let y = &5;
let &z = y;  // z: i32 (dereference)
```

## A retenir
- `ref` : pattern qui emprunte
- `&` : pattern qui dereference
- `ref` souvent dans match"""},
    {"topic": "async", "difficulty": "debutant", "user": "Pourquoi mon programme async se termine sans rien faire ?", "assistant": """## TL;DR
Tu as probablement oublie `.await` ou le runtime se termine avant les taches.

## Solution
```rust
#[tokio::main]
async fn main() {
    // MAUVAIS - la tache n'est pas attendue
    tokio::spawn(async { println!("Never printed"); });

    // BON - on attend
    tokio::spawn(async { println!("Printed!"); }).await.unwrap();
}
```

## A retenir
- Toujours `.await` les futures
- spawn sans await peut etre abandonne
- Le runtime termine quand main termine"""},
    {"topic": "traits", "difficulty": "debutant", "user": "Comment rendre mon type printable avec println! ?", "assistant": """## TL;DR
Derive ou implemente `Debug` pour `{:?}`, ou `Display` pour `{}`.

## Solution
```rust
#[derive(Debug)]
struct Point { x: i32, y: i32 }

use std::fmt;
impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}

fn main() {
    let p = Point { x: 1, y: 2 };
    println!("{:?}", p);  // Debug
    println!("{}", p);    // Display
}
```

## A retenir
- `Debug` : derive, format {:?}
- `Display` : impl manuelle, format {}"""},
    {"topic": "error_handling", "difficulty": "debutant", "user": "Comment retourner plusieurs types d'erreurs ?", "assistant": """## TL;DR
Utilise un enum d'erreur ou `Box<dyn Error>`.

## Solution
```rust
use std::io;
use std::num::ParseIntError;

#[derive(Debug)]
enum MyError {
    Io(io::Error),
    Parse(ParseIntError),
}

impl From<io::Error> for MyError {
    fn from(e: io::Error) -> Self { MyError::Io(e) }
}

impl From<ParseIntError> for MyError {
    fn from(e: ParseIntError) -> Self { MyError::Parse(e) }
}

fn process() -> Result<i32, MyError> {
    let content = std::fs::read_to_string("num.txt")?;
    let n: i32 = content.trim().parse()?;
    Ok(n)
}
```

## A retenir
- Enum pour erreurs typees
- `impl From` pour conversion avec ?
- `Box<dyn Error>` pour simplicite"""},
    {"topic": "generics", "difficulty": "debutant", "user": "Comment retourner un type qui implemente un trait ?", "assistant": """## TL;DR
Utilise `impl Trait` en retour ou `Box<dyn Trait>`.

## Solution
```rust
// impl Trait - type concret (compile-time)
fn make_iter() -> impl Iterator<Item = i32> {
    (1..10).filter(|x| x % 2 == 0)
}

// Box<dyn Trait> - polymorphisme (runtime)
fn make_animal(dog: bool) -> Box<dyn Animal> {
    if dog { Box::new(Dog) } else { Box::new(Cat) }
}
```

## A retenir
- `impl Trait` : un seul type concret
- `Box<dyn Trait>` : plusieurs types possibles"""},
    {"topic": "pattern_matching", "difficulty": "debutant", "user": "Comment ignorer des valeurs dans un pattern ?", "assistant": """## TL;DR
Utilise `_` pour ignorer une valeur, `..` pour ignorer plusieurs.

## Solution
```rust
fn main() {
    let tuple = (1, 2, 3, 4, 5);

    // Ignore un element
    let (first, _, third, _, _) = tuple;

    // Ignore le reste
    let (first, ..) = tuple;
    let (.., last) = tuple;
    let (first, .., last) = tuple;

    // Dans les structs
    struct Point { x: i32, y: i32, z: i32 }
    let p = Point { x: 1, y: 2, z: 3 };
    let Point { x, .. } = p;  // Ignore y et z
}
```

## A retenir
- `_` pour une valeur
- `..` pour plusieurs
- `_name` si tu veux le nom sans warning"""},
    {"topic": "ownership", "difficulty": "debutant", "user": "Comment fonctionne to_owned() vs clone() ?", "assistant": """## TL;DR
`to_owned()` convertit une reference en type owned. `clone()` copie un type owned.

## Solution
```rust
fn main() {
    let s: &str = "hello";

    // to_owned: &str -> String
    let owned: String = s.to_owned();

    // clone: String -> String
    let cloned: String = owned.clone();

    // Les deux sont equivalents ici
    let also: String = s.to_string();
}
```

## Explication
- `to_owned()` : `&T` -> `T::Owned` (via ToOwned trait)
- `clone()` : `&T` -> `T` (via Clone trait)

## A retenir
- `to_owned` pour ref -> owned
- `clone` pour owned -> owned
- Pour &str, les deux donnent String"""},
    {"topic": "iterators", "difficulty": "debutant", "user": "Comment transformer un Vec avec map ?", "assistant": """## TL;DR
`.map()` transforme chaque element. Utilise `.collect()` pour avoir un nouveau Vec.

## Solution
```rust
fn main() {
    let numbers = vec![1, 2, 3, 4, 5];

    let doubled: Vec<i32> = numbers.iter()
        .map(|x| x * 2)
        .collect();
    // [2, 4, 6, 8, 10]

    // Transformer en autre type
    let strings: Vec<String> = numbers.iter()
        .map(|n| n.to_string())
        .collect();
}
```

## A retenir
- `map` transforme element par element
- Lazy : rien n'arrive avant collect
- Le type de collect determine le resultat"""},
    {"topic": "concurrency", "difficulty": "debutant", "user": "Comment creer un thread simple ?", "assistant": """## TL;DR
Utilise `std::thread::spawn` avec une closure.

## Solution
```rust
use std::thread;
use std::time::Duration;

fn main() {
    let handle = thread::spawn(|| {
        for i in 1..5 {
            println!("Thread: {}", i);
            thread::sleep(Duration::from_millis(100));
        }
    });

    for i in 1..3 {
        println!("Main: {}", i);
        thread::sleep(Duration::from_millis(100));
    }

    handle.join().unwrap();  // Attend la fin du thread
}
```

## A retenir
- `spawn` lance un thread
- `join` attend sa fin
- `move` pour capturer des variables"""},
    {"topic": "structs", "difficulty": "debutant", "user": "Comment avoir des champs prives avec un constructeur public ?", "assistant": """## TL;DR
Les champs sont prives par defaut. Fournis une fonction `new` publique.

## Solution
```rust
pub struct User {
    name: String,  // prive
    age: u32,      // prive
}

impl User {
    pub fn new(name: String, age: u32) -> Self {
        User { name, age }
    }

    pub fn name(&self) -> &str { &self.name }
    pub fn age(&self) -> u32 { self.age }
}

// Depuis un autre module :
// let u = User { name: ... };  // ERREUR: champs prives
// let u = User::new(...);       // OK
```

## A retenir
- Champs prives par defaut
- `pub fn new()` pour construction
- Getters pour lecture"""},
    {"topic": "enums", "difficulty": "debutant", "user": "Comment ajouter des methodes a un enum ?", "assistant": """## TL;DR
Utilise `impl` comme pour une struct.

## Solution
```rust
enum Status {
    Active,
    Inactive,
    Pending(String),
}

impl Status {
    fn is_active(&self) -> bool {
        matches!(self, Status::Active)
    }

    fn description(&self) -> &str {
        match self {
            Status::Active => "Currently active",
            Status::Inactive => "Not active",
            Status::Pending(_) => "Waiting",
        }
    }
}

fn main() {
    let s = Status::Active;
    println!("{}: {}", s.is_active(), s.description());
}
```

## A retenir
- `impl EnumName` pour methodes
- `matches!` pour test rapide
- Methodes peuvent matcher les variants"""},
    {"topic": "modules", "difficulty": "debutant", "user": "C'est quoi la difference entre `mod` et `use` ?", "assistant": """## TL;DR
`mod` declare/inclut un module. `use` cree un raccourci pour y acceder.

## Solution
```rust
// mod declare le module
mod math {
    pub fn add(a: i32, b: i32) -> i32 { a + b }
}

// use cree un raccourci
use math::add;

fn main() {
    // Sans use
    let x = math::add(1, 2);

    // Avec use
    let y = add(3, 4);
}
```

## A retenir
- `mod` : declare/charge le module
- `use` : raccourci pour l'acces
- `mod nom;` charge nom.rs ou nom/mod.rs"""},
    {"topic": "closures", "difficulty": "debutant", "user": "Comment passer une closure a une fonction ?", "assistant": """## TL;DR
Utilise un parametre generique avec trait bound `Fn`, `FnMut`, ou `FnOnce`.

## Solution
```rust
fn apply<F>(f: F, x: i32) -> i32
where F: Fn(i32) -> i32
{
    f(x)
}

fn main() {
    let double = |x| x * 2;
    let result = apply(double, 5);
    println!("{}", result);  // 10

    // Avec capture
    let multiplier = 3;
    let triple = |x| x * multiplier;
    println!("{}", apply(triple, 5));  // 15
}
```

## A retenir
- `Fn` : peut etre appelee plusieurs fois
- `FnMut` : peut modifier ses captures
- `FnOnce` : consomme ses captures"""},
    {"topic": "testing", "difficulty": "debutant", "user": "Comment tester qu'une fonction panic ?", "assistant": """## TL;DR
Utilise `#[should_panic]` sur le test.

## Solution
```rust
fn divide(a: i32, b: i32) -> i32 {
    if b == 0 { panic!("Division by zero"); }
    a / b
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[should_panic(expected = "Division by zero")]
    fn test_divide_by_zero() {
        divide(10, 0);
    }

    #[test]
    fn test_normal_divide() {
        assert_eq!(divide(10, 2), 5);
    }
}
```

## A retenir
- `#[should_panic]` attend un panic
- `expected = "msg"` verifie le message
- Le test passe si le panic arrive"""},
    {"topic": "smart_pointers", "difficulty": "debutant", "user": "Quand utiliser Box vs juste mettre la valeur sur la stack ?", "assistant": """## TL;DR
Box quand : type recursif, grande taille, ou trait object.

## Solution
```rust
// Type recursif
enum List {
    Cons(i32, Box<List>),  // Box necessaire
    Nil,
}

// Grande taille
struct BigData { data: [u8; 1_000_000] }
let big = Box::new(BigData { data: [0; 1_000_000] });

// Trait object
let animal: Box<dyn Animal> = Box::new(Dog);
```

## A retenir
- Box pour types de taille inconnue a la compilation
- Box pour eviter de copier de gros objets
- Box pour le polymorphisme avec dyn Trait"""},
    {"topic": "unsafe", "difficulty": "debutant", "user": "Quand est-ce que unsafe est vraiment necessaire ?", "assistant": """## TL;DR
FFI, optimisations bas-niveau, et abstractions sur des invariants que Rust ne peut pas verifier.

## Solution
```rust
// 1. FFI
extern "C" { fn strlen(s: *const i8) -> usize; }

// 2. Raw pointers
let ptr: *const i32 = &x;
unsafe { println!("{}", *ptr); }

// 3. Static mut
static mut COUNTER: i32 = 0;
unsafe { COUNTER += 1; }

// La plupart du code n'en a PAS besoin!
```

## A retenir
- FFI = unsafe
- Raw pointer deref = unsafe
- 99% du code Rust est safe"""},
    {"topic": "collections", "difficulty": "debutant", "user": "Comment inserer dans un HashMap seulement si la cle n'existe pas ?", "assistant": """## TL;DR
Utilise `entry().or_insert()`.

## Solution
```rust
use std::collections::HashMap;

fn main() {
    let mut map = HashMap::new();
    map.insert("a", 1);

    // N'insere que si absent
    map.entry("a").or_insert(99);  // Ignore: "a" existe
    map.entry("b").or_insert(2);   // Insere: "b" absent

    println!("{:?}", map);  // {"a": 1, "b": 2}
}
```

## A retenir
- `or_insert(v)` : insere v si absent
- `or_insert_with(|| v)` : lazy
- Retourne &mut a la valeur"""},
    {"topic": "macros", "difficulty": "debutant", "user": "Pourquoi certaines fonctions s'appellent avec un `!` ?", "assistant": """## TL;DR
Ce sont des macros, pas des fonctions. Elles operent a la compilation.

## Solution
```rust
// Macros courantes
println!("Hello, {}!", name);  // Nombre variable d'args
vec![1, 2, 3];                  // Genere du code
format!("{} {}", a, b);        // Formatte une String
assert!(condition);            // Teste et panic
panic!("Error!");              // Termine le programme

// Les macros peuvent faire ce que les fonctions ne peuvent pas :
// - Arguments variables
// - Code generation
// - Syntaxe custom
```

## A retenir
- `!` indique une macro
- Operent a la compilation
- Plus puissantes mais moins lisibles"""},
]

EXTRA_MISC = [
    {"topic": "lifetimes", "difficulty": "debutant", "user": "Pourquoi les references doivent vivre assez longtemps ?", "assistant": """## TL;DR
Une reference ne peut pas pointer vers des donnees detruites. Le compilateur verifie que la source vit plus longtemps que la reference.

## Solution
```rust
fn main() {
    let r;
    {
        let x = 5;
        r = &x;  // r emprunte x
    }  // x detruit ici
    // println!("{}", r);  // ERREUR: r pointe vers rien

    // Correct
    let x = 5;
    let r = &x;
    println!("{}", r);  // OK: x toujours valide
}
```

## A retenir
- Reference = pointeur + garantie de validite
- La source doit vivre plus longtemps
- Le compilateur verifie a la compilation"""},
    {"topic": "lifetimes", "difficulty": "debutant", "user": "Que se passe-t-il si je retourne une reference vers une variable locale ?", "assistant": """## TL;DR
Erreur de compilation. La variable locale est detruite a la fin de la fonction.

## Solution
```rust
// ERREUR
fn bad() -> &str {
    let s = String::from("hello");
    &s  // s sera detruite!
}

// BON : retourne owned
fn good() -> String {
    String::from("hello")
}

// BON : litterale (static)
fn also_good() -> &'static str {
    "hello"
}
```

## A retenir
- Variables locales meurent a la fin de la fonction
- Retourne owned ou 'static
- Le compilateur te protege"""},
    {"topic": "borrowing", "difficulty": "debutant", "user": "Comment modifier un element de vecteur par son index ?", "assistant": """## TL;DR
Accede avec `vec[i]` et le vecteur doit etre mutable.

## Solution
```rust
fn main() {
    let mut v = vec![1, 2, 3];

    v[0] = 10;  // Modification directe
    v[1] *= 2;  // Modification en place

    // Avec get_mut pour Option
    if let Some(x) = v.get_mut(2) {
        *x = 99;
    }

    println!("{:?}", v);  // [10, 4, 99]
}
```

## A retenir
- `let mut` necessaire
- `[i]` panic si hors bornes
- `get_mut(i)` retourne Option"""},
    {"topic": "async", "difficulty": "debutant", "user": "Comment attendre plusieurs futures sequentiellement ?", "assistant": """## TL;DR
Chaine les `.await` l'un apres l'autre.

## Solution
```rust
async fn step1() -> i32 { 1 }
async fn step2(x: i32) -> i32 { x + 1 }
async fn step3(x: i32) -> i32 { x * 2 }

#[tokio::main]
async fn main() {
    let a = step1().await;
    let b = step2(a).await;
    let c = step3(b).await;
    println!("{}", c);  // 4
}
```

## A retenir
- Chaque `.await` attend la completion
- Les resultats passent au suivant
- Sequentiel, pas parallele"""},
    {"topic": "traits", "difficulty": "debutant", "user": "Comment verifier si un type implemente un trait ?", "assistant": """## TL;DR
Le compilateur verifie automatiquement. Pas de verification runtime.

## Solution
```rust
fn process<T: Clone>(x: T) -> T {
    x.clone()
}

fn main() {
    let s = String::from("hello");
    process(s);  // OK: String impl Clone

    // let arr = [1; 100];
    // process(arr);  // OK: arrays impl Clone

    // Certains types n'implementent pas Clone
    // let file = File::open("x").unwrap();
    // process(file);  // ERREUR: File !Clone
}
```

## A retenir
- `T: Trait` = contrainte a la compilation
- Pas de verification runtime
- Erreur claire si pas implemente"""},
    {"topic": "error_handling", "difficulty": "debutant", "user": "Comment ignorer une erreur si je n'en ai pas besoin ?", "assistant": """## TL;DR
Utilise `let _ = ...` ou `if let Ok(_) = ...`.

## Solution
```rust
fn main() {
    // Ignorer completement
    let _ = std::fs::remove_file("temp.txt");

    // Ignorer mais executer
    let _ = do_something_fallible();

    // Traiter seulement le succes
    if let Ok(data) = fetch_data() {
        println!("Got: {}", data);
    }
    // L'erreur est ignoree silencieusement

    // Unwrap en dev (panic si erreur)
    let result = risky_op().unwrap();
}

fn do_something_fallible() -> Result<(), String> { Ok(()) }
fn fetch_data() -> Result<String, ()> { Ok("data".into()) }
fn risky_op() -> Result<i32, ()> { Ok(42) }
```

## A retenir
- `let _ = ...` ignore explicitement
- `if let Ok` traite le succes seulement
- En production, loggue les erreurs"""},
    {"topic": "generics", "difficulty": "debutant", "user": "Comment avoir un parametre optionnel avec Option<T> ?", "assistant": """## TL;DR
Accepte `Option<T>` et utilise `unwrap_or` ou `match`.

## Solution
```rust
fn greet(name: Option<&str>) {
    let name = name.unwrap_or("World");
    println!("Hello, {}!", name);
}

fn main() {
    greet(Some("Alice"));  // Hello, Alice!
    greet(None);           // Hello, World!
}

// Ou avec impl Into<Option<T>>
fn greet2(name: impl Into<Option<&'static str>>) {
    let name = name.into().unwrap_or("World");
    println!("Hello, {}!", name);
}
```

## A retenir
- `Option<T>` pour parametres optionnels
- `unwrap_or(default)` pour valeur par defaut
- `None` indique l'absence"""},
    {"topic": "pattern_matching", "difficulty": "debutant", "user": "Comment matcher plusieurs valeurs en une branche ?", "assistant": """## TL;DR
Utilise `|` pour combiner des patterns.

## Solution
```rust
fn describe(n: i32) -> &'static str {
    match n {
        0 => "zero",
        1 | 2 | 3 => "small",
        4..=10 => "medium",
        _ => "large",
    }
}

fn main() {
    println!("{}", describe(2));   // small
    println!("{}", describe(7));   // medium
    println!("{}", describe(100)); // large
}
```

## A retenir
- `|` pour alternatives
- `..=` pour ranges inclusifs
- `_` pour tout le reste"""},
    {"topic": "ownership", "difficulty": "debutant", "user": "Pourquoi certains types sont Copy et pas d'autres ?", "assistant": """## TL;DR
Copy = copie bit-a-bit safe. Les types qui gerent des ressources (heap, fichiers) ne peuvent pas etre Copy.

## Solution
```rust
// Copy types : copie implicite
let x: i32 = 5;
let y = x;  // Copy
println!("{}", x);  // OK

// Non-Copy : move
let s = String::from("hello");
let t = s;  // Move
// println!("{}", s);  // ERREUR

// Pourquoi String n'est pas Copy ?
// Car elle pointe vers le heap
// Copier les bits = deux pointeurs vers la meme memoire
// = double free a la destruction
```

## A retenir
- Copy = pas de gestion de ressources
- String, Vec, File = non-Copy
- i32, bool, &T, tuples de Copy = Copy"""},
    {"topic": "iterators", "difficulty": "debutant", "user": "Comment enumerer avec l'index ?", "assistant": """## TL;DR
Utilise `.enumerate()` pour avoir (index, element).

## Solution
```rust
fn main() {
    let items = vec!["a", "b", "c"];

    for (i, item) in items.iter().enumerate() {
        println!("{}: {}", i, item);
    }
    // 0: a
    // 1: b
    // 2: c

    // Avec find
    let pos = items.iter().position(|&x| x == "b");
    println!("Position of 'b': {:?}", pos);  // Some(1)
}
```

## A retenir
- `enumerate()` ajoute l'index
- Index commence a 0
- `position()` trouve l'index d'un element"""},
    {"topic": "concurrency", "difficulty": "debutant", "user": "Comment attendre plusieurs threads ?", "assistant": """## TL;DR
Stocke les handles et appelle `.join()` sur chacun.

## Solution
```rust
use std::thread;

fn main() {
    let mut handles = vec![];

    for i in 0..5 {
        handles.push(thread::spawn(move || {
            println!("Thread {} working", i);
            i * 10
        }));
    }

    // Attendre tous les threads
    let results: Vec<i32> = handles
        .into_iter()
        .map(|h| h.join().unwrap())
        .collect();

    println!("Results: {:?}", results);
}
```

## A retenir
- `spawn` retourne un `JoinHandle`
- `join()` attend et retourne le resultat
- Collect les handles pour attendre tous"""},
    {"topic": "structs", "difficulty": "debutant", "user": "C'est quoi #[derive] et comment l'utiliser ?", "assistant": """## TL;DR
`#[derive]` genere automatiquement l'implementation de certains traits.

## Solution
```rust
#[derive(Debug, Clone, PartialEq)]
struct Point {
    x: i32,
    y: i32,
}

fn main() {
    let p1 = Point { x: 1, y: 2 };

    println!("{:?}", p1);       // Debug
    let p2 = p1.clone();        // Clone
    assert_eq!(p1, p2);         // PartialEq
}
```

## A retenir
- Ajoute `#[derive(Trait1, Trait2)]`
- Tous les champs doivent supporter le trait
- Debug, Clone, Copy, PartialEq, Eq, Hash, Default"""},
    {"topic": "enums", "difficulty": "debutant", "user": "Comment extraire la valeur d'un variant d'enum ?", "assistant": """## TL;DR
Utilise `match`, `if let`, ou les methodes de Option/Result.

## Solution
```rust
enum Message {
    Text(String),
    Number(i32),
}

fn main() {
    let msg = Message::Text("hello".into());

    // match
    match &msg {
        Message::Text(s) => println!("Text: {}", s),
        Message::Number(n) => println!("Number: {}", n),
    }

    // if let pour un seul cas
    if let Message::Text(s) = &msg {
        println!("Got text: {}", s);
    }

    // Pour Option
    let opt = Some(42);
    let value = opt.unwrap();  // ou expect, unwrap_or
}
```

## A retenir
- `match` pour tous les cas
- `if let` pour un seul cas
- Option/Result ont des methodes helpers"""},
    {"topic": "modules", "difficulty": "debutant", "user": "Comment rendre un module ou une fonction publique ?", "assistant": """## TL;DR
Ajoute `pub` devant la declaration.

## Solution
```rust
// src/lib.rs
pub mod utils {
    pub fn helper() -> i32 { 42 }
    fn private_helper() {}  // Reste prive
}

pub fn public_fn() {}
fn private_fn() {}  // Prive au crate

// Visibilite restreinte
pub(crate) fn crate_only() {}
pub(super) fn parent_only() {}
```

## A retenir
- `pub` : visible partout
- `pub(crate)` : visible dans le crate
- Sans `pub` : prive au module"""},
    {"topic": "closures", "difficulty": "debutant", "user": "Pourquoi ma closure ne capture pas ma variable ?", "assistant": """## TL;DR
Les closures capturent par reference par defaut. Utilise `move` pour prendre ownership.

## Solution
```rust
fn main() {
    let s = String::from("hello");

    // Capture par reference
    let print = || println!("{}", s);
    print();
    println!("{}", s);  // s toujours valide

    // Capture par move
    let s = String::from("world");
    let consume = move || println!("{}", s);
    consume();
    // println!("{}", s);  // ERREUR: s moved
}
```

## A retenir
- Par defaut : reference minimale
- `move` : prend ownership
- move necessaire pour threads"""},
    {"topic": "testing", "difficulty": "debutant", "user": "Comment organiser les tests dans un projet ?", "assistant": """## TL;DR
Tests unitaires dans le meme fichier, tests d'integration dans `tests/`.

## Solution
```
my_crate/
├── src/
│   └── lib.rs      # Code + tests unitaires
└── tests/
    └── integration.rs  # Tests d'integration
```

```rust
// src/lib.rs
pub fn add(a: i32, b: i32) -> i32 { a + b }

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        assert_eq!(add(2, 2), 4);
    }
}

// tests/integration.rs
use my_crate::add;

#[test]
fn test_from_outside() {
    assert_eq!(add(1, 1), 2);
}
```

## A retenir
- `#[cfg(test)] mod tests` pour unitaires
- `tests/` pour integration
- `cargo test` lance tous les tests"""},
    {"topic": "smart_pointers", "difficulty": "debutant", "user": "Pourquoi Rc et non pas juste des references ?", "assistant": """## TL;DR
Rc permet plusieurs proprietaires. Les references ont une hierarchie stricte.

## Solution
```rust
use std::rc::Rc;

fn main() {
    // Avec Rc : plusieurs proprietaires
    let data = Rc::new(vec![1, 2, 3]);
    let ref1 = Rc::clone(&data);
    let ref2 = Rc::clone(&data);

    println!("Count: {}", Rc::strong_count(&data));  // 3

    // Les trois peuvent acceder aux donnees
    // Donnees liberees quand le dernier Rc est dropped
}
```

## A retenir
- Rc = ownership partage
- Comptage de references automatique
- Single-thread seulement (Arc pour multi-thread)"""},
]

LAST_EXERCISES = [
    {"topic": "ownership", "difficulty": "debutant", "user": "Un exercice simple sur le move.", "assistant": """## TL;DR
Exercice : comprendre quand une valeur est moved.

## Solution
```rust
fn main() {
    let s1 = String::from("hello");
    let s2 = s1;  // Move!

    // println!("{}", s1);  // ERREUR: s1 moved

    // Avec clone
    let s3 = String::from("world");
    let s4 = s3.clone();  // Clone, pas move
    println!("{} {}", s3, s4);  // OK

    // Les types Copy ne sont pas moved
    let n1 = 5;
    let n2 = n1;  // Copy
    println!("{} {}", n1, n2);  // OK
}
```

## A retenir
- String = move
- i32 = copy
- clone() pour copier explicitement"""},
    {"topic": "error_handling", "difficulty": "debutant", "user": "Un exercice sur l'operateur `?`.", "assistant": """## TL;DR
Exercice : propager les erreurs avec ?.

## Solution
```rust
use std::fs::File;
use std::io::{self, Read};

fn read_file(path: &str) -> Result<String, io::Error> {
    let mut file = File::open(path)?;  // Propage si erreur
    let mut content = String::new();
    file.read_to_string(&mut content)?;  // Propage si erreur
    Ok(content)
}

fn main() {
    match read_file("test.txt") {
        Ok(content) => println!("Content: {}", content),
        Err(e) => println!("Error: {}", e),
    }
}
```

## A retenir
- `?` propage Err automatiquement
- La fonction doit retourner Result
- Plus propre que match a chaque ligne"""},
    {"topic": "iterators", "difficulty": "debutant", "user": "Un exercice sur fold et reduce.", "assistant": """## TL;DR
Exercice : calculer des aggregats avec fold.

## Solution
```rust
fn main() {
    let numbers = vec![1, 2, 3, 4, 5];

    // fold avec valeur initiale
    let sum = numbers.iter().fold(0, |acc, x| acc + x);
    println!("Sum: {}", sum);  // 15

    // product
    let product = numbers.iter().fold(1, |acc, x| acc * x);
    println!("Product: {}", product);  // 120

    // reduce sans valeur initiale
    let max = numbers.iter().copied().reduce(|a, b| if a > b { a } else { b });
    println!("Max: {:?}", max);  // Some(5)
}
```

## A retenir
- `fold(init, |acc, x| ...)` avec valeur initiale
- `reduce` utilise le premier element comme init
- Retourne Option (liste peut etre vide)"""},
    {"topic": "concurrency", "difficulty": "intermediaire", "user": "Un exercice sur les channels.", "assistant": """## TL;DR
Exercice : communication entre threads avec mpsc.

## Solution
```rust
use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();

    // Producteur
    thread::spawn(move || {
        for i in 1..=5 {
            tx.send(i * 10).unwrap();
        }
    });

    // Consommateur (main thread)
    let mut sum = 0;
    for received in rx {
        println!("Got: {}", received);
        sum += received;
    }
    println!("Total: {}", sum);  // 150
}
```

## A retenir
- `channel()` cree tx (send) et rx (receive)
- `move` pour donner tx au thread
- La boucle for termine quand tx est dropped"""},
    {"topic": "structs", "difficulty": "debutant", "user": "Un exercice sur les methodes de struct.", "assistant": """## TL;DR
Exercice : creer une struct avec des methodes.

## Solution
```rust
struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    // Constructeur (fonction associee)
    fn new(width: u32, height: u32) -> Self {
        Rectangle { width, height }
    }

    // Methode (&self)
    fn area(&self) -> u32 {
        self.width * self.height
    }

    // Methode mutable (&mut self)
    fn scale(&mut self, factor: u32) {
        self.width *= factor;
        self.height *= factor;
    }
}

fn main() {
    let mut rect = Rectangle::new(10, 5);
    println!("Area: {}", rect.area());  // 50
    rect.scale(2);
    println!("Area: {}", rect.area());  // 200
}
```

## A retenir
- `Self` = le type de la struct
- `&self` pour lire
- `&mut self` pour modifier"""},
]

# Combiner tous les exemples - VERSION FINALE 200+
ALL_ADDITIONAL_EXAMPLES = {
    "debug": (
        ADDITIONAL_DEBUG_EXAMPLES + MORE_DEBUG_EXAMPLES + FINAL_DEBUG_EXAMPLES +
        MORE_DEBUG
    ),
    "concepts": (
        ADDITIONAL_CONCEPTS_EXAMPLES + MORE_CONCEPTS_EXAMPLES + FINAL_CONCEPTS_EXAMPLES +
        LIFETIMES_EXAMPLES + BORROWING_EXAMPLES + ASYNC_EXAMPLES +
        CONCURRENCY_EXAMPLES + SMART_POINTERS_EXAMPLES + ERROR_HANDLING_EXAMPLES +
        TRAITS_EXAMPLES + ITERATORS_EXAMPLES +
        MORE_LIFETIMES + MORE_BORROWING + MORE_ASYNC + MORE_CONCEPTS +
        EXTRA_LIFETIMES + EXTRA_BORROWING + EXTRA_ASYNC + EXTRA_OWNERSHIP +
        EXTRA_TRAITS + EXTRA_ERROR + EXTRA_STRUCTS + EXTRA_ENUMS +
        EXTRA_MODULES + EXTRA_COLLECTIONS + EXTRA_TESTING + EXTRA_UNSAFE +
        FINAL_LIFETIMES + FINAL_BORROWING + FINAL_ASYNC + FINAL_TRAITS +
        FINAL_GENERICS + FINAL_PATTERNS + FINAL_ERRORS + FINAL_ITERATORS +
        LAST_BATCH + EXTRA_MISC
    ),
    "exercises": (
        ADDITIONAL_EXERCISES_EXAMPLES + MORE_EXERCISES_EXAMPLES + FINAL_EXERCISES_EXAMPLES +
        LIFETIMES_EXERCISES + BORROWING_EXERCISES + MORE_EXERCISES + FINAL_EXERCISES +
        LAST_EXERCISES
    ),
}
