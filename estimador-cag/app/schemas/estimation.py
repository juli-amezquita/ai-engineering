"""Schemas de request y response del endpoint de estimación (paso 5).

La response cumple el contrato del enunciado (`estimation`, `model`, `provider`) y añade lo que
la consultora necesita de cada estimación:
- `estimation` es el informe interno, en Markdown: es confidencial;
- `client_proposal` es la propuesta para el cliente, en un campo aparte para que el informe
  interno no llegue al cliente por error;
- `summary` resume las cifras clave, para no tener que leerlas del Markdown;
- `usage`, `estimated_cost_usd`, `latency_ms` y `created_at` registran lo que costó la llamada.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

EXAMPLE_TRANSCRIPTION = (
    "Reunión con la directora de RR. HH. y el gerente de seguridad de un productor de áridos "
    "de California con 350 personas en nueve canteras. Contratan unas 120 personas al año y "
    "casi un tercio se va antes de los 90 días. Quieren una app para tablet, que funcione sin "
    "conexión y en inglés y español, para la formación MSHA de la Parte 46: módulos con videos "
    "y cuestionarios, firma del supervisor en la tablet, el certificado 5000-23 generado solo "
    "y avisos del reciclaje anual. También un panel por cantera para EHS y un piloto en dos "
    "canteras antes de la temporada, en unos cuatro meses."
)


class EstimateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    transcription: str = Field(
        min_length=50,
        max_length=200_000,
        description="Transcripción de la reunión con el cliente, en texto plano",
        examples=[EXAMPLE_TRANSCRIPTION],
    )


class TokenUsage(BaseModel):
    input_tokens: int = Field(description="Entrada que no salió de la caché")
    cache_creation_input_tokens: int = Field(description="Entrada escrita en la caché")
    cache_read_input_tokens: int = Field(description="Entrada leída de la caché")
    output_tokens: int = Field(description="Salida, con los tokens de thinking")


class EstimateSummary(BaseModel):
    """Las cifras clave de la estimación, todas calculadas en Python."""

    project_name: str
    project_type: str
    duration_weeks: int
    phases: int
    base_hours: int = Field(description="Horas base, sin imprevistos")
    total_hours: float = Field(description="Horas con el 10 % de imprevistos")
    fees_usd: int
    expenses_usd: int = Field(description="Gastos reembolsables, a coste")
    total_price_usd: int
    blended_rate_usd: float = Field(description="Honorarios ÷ horas con imprevistos")
    net_margin: float = Field(description="Utilidad neta después de impuestos ÷ precio")
    max_cash_needed_usd: int = Field(description="Caja máxima que la consultora adelanta")
    schedule_adjustments: list[str] = Field(
        description="Etapas que Python alargó para que nadie pase del 100 % de dedicación"
    )
    warnings: list[str] = Field(description="Alertas del informe interno")


class EstimateResponse(BaseModel):
    estimation: str = Field(
        description="Informe interno en Markdown. Confidencial: no se envía al cliente"
    )
    client_proposal: str = Field(
        description="Propuesta de valor y de negocio para el cliente, en Markdown"
    )
    model: str
    provider: str
    summary: EstimateSummary
    usage: TokenUsage
    estimated_cost_usd: float | None = Field(
        description="Costo estimado de la llamada al modelo; null si no se conoce su precio"
    )
    latency_ms: int = Field(description="Duración de la llamada al modelo")
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str
