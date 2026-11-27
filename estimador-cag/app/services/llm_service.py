"""Servicio del LLM: envía la transcripción con el contexto CAG y devuelve el borrador.

La llamada es single-turn, el modo transaccional del ejercicio:
- [system]    instrucciones + estimaciones de referencia (en el parámetro `system=` de Anthropic,
              no como un mensaje más);
- [user]      la transcripción de la reunión;
- [assistant] la respuesta del modelo: un JSON con el esquema de app/schemas/draft.py.

Decisiones:
- Structured outputs (`output_config.format`): la API garantiza que la respuesta cumple el
  esquema. El modelo solo estima y redacta; los cálculos los hace Python.
- `messages.stream` con `get_final_message()` y la validación con Pydantic aparte, en lugar de
  `messages.parse`: así se comprueba `stop_reason` antes de interpretar el JSON, porque una
  respuesta cortada o rechazada no cumple el esquema.
- `AsyncAnthropic` con `await`, para no bloquear el event loop de FastAPI.
- El cliente y el system prompt se crean en la primera llamada, no al importar el módulo: el
  router y los tests pueden importar este archivo sin una API key.
- `max_tokens` de 32,000, con streaming: el JSON de una estimación ocupa unos 5,000 tokens, pero
  el thinking adaptativo de `claude-haiku-5-5` puede pasar de 10,000. Con 16,000 una estimación
  real se cortó. Por encima de unos 21,000, el SDK exige streaming, porque la llamada podría
  pasar de 10 minutos.
- La respuesta se lee uniendo los bloques de texto: el primero puede ser de thinking.
- Prompt caching en el system prompt: es idéntico en cada llamada, y al reutilizarlo se paga
  una décima parte del precio de entrada.
- Un tiempo de espera de 180 segundos sin recibir datos (`LLM_TIMEOUT_SECONDS`), en lugar de los
  600 del SDK, con los que una llamada colgada tardaba 10 minutos en fallar. Mientras el modelo
  piensa, la API no envía nada: en una estimación medida, ese silencio duró 23 y 25 segundos, y
  en la llamada más larga de las tandas (16,700 tokens en 68 segundos) rondaría el minuto. Con
  180 segundos cabe incluso una respuesta que gaste los 32,000 tokens de `max_tokens` pensando.
- Los errores de la API de Anthropic se propagan tal cual, para que el router los traduzca a
  una respuesta HTTP. La excepción es el tiempo de espera a mitad de la respuesta: el SDK
  reintenta y convierte en `APITimeoutError` el que pasa antes de que la respuesta empiece, pero
  el otro no. Aquí la llamada se repite una vez, y si vuelve a colgarse se convierte el error,
  para que el router responda 504 y no 500.
"""

import logging
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import TypeVar

import httpx2  # la librería HTTP del SDK de Anthropic, que la instala con él
from anthropic import APITimeoutError, AsyncAnthropic, Timeout, transform_schema
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.schemas.draft import EstimationDraft
from app.schemas.inventory import ScopeInventory
from app.services.prompt_builder import build_system_prompt, build_user_message

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_TOKENS = 32_000
CONNECT_TIMEOUT_SECONDS = 5.0  # el del SDK: para abrir la conexión, 5 segundos bastan
MID_RESPONSE_RETRIES = 1  # veces que se repite una llamada cuya respuesta dejó de llegar a mitad

# Precio por millón de tokens (entrada, salida) de los modelos que se usan, para estimar el costo
# de cada llamada. claude-haiku-5-5 cuesta más si el prompt pasa de 100K tokens.
MODEL_PRICES_USD_PER_MTOK: dict[str, tuple[float, float]] = {"claude-haiku-5-5": (0.10, 0.50)}
LONG_PROMPT_PRICES_USD_PER_MTOK: dict[str, tuple[int, float, float]] = {
    "claude-haiku-5-5": (100_000, 0.50, 2.50),  # desde 100K tokens de prompt
}
CACHE_WRITE_MULTIPLIER = 1.25  # escribir en la caché cuesta 1.25 veces la entrada
CACHE_READ_MULTIPLIER = 0.10  # leerla, una décima parte


