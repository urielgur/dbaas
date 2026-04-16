from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env into os.environ before any Settings class is instantiated.
# This makes variables available to all nested BaseSettings subclasses.
for _env_path in (Path(".env"), Path("../.env")):
    if _env_path.exists():
        load_dotenv(_env_path)
        break


class GitLabSettings(BaseSettings):
    url: str = "https://gitlab.example.com"
    token: str = ""
    parent_group_path: str = ""  # e.g. "ugurfinkel-group/dbaas"
    request_concurrency: int = 20

    model_config = SettingsConfigDict(env_prefix="GITLAB_")


class ArgoCDInstanceConfig(BaseModel):
    cluster_name: str
    url: str
    token: str


class ArgoCDSettings(BaseSettings):
    instances: list[ArgoCDInstanceConfig] = []
    # Prefix used in ArgoCD app names: "{app_name_prefix}-{project_slug}"
    # e.g. prefix="dbaas", project="analytics-pg" → app name "dbaas-analytics-pg"
    app_name_prefix: str = "dbaas"

    @field_validator("instances", mode="before")
    @classmethod
    def parse_instances(cls, v: Any) -> Any:
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(env_prefix="ARGOCD_")


class StorageSettings(BaseSettings):
    backend: Literal["json", "mongodb"] = "json"
    json_path: str = "data/databases.json"
    mongo_uri: str | None = None
    mongo_database: str = "dbaas"

    model_config = SettingsConfigDict(env_prefix="STORAGE_")


class AuthSettings(BaseSettings):
    secret_key: str = ""  # AUTH_SECRET_KEY — generate with: openssl rand -hex 32
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    users_json_path: str = "data/users.json"
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = ""  # Set on first deploy to auto-create admin, then clear

    model_config = SettingsConfigDict(env_prefix="AUTH_")


class Settings(BaseSettings):
    gitlab: GitLabSettings = GitLabSettings()
    argocd: ArgoCDSettings = ArgoCDSettings()
    storage: StorageSettings = StorageSettings()
    auth: AuthSettings = AuthSettings()
    scan_interval_seconds: int = 300
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        extra="ignore",
    )


# Singleton — imported everywhere
settings = Settings()
