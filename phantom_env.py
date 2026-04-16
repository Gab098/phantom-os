#!/usr/bin/env python3
import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def project_root() -> Path:
    return PROJECT_ROOT


def runtime_root() -> Path:
    configured = os.environ.get("PHANTOM_RUNTIME_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return PROJECT_ROOT / "runtime"


def config_dir() -> Path:
    return runtime_root() / "etc" / "phantom"


def data_dir() -> Path:
    return runtime_root() / "var" / "lib" / "phantom"


def opt_dir() -> Path:
    return runtime_root() / "opt" / "phantom"


def user_state_dir() -> Path:
    return runtime_root() / "home" / "phantom" / ".phantom"


def ensure_runtime_layout() -> None:
    for path in [
        config_dir(),
        config_dir() / "gui",
        config_dir() / "locales",
        config_dir() / "privacy",
        data_dir(),
        data_dir() / "vms",
        opt_dir(),
        opt_dir() / "applications",
        opt_dir() / "extensions",
        opt_dir() / "hacking-tools",
        opt_dir() / "themes",
        user_state_dir(),
        user_state_dir() / "extensions",
        user_state_dir() / "prefixes",
        user_state_dir() / "themes",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def load_system_config() -> dict:
    ensure_runtime_layout()
    candidates = [
        os.environ.get("PHANTOM_CONFIG_PATH"),
        str(config_dir() / "config.json"),
        str(PROJECT_ROOT / "system" / "config" / "config.json"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.exists():
            with path.open() as handle:
                return json.load(handle)
    return {}


def resolve_path(value: str | None, *, base: Path | None = None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (base or PROJECT_ROOT) / path


def resolve_model_path(explicit: str | None = None) -> Path:
    config = load_system_config()
    configured = explicit or os.environ.get("PHANTOM_MODEL_PATH")
    candidates = [
        resolve_path(configured),
        resolve_path(config.get("ai", {}).get("model_path")),
        runtime_root() / "models" / "Qwen3.5-0.8B-BF16.gguf",
        PROJECT_ROOT / "Qwen3.5-0.8B-BF16.gguf",
        Path.home() / "models" / "qwen3-0.8b",
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    return candidates[1] or (PROJECT_ROOT / "Qwen3.5-0.8B-BF16.gguf")
