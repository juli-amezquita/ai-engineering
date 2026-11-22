"""Orquestación de una estimación: modelo → planificación → precio → informes.

Es lo que llamará el router del paso 5. Cada capa hace una sola cosa:
- llm_service: el modelo estima y redacta, y devuelve un borrador en JSON;
- planning: Python valida el borrador y arma un cronograma en el que nadie pasa del 100 %;
- pricing: Python calcula costos, precio, márgenes, caja y controles;
- report_builder: Python escribe el informe interno y la propuesta al cliente.
"""

from dataclasses import dataclass

from app.services.llm_service import DraftResult, generate_draft
from app.services.planning import build_plan
from app.services.pricing import ProjectPricing, price_project
from app.services.report_builder import build_client_proposal, build_internal_report


@dataclass(frozen=True)
class EstimationResult:
    internal_report: str  # confidencial: costos, márgenes y tarifas internas
    client_proposal: str  # lo que se envía al cliente
    pricing: ProjectPricing
    llm: DraftResult


def estimate_from_draft(llm: DraftResult) -> EstimationResult:
    """La parte determinista: se puede probar sin llamar al modelo."""
    pricing = price_project(build_plan(llm.draft))
    return EstimationResult(
        internal_report=build_internal_report(pricing),
        client_proposal=build_client_proposal(pricing),
        pricing=pricing,
        llm=llm,
    )


async def estimate(transcription: str) -> EstimationResult:
    return estimate_from_draft(await generate_draft(transcription))
