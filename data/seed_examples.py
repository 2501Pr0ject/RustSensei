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

# Combiner tous les exemples
ALL_ADDITIONAL_EXAMPLES = {
    "debug": ADDITIONAL_DEBUG_EXAMPLES + MORE_DEBUG_EXAMPLES + FINAL_DEBUG_EXAMPLES,
    "concepts": ADDITIONAL_CONCEPTS_EXAMPLES + MORE_CONCEPTS_EXAMPLES + FINAL_CONCEPTS_EXAMPLES,
    "exercises": ADDITIONAL_EXERCISES_EXAMPLES + MORE_EXERCISES_EXAMPLES + FINAL_EXERCISES_EXAMPLES,
}
