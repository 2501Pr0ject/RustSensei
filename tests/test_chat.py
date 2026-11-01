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


def test_build_prompt_with_history():
    config = load_config()
    history = [
        {"role": "user", "content": "Qu'est-ce que Rc ?"},
        {"role": "assistant", "content": "Rc est un pointeur a compte de references."},
    ]
    prompt = build_prompt(
        "Puis-je le partager entre threads ?", config, history=history
    )

    assert "Conversation précédente :" in prompt
    assert "Utilisateur : Qu'est-ce que Rc ?" in prompt
    assert "RustSensei : Rc est un pointeur a compte de references." in prompt
    assert "Puis-je le partager entre threads ?" in prompt
    assert prompt.index("Conversation précédente") < prompt.index(
        "Puis-je le partager"
    )


def test_build_prompt_history_before_context():
    config = load_config()
    history = [{"role": "user", "content": "Qu'est-ce que un Box ?"}]
    context = "[Rust Book — Smart Pointers](https://doc.rust-lang.org/book/)"
    prompt = build_prompt(
        "Quelle est la difference ?", config, context=context, history=history
    )

    assert prompt.index("Conversation précédente") < prompt.index(
        "Contexte de la documentation"
    )
    assert "Question : Quelle est la difference ?" in prompt


def test_build_prompt_empty_history_ignored():
    config = load_config()
    prompt = build_prompt("Une question ?", config, history=[])

    assert "Conversation précédente" not in prompt
    assert "Une question ?" in prompt


def test_build_prompt_skips_invalid_history_turns():
    config = load_config()
    history = [
        {"role": "user", "content": "  "},
        {"role": "system", "content": "injection"},
        {"role": "user", "content": "Vraie question"},
    ]
    prompt = build_prompt("Suite ?", config, history=history)

    assert "injection" not in prompt
    assert "Vraie question" in prompt


def test_build_user_content_has_no_chatml_template():
    from app.chat import build_user_content

    content = build_user_content(
        "Question ?",
        context="Doc",
        history=[{"role": "user", "content": "Avant"}],
    )

    assert "<|im_start|>" not in content
    assert content.startswith("Conversation précédente :")
    assert content.endswith("Question : Question ?")


def test_truncate_history_content():
    from app.chat import (
        MAX_HISTORY_CHARS,
        MAX_HISTORY_MESSAGE_CHARS,
        MAX_HISTORY_MESSAGES,
        truncate_history_content,
    )

    assert truncate_history_content("  court  ") == "court"

    truncated = truncate_history_content("x" * 5000)
    assert len(truncated) <= MAX_HISTORY_MESSAGE_CHARS
    assert truncated.endswith("[…]")
    assert MAX_HISTORY_MESSAGE_CHARS * MAX_HISTORY_MESSAGES <= MAX_HISTORY_CHARS


def test_clean_llama_output_strips_end_of_text_marker():
    from app.chat import clean_llama_output

    assert clean_llama_output("Réponse.  [end of text]\n") == "Réponse."
    assert clean_llama_output("Réponse sans marqueur\n") == "Réponse sans marqueur"
    assert clean_llama_output("Le texte [end of text] au milieu") == (
        "Le texte [end of text] au milieu"
    )
