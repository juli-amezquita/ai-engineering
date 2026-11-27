"""Planificación, precios e informes: los cálculos que hace Python, no el modelo."""

import pytest

from app.context.examples import ESTIMATION_EXAMPLES
from app.schemas.draft import EstimationDraft, RoleHours, Task
from app.services.planning import InvalidDraftError, NotASoftwareProjectError, build_plan, fit_to_deadline
from app.services.pricing import OK, WARNING, price_project
from app.services.report_builder import build_client_proposal, build_internal_report

# Análisis v6 del vault: precio, honorarios, costo del equipo, utilidad neta y tarifa media.
V6 = [
    (366_797, 364_275, 192_084, 110_041, 146.79),
    (265_951, 261_035, 129_795, 79_784, 114.75),
    (272_637, 270_492, 142_718, 81_791, 149.94),
]
HIDDEN_FROM_CLIENT = [
    "Latinoamérica", "Los Ángeles", "imprevistos", "margen", "rentabilidad", "Contratista", "W-2",
]


def pricing_of(draft: EstimationDraft):
    return price_project(build_plan(draft))


@pytest.mark.parametrize(("example", "expected"), list(zip(ESTIMATION_EXAMPLES, V6)))
def test_reproduces_the_v6_prices(example, expected):
    pricing = pricing_of(example.draft)
    s = pricing.statement
    assert (s.price, s.fees, s.labor, s.net_profit, pricing.rate) == expected
    assert round(s.net_margin, 3) == 0.300


@pytest.mark.parametrize("example", ESTIMATION_EXAMPLES)
def test_examples_fit_without_extending_the_schedule(example):
    plan = build_plan(example.draft)
    assert plan.adjustments == ()
    assert all(plan.peak_dedication(role) <= 1 for role in plan.weekly_hours)


@pytest.mark.parametrize("example", ESTIMATION_EXAMPLES)
def test_client_proposal_adds_up_and_hides_costs(example):
    pricing = pricing_of(example.draft)
    s = pricing.statement
    consultants = sum(line.client_amount for line in pricing.lines)
    total = consultants + pricing.overhead_client_amount + s.expenses
    assert total == s.price
    assert sum(milestone.amount for milestone in pricing.milestones) == s.fees
    proposal = build_client_proposal(pricing)
    for word in HIDDEN_FROM_CLIENT:
        assert word not in proposal, f"la propuesta no debería decir {word!r}"
    assert "## 6. Cronograma de implementación" in proposal
    assert "| Actividad | Horas | Tarifa (USD/h) | Importe (USD) |" in proposal


@pytest.mark.parametrize("example", ESTIMATION_EXAMPLES)
def test_internal_report_has_every_section(example):
    report = build_internal_report(pricing_of(example.draft))
    for number in range(1, 19):
        assert f"\n## {number}. " in report


def test_overloaded_phase_is_extended():
    draft = ESTIMATION_EXAMPLES[0].draft.model_copy(deep=True)
    hours = [RoleHours(role="IA / ML", hours=120)]
    extra = Task(name="Más IA", first_phase=2, last_phase=2, hours=hours)
    draft.tasks.append(extra)
    plan = build_plan(draft)
    assert plan.adjustments and plan.phases[1].weeks > plan.phases[1].proposed_weeks
    assert all(plan.peak_dedication(role) <= 1 + 1e-9 for role in plan.weekly_hours)


def test_rate_is_capped_at_the_market_price():
    draft = ESTIMATION_EXAMPLES[0].draft.model_copy(deep=True)
    hours = [RoleHours(role="Liderazgo técnico", hours=300)]
    extra = Task(name="Arquitectura", first_phase=1, last_phase=4, hours=hours)
    draft.tasks.append(extra)
    pricing = pricing_of(draft)
    assert pricing.rate == 150 and pricing.capped and pricing.statement.net_margin < 0.30
    assert any(check.status == WARNING and "tope" in check.text for check in pricing.checks)


