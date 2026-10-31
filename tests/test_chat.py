"""Tests unitaires du module app.chat (construction des prompts)."""

from app.chat import build_prompt, load_config


def test_build_prompt_contains_system_user_and_assistant():
    config = load_config()
    prompt = build_prompt("Pourquoi ce code ne compile pas ?", config)

    assert "<|im_start|>system" in prompt
    assert "<|im_start|>user" in prompt
    assert "<|im_start|>assistant" in prompt
    assert config["prompt"]["system"] in prompt
    assert "Pourquoi ce code ne compile pas ?" in prompt


def test_build_prompt_without_context():
    config = load_config()
    prompt = build_prompt("Quelle est la différence entre let et const ?", config)

    assert "Contexte de la documentation" not in prompt
    assert "Question :" not in prompt
    assert "Quelle est la différence entre let et const ?" in prompt


def test_build_prompt_with_context():
    config = load_config()
    context = "[Rust Book — Ownership](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html)"
    prompt = build_prompt("Explique-moi le concept d'ownership ?", config, context=context)

    assert context in prompt
    assert "Contexte de la documentation Rust officielle" in prompt
    assert "Question : Explique-moi le concept d'ownership ?" in prompt
