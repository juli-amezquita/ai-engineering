"""La estimación en dos llamadas: primero el inventario de alcance, después el plan.

1. El modelo hace el inventario de alcance (app/services/inventory_service.py) y Python calcula
   las horas de cada partida con el catálogo (app/services/catalog_hours.py).
2. El modelo recibe la transcripción y el inventario, reparte las partidas en etapas y redacta la
   propuesta (app/schemas/plan.py). No puede cambiar ni el alcance ni las horas.
3. Python une las dos respuestas en un `EstimationDraft`: las tareas son las partidas con las
   horas del catálogo, la gestión y el QA transversal abarcan todas las etapas, y los puntos por
   confirmar son los requisitos que el inventario no da por acordados.

Desde el `EstimationDraft`, la planificación, el precio y los informes son los mismos que con una
sola llamada (app/services/llm_service.generate_draft), que se mantiene como línea base para el
evaluador de consistencia.
"""

from functools import lru_cache

from anthropic import transform_schema

from app.config import get_settings
from app.schemas.draft import EstimationDraft, RoleHours, Task
from app.schemas.inventory import ScopeInventory
from app.schemas.plan import PlanDraft
from app.services.catalog_hours import OVERHEAD, HoursLine, InventoryHours, inventory_hours
from app.services.inventory_service import generate_inventory
from app.services.llm_service import DraftResult, call_structured
from app.services.plan_prompt import build_plan_message, build_plan_prompt, work_items
from app.services.planning import InvalidDraftError, NotASoftwareProjectError

# Cómo se presenta al cliente cada requisito que la reunión no dio por acordado.
PENDING = {
    "opcional": "se mencionó como deseable, sin decidirlo",
    "condicionado": "depende de algo que la reunión no decidió",
}


@lru_cache
def get_plan_prompt() -> str:
    return build_plan_prompt()


@lru_cache
def get_plan_format() -> dict:
    return {"type": "json_schema", "schema": transform_schema(PlanDraft)}


def open_questions(inventory: ScopeInventory) -> list[str]:
    """Los requisitos opcionales o condicionados: no se estiman, los decide la consultora."""
    return [
        f"{requirement.description.rstrip('. ')}: {PENDING[requirement.status]}."
        for requirement in inventory.requirements
        if requirement.status in PENDING
    ]


def _task(line: HoursLine, first_phase: int, last_phase: int) -> Task:
    return Task(
        name=line.name,
        first_phase=first_phase,
        last_phase=last_phase,
        hours=[RoleHours(role=role, hours=value) for role, value in line.hours.items()],
    )


def assemble_draft(inventory: ScopeInventory, hours: InventoryHours, plan: PlanDraft) -> EstimationDraft:
    """Une el inventario, las horas del catálogo y el plan del modelo en el borrador de siempre."""
    items = work_items(hours)
    assigned: dict[int, tuple[int, int]] = {}
    problems: list[str] = []
    for assignment in plan.assignments:
        if not 1 <= assignment.item <= len(items):
            problems.append(f"la partida {assignment.item} no existe")
        elif assignment.item in assigned:
            problems.append(f"la partida {assignment.item} está repetida")
        else:
            assigned[assignment.item] = (assignment.first_phase, assignment.last_phase)
    missing = [str(item) for item in range(1, len(items) + 1) if item not in assigned]
    if missing:
        problems.append(f"faltan las partidas {', '.join(missing)}")
    if problems:
        raise InvalidDraftError(problems)

    tasks = [_task(line, *assigned[item]) for item, line in enumerate(items, start=1)]
    last_phase = max(len(plan.phases), 1)
    tasks += [_task(line, 1, last_phase) for line in hours.lines if line.kind == OVERHEAD and line.total > 0]
    return EstimationDraft(
        is_software_project=True,
        not_software_reason="",
        project_name=plan.project_name,
        project_type=plan.project_type,
        project_summary=plan.project_summary,
        value_proposition=plan.value_proposition,
        phases=plan.phases,
        tasks=tasks,
        expenses=plan.expenses,
        open_scope_questions=open_questions(inventory),
        internal_risks=plan.internal_risks,
    )


async def generate_draft_from_inventory(
    transcription: str, scope_changes: str | None = None
) -> DraftResult:
    """El borrador en dos llamadas. Si el inventario dice que no es software, no hay segunda."""
    inventory_result = await generate_inventory(transcription, scope_changes)
    inventory = inventory_result.inventory
    if not inventory.is_software_project:
        raise NotASoftwareProjectError(
            inventory.not_software_reason or "La transcripción no describe un proyecto de software"
        )
    hours = inventory_hours(inventory)
    plan, plan_call = await call_structured(
        get_plan_prompt(),
        build_plan_message(transcription, inventory, hours, scope_changes),
        get_plan_format(),
        PlanDraft,
        "Plan",
    )
    return DraftResult(
        draft=assemble_draft(inventory, hours, plan),
        provider=get_settings().LLM_PROVIDER,
        calls=(*inventory_result.calls, plan_call),
        scope_changes=scope_changes,
        inventory=inventory,
    )