class EstimationError(RuntimeError):
    """El modelo respondió, pero su respuesta no sirve como estimación."""


def estimate_cost_usd(
    model: str,
    input_tokens: int,
    cache_creation_input_tokens: int,
    cache_read_input_tokens: int,
    output_tokens: int,
) -> float | None:
    """Costo de una llamada según el precio público del modelo; None si no se conoce."""
    prices = MODEL_PRICES_USD_PER_MTOK.get(model)
    if prices is None:
        return None
    input_price, output_price = prices
    prompt_tokens = input_tokens + cache_creation_input_tokens + cache_read_input_tokens
    long_prompt = LONG_PROMPT_PRICES_USD_PER_MTOK.get(model)
    if long_prompt is not None and prompt_tokens > long_prompt[0]:
        input_price, output_price = long_prompt[1], long_prompt[2]
    cost = (
        input_tokens * input_price
        + cache_creation_input_tokens * input_price * CACHE_WRITE_MULTIPLIER
        + cache_read_input_tokens * input_price * CACHE_READ_MULTIPLIER
        + output_tokens * output_price
    ) / 1_000_000
    return round(cost, 6)


@dataclass(frozen=True)
class CallUsage:
    """Los datos de una llamada al modelo que conviene registrar."""

    model: str
    input_tokens: int  # entrada que no salió de la caché
    cache_creation_input_tokens: int  # entrada escrita en la caché en esta llamada
    cache_read_input_tokens: int  # entrada leída de la caché
    output_tokens: int  # incluye los tokens de thinking
    latency_ms: int  # con la espera de los intentos que se colgaron
    # Veces que se repitió porque la respuesta dejó de llegar. El intento cortado no devuelve el
    # uso de tokens, así que su costo no entra en estas cifras.
    retries: int = 0

    @property
    def estimated_cost_usd(self) -> float | None:
        return estimate_cost_usd(
            self.model,
            self.input_tokens,
            self.cache_creation_input_tokens,
            self.cache_read_input_tokens,
            self.output_tokens,
        )


@dataclass(frozen=True)
class DraftResult:
    """El borrador de la estimación y las llamadas al modelo que hicieron falta para obtenerlo.

    Con una sola llamada, `calls` tiene el borrador. Con el inventario, tiene el inventario de
    alcance, la llamada que completa horas si hizo falta y el plan (app/services/plan_service.py).
    Los tokens, la latencia y el costo son la suma de todas.
    """

    draft: EstimationDraft
    provider: str
    calls: tuple[CallUsage, ...]
    scope_changes: str | None = None  # cambios de alcance que indicó la consultora
    inventory: ScopeInventory | None = None  # el inventario, si la estimación partió de él

    @property
    def model(self) -> str:
        return self.calls[-1].model

    @property
    def input_tokens(self) -> int:
        return sum(call.input_tokens for call in self.calls)

    @property
    def cache_creation_input_tokens(self) -> int:
        return sum(call.cache_creation_input_tokens for call in self.calls)

    @property
    def cache_read_input_tokens(self) -> int:
        return sum(call.cache_read_input_tokens for call in self.calls)

    @property
    def output_tokens(self) -> int:
        return sum(call.output_tokens for call in self.calls)

    @property
    def latency_ms(self) -> int:
        """Las llamadas van una detrás de otra, así que la latencia es la suma."""
        return sum(call.latency_ms for call in self.calls)

    @property
    def estimated_cost_usd(self) -> float | None:
        """Suma del costo de cada llamada; None si no se conoce el precio de alguna."""
        costs = [call.estimated_cost_usd for call in self.calls]
        return None if None in costs else round(sum(costs), 6)


