"""Unit tests for ExtensionManager."""

import json
from pathlib import Path

from gui.extensions.extension_manager import ExtensionManager


def test_list_installed_empty(tmp_runtime):
    mgr = ExtensionManager()
    assert mgr.list_installed() == []


def test_install_from_directory(tmp_runtime, tmp_path):
    ext_dir = tmp_path / "my-ext"
    ext_dir.mkdir()
    (ext_dir / "manifest.json").write_text(
        json.dumps({"name": "test-ext", "version": "1.0", "author": "test"})
    )
    (ext_dir / "index.js").write_text("// hello")

    mgr = ExtensionManager()
    ok, msg = mgr.install(str(ext_dir))
    assert ok is True

    installed = mgr.list_installed()
    assert len(installed) == 1
    assert installed[0]["name"] == "test-ext"


def test_uninstall(tmp_runtime, tmp_path):
    ext_dir = tmp_path / "remove-me"
    ext_dir.mkdir()
    (ext_dir / "manifest.json").write_text(
        json.dumps({"name": "remove-me", "version": "1.0", "author": "test"})
    )

    mgr = ExtensionManager()
    mgr.install(str(ext_dir))
    ok, _ = mgr.uninstall("remove-me")
    assert ok is True
    assert mgr.list_installed() == []


def test_enable_disable(tmp_runtime, tmp_path):
    ext_dir = tmp_path / "toggle-ext"
    ext_dir.mkdir()
    (ext_dir / "manifest.json").write_text(
        json.dumps({"name": "toggle-ext", "version": "1.0", "author": "test"})
    )

    mgr = ExtensionManager()
    mgr.install(str(ext_dir))

    mgr.enable("toggle-ext")
    enabled_file = mgr.user_ext_dir / "enabled.json"
    assert "toggle-ext" in json.loads(enabled_file.read_text())

    mgr.disable("toggle-ext")
    assert "toggle-ext" not in json.loads(enabled_file.read_text())
