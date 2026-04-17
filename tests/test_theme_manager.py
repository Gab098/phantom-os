"""Unit tests for ThemeManager."""

import json

from gui.themes.theme_manager import ThemeManager


def test_list_themes_includes_bundled(tmp_runtime):
    mgr = ThemeManager()
    themes = mgr.list_themes()
    assert "mint" in themes
    assert "phantom-dark" in themes
    assert "phantom-light" in themes


def test_apply_mint_theme(tmp_runtime):
    from phantom_env import config_dir

    mgr = ThemeManager()
    ok, msg = mgr.apply_theme("mint")
    assert ok is True

    css_path = config_dir() / "gui" / "theme.css"
    assert css_path.exists()
    css = css_path.read_text()
    assert "--bg-primary" in css
    assert "#2D2D2D" in css
    assert "--accent" in css


def test_apply_dark_theme(tmp_runtime):
    from phantom_env import config_dir

    mgr = ThemeManager()
    ok, msg = mgr.apply_theme("phantom-dark")
    assert ok is True

    css = (config_dir() / "gui" / "theme.css").read_text()
    assert "#0D0D14" in css
    assert "#00FFAA" in css


def test_apply_nonexistent_theme(tmp_runtime):
    mgr = ThemeManager()
    ok, msg = mgr.apply_theme("does-not-exist")
    assert ok is False
    assert "not found" in msg.lower()


def test_create_custom_theme(tmp_runtime):
    mgr = ThemeManager()
    mgr.create_theme("custom-cyber", {
        "bg_primary": "#000000",
        "accent": "#FF00FF",
    })

    themes = mgr.list_themes()
    assert "custom-cyber" in themes
