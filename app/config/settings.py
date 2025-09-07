# =========================================
# File: app/config/settings.py
# Purpose: Load YAML config + env; expose strongly-typed settings
# =========================================
from __future__ import annotations
import os, yaml
from pathlib import Path

CONFIG_FILE = os.environ.get("APP_CONFIG_FILE", "config.yaml")


class Settings:
    def __init__(self) -> None:
        self._cfg = self._load_yaml(CONFIG_FILE)
        # App
        self.APP_NAME = self._get(["app", "name"], default="Agentic SF Dev")
        self.APP_ENV = self._get(["app", "env"], default="sandbox")
        self.BASE_URL = self._get(["app", "base_url"], default="http://localhost:8000")
        # LLM
        self.LLM_PROVIDER = self._get(["llm", "provider"], default="openai")
        self.LLM_MODEL = self._get(["llm", "model"], default="gpt-4o-mini")
        self.LLM_TEMPERATURE = float(self._get(["llm", "temperature"], default=0.2))
        self.LLM_MAX_TOKENS = int(self._get(["llm", "max_tokens"], default=4096))
        # Paths
        self.PATHS = self._get(["paths"], default={})
        self.DB_PATH = self.PATHS.get("db", os.environ.get("AGENTIC_DB_PATH", os.path.join("data", "app.db")))
        # Secrets
        self.OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
        self.GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

    def _load_yaml(self, path: str) -> dict:
        p = Path(path)
        if not p.exists():
            return {}
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _get(self, keys: list[str], default=None):
        cur = self._cfg
        try:
            for k in keys:
                cur = cur[k]
            return cur
        except Exception:
            return default


settings = Settings()
