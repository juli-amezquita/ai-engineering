"""El servicio del LLM y el system prompt, con un cliente de Anthropic simulado."""

import asyncio
import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from app.config import get_settings
from app.context.examples import ESTIMATION_EXAMPLES
from app.services import llm_service
from app.services.llm_service import (
    CallUsage,
    DraftResult,
    EstimationError,
    generate_draft,
    get_system_prompt,
)

from .conftest import model_response

THINKING_ONLY = SimpleNamespace(type="thinking", thinking="", signature="s")


def stopped_arriving() -> httpx2.ReadTimeout:
    """El error que deja pasar el SDK cuando la respuesta ya había empezado y deja de llegar."""
    return httpx2.ReadTimeout("", request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages"))


def test_call_shape(fake_anthropic):
    messages = fake_anthropic()
    result = asyncio.run(generate_draft("Transcripción de prueba"))
    call = messages.calls[0]
    assert set(call) == {"model", "max_tokens", "system", "messages", "output_config"}
    assert call["model"] == "claude-haiku-5-5" and call["max_tokens"] == llm_service.MAX_TOKENS
    assert call["system"] == [
        {"type": "text", "text": get_system_prompt(), "cache_control": {"type": "ephemeral"}}
    ]
    assert call["messages"] == [{"role": "user", "content": "Transcripción de prueba"}]
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert result.draft == ESTIMATION_EXAMPLES[1].draft
    assert (result.provider, result.cache_read_input_tokens) == ("anthropic", 20_639)


def test_schema_is_strict_and_lists_the_roles(fake_anthropic):
    schema = llm_service.get_output_format()["schema"]

    def objects(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                yield node
            for value in node.values():
                yield from objects(value)
        elif isinstance(node, list):
            for value in node:
                yield from objects(value)

    assert all(node.get("additionalProperties") is False for node in objects(schema))
    text = json.dumps(schema, ensure_ascii=False)
    assert "Gestión de proyecto" in text and "QA" in text


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (model_response(stop_reason="max_tokens"), "se cortó"),
        (model_response(stop_reason="refusal"), "se negó"),
        (model_response(blocks=[THINKING_ONLY]), "no devolvió texto"),
        (model_response(text='{"project_name": "a medias"}'), "no cumple el esquema"),
    ],
)
def test_unusable_responses_raise(fake_anthropic, response, message):
    fake_anthropic(response)
    with pytest.raises(EstimationError, match=message):
        asyncio.run(generate_draft("Transcripción de prueba"))


def test_the_client_gives_up_after_three_minutes_without_data(monkeypatch):
    timeout = llm_service.get_client().timeout
    assert (timeout.connect, timeout.read) == (5.0, 180)
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "30")
    get_settings.cache_clear()
    llm_service.get_client.cache_clear()
    assert llm_service.get_client().timeout.read == 30


def test_a_response_that_stops_arriving_is_retried_once(fake_anthropic):
    messages = fake_anthropic(stopped_arriving(), model_response())
    result = asyncio.run(generate_draft("Transcripción de prueba"))
    assert len(messages.calls) == 2 and messages.calls[0] == messages.calls[1]
    assert result.calls[0].retries == 1


def test_a_response_that_stops_arriving_twice_is_a_timeout(fake_anthropic):
    messages = fake_anthropic(stopped_arriving())  # la repite en cada intento
    with pytest.raises(anthropic.APITimeoutError):
        asyncio.run(generate_draft("Transcripción de prueba"))
    assert len(messages.calls) == 2


def test_openai_is_not_implemented_yet(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-clave-falsa-para-tests")
    get_settings.cache_clear()
    with pytest.raises(NotImplementedError, match="openai"):
        llm_service.get_client()


def test_system_prompt_order_and_no_money():
    prompt = get_system_prompt()
    headings = ["# Rol", "# Tarea", "# Qué devolver", "===== ESTIMACIÓN DE REFERENCIA 1",
                "===== FIN DE LAS ESTIMACIONES", "# Alcance", "# Reglas de estimación",
                "# Restricciones"]
    positions = [prompt.index(heading) for heading in headings]
    assert positions == sorted(positions)
    for word in ["USD/h", "146.79", "366,797", "margen", "Latinoamérica", "Los Ángeles"]:
        assert word not in prompt, f"el prompt no debería contener {word!r}"


def test_estimated_cost():
    draft = ESTIMATION_EXAMPLES[0].draft
    call = CallUsage("claude-haiku-5-5", 1_656, 20_515, 0, 9_759, 44_466)
    real_call = DraftResult(draft, "anthropic", (call,))
    assert real_call.estimated_cost_usd == pytest.approx(0.0076095, abs=1e-6)
    # Con dos llamadas, cada costo se calcula aparte y se suma; la latencia también se suma.
    two_calls = DraftResult(draft, "anthropic", (call, call))
    assert two_calls.estimated_cost_usd == pytest.approx(2 * 0.0076095, abs=1e-6)
    assert two_calls.latency_ms == 2 * 44_466 and two_calls.output_tokens == 2 * 9_759
    unknown = DraftResult(draft, "anthropic", (call, CallUsage("otro-modelo", 1, 0, 0, 1, 1)))
    assert unknown.estimated_cost_usd is None


def test_scope_changes_go_in_the_user_message(fake_anthropic):
    messages = fake_anthropic()
    result = asyncio.run(generate_draft("Transcripción", "Incluir la producción de contenidos."))
    content = messages.calls[0]["messages"][0]["content"]
    assert content.startswith("<transcripcion>\nTranscripción\n</transcripcion>")
    changes = "<cambios_de_alcance>\nIncluir la producción de contenidos.\n</cambios_de_alcance>"
    assert changes in content
    assert result.scope_changes == "Incluir la producción de contenidos."
