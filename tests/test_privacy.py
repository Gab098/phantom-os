"""Unit tests for PhantomPrivacy (mocked subprocess)."""

from unittest.mock import patch, MagicMock

from privacy.firewall.phantom_privacy import PhantomPrivacy


def test_setup_firewall_saves_config(tmp_runtime):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        p = PhantomPrivacy()
        p.setup_firewall("default")

    config_file = p.config_dir / "config.json"
    assert config_file.exists()

    import json
    cfg = json.loads(config_file.read_text())
    assert cfg["profile"] == "default"
    assert cfg["rules"]["incoming"] == "DROP"
    assert cfg["rules"]["outgoing"] == "ACCEPT"
    assert 53 in cfg["rules"]["allowed_ports"]
    assert 443 in cfg["rules"]["allowed_ports"]


def test_setup_firewall_strict_profile(tmp_runtime):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        p = PhantomPrivacy()
        p.setup_firewall("strict")

    import json
    cfg = json.loads((p.config_dir / "config.json").read_text())
    assert cfg["profile"] == "strict"
    assert cfg["rules"]["incoming"] == "DROP"
    assert cfg["rules"]["outgoing"] == "DROP"
    assert cfg["rules"]["allowed_ports"] == []


def test_setup_firewall_paranoid(tmp_runtime):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        p = PhantomPrivacy()
        p.setup_firewall("paranoid")

    import json
    cfg = json.loads((p.config_dir / "config.json").read_text())
    assert cfg["profile"] == "paranoid"
    assert cfg["rules"]["incoming"] == "REJECT"


def test_app_sandbox_returns_bwrap_cmd(tmp_runtime):
    p = PhantomPrivacy()
    cmd = p.app_sandbox("/usr/bin/firefox", perms=["net", "gpu"])
    assert cmd[0] == "bwrap"
    assert "/usr/bin/firefox" in cmd
    assert "--share-net" in cmd
