"""Configuración común de los tests: nunca usan la clave real ni llaman a la API del proveedor.

- Las variables de entorno se fijan con una clave falsa y el `.env` no se lee, así que los tests
  dan lo mismo en local y en CI, donde no hay `.env`.
- `fake_anthropic` sustituye el cliente de Anthropic por uno simulado que devuelve la respuesta
  que se le dé, o lanza la excepción que se le dé.
"""

from types import SimpleNamespace

import pytest

from app.config import Settings, get_settings
from app.context.examples import ESTIMATION_EXAMPLES
from app.services import llm_service

FAKE_KEY = "sk-ant-clave-falsa-para-tests"
REAL_GET_CLIENT = llm_service.get_client  # `fake_anthropic` lo sustituye durante algunos tests


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_MODEL", "claude-haiku-5-5")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    REAL_GET_CLIENT.cache_clear()
    yield
    get_settings.cache_clear()
    REAL_GET_CLIENT.cache_clear()


def model_response(text: str | None = None, stop_reason: str = "end_turn", blocks=None):
    """Una respuesta como la de la API: un bloque de thinking y el JSON en un bloque de texto."""
    if text is None:
        text = ESTIMATION_EXAMPLES[1].draft.model_dump_json()
    if blocks is None:
        blocks = [
            SimpleNamespace(type="thinking", thinking="", signature="firma"),
            SimpleNamespace(type="text", text=text),
        ]
    usage = SimpleNamespace(
        input_tokens=1_656,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=20_639,
        output_tokens=9_000,
    )
    return SimpleNamespace(
        content=blocks, stop_reason=stop_reason, usage=usage, model="claude-haiku-5-5"
    )


class FakeStream:
    """Imita el `async with client.messages.stream(...)` del SDK."""

    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def get_final_message(self):
        if isinstance(self.response, BaseException):  # la respuesta se cortó a mitad
            raise self.response
        return self.response


class FakeMessages:
    """Devuelve las respuestas en orden; cuando se acaban, repite la última."""

    def __init__(self, responses):
        self.responses = responses
        self.calls: list[dict] = []

    def stream(self, **kwargs):
        self.calls.append(kwargs)
        return FakeStream(self.responses[min(len(self.calls), len(self.responses)) - 1])


@pytest.fixture
def fake_anthropic(monkeypatch):
    """Sustituye el cliente de Anthropic. Devuelve una función para fijar las respuestas, en orden."""

    def use(*responses) -> FakeMessages:
        messages = FakeMessages(list(responses) or [model_response()])
        monkeypatch.setattr(llm_service, "get_client", lambda: SimpleNamespace(messages=messages))
        return messages

    return use