@lru_cache
def get_client() -> AsyncAnthropic:
    """Un solo cliente por proceso. Solo Anthropic: el multiproveedor llega en la sesión 3."""
    settings = get_settings()
    if settings.LLM_PROVIDER != "anthropic":
        raise NotImplementedError(
            f"LLM_PROVIDER={settings.LLM_PROVIDER} todavía no está implementado: usa anthropic"
        )
    return AsyncAnthropic(
        api_key=settings.ANTHROPIC_API_KEY.get_secret_value(),
        timeout=Timeout(settings.LLM_TIMEOUT_SECONDS, connect=CONNECT_TIMEOUT_SECONDS),
    )


@lru_cache
def get_system_prompt() -> str:
    """Los ejemplos son estáticos: el system prompt se construye una sola vez."""
    return build_system_prompt()


@lru_cache
def get_output_format() -> dict:
    """El esquema JSON del borrador, adaptado a lo que acepta la API."""
    return {"type": "json_schema", "schema": transform_schema(EstimationDraft)}


async def _stream(system_prompt: str, user_message: str, output_format: dict):
    """Un intento de la llamada, con streaming: devuelve el mensaje completo."""
    async with get_client().messages.stream(
        model=get_settings().LLM_MODEL,
        max_tokens=MAX_TOKENS,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_message}],
        output_config={"format": output_format},
    ) as stream:
        return await stream.get_final_message()


async def call_structured(
    system_prompt: str, user_message: str, output_format: dict, schema: type[T], label: str
) -> tuple[T, CallUsage]:
    """Una llamada con structured outputs: el system prompt va cacheado y la respuesta se valida.

    La usan el borrador de la estimación y el inventario de alcance. `label` solo sirve para el log.
    Si la respuesta deja de llegar a mitad, la llamada se repite `MID_RESPONSE_RETRIES` veces.
    """
    settings = get_settings()
    start = time.perf_counter()
    retries = 0
    while True:
        try:
            response = await _stream(system_prompt, user_message, output_format)
            break
        except httpx2.TimeoutException as error:
            # La respuesta empezó y dejó de llegar: el SDK no la reintenta ni la convierte.
            logger.warning(
                "%s: el proveedor pasó %s s sin enviar datos (intento %d de %d)",
                label,
                settings.LLM_TIMEOUT_SECONDS,
                retries + 1,
                MID_RESPONSE_RETRIES + 1,
            )
            if retries == MID_RESPONSE_RETRIES:
                raise APITimeoutError(request=error.request) from error
            retries += 1
    latency_ms = round((time.perf_counter() - start) * 1000)

    if response.stop_reason == "max_tokens":
        raise EstimationError(f"La respuesta se cortó al llegar a max_tokens ({MAX_TOKENS})")
    if response.stop_reason == "refusal":
        raise EstimationError("El modelo se negó a responder")
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if not text:
        raise EstimationError("El modelo no devolvió texto")
    try:
        parsed = schema.model_validate_json(text)
    except ValidationError as error:
        detail = f"La respuesta del modelo no cumple el esquema: {error.error_count()} errores"
        raise EstimationError(detail) from error

    usage = response.usage
    call = CallUsage(
        model=response.model,
        input_tokens=usage.input_tokens,
        cache_creation_input_tokens=usage.cache_creation_input_tokens or 0,
        cache_read_input_tokens=usage.cache_read_input_tokens or 0,
        output_tokens=usage.output_tokens,
        latency_ms=latency_ms,
        retries=retries,
    )
    logger.info(
        "%s generado: modelo=%s entrada=%d caché escrita=%d caché leída=%d salida=%d "
        "latencia=%d ms reintentos=%d",
        label,
        call.model,
        call.input_tokens,
        call.cache_creation_input_tokens,
        call.cache_read_input_tokens,
        call.output_tokens,
        call.latency_ms,
        call.retries,
    )
    return parsed, call


async def generate_draft(transcription: str, scope_changes: str | None = None) -> DraftResult:
    """Pide al modelo el borrador de la estimación, con los cambios de alcance si los hay."""
    draft, call = await call_structured(
        get_system_prompt(),
        build_user_message(transcription, scope_changes),
        get_output_format(),
        EstimationDraft,
        "Borrador",
    )
    return DraftResult(draft, get_settings().LLM_PROVIDER, (call,), scope_changes)
