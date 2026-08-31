from __future__ import annotations

import json

from syntarus.cli import main


def test_config_is_non_secret(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / "continuum.json"
    monkeypatch.setenv("CONTINUUM_CONFIG", str(config_path))
    assert main(["config", "set-endpoint", "http://localhost:8000/v1"]) == 0
    assert json.loads(config_path.read_text()) == {"base_url": "http://localhost:8000/v1"}
    assert main(["auth", "status", "--json"]) == 0
    result = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert result["data"]["keys_stored"] is False


def test_memory_command_requires_a_key(monkeypatch, capsys):
    monkeypatch.delenv("CONTINUUM_API_KEY", raising=False)
    monkeypatch.delenv("SYNTARUS_API_KEY", raising=False)
    assert main(["memory", "search", "hello", "--user", "customer_1", "--json"]) == 2
    assert "CONTINUUM_API_KEY" in json.loads(capsys.readouterr().out)["error"]["message"]
