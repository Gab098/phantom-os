"""Unit tests for the LLM service (mocked model)."""

import json
from unittest.mock import MagicMock, patch

from ai.llm.llm_server import LLMService


def test_llm_service_init(tmp_runtime, fake_config, fake_model):
    svc = LLMService(model_path=str(fake_model), port=9999)
    assert svc.port == 9999
    assert svc.model_path == fake_model
    assert svc.ready is False


def test_generate_not_loaded(tmp_runtime, fake_config):
    svc = LLMService(model_path="/tmp/fake.gguf")
    result = svc.generate("hello")
    assert "error" in result
    assert result["error"] == "Model not loaded"


def test_generate_with_mocked_llama(tmp_runtime, fake_config):
    svc = LLMService(model_path="/tmp/fake.gguf")
    svc.ready = True
    svc.model = MagicMock()
    svc.model.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "ls -la"}}]
    }

    result = svc.generate("list files", max_tokens=32)
    assert result == {"response": "ls -la"}


def test_natural_to_bash_with_mocked_model(tmp_runtime, fake_config):
    svc = LLMService(model_path="/tmp/fake.gguf")
    svc.ready = True
    svc.model = MagicMock()
    svc.model.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "df -h"}}]
    }

    cmd = svc.natural_to_bash("show disk usage")
    assert cmd == "df -h"


def test_natural_to_bash_filters_comments(tmp_runtime, fake_config):
    svc = LLMService(model_path="/tmp/fake.gguf")
    svc.ready = True
    svc.model = MagicMock()
    svc.model.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "# comment\nls -la"}}]
    }

    cmd = svc.natural_to_bash("list everything")
    assert cmd == "ls -la"
