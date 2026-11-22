"""Planificación, precios e informes: los cálculos que hace Python, no el modelo."""

import pytest

from app.context.examples import ESTIMATION_EXAMPLES
from app.schemas.draft import EstimationDraft, RoleHours, Task
from app.services.planning import InvalidDraftError, NotASoftwareProjectError, build_plan
from app.services.pricing import WARNING, price_project
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
