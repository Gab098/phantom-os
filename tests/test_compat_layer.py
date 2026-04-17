"""Unit tests for CompatibilityLayer."""

from compatibility.packages.compat_layer import CompatibilityLayer


def test_wine_setup_creates_prefix(tmp_runtime):
    c = CompatibilityLayer()
    prefix = c.wine_setup("test-prefix")
    from pathlib import Path

    assert Path(prefix).exists()
    assert (Path(prefix) / "drive_c").exists()


def test_create_launcher(tmp_runtime):
    c = CompatibilityLayer()
    c.create_launcher("TestApp", "/usr/bin/test", category="Game")

    from phantom_env import user_state_dir

    desktop = user_state_dir() / "applications" / "TestApp.desktop"
    assert desktop.exists()
    content = desktop.read_text()
    assert "Exec=/usr/bin/test" in content
    assert "Categories=Game;" in content


def test_create_launcher_with_icon(tmp_runtime):
    c = CompatibilityLayer()
    c.create_launcher("IconApp", "/usr/bin/app", icon="/usr/share/icons/app.png")

    from phantom_env import user_state_dir

    desktop = user_state_dir() / "applications" / "IconApp.desktop"
    content = desktop.read_text()
    assert "Icon=/usr/share/icons/app.png" in content


def test_proton_setup(tmp_runtime):
    c = CompatibilityLayer()
    path = c.proton_setup("TestGame")
    from pathlib import Path

    assert Path(path).exists()
    config = Path(path) / "config.json"
    assert config.exists()
