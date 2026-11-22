"""La API completa: arranque, /health, Swagger y POST /api/v1/estimate."""

import anthropic
import httpx2
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import get_settings
from app.context.examples import ESTIMATION_EXAMPLES
from app.main import app
from app.routers.estimations import get_estimator
from app.schemas.estimation import EXAMPLE_TRANSCRIPTION
from app.services.estimation_service import estimate_from_draft
from app.services.llm_service import DraftResult, EstimationError
from app.services.planning import InvalidDraftError, NotASoftwareProjectError

URL = "/api/v1/estimate"
BODY = {"transcription": EXAMPLE_TRANSCRIPTION}


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as test_client:  # ejecuta el lifespan
        yield test_client
    app.dependency_overrides.clear()


def use_estimator(estimator):
    app.dependency_overrides[get_estimator] = lambda: estimator


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "0.1.0",
        "environment": "development",
        "provider": "anthropic",
        "model": "claude-haiku-5-5",
    }


def test_swagger_and_routes(client):
    assert client.get("/docs").status_code == 200
    root = client.get("/", follow_redirects=False)
    assert root.status_code == 307 and root.headers["location"] == "/docs"
    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "Estimador de proyectos de software (CAG)"
    assert set(schema["paths"]) == {"/api/v1/estimate", "/health"}


def test_estimate_returns_both_reports(client):
    draft = ESTIMATION_EXAMPLES[1].draft
    tokens = (1_656, 20_515, 0, 9_759)
    draft_result = DraftResult(draft, "claude-haiku-5-5", "anthropic", *tokens, 44_466)

    async def estimator(transcription, scope_changes=None):
        return estimate_from_draft(draft_result)

    use_estimator(estimator)
    response = client.post(URL, json=BODY)
    assert response.status_code == 200, response.text
    data = response.json()
    assert {"estimation", "model", "provider", "client_proposal"} <= set(data)
    assert data["estimation"].startswith("# Informe interno:")
    assert data["client_proposal"].startswith("# Propuesta:")
    assert data["summary"]["total_price_usd"] == 265_951
    assert len(data["summary"]["open_scope_questions"]) == 1
    assert data["estimated_cost_usd"] == pytest.approx(0.0076095, abs=1e-6)


def test_real_estimator_with_fake_anthropic(client, fake_anthropic):
    fake_anthropic()
    response = client.post(URL, json=BODY)
    assert response.status_code == 200, response.text
    assert response.json()["summary"]["total_price_usd"] == 265_951


@pytest.mark.parametrize(
    "body",
    [{}, {"transcription": "Hola"}, {"transcription": " " * 80}, {"transcription": "x" * 200_001}],
)
def test_invalid_body_is_422(client, body):
    assert client.post(URL, json=body).status_code == 422


REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def status_error(error_class, code):
    response = httpx2.Response(code, request=REQUEST)
    return error_class("error de prueba", response=response, body=None)


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (NotASoftwareProjectError("Es una reunión de presupuesto anual."), 422),
        (EstimationError("La estimación se cortó"), 502),
        (InvalidDraftError(["no hay etapas"]), 502),
        (NotImplementedError("LLM_PROVIDER=openai todavía no está implementado"), 501),
        (status_error(anthropic.AuthenticationError, 401), 500),
        (status_error(anthropic.RateLimitError, 429), 503),
        (status_error(anthropic.OverloadedError, 529), 503),
        (anthropic.APITimeoutError(request=REQUEST), 504),
        (anthropic.APIConnectionError(request=REQUEST), 503),
        (status_error(anthropic.BadRequestError, 400), 502),
    ],
    ids=lambda value: type(value).__name__ if isinstance(value, Exception) else str(value),
)
def test_errors_map_to_http_codes(client, error, code):
    async def failing(transcription, scope_changes=None):
        raise error

    use_estimator(failing)
    response = client.post(URL, json=BODY)
    assert response.status_code == code
    assert response.json()["detail"] and "sk-" not in response.text


def test_server_does_not_start_without_the_provider_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    get_settings.cache_clear()
    with pytest.raises(ValidationError, match="OPENAI_API_KEY"):
        with TestClient(app):
            pass


@pytest.mark.parametrize(("scope_changes", "expected"), [
    ("Incluir la conexión con el despacho.", "Incluir la conexión con el despacho."),
    ("   ", None),
    (None, None),
])
def test_scope_changes_reach_the_estimator(client, scope_changes, expected):
    received = {}
    draft = ESTIMATION_EXAMPLES[0].draft

    async def estimator(transcription, scope_changes=None):
        received["scope_changes"] = scope_changes
        llm = DraftResult(draft, "claude-haiku-5-5", "anthropic", 1, 0, 0, 1, 1, scope_changes)
        return estimate_from_draft(llm)

    use_estimator(estimator)
    response = client.post(URL, json={**BODY, "scope_changes": scope_changes})
    assert response.status_code == 200, response.text
    assert received["scope_changes"] == expected
    if expected:
        assert "Cambios de alcance indicados por la consultora" in response.json()["estimation"]
