"""Unit tests for PhantomTerminal._extract_command."""

from ai.terminal.phantom_terminal import PhantomTerminal


def test_extract_simple_command(tmp_runtime, fake_config):
    t = PhantomTerminal()
    assert t._extract_command("ls -la") == "ls -la"


def test_extract_skips_comments(tmp_runtime, fake_config):
    t = PhantomTerminal()
    assert t._extract_command("# WARNING: dangerous\nrm -rf /tmp/foo") == "rm -rf /tmp/foo"


def test_extract_skips_command_prefix(tmp_runtime, fake_config):
    t = PhantomTerminal()
    assert t._extract_command("Command: ls\nls -la") == "ls -la"


def test_extract_multiline(tmp_runtime, fake_config):
    t = PhantomTerminal()
    text = "Here is the command:\n# comment\nfind . -name '*.py'"
    assert t._extract_command(text) == "find . -name '*.py'"


def test_extract_empty(tmp_runtime, fake_config):
    t = PhantomTerminal()
    assert t._extract_command("") is None


def test_extract_only_comments(tmp_runtime, fake_config):
    t = PhantomTerminal()
    assert t._extract_command("# just a comment\n# another") is None


def test_natural_to_bash_no_model_no_server(tmp_runtime, fake_config):
    t = PhantomTerminal()
    t.model = None
    # With no server running, should return None
    result = t.natural_to_bash("list files")
    assert result is None
