from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import yaml


def _load_yaml_config() -> dict:
    """Load config.yaml once from the backend folder."""
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "config.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


_raw_cfg = _load_yaml_config()


@dataclass
class LoggingConfig:
    enabled: bool
    path: str


@dataclass
class ModelsConfig:
    default_provider: str
    providers: Dict[str, List[str]]


def _build_logging_config(raw: dict) -> LoggingConfig:
    logging_section = raw.get("logging", {})
    enabled = bool(logging_section.get("enabled", False))
    path = logging_section.get("path", "logs/easygpt.jsonl")
    return LoggingConfig(enabled=enabled, path=path)


def _build_models_config(raw: dict) -> ModelsConfig:
    models_section = raw.get("models", {})
    default_provider = str(models_section.get("default_provider", "mock")).lower()
    providers = models_section.get("providers", {}) or {}
    # normalize provider keys and ensure lists
    normalized: Dict[str, List[str]] = {}
    for provider_key, models in providers.items():
        key = str(provider_key).lower()
        if isinstance(models, list):
            model_list = [str(m) for m in models]
        elif isinstance(models, str):
            model_list = [str(models)]
        else:
            model_list = []
        normalized[key] = model_list
    # guarantee mock provider exists
    if "mock" not in normalized:
        normalized["mock"] = ["mock-model"]
    if default_provider not in normalized:
        default_provider = "mock"
    return ModelsConfig(default_provider=default_provider, providers=normalized)


@dataclass
class Settings:
    # load the .env file
    from dotenv import load_dotenv
    load_dotenv()

    # Server/runtime configuration can still come from env; models/logging come from YAML only.
    backend_host: str = os.getenv("EASYGPT_BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("EASYGPT_BACKEND_PORT", "8000"))

    frontend_origin: str = os.getenv("EASYGPT_FRONTEND_ORIGIN", "http://localhost:8501")

    # API keys remain environment-driven; not part of the YAML requirements
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    deepseek_api_key: Optional[str] = os.getenv("DEEPSEEK_API_KEY")

    logging: LoggingConfig = field(default_factory=lambda: _build_logging_config(_raw_cfg))
    models: ModelsConfig = field(default_factory=lambda: _build_models_config(_raw_cfg))


settings = Settings()


def resolve_provider_and_model(provider: Optional[str], model_override: Optional[str]) -> Tuple[str, str]:
    """Resolve provider and model using YAML-configured defaults.

    - If provider is None, use default_provider from config.
    - If model_override is provided, use it; else pick the first model for the provider.
    - Fallback to mock provider/model when necessary.
    """
    chosen_provider = (provider or settings.models.default_provider).lower()
    provider_models = settings.models.providers.get(chosen_provider)
    if not provider_models:
        chosen_provider = "mock"
        provider_models = settings.models.providers.get("mock", ["mock-model"])
    if model_override:
        return chosen_provider, model_override
    # pick the first configured model
    model_name = provider_models[0] if provider_models else "mock-model"
    return chosen_provider, model_name
