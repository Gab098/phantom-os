"""Unit tests for phantom_env.py path resolution and config loading."""

import json
from pathlib import Path

from phantom_env import (
    config_dir,
    data_dir,
    ensure_runtime_layout,
    load_system_config,
    opt_dir,
    project_root,
    resolve_model_path,
    resolve_path,
    runtime_root,
    user_state_dir,
)


def test_project_root_is_directory():
    root = project_root()
    assert root.is_dir()
    assert (root / "phantom_env.py").exists()


def test_runtime_root_respects_env(tmp_runtime):
    rr = runtime_root()
    assert rr == tmp_runtime


def test_config_dir_within_runtime(tmp_runtime):
    cd = config_dir()
    assert str(cd).startswith(str(tmp_runtime))
    assert cd == tmp_runtime / "etc" / "phantom"


def test_data_dir_within_runtime(tmp_runtime):
    dd = data_dir()
    assert dd == tmp_runtime / "var" / "lib" / "phantom"


def test_opt_dir_within_runtime(tmp_runtime):
    od = opt_dir()
    assert od == tmp_runtime / "opt" / "phantom"


def test_user_state_dir_within_runtime(tmp_runtime):
    usd = user_state_dir()
    assert usd == tmp_runtime / "home" / "phantom" / ".phantom"


def test_ensure_runtime_layout(tmp_runtime):
    ensure_runtime_layout()
    assert (config_dir() / "gui").is_dir()
    assert (config_dir() / "locales").is_dir()
    assert (config_dir() / "privacy").is_dir()
    assert (data_dir() / "vms").is_dir()
    assert (opt_dir() / "applications").is_dir()
    assert (opt_dir() / "extensions").is_dir()
    assert (opt_dir() / "hacking-tools").is_dir()
    assert (opt_dir() / "themes").is_dir()
    assert (user_state_dir() / "extensions").is_dir()
    assert (user_state_dir() / "prefixes").is_dir()
    assert (user_state_dir() / "themes").is_dir()


def test_load_system_config_with_file(fake_config, tmp_runtime):
    cfg = load_system_config()
    assert cfg["system"]["name"] == "PhantomOS"
    assert cfg["ai"]["server_port"] == 18080


def test_load_system_config_missing(tmp_runtime, monkeypatch, tmp_path):
    """Without a config in the runtime tree AND no project config, returns {}."""
    # Point project root away so the fallback doesn't find system/config/config.json
    monkeypatch.setattr("phantom_env.PROJECT_ROOT", tmp_path)
    cfg = load_system_config()
    assert cfg == {}


def test_resolve_path_absolute():
    result = resolve_path("/usr/bin/python3")
    assert result == Path("/usr/bin/python3")


def test_resolve_path_relative():
    result = resolve_path("foo/bar")
    assert result == project_root() / "foo" / "bar"


def test_resolve_path_none():
    result = resolve_path(None)
    assert result is None


def test_resolve_path_empty():
    result = resolve_path("")
    assert result is None


def test_resolve_model_path_explicit(fake_model):
    result = resolve_model_path(str(fake_model))
    assert result == fake_model