def test_not_a_software_project_is_rejected():
    data = ESTIMATION_EXAMPLES[0].draft.model_dump()
    reason = "Es una reunión de presupuesto anual."
    data.update(is_software_project=False, not_software_reason=reason)
    with pytest.raises(NotASoftwareProjectError, match="presupuesto anual"):
        build_plan(EstimationDraft.model_validate(data))


def test_invalid_draft_is_rejected():
    draft = ESTIMATION_EXAMPLES[0].draft.model_copy(update={"phases": []})
    with pytest.raises(InvalidDraftError, match="no hay etapas"):
        build_plan(draft)


def test_open_scope_questions_are_flagged_not_estimated():
    with_questions = pricing_of(ESTIMATION_EXAMPLES[1].draft)
    proposal = build_client_proposal(with_questions)
    assert "## 10. Puntos por confirmar" in proposal and "sistema de despacho" in proposal
    assert not any("despacho" in task.name for task in with_questions.plan.tasks)
    warnings = [check.text for check in with_questions.checks if check.status == WARNING]
    assert any("sin decidir" in text for text in warnings)
    without = pricing_of(ESTIMATION_EXAMPLES[0].draft)
    assert "Puntos por confirmar" not in build_client_proposal(without)
    assert not any("sin decidir" in check.text for check in without.checks)


@pytest.mark.parametrize(
    ("weeks", "deadline", "fitted"),
    [
        ([3, 9, 4, 2], 17, [3, 8, 4, 2]),  # 18 semanas: se quita una a la etapa con menos resto
        ([3, 7, 3], 17, [4, 9, 4]),  # 13 semanas: se reparten 4 más en la misma proporción
        ([3, 9, 2, 2], 16, [3, 9, 2, 2]),  # ya suma el plazo
        ([1, 1, 10], 4, [1, 1, 2]),  # cada etapa conserva al menos una semana
        ([2, 2], 1, [2, 2]),  # más etapas que semanas: no se toca
    ],
)
def test_phases_are_fitted_to_the_deadline(weeks, deadline, fitted):
    assert fit_to_deadline(weeks, deadline) == fitted
    assert sum(fitted) == deadline or deadline < len(weeks)


def test_a_feasible_deadline_is_met():
    draft = ESTIMATION_EXAMPLES[0].draft  # 16 semanas propuestas
    plan = build_plan(draft, deadline_weeks=17)
    assert plan.duration_weeks == 17 and plan.proposed_weeks == 16 and plan.meets_deadline
    assert build_plan(draft).meets_deadline is None
    checks = price_project(plan).checks
    assert any(check.status == OK and "cumple el plazo" in check.text for check in checks)


def test_an_impossible_deadline_is_flagged_not_forced():
    draft = ESTIMATION_EXAMPLES[0].draft  # 16 semanas propuestas: [3, 9, 2, 2]
    plan = build_plan(draft, deadline_weeks=15)
    assert plan.fitted_to_deadline and plan.meets_deadline is False
    assert plan.duration_weeks == 16
    assert all(plan.peak_dedication(role) <= 1 + 1e-9 for role in plan.weekly_hours)
    # el alargue parte de las semanas ajustadas al plazo, no de las del modelo
    assert plan.adjustments == (
        "La etapa 2, «Construcción», pasa de 8 a 9 semanas para que Backend, IA / ML no pase de 40 horas por semana.",
    )
    checks = price_project(plan).checks
    assert any(check.status == WARNING and "el cliente pidió 15" in check.text for check in checks)


def test_a_squeezed_schedule_never_ends_later_than_the_model_proposal():
    draft = ESTIMATION_EXAMPLES[0].draft
    # Apretadas a 8 semanas y alargadas etapa por etapa, terminarían en la 17; las del modelo, en la 16.
    plan = build_plan(draft, deadline_weeks=8)
    assert plan.duration_weeks == build_plan(draft).duration_weeks == 16
    assert not plan.fitted_to_deadline and plan.meets_deadline is False
    report = build_internal_report(price_project(plan))
    assert "Ajustarlas al plazo daba un cronograma más largo" in report
    assert "El cronograma no cabe en el plazo: dura 16 semanas." in report
