"""La estimación en dos llamadas: el prompt del plan, la unión con el inventario y la orquestación."""

import asyncio

import pytest

from app.context.examples import ESTIMATION_EXAMPLES
from app.schemas.draft import Phase
from app.schemas.plan import PlanDraft, WorkAssignment
from app.services.catalog_hours import inventory_hours
from app.services.estimation_service import estimate_from_draft
from app.services.llm_service import CallUsage, DraftResult
from app.services.plan_prompt import build_plan_message, plan_from_draft, work_items
from app.services.plan_service import (
    assemble_draft,
    generate_draft_from_inventory,
    get_plan_format,
    get_plan_prompt,
)
from app.services.planning import InvalidDraftError, NotASoftwareProjectError, build_plan

from .conftest import model_response
from .test_inventory import SAMPLE, inventory, requirement


def plan(*assignments: tuple[int, int, int]) -> PlanDraft:
    example = ESTIMATION_EXAMPLES[1].draft
    return PlanDraft(
        project_name="Formación de seguridad en tablet",
        project_type="Web instalable en tablets",
        project_summary="Resumen interno.",
        value_proposition=example.value_proposition,
        phases=[
            Phase(name="Descubrimiento y diseño", weeks=3, deliverables=["Prototipo validado"]),
            Phase(name="Construcción", weeks=6, deliverables=["Aplicación en pruebas"]),
            Phase(name="Piloto y lanzamiento", weeks=2, deliverables=["Aplicación en producción"]),
        ],
        assignments=[WorkAssignment(item=i, first_phase=f, last_phase=l) for i, f, l in assignments],
        expenses=[],
        internal_risks=["El HRIS puede no tener la API que dice el cliente."],
    )


# Las partidas de SAMPLE: descubrimiento, configuración, diseño, cuentas, HRIS y encuestas.
PLAN = plan((1, 1, 1), (2, 1, 3), (3, 1, 2), (4, 2, 2), (5, 2, 3), (6, 2, 2))


def test_prompt_order_examples_and_no_money():
    prompt = get_plan_prompt()
    headings = ["# Rol", "# Tarea", "# Qué devolver", "===== ESTIMACIÓN DE REFERENCIA 1",
                "## Partidas de trabajo", "===== FIN DE LAS ESTIMACIONES", "# Alcance",
                "# Reglas del cronograma", "# Restricciones"]
    positions = [prompt.index(heading) for heading in headings]
    assert positions == sorted(positions)
    assert '"assignments"' in prompt and '"tasks"' not in prompt
    for word in ["USD/h", "146.79", "366,797", "margen", "Latinoamérica", "Los Ángeles"]:
        assert word not in prompt, f"el prompt no debería contener {word!r}"


@pytest.mark.parametrize("example", ESTIMATION_EXAMPLES, ids=lambda e: e.draft.project_name[:30])
def test_examples_keep_every_task_as_an_item(example):
    plan_draft = plan_from_draft(example.draft)
    assert [(a.first_phase, a.last_phase) for a in plan_draft.assignments] == [
        (task.first_phase, task.last_phase) for task in example.draft.tasks
    ]
    assert [a.item for a in plan_draft.assignments] == list(range(1, len(example.draft.tasks) + 1))


def test_schema_has_no_hours():
    schema = get_plan_format()["schema"]
    assert "assignments" in schema["properties"] and "tasks" not in schema["properties"]
    assert "hours" not in str(schema["$defs"]["WorkAssignment"])


def test_message_has_numbered_items_and_what_is_not_agreed():
    message = build_plan_message("Transcripción", SAMPLE, inventory_hours(SAMPLE), "Sin piloto.")
    assert message.startswith("<transcripcion>\nTranscripción\n</transcripcion>\n\n<inventario>")
    assert "1. Descubrimiento: 120 h" in message
    assert "6. Encuestas a empleados (S): Requisito de encuestas: 30 h (Full-stack 30)" in message
    assert "7." not in message  # la gestión y el QA no son partidas
    assert "el sistema reparte en todas las etapas «Gestión, liderazgo técnico, QA y lanzamiento»: 168 h" in message
    assert "- Requisito de lecciones_y_cuestionarios (opcional)" in message
    assert "Se asume: web." in message
    assert "## Plazo\nEl cliente pidió el producto en 17 semanas («en unos cuatro meses»): las etapas suman 17 semanas." in message
    assert message.endswith("<cambios_de_alcance>\nSin piloto.\n</cambios_de_alcance>")


def test_without_deadline_the_model_gives_the_weeks():
    without_deadline = SAMPLE.model_copy(update={"deadline": None})
    message = build_plan_message("Transcripción", without_deadline, inventory_hours(without_deadline))
    assert "La reunión no fija un plazo: da a cada etapa las semanas que necesite el equipo." in message
    assert "suman exactamente ese plazo" in get_plan_prompt()


