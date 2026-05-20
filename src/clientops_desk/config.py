from __future__ import annotations
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    app_env: str = 'development'
    llm_mode: str = 'mock'
    anthropic_api_key: str | None = None
    anthropic_model: str = 'claude-sonnet-4-6'
    slack_webhook_url: str | None = None
    knowledge_path: Path = BASE_DIR / 'data' / 'knowledge_base' / 'cases.jsonl'
    clients_path: Path = BASE_DIR / 'data' / 'clients.json'
    generated_tasks_path: Path = BASE_DIR / 'data' / 'generated_tasks'

settings = Settings()
