"""Endpoint POST /api/v1/estimate (paso 5): recibe una transcripción y devuelve la estimación.

El router solo hace de capa HTTP: valida el request, llama al servicio de estimación, arma la
response y traduce cada fallo a un código HTTP. El prefijo /api/v1 lo pone main.py.

El estimador se inyecta con `Depends`, así los tests lo sustituyen con
`app.dependency_overrides` y prueban el endpoint sin llamar al modelo ni tener una API key.

| Situación | Código |
|---|---|
| El body no trae una transcripción válida (FastAPI) | 422 |
| La transcripción no describe un proyecto de software | 422 |
| El modelo devolvió algo que no sirve como estimación | 502 |
| El proveedor está saturado, limita las peticiones o no responde | 503 |
| El proveedor tardó demasiado | 504 |
| La API key no es válida o no tiene permisos | 500, sin dar detalles |
| `LLM_PROVIDER` todavía no está implementado | 501 |
"""

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Annotated

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.estimation import (
    ErrorResponse,
    EstimateRequest,
    EstimateResponse,
    EstimateSummary,
    TokenUsage,
)
from app.services.estimation_service import EstimationResult, estimate
from app.services.llm_service import EstimationError
from app.services.planning import InvalidDraftError, NotASoftwareProjectError
from app.services.pricing import WARNING

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Estimaciones"])

Estimator = Callable[[str], Awaitable[EstimationResult]]


def get_estimator() -> Estimator:
    """El estimador real. Los tests lo sustituyen por uno que no llama al modelo."""
    return estimate


def _to_response(result: EstimationResult) -> EstimateResponse:
    pricing, llm = result.pricing, result.llm
    statement = pricing.statement
    return EstimateResponse(
        estimation=result.internal_report,
        client_proposal=result.client_proposal,
        model=llm.model,
        provider=llm.provider,
        summary=EstimateSummary(
            project_name=llm.draft.project_name,
            project_type=llm.draft.project_type,
            duration_weeks=pricing.plan.duration_weeks,
            phases=len(pricing.plan.phases),
            base_hours=pricing.base_hours,
            total_hours=round(pricing.total_hours, 1),
            fees_usd=statement.fees,
            expenses_usd=statement.expenses,
            total_price_usd=statement.price,
            blended_rate_usd=pricing.rate,
            net_margin=round(statement.net_margin, 4),
            max_cash_needed_usd=pricing.max_cash_needed,
            schedule_adjustments=list(pricing.plan.adjustments),
            warnings=[check.text for check in pricing.checks if check.status == WARNING],
        ),
        usage=TokenUsage(
            input_tokens=llm.input_tokens,
            cache_creation_input_tokens=llm.cache_creation_input_tokens,
            cache_read_input_tokens=llm.cache_read_input_tokens,
            output_tokens=llm.output_tokens,
        ),
        estimated_cost_usd=llm.estimated_cost_usd,
        latency_ms=llm.latency_ms,
        created_at=datetime.now(UTC),
    )


def _error(status_code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=detail)


RESPONSES: dict[int | str, dict] = {
    422: {"model": ErrorResponse, "description": "Transcripción inválida o que no es un proyecto"},
    500: {"model": ErrorResponse, "description": "Error de configuración del servidor"},
    501: {"model": ErrorResponse, "description": "Proveedor del LLM no implementado"},
    502: {"model": ErrorResponse, "description": "El modelo devolvió algo que no sirve"},
    503: {"model": ErrorResponse, "description": "El proveedor del LLM no está disponible"},
    504: {"model": ErrorResponse, "description": "El proveedor del LLM tardó demasiado"},
}
SATURATED = (
    anthropic.RateLimitError,
    anthropic.OverloadedError,
    anthropic.ServiceUnavailableError,
)
REJECTED_KEY = (anthropic.AuthenticationError, anthropic.PermissionDeniedError)


@router.post(
    "/estimate",
    response_model=EstimateResponse,
    summary="Estima un proyecto a partir de la transcripción de una reunión",
    description=(
        "Envía la transcripción al LLM junto con las estimaciones de referencia (CAG). "
        "El modelo devuelve un borrador estructurado y Python calcula el cronograma, los "
        "costos, el precio y los márgenes, y escribe el informe interno y la propuesta para "
        "el cliente."
    ),
    responses=RESPONSES,
)
async def create_estimate(
    request: EstimateRequest,
    estimator: Annotated[Estimator, Depends(get_estimator)],
) -> EstimateResponse:
    try:
        result = await estimator(request.transcription)
    except NotASoftwareProjectError as error:
        detail = f"La transcripción no describe un proyecto de software: {error}"
        raise _error(status.HTTP_422_UNPROCESSABLE_CONTENT, detail) from error
    except (EstimationError, InvalidDraftError) as error:
        logger.warning("Respuesta del modelo inservible: %s", error)
        raise _error(status.HTTP_502_BAD_GATEWAY, str(error)) from error
    except NotImplementedError as error:
        raise _error(status.HTTP_501_NOT_IMPLEMENTED, str(error)) from error
    except REJECTED_KEY as error:
        logger.error("El proveedor rechazó la API key: %s", type(error).__name__)
        detail = "Error de configuración del servidor con el proveedor del LLM"
        raise _error(status.HTTP_500_INTERNAL_SERVER_ERROR, detail) from error
    except SATURATED as error:
        logger.warning("Proveedor saturado: %s", type(error).__name__)
        detail = "El proveedor del LLM está saturado. Inténtalo de nuevo en unos minutos"
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, detail) from error
    except anthropic.APITimeoutError as error:
        detail = "El proveedor del LLM tardó demasiado en responder"
        raise _error(status.HTTP_504_GATEWAY_TIMEOUT, detail) from error
    except anthropic.APIConnectionError as error:
        logger.warning("Sin conexión con el proveedor: %s", error)
        detail = "No se pudo conectar con el proveedor del LLM"
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, detail) from error
    except anthropic.APIStatusError as error:
        logger.error("Error del proveedor: %s %s", error.status_code, type(error).__name__)
        detail = f"El proveedor del LLM respondió con un error ({error.status_code})"
        raise _error(status.HTTP_502_BAD_GATEWAY, detail) from error
    return _to_response(result)
