# Exemples Baseline — RustSensei

Évaluation du modèle **Qwen2.5-Coder-1.5B-Instruct** (Q4_K_M) sans RAG ni fine-tuning.

- **Date** : 2025-01-09
- **Score global** : 2.87/5
- **llama.cpp rev** : b4823
- **Seed** : 42

---

## Résumé par catégorie

| Catégorie | N | Score |
|-----------|---|-------|
| basics | 5 | 3.00/5 |
| ownership | 3 | 2.33/5 |
| borrowing | 2 | 3.33/5 |

---

## Exemple 1 — Variable mutable (basics)

**Prompt** : Comment déclarer une variable mutable en Rust ?

**Réponse** :
> Pour déclarer une variable mutable en Rust, utilisez la syntaxe `let mut nom = valeur;`, où `nom` est le nom de votre variable. La variable sera alors modifiable après sa déclaration.

**Score** : 2.33/5 | Langue: ✅ | Code: ❌ | Longueur: ❌

**Analyse** : Réponse correcte mais trop courte, sans exemple de code.

---

## Exemple 2 — let vs const (basics)

**Prompt** : Quelle est la différence entre let et const en Rust ?

**Réponse** :
> `let` et `const` sont deux mots-clés en Rust pour déclarer des variables, mais ils ont des différences importantes.
>
> - **Type de données**: `let` peut avoir un type de donnée défini à l'avance (telle que `i32`, `f64`, `String`), tandis que `const` doit avoir un type qui est déterminé lors de la compilation.
>
> - **Durabilité**: Les variables créées avec `let` sont temporaires et existent pendant toute la durée du bloc dans lequel elles sont déclarées. Les variables créées avec `const` doivent avoir une valeur qui est résolue à l'exécution du code.
>
> ```rust
> // Déclaration avec let
> let x = 10;
>
> // Déclaration avec const
> const Y: i32 = 20;
> ```

**Score** : 4.00/5 | Langue: ✅ | Code: ✅ | Longueur: ✅

