"""Configuración centralizada: carga y valida las variables de entorno desde .env.

Las variables de entorno del sistema tienen prioridad sobre las del archivo .env.
Si falta la API key del proveedor elegido, la aplicación falla al arrancar.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta absoluta a estimador-cag/.env, para que funcione se ejecute desde donde se ejecute.
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Variables que cambian entre entornos: desarrollo, staging y producción."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        env_ignore_empty=True,  # una variable vacía cuenta como no definida
        extra="ignore",  # otras variables del .env no rompen la carga
    )

    # Proveedor del LLM. SecretStr evita que las claves aparezcan en logs o trazas.
    OPENAI_API_KEY: SecretStr | None = None
    ANTHROPIC_API_KEY: SecretStr | None = None
    LLM_PROVIDER: Literal["openai", "anthropic"] = "anthropic"
    LLM_MODEL: str = "claude-haiku-5-5"

    # Aplicación
    APP_ENV: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "DEBUG"

    @model_validator(mode="after")
    def check_provider_key(self) -> Self:
        """Exige la API key del proveedor elegido: mejor fallar al arrancar que en una petición."""
        if self.LLM_PROVIDER == "anthropic":
            key = self.ANTHROPIC_API_KEY
        else:
            key = self.OPENAI_API_KEY
        if key is None or not key.get_secret_value().strip():
            name = f"{self.LLM_PROVIDER.upper()}_API_KEY"
            raise ValueError(
                f"Falta {name}, obligatoria con LLM_PROVIDER={self.LLM_PROVIDER}. "
                "Defínela en .env (ver .env.example)."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Carga la configuración una sola vez y la reutiliza en todas las peticiones."""
    return Settings()
