"""Servicio del LLM: envía la transcripción con el contexto CAG y devuelve el borrador de la estimación.

La llamada es single-turn, el modo transaccional del ejercicio:
- [system]    instrucciones + estimaciones de referencia (en el parámetro `system=` de Anthropic,
              no como un mensaje más);
- [user]      la transcripción de la reunión;
- [assistant] la respuesta del modelo: un JSON con el esquema de app/schemas/draft.py.

Decisiones:
- Structured outputs (`output_config.format`): la API garantiza que la respuesta cumple el
  esquema. El modelo solo estima y redacta; los cálculos los hace Python.
- `messages.create` y la validación con Pydantic aparte, en lugar de `messages.parse`: así se
  comprueba `stop_reason` antes de interpretar el JSON, porque una respuesta cortada o rechazada
  no cumple el esquema.
- `AsyncAnthropic` con `await`, para no bloquear el event loop de FastAPI.
- El cliente y el system prompt se crean en la primera llamada, no al importar el módulo: el
  router y los tests pueden importar este archivo sin una API key.
- `max_tokens` explícito y con margen: el JSON de una estimación ocupa unos 5,000 tokens, y el
  thinking adaptativo de `claude-haiku-5-5` también consume tokens de salida.
- La respuesta se lee uniendo los bloques de texto: el primero puede ser de thinking.
- Prompt caching en el system prompt: es idéntico en cada llamada, y al reutilizarlo se paga
  una décima parte del precio de entrada.
- Los errores de la API de Anthropic se propagan tal cual, para que el router los traduzca a
  una respuesta HTTP.
"""

import logging
import time
from dataclasses import dataclass
from functools import lru_cache

from anthropic import AsyncAnthropic, transform_schema
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.draft import EstimationDraft
from app.services.prompt_builder import build_system_prompt

logger = logging.getLogger(__name__)

MAX_TOKENS = 16_000


class EstimationError(RuntimeError):
    """El modelo respondió, pero su respuesta no sirve como estimación."""


@dataclass(frozen=True)
class DraftResult:
    """El borrador del modelo y los datos de la llamada que conviene registrar."""

    draft: EstimationDraft
    model: str
    provider: str
    input_tokens: int  # entrada que no salió de la caché
    cache_creation_input_tokens: int  # entrada escrita en la caché en esta llamada
    cache_read_input_tokens: int  # entrada leída de la caché
    output_tokens: int  # incluye los tokens de thinking
    latency_ms: int


@lru_cache
def get_client() -> AsyncAnthropic:
    """Un solo cliente por proceso. Solo Anthropic: el wrapper multiproveedor llega en la sesión 3."""
    settings = get_settings()
    if settings.LLM_PROVIDER != "anthropic":
        raise NotImplementedError(
            f"LLM_PROVIDER={settings.LLM_PROVIDER} todavía no está implementado: usa anthropic"
        )
    return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY.get_secret_value())


@lru_cache
def get_system_prompt() -> str:
    """Los ejemplos son estáticos: el system prompt se construye una sola vez."""
    return build_system_prompt()


@lru_cache
def get_output_format() -> dict:
    """El esquema JSON del borrador, adaptado a lo que acepta la API."""
    return {"type": "json_schema", "schema": transform_schema(EstimationDraft)}


async def generate_draft(transcription: str) -> DraftResult:
    """Pide al modelo el borrador de la estimación de la reunión."""
    settings = get_settings()
    start = time.perf_counter()
    response = await get_client().messages.create(
        model=settings.LLM_MODEL,
        max_tokens=MAX_TOKENS,
        system=[{"type": "text", "text": get_system_prompt(), "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": transcription}],
        output_config={"format": get_output_format()},
    )
    latency_ms = round((time.perf_counter() - start) * 1000)

    if response.stop_reason == "max_tokens":
        raise EstimationError(f"La estimación se cortó al llegar a max_tokens ({MAX_TOKENS})")
    if response.stop_reason == "refusal":
        raise EstimationError("El modelo se negó a generar la estimación")
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if not text:
        raise EstimationError("El modelo no devolvió texto")
    try:
        draft = EstimationDraft.model_validate_json(text)
    except ValidationError as error:
        raise EstimationError(f"La respuesta del modelo no cumple el esquema: {error.error_count()} errores") from error

    usage = response.usage
    result = DraftResult(
        draft=draft,
        model=response.model,
        provider=settings.LLM_PROVIDER,
        input_tokens=usage.input_tokens,
        cache_creation_input_tokens=usage.cache_creation_input_tokens or 0,
        cache_read_input_tokens=usage.cache_read_input_tokens or 0,
        output_tokens=usage.output_tokens,
        latency_ms=latency_ms,
    )
    logger.info(
        "Borrador generado: modelo=%s entrada=%d caché escrita=%d caché leída=%d salida=%d latencia=%d ms",
        result.model,
        result.input_tokens,
        result.cache_creation_input_tokens,
        result.cache_read_input_tokens,
        result.output_tokens,
        result.latency_ms,
    )
    return result
