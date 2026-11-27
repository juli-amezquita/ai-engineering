"""Orquestación de una estimación: modelo → planificación → precio → informes.

Es lo que llama el router. Cada capa hace una sola cosa:
- plan_service: el modelo hace el inventario de alcance, Python calcula las horas con el catálogo
  y el modelo organiza las etapas y redacta la propuesta; el resultado es un borrador en JSON;
- planning: Python valida el borrador y arma un cronograma en el que nadie pasa del 100 %;
- pricing: Python calcula costos, precio, márgenes, caja y controles;
- report_builder: Python escribe el informe interno y la propuesta al cliente.

La estimación en una sola llamada (llm_service.generate_draft) se mantiene como línea base del
evaluador de consistencia: el resto del recorrido es el mismo.
"""

from dataclasses import dataclass

from app.services.catalog_hours import InventoryHours, inventory_hours
from app.services.llm_service import DraftResult
from app.services.plan_service import generate_draft_from_inventory
from app.services.planning import build_plan
from app.services.pricing import ProjectPricing, price_project
from app.services.report_builder import build_client_proposal, build_internal_report


@dataclass(frozen=True)
class EstimationResult:
    internal_report: str  # confidencial: costos, márgenes y tarifas internas
    client_proposal: str  # lo que se envía al cliente
    pricing: ProjectPricing
    llm: DraftResult
    hours: InventoryHours | None = None  # de dónde sale cada hora, si hubo inventario


def estimate_from_draft(llm: DraftResult) -> EstimationResult:
    """La parte determinista: se puede probar sin llamar al modelo."""
    deadline = llm.inventory.deadline_weeks if llm.inventory is not None else None
    pricing = price_project(build_plan(llm.draft, deadline_weeks=deadline))
    hours = inventory_hours(llm.inventory) if llm.inventory is not None else None
    return EstimationResult(
        internal_report=build_internal_report(
            pricing, scope_changes=llm.scope_changes, inventory=llm.inventory, breakdown=hours
        ),
        client_proposal=build_client_proposal(pricing),
        pricing=pricing,
        llm=llm,
        hours=hours,
    )


async def estimate(transcription: str, scope_changes: str | None = None) -> EstimationResult:
    """La estimación completa. `scope_changes` son los cambios de alcance de la consultora."""
    return estimate_from_draft(await generate_draft_from_inventory(transcription, scope_changes))
