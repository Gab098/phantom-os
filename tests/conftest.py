"""Shared test fixtures for PhantomOS unit tests."""

import json
import os
import sys
from pathlib import Path

import pytest

# Make sure the project root is importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def tmp_runtime(tmp_path, monkeypatch):
    """Create a temporary runtime tree and point PHANTOM_RUNTIME_ROOT at it."""
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    monkeypatch.setenv("PHANTOM_RUNTIME_ROOT", str(runtime))
    return runtime


@pytest.fixture()
def fake_config(tmp_runtime):
    """Write a minimal config.json into the tmp runtime."""
    cfg_dir = tmp_runtime / "etc" / "phantom"
    cfg_dir.mkdir(parents=True)
    config = {
        "system": {"name": "PhantomOS", "version": "0.1.0", "locale": "en_US.UTF-8", "timezone": "UTC"},
        "ai": {"model_path": "./Qwen3.5-0.8B-BF16.gguf", "server_port": 18080},
        "gui": {"theme": "mint"},
        "privacy": {"firewall": {"enabled": True}},
        "compatibility": {},
        "extensions": {"enabled": []},
    }
    (cfg_dir / "config.json").write_text(json.dumps(config))
    return config


@pytest.fixture()
def fake_model(tmp_path):
    """Create a dummy model file for tests that check model resolution."""
    model = tmp_path / "fake-model.gguf"
    model.write_bytes(b"\x00" * 64)
    return model
