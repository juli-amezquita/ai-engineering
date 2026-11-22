"""Schema de GET /health (paso 6): el estado del servicio, sin datos sensibles."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    environment: str = Field(description="APP_ENV: development, staging o production")
    provider: str = Field(description="Proveedor del LLM configurado")
    model: str = Field(description="Modelo del LLM configurado")
