from __future__ import annotations

import json
from typing import Annotated, Any, Literal

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GitLabSettings(BaseSettings):
    url: str = "https://gitlab.example.com"
    token: str = ""
    parent_group_id: int = 0
    request_concurrency: int = 20

    model_config = SettingsConfigDict(env_prefix="GITLAB_")


class ArgoCDInstanceConfig(BaseModel):
    cluster_name: str
    url: str
    token: str


class ArgoCDSettings(BaseSettings):
    instances: list[ArgoCDInstanceConfig] = []
    # If app names follow a different convention, override via ARGOCD_APP_NAME_SUFFIX_SEPARATOR
    app_name_separator: str = "-"

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


class Settings(BaseSettings):
    gitlab: GitLabSettings = GitLabSettings()
    argocd: ArgoCDSettings = ArgoCDSettings()
    storage: StorageSettings = StorageSettings()
    scan_interval_seconds: int = 300
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )


# Singleton — imported everywhere
settings = Settings()