def test_assemble_uses_the_catalog_hours():
    hours = inventory_hours(SAMPLE)
    draft = assemble_draft(SAMPLE, hours, PLAN)
    plan_ = build_plan(draft)
    assert sum(plan_.base_hours_by_role.values()) == hours.base_hours == 768
    assert len(draft.tasks) == 7
    overhead = draft.tasks[-1]
    assert overhead.name == "Gestión, liderazgo técnico, QA y lanzamiento"
    assert (overhead.first_phase, overhead.last_phase) == (1, 3)
    assert draft.open_scope_questions == [
        "Requisito de lecciones_y_cuestionarios: se mencionó como deseable, sin decidirlo."
    ]
    assert draft.value_proposition == PLAN.value_proposition


@pytest.mark.parametrize(
    ("assignments", "problem"),
    [
        (PLAN.assignments[:-1], "faltan las partidas 6"),
        ([*PLAN.assignments, WorkAssignment(item=2, first_phase=1, last_phase=1)], "la partida 2 está repetida"),
        ([*PLAN.assignments, WorkAssignment(item=9, first_phase=1, last_phase=1)], "la partida 9 no existe"),
    ],
)
def test_assemble_rejects_incomplete_assignments(assignments, problem):
    with pytest.raises(InvalidDraftError, match=problem):
        assemble_draft(SAMPLE, inventory_hours(SAMPLE), PLAN.model_copy(update={"assignments": assignments}))


def test_a_requirement_without_hours_is_not_a_task_but_is_reported():
    without_hours = inventory([requirement("cuentas_y_roles"), requirement("encuestas")])
    hours = inventory_hours(without_hours)
    assert len(work_items(hours)) == 4  # descubrimiento, configuración, diseño y cuentas
    draft = assemble_draft(without_hours, hours, plan((1, 1, 1), (2, 1, 3), (3, 1, 2), (4, 2, 2)))
    llm = DraftResult(draft, "anthropic", (CallUsage("claude-haiku-5-5", 1, 0, 0, 1, 1),), inventory=without_hours)
    report = estimate_from_draft(llm).internal_report
    assert "Encuestas a empleados (S): Requisito de encuestas: sin horas; no está en la estimación." in report


def test_internal_report_shows_where_the_hours_come_from():
    llm = DraftResult(
        assemble_draft(SAMPLE, inventory_hours(SAMPLE), PLAN),
        "anthropic",
        (CallUsage("claude-haiku-5-5", 1, 0, 0, 1, 1),),
        inventory=SAMPLE,
    )
    result = estimate_from_draft(llm)
    report = result.internal_report
    assert "**De dónde salen las horas.**" in report
    # PLAN suma 11 semanas y el cliente pidió cuatro meses: Python ajusta las etapas a 17
    plan_ = result.pricing.plan
    assert [phase.weeks for phase in plan_.phases] == [5, 9, 3] and plan_.meets_deadline
    assert "- Plazo que pidió el cliente: 17 semanas («en unos cuatro meses»)." in report
    assert "- Las etapas del modelo sumaban 11 semanas: Python las ajustó al plazo en la misma proporción." in report
    assert "- El cronograma cumple el plazo." in report
    assert "| Encuestas a empleados (S): Requisito de encuestas | a revisar | 30 |" in report
    assert "**Decisiones abiertas, estimadas con un supuesto:**" in report
    assert result.hours is not None and result.hours.base_hours == result.pricing.base_hours


def test_generate_draft_from_inventory(fake_anthropic):
    messages = fake_anthropic(
        model_response(text=SAMPLE.model_dump_json()), model_response(text=PLAN.model_dump_json())
    )
    result = asyncio.run(generate_draft_from_inventory("Transcripción de prueba"))
    inventory_call, plan_call = messages.calls
    assert plan_call["system"][0]["text"] == get_plan_prompt()
    assert plan_call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert plan_call["output_config"]["format"] == get_plan_format()
    assert "<inventario>" in plan_call["messages"][0]["content"]
    assert "<inventario>" not in inventory_call["messages"][0]["content"]
    assert result.inventory == SAMPLE and len(result.calls) == 2
    assert result.estimated_cost_usd == pytest.approx(2 * result.calls[0].estimated_cost_usd)


def test_missing_hours_are_completed_before_the_plan(fake_anthropic):
    from .test_inventory import FILLED, WITHOUT_HOURS

    messages = fake_anthropic(
        model_response(text=WITHOUT_HOURS.model_dump_json()),
        model_response(text=FILLED.model_dump_json()),
        model_response(text=plan((1, 1, 1), (2, 1, 3), (3, 1, 2), (4, 2, 2), (5, 2, 2)).model_dump_json()),
    )
    result = asyncio.run(generate_draft_from_inventory("Transcripción de prueba"))
    assert len(messages.calls) == len(result.calls) == 3
    assert "5. Encuestas a empleados (S): Requisito de encuestas: 25 h" in messages.calls[2]["messages"][0]["content"]
    assert result.inventory.requirements[1].custom_hours[0].hours == 25


def test_not_software_stops_after_the_inventory(fake_anthropic):
    not_software = SAMPLE.model_copy(
        update={"is_software_project": False, "not_software_reason": "Es una reunión de presupuesto."}
    )
    messages = fake_anthropic(model_response(text=not_software.model_dump_json()))
    with pytest.raises(NotASoftwareProjectError, match="presupuesto"):
        asyncio.run(generate_draft_from_inventory("Transcripción de prueba"))
    assert len(messages.calls) == 1
