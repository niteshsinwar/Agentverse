import os
from app.config.settings import Settings, Environment


def test_settings_relaxed_in_development(monkeypatch, tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("""
app:
  env: development
llm:
  provider: openai
    """.strip())
    s = Settings(config_file=str(cfg))
    assert s.APP_ENV == Environment.DEVELOPMENT
    # Should not raise due to missing OPENAI_API_KEY in development
    assert s.OPENAI_API_KEY is None


def test_settings_strict_in_production(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("""
app:
  env: production
llm:
  provider: openai
    """.strip())
    try:
        Settings(config_file=str(cfg))
        raised = False
    except ValueError as e:
        raised = True
        assert "OPENAI_API_KEY" in str(e)
    assert raised


