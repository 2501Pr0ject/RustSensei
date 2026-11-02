"""Tests unitaires de app.inference (source unique de l'echantillonnage)."""

import pytest

from app.inference import (
    chat_ctx_size,
    cli_sampling_args,
    overflow_message,
    sampling_params,
    server_payload_sampling,
)

CONFIG = {
    "paths": {"model": "models/base.gguf"},
    "inference": {
        "n_ctx": 4096,
        "n_ctx_chat": 8192,
        "n_predict": 1024,
        "temp": 0.7,
        "top_k": 40,
        "top_p": 0.9,
        "min_p": 0.05,
        "repeat_penalty": 1.1,
    },
    "sampling_by_model": {"autre.gguf": {"top_k": 20, "top_p": 0.8, "min_p": 0.0}},
}


def test_sampling_params_defaults_from_inference():
    assert sampling_params(CONFIG) == {
        "temp": 0.7,
        "top_k": 40,
        "top_p": 0.9,
        "min_p": 0.05,
        "repeat_penalty": 1.1,
        "n_predict": 1024,
    }


def test_sampling_params_per_model_override():
    params = sampling_params(CONFIG, "models/autre.gguf")

    assert params["top_k"] == 20 and params["top_p"] == 0.8 and params["min_p"] == 0.0
    assert params["temp"] == 0.7 and params["repeat_penalty"] == 1.1


def test_sampling_params_rejects_unknown_override_key():
    config = {**CONFIG, "sampling_by_model": {"base.gguf": {"topk": 20}}}

    with pytest.raises(ValueError, match="topk"):
        sampling_params(config)


def test_repository_config_matches_current_eval_values():
    import yaml

    with open("configs/model_config.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    common = {
        "temp": 0.7,
        "top_k": 40,
        "top_p": 0.9,
        "min_p": 0.05,
        "repeat_penalty": 1.1,
        "n_predict": 1024,
    }
    assert sampling_params(config, "models/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf") == common
    assert sampling_params(config, "models/Qwen_Qwen3-4B-Instruct-2507-Q4_K_M.gguf") == {
        **common,
        "top_k": 20,
        "top_p": 0.8,
        "min_p": 0.0,
        "n_predict": 1536,
    }
    assert chat_ctx_size(config) == 8192
    assert config["inference"]["n_ctx"] == 4096


def test_server_and_cli_formats():
    params = sampling_params(CONFIG)

    assert server_payload_sampling(params) == {
        "temperature": 0.7,
        "top_k": 40,
        "top_p": 0.9,
        "min_p": 0.05,
        "repeat_penalty": 1.1,
        "max_tokens": 1024,
    }
    args = cli_sampling_args(params)
    assert args[args.index("--min-p") + 1] == "0.05"
    assert args[args.index("-n") + 1] == "1024"


def test_overflow_message_formats():
    assert "9000 tokens pour un maximum de 8188" in overflow_message(
        "prompt is too long (9000 tokens, max 8188)"
    )
    assert "9100 tokens pour un maximum de 8192" in overflow_message(
        "request (9100 tokens) exceeds the available context size (8192 tokens), try increasing it"
    )
    assert "Effacez la conversation" in overflow_message("")
