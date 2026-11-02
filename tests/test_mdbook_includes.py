"""Tests de la resolution des directives mdBook (scripts/mdbook_includes.py)."""

from mdbook_includes import resolve_includes

SOURCE = """use std::fmt;

// ANCHOR: here
fn main() {
    let x = 5;
}
// ANCHOR_END: here

fn autre() {}
"""


def _setup(tmp_path):
    listing = tmp_path / "listings" / "ch01" / "src"
    listing.mkdir(parents=True)
    (listing / "main.rs").write_text(SOURCE, encoding="utf-8")
    (tmp_path / "listings" / "ch01" / "output.txt").write_text(
        "error[E0382]: borrow of moved value\n", encoding="utf-8"
    )
    md_dir = tmp_path / "src"
    md_dir.mkdir()
    return md_dir


def test_whole_file_and_anchor_lines_removed(tmp_path):
    md_dir = _setup(tmp_path)

    text, ok, ko = resolve_includes("{{#include ../listings/ch01/src/main.rs}}", md_dir)

    assert (ok, ko) == (1, 0)
    assert "fn main()" in text and "fn autre()" in text
    assert "ANCHOR" not in text


def test_rustdoc_include_with_anchor_keeps_visible_part(tmp_path):
    md_dir = _setup(tmp_path)

    text, ok, _ = resolve_includes(
        "```rust\n{{#rustdoc_include ../listings/ch01/src/main.rs:here}}\n```", md_dir
    )

    assert ok == 1
    assert text == "```rust\nfn main() {\n    let x = 5;\n}\n```"


def test_line_ranges(tmp_path):
    md_dir = _setup(tmp_path)
    resolve = lambda spec: resolve_includes(  # noqa: E731
        "{{#include ../listings/ch01/src/main.rs" + spec + "}}", md_dir
    )[0]

    assert resolve(":1") == "use std::fmt;"
    assert resolve(":4:5") == "fn main() {\n    let x = 5;"
    assert resolve(":9:") == "fn autre() {}"
    assert resolve("::1") == "use std::fmt;"


def test_console_output_and_unresolvable_directives(tmp_path):
    md_dir = _setup(tmp_path)
    content = (
        "{{#include ../listings/ch01/output.txt}}\n"
        "{{#include ../listings/absent.rs}}\n"
        "{{#include ../listings/ch01/src/main.rs:ancre_inexistante}}"
    )

    text, ok, ko = resolve_includes(content, md_dir)

    assert (ok, ko) == (1, 2)
    assert "error[E0382]" in text
    assert "{{#include ../listings/absent.rs}}" in text


def test_nested_includes_are_resolved_relative_to_included_file(tmp_path):
    md_dir = _setup(tmp_path)
    shared = tmp_path / "listings" / "ch01"
    (shared / "recipe.md").write_text("Recette\n{{#include links.md}}\n", encoding="utf-8")
    (shared / "links.md").write_text("[doc]: https://doc.rust-lang.org\n", encoding="utf-8")

    text, ok, ko = resolve_includes("{{#include ../listings/ch01/recipe.md}}", md_dir)

    assert (ok, ko) == (1, 0)
    assert text == "Recette\n[doc]: https://doc.rust-lang.org"


def test_self_inclusion_stops_at_max_depth(tmp_path):
    md_dir = _setup(tmp_path)
    loop = tmp_path / "listings" / "ch01" / "loop.md"
    loop.write_text("x {{#include loop.md}}\n", encoding="utf-8")

    text, ok, _ = resolve_includes("{{#include ../listings/ch01/loop.md}}", md_dir)

    assert ok == 1
    assert text.count("x") <= 7
