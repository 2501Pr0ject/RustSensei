"""Tests unitaires du module scripts.compile_check."""

from compile_check import (
    check_response,
    extract_rust_blocks,
    is_complete_program,
    wrap_in_main,
)


def test_extract_rust_blocks():
    text = (
        "## Solution\n"
        "```rust\n"
        "fn main() {\n"
        "    let x = 5;\n"
        "}\n"
        "```\n"
        "\n"
        "```\n"
        "fn main() {\n"
        "    println!(\"hello\");\n"
        "}\n"
        "```"
    )

    blocks = extract_rust_blocks(text)

    assert len(blocks) == 2
    assert "fn main" in blocks[0]
    assert "fn main" in blocks[1]


def test_is_complete_program():
    assert is_complete_program("fn main() {\n    let x = 5;\n}") is True
    assert is_complete_program("let x = 5;") is False


def test_wrap_in_main():
    wrapped = wrap_in_main("let x = 5;")
    assert "fn main() {" in wrapped
    assert "let x = 5;" in wrapped


def test_check_response_without_code():
    result = check_response("Cette erreur est simple et aucune variable ne compile.")

    assert result["has_code"] is False
    assert result["blocks_count"] == 0
    assert result["compiled"] == 0
    assert result["compilation_rate"] is None
    assert result["errors"] == []


def test_check_response_compiles_valid_code():
    response = (
        "## Solution\n"
        "```rust\n"
        "fn main() {\n"
        "    let x = 5;\n"
        "    println!(\"{}\", x);\n"
        "}\n"
        "```"
    )

    result = check_response(response)

    assert result["has_code"] is True
    assert result["blocks_count"] == 1
    assert result["compiled"] == 1
    assert result["compilation_rate"] == 1.0
    assert result["errors"] == []
