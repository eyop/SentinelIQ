"""Configuration helpers for SentinelIQ."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _get_env(name: str, default: str | None = None) -> str | None:
	value = os.getenv(name)
	if value is None or value == "":
		return default
	return value


def _get_int_env(name: str, default: int) -> int:
	value = _get_env(name)
	if value is None:
		return default
	try:
		return int(value)
	except ValueError:
		return default


def _get_list_env(name: str, default: list[str]) -> list[str]:
	value = _get_env(name)
	if value is None:
		return default
	return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
	env: str = "development"
	log_level: str = "INFO"
	origins_list: list[str] = field(default_factory=lambda: ["*"])
	openai_api_key: str | None = None
	pinecone_api_key: str | None = None
	pinecone_environment: str | None = None
	elastic_url: str = "http://localhost:9200"
	elastic_username: str | None = None
	elastic_password: str | None = None
	postgres_user: str = "sentineliq"
	postgres_password: str = "sentineliq"
	postgres_db: str = "sentineliq"
	postgres_host: str = "localhost"
	postgres_port: str = "5432"
	database_url: str = "postgresql+asyncpg://sentineliq:sentineliq@localhost:5432/sentineliq"
	redis_url: str = "redis://localhost:6379/0"
	secret_key: str = "change-me"
	vectorstore: str = "pinecone"
	nvd_lookback_days: int = 7
	ingest_interval_hours: int = 6
	llm_model: str = "gpt-4o-mini"


def get_settings() -> Settings:
	log_level = _get_env("LOG_LEVEL")
	if log_level is None:
		log_level = "INFO"
	elif log_level.lower() in {"debug", "info", "warning", "error", "critical"}:
		log_level = log_level.lower()

	return Settings(
		env=_get_env("ENV", "development") or "development",
		log_level=log_level,
		origins_list=_get_list_env("ALLOWED_ORIGINS", ["*"]),
		openai_api_key=_get_env("OPENAI_API_KEY"),
		pinecone_api_key=_get_env("PINECONE_API_KEY"),
		pinecone_environment=_get_env("PINECONE_ENVIRONMENT"),
		elastic_url=_get_env("ELASTIC_URL", "http://localhost:9200") or "http://localhost:9200",
		elastic_username=_get_env("ELASTIC_USERNAME"),
		elastic_password=_get_env("ELASTIC_PASSWORD"),
		postgres_user=_get_env("POSTGRES_USER", "sentineliq") or "sentineliq",
		postgres_password=_get_env("POSTGRES_PASSWORD", "sentineliq") or "sentineliq",
		postgres_db=_get_env("POSTGRES_DB", "sentineliq") or "sentineliq",
		postgres_host=_get_env("POSTGRES_HOST", "localhost") or "localhost",
		postgres_port=_get_env("POSTGRES_PORT", "5432") or "5432",
		database_url=_get_env("DATABASE_URL", "postgresql+asyncpg://sentineliq:sentineliq@localhost:5432/sentineliq") or "postgresql+asyncpg://sentineliq:sentineliq@localhost:5432/sentineliq",
		redis_url=_get_env("REDIS_URL", "redis://localhost:6379/0") or "redis://localhost:6379/0",
		secret_key=_get_env("SECRET_KEY", "change-me") or "change-me",
		vectorstore=_get_env("VECTORSTORE", "pinecone") or "pinecone",
		nvd_lookback_days=_get_int_env("NVD_LOOKBACK_DAYS", 7),
		ingest_interval_hours=_get_int_env("INGEST_INTERVAL_HOURS", 6),
		llm_model=_get_env("LLM_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
	)
