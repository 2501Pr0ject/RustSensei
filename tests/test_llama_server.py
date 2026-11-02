"""Tests du llama-server persistant (app.llama_server)."""

import asyncio

import pytest

from app import llama_server
from app.llama_server import LlamaServerManager, is_persistent, server_args


class FakeProc:
    def __init__(self, args):
        self.args = args
        self.alive = True

    def poll(self):
        return None if self.alive else 0

    def terminate(self):
        self.alive = False

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.alive = False


@pytest.fixture
def fake_server(monkeypatch):
    started = []

    def fake_start(config, port):
        proc = FakeProc(server_args(config, port))
        started.append(proc)
        return proc

    async def fake_wait(port, proc, timeout=0):
        return None

    monkeypatch.setattr(llama_server, "start_process", fake_start)
    monkeypatch.setattr(llama_server, "wait_healthy", fake_wait)
    return started


def _config(model="models/a.gguf", ctx=8192):
    return {"paths": {"model": model}, "inference": {"n_ctx_chat": ctx}}


def test_persistent_server_is_reused(fake_server):
    manager = LlamaServerManager()

    url1 = asyncio.run(manager.ensure(_config()))
    url2 = asyncio.run(manager.ensure(_config()))

    assert url1 == url2
    assert len(fake_server) == 1
    assert manager.status()["loads"] == 1
    args = fake_server[0].args
    assert args[args.index("-c") + 1] == "8192"
    assert args[args.index("--parallel") + 1] == "1"


def test_server_reloads_only_when_model_or_context_changes(fake_server):
    manager = LlamaServerManager()

    asyncio.run(manager.ensure(_config("models/a.gguf")))
    asyncio.run(manager.ensure(_config("models/b.gguf")))
    asyncio.run(manager.ensure(_config("models/b.gguf", ctx=4096)))

    assert len(fake_server) == 3
    assert [p.alive for p in fake_server] == [False, False, True]
    assert manager.status()["model"] == "b.gguf"
    assert manager.status()["ctx"] == 4096


def test_server_restarts_if_it_died(fake_server):
    manager = LlamaServerManager()
    asyncio.run(manager.ensure(_config()))
    fake_server[0].alive = False  # le processus s'est arrete

    asyncio.run(manager.ensure(_config()))

    assert len(fake_server) == 2
    assert manager.is_running()


def test_failed_start_is_cleaned_up(monkeypatch):
    started = []

    def fake_start(config, port):
        proc = FakeProc([])
        started.append(proc)
        return proc

    async def failing_wait(port, proc, timeout=0):
        raise RuntimeError("llama-server did not start in time")

    monkeypatch.setattr(llama_server, "start_process", fake_start)
    monkeypatch.setattr(llama_server, "wait_healthy", failing_wait)
    manager = LlamaServerManager()

    with pytest.raises(RuntimeError):
        asyncio.run(manager.ensure(_config()))

    assert not started[0].alive
    assert not manager.is_running()


def test_is_persistent_defaults_to_true():
    assert is_persistent({}) is True
    assert is_persistent({"server": {"persistent": False}}) is False
