from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    database_url: str = "postgresql+psycopg://ortelana:demo-db-local@127.0.0.1:5433/ortelana"
    data_mode: str = Field(default="demo", pattern="^(demo|historical)$")
    data_dir: Path = ROOT / "data"
    checkpoint_path: str = str(ROOT / ".local/checkpoints.db")
    operator_token: str = "demo-operator-local"
    supervisor_token: str = "demo-supervisor-local"
    automation_token: str = "demo-automation-local"
    deployment: str = Field(default="local", pattern="^(local|production)$")

    @model_validator(mode="after")
    def credentials(self):
        tokens = [self.operator_token, self.supervisor_token, self.automation_token]
        if min(map(len, tokens)) < 16 or len(set(tokens)) != 3:
            raise ValueError("Use three different tokens of at least 16 characters")
        if self.deployment == "production" and any(t.startswith("demo-") for t in tokens):
            raise ValueError("Replace local demonstration credentials")
        return self


class DomainError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
