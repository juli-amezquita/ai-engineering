"""El inventario de alcance: la primera llamada, antes de estimar.

El modelo lee la reunión y clasifica cada requisito con el catálogo de componentes; Python calcula
las horas con app/services/catalog_hours.py. La llamada usa la misma configuración que el borrador:
structured outputs, streaming y el system prompt en la caché del proveedor.

Los componentes sin horas en el catálogo necesitan horas del modelo, y a veces el modelo deja la
lista vacía. El esquema no puede exigir una lista con elementos (la API no admite esa restricción),
así que Python lo comprueba: si a algún requisito acordado le faltan horas, una llamada corta pide
solo esas horas. Si siguen faltando, el inventario falla en vez de dar una estimación incompleta.
"""

from dataclasses import dataclass
from functools import lru_cache

from anthropic import transform_schema

from app.schemas.inventory import MissingHours, ScopeInventory
from app.services.catalog_hours import InventoryHours, inventory_hours, missing_hours
from app.services.inventory_prompt import build_hours_prompt, build_inventory_prompt, format_missing
from app.services.llm_service import CallUsage, EstimationError, call_structured
from app.services.prompt_builder import build_user_message


@dataclass(frozen=True)
class InventoryResult:
    inventory: ScopeInventory
    calls: tuple[CallUsage, ...]  # el inventario y, si hizo falta, la que completó las horas
    scope_changes: str | None = None
    completed: tuple[str, ...] = ()  # requisitos cuyas horas puso la segunda llamada

    @property
    def hours(self) -> InventoryHours:
        return inventory_hours(self.inventory)

    @property
    def estimated_cost_usd(self) -> float | None:
        costs = [call.estimated_cost_usd for call in self.calls]
        return None if None in costs else round(sum(costs), 6)


@lru_cache
def get_inventory_prompt() -> str:
    return build_inventory_prompt()


@lru_cache
def get_inventory_format() -> dict:
    return {"type": "json_schema", "schema": transform_schema(ScopeInventory)}


@lru_cache
def get_hours_prompt() -> str:
    return build_hours_prompt()


@lru_cache
def get_hours_format() -> dict:
    return {"type": "json_schema", "schema": transform_schema(MissingHours)}


def fill_hours(inventory: ScopeInventory, positions: list[int], answer: MissingHours) -> ScopeInventory:
    """Pone en cada requisito de `positions` las horas de la respuesta, por su número en la lista."""
    requirements = list(inventory.requirements)
    for entry in answer.requirements:
        if 1 <= entry.item <= len(positions):
            index = positions[entry.item - 1]
            requirements[index] = requirements[index].model_copy(update={"custom_hours": entry.hours})
    return inventory.model_copy(update={"requirements": requirements})


async def generate_inventory(
    transcription: str, scope_changes: str | None = None
) -> InventoryResult:
    """Pide al modelo el inventario de alcance y completa las horas que falten."""
    user_message = build_user_message(transcription, scope_changes)
    inventory, call = await call_structured(
        get_inventory_prompt(), user_message, get_inventory_format(), ScopeInventory, "Inventario"
    )
    positions = missing_hours(inventory)
    if not positions:
        return InventoryResult(inventory, (call,), scope_changes)

    missing = [inventory.requirements[index] for index in positions]
    message = (
        f"{user_message}\n\n<requisitos_sin_horas>\n"
        f"{format_missing(missing, inventory.platform)}\n</requisitos_sin_horas>"
    )
    answer, hours_call = await call_structured(
        get_hours_prompt(), message, get_hours_format(), MissingHours, "Horas que faltaban"
    )
    inventory = fill_hours(inventory, positions, answer)
    still_missing = [inventory.requirements[index].description for index in missing_hours(inventory)]
    if still_missing:
        raise EstimationError("El modelo no puso horas a: " + "; ".join(still_missing))
    completed = tuple(requirement.description for requirement in missing)
    return InventoryResult(inventory, (call, hours_call), scope_changes, completed)