**Analyse** : Bonne réponse avec code. Quelques imprécisions (const est résolu à la compilation, pas à l'exécution).

---

## Exemple 3 — println! (basics)

**Prompt** : Comment afficher du texte dans la console en Rust ?

**Réponse** :
> Pour afficher du texte dans la console en Rust, vous utilisez l'instruction `println!`. Voici un exemple :
>
> ```rust
> fn main() {
>     println!("Bonjour, monde!");
> }
> ```
>
> `println!` est une fonction qui prend une chaîne de caractères comme premier argument et affiche ce texte dans la console avec un retour à la ligne.
>
> Vous pouvez également utiliser `print!` pour afficher des textes sans saut de ligne.

**Score** : 3.67/5 | Langue: ✅ | Code: ✅ | Longueur: ✅

**Analyse** : Réponse claire avec exemple. Mentionne `print!` comme alternative.

---

## Exemple 4 — Types primitifs (basics)

**Prompt** : Quels sont les types primitifs scalaires en Rust ?

**Réponse** :
> En Rust, les types primitifs scalaires sont : i8 (entier signé), u8 (entier non signé), i16, u16, i32, u32, i64, u64, f32 et f64.

**Score** : 1.00/5 | Langue: ❌ | Code: ❌ | Longueur: ❌

**Analyse** : Réponse incomplète (manque bool, char). Trop courte, sans exemple.

---

## Exemple 5 — Fonction avec retour (basics)

**Prompt** : Comment créer une fonction en Rust qui retourne une valeur ?

**Réponse** :
> Pour créer une fonction en Rust qui retourne une valeur, vous devez déclarer la fonction avec un type d'entrée et un type de sortie. Voici comment faire :
>
> ```rust
> fn addition(a: i32, b: i32) -> i32 {
>     a + b
> }
>
> fn main() {
>     let result = addition(5, 10);
>     println!("Le résultat est {}", result);
> }
> ```
>
> Le type de sortie est spécifié après la flèche (`-> i32`).

**Score** : 4.00/5 | Langue: ✅ | Code: ✅ | Longueur: ✅

**Analyse** : Bonne réponse avec exemple complet et explication.

---

## Exemple 6 — Ownership (ownership)

**Prompt** : Explique-moi le concept d'ownership en Rust avec un exemple simple.

**Réponse** :
> Ownership est une notion cruciale en Rust qui définit qui possède un objet et qui peut accéder à ses données. Dans Rust, chaque objet a son propre espace mémoire et la所有权 est transférée entre les variables.
>
> ```rust
> let mut box_of_crayons = vec![1, 2, 3];
> ```
>
> Dans cet exemple, `box_of_crayons` est la variable qui possède le所有权 du vecteur.

**Score** : 3.00/5 | Langue: ✅ | Code: ✅ | Longueur: ✅

**Analyse** : Explication correcte mais contient des caractères chinois (所有权 = ownership). Exemple pertinent mais l'explication du transfert de propriété n'est pas claire.

---

## Exemple 7 — Move semantics (ownership)

**Prompt** : Pourquoi ce code ne compile pas : `let s1 = String::from("hello"); let s2 = s1; println!("{}", s1);`

**Réponse** :
> Le code ne compile pas car vous essayez d'assigner une copie de la chaîne `s1` à `s2`, ce qui n'est pas possible en Rust. La chaîne est immuable, elle ne peut être modifiée une fois créée. Pour passer une chaîne par référence, vous devez utiliser le mot-clé `&`.

**Score** : 1.00/5 | Langue: ✅ | Code: ❌ | Longueur: ❌

**Analyse** : **Réponse incorrecte**. Le vrai problème est le "move" de s1 vers s2, pas l'immutabilité. s1 n'est plus valide après le move.

---

## Exemple 8 — Passage par référence (ownership)

**Prompt** : Comment passer une String à une fonction sans perdre la propriété ?

**Réponse** :
> Pour passer une `String` à une fonction en Rust sans perdre la propriété, utilisez la syntaxe pour passer un argument par référence (`&`). Par exemple :
>
> ```rust
> fn main() {
>     let s = String::from("Hello world!");
>     println!("{}", &s); // Affiche "Hello world!"
> }
> ```
>
> `&s` est une référence à la `String`. Rust conserve le contrôle sur la `String` jusqu'à ce que votre fonction ait terminé.

**Score** : 3.00/5 | Langue: ✅ | Code: ✅ | Longueur: ❌

**Analyse** : Concept correct (référence), mais l'exemple n'illustre pas vraiment le passage à une fonction.

---

## Exemple 9 — &T vs &mut T (borrowing)

**Prompt** : Quelle est la différence entre &T et &mut T ?

**Réponse** :
> - **`&T`** : C'est une référence constante vers un objet de type `T`. Les objets pointés par des références constantes sont immutables.
>
> - **`&mut T`** : C'est une référence mutable vers un objet de type `T`. Les objets pointés par des références mutables sont modifiables.
>
> ```rust
> let x = 5;
> let y: &i32 = &x; // référence constante
>
> let mut x = 5;
> let y: &mut i32 = &mut x; // référence mutable
> *y += 1; // correct
> ```

**Score** : 3.67/5 | Langue: ✅ | Code: ✅ | Longueur: ✅

**Analyse** : Bonne explication avec exemples clairs. Réponse assez complète avec des exemples additionnels (swap, struct).

---

## Exemple 10 — Références mutables multiples (borrowing)

**Prompt** : Pourquoi ne peut-on pas avoir plusieurs références mutables en même temps ?

**Réponse** :
> Dans Rust, les références mutables sont limitées par le principe d'indépendance des références. Une fois qu'une référence mutable est créée sur un objet, elle doit être utilisée entièrement pendant la vie du programme pour éviter les bugs de données inconsistentes.
>
> ```rust
> fn main() {
>     let mut x = 10;
>     x += 5;
>     // x -= 3; // Cela donnerait un error
>     println!("x: {}", x);
> }
> ```

**Score** : 3.00/5 | Langue: ✅ | Code: ✅ | Longueur: ✅

**Analyse** : L'explication est partiellement correcte (éviter les data races) mais l'exemple n'illustre pas le problème des références mutables multiples. Il aurait fallu montrer deux `&mut` sur la même variable.

---

## Observations générales

### Points forts
- Réponses en français (90%)
- Exemples de code présents (70%)
- Syntaxe Rust généralement correcte

### Points faibles
- Format structuré non respecté (TL;DR / Problème / Solution / etc.)
- Quelques erreurs conceptuelles (move vs immutabilité)
- Réponses parfois trop courtes ou trop longues
- Caractères chinois occasionnels (bug tokenizer ?)

### Amélioration attendue avec RAG
- Précision des concepts (ownership, borrowing)
- Citations de la documentation officielle
- Meilleure couverture des edge cases
