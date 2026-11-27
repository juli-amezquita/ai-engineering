"""El catálogo de componentes: que cada cifra tenga fuente y que las reglas sean coherentes."""

import pytest

from app.context.catalog import (
    BUILD,
    BUILD_ROLES,
    COMPONENTS,
    OVERHEAD_RATE,
    OVERHEAD_SPLIT,
    PRODUCT_TYPES,
    SIZE_FACTORS,
    SOURCES,
)
from app.context.cost_model import ROLES
from app.context.examples import ESTIMATION_EXAMPLES


def reference_hours(number: int) -> dict[str, int]:
    """Las horas de cada perfil en una estimación de referencia (1, 2 o 3)."""
    totals: dict[str, int] = {}
    for task in ESTIMATION_EXAMPLES[number - 1].draft.tasks:
        for entry in task.hours:
            totals[entry.role] = totals.get(entry.role, 0) + entry.hours
    return totals


def test_build_roles_come_from_the_reference_estimates():
    web, mobile = reference_hours(1), reference_hours(2)
    assert BUILD_ROLES["web"] == {"Backend": web["Backend"], "Frontend": web["Frontend"]}
    assert BUILD_ROLES["web_y_movil"] == {role: mobile[role] for role in ("Backend", "Frontend", "Móvil")}
    assert BUILD_ROLES["movil"] == {role: mobile[role] for role in ("Backend", "Móvil")}
    assert all(set(roles) <= set(ROLES) for roles in BUILD_ROLES.values())


def test_overhead_split_is_the_average_share_in_the_reference_estimates():
    for role, weight in OVERHEAD_SPLIT.items():
        shares = []
        for number in (1, 2, 3):
            hours = reference_hours(number)
            shares.append(100 * hours.get(role, 0) / sum(hours.values()))
        assert weight == round(sum(shares) / len(shares), 1), role


def test_feature_tests_are_done_by_who_builds():
    """El QA independiente está en el 35 %: ninguna funcionalidad del catálogo lo reparte otra vez."""
    for component in COMPONENTS.values():
        if component.id not in ("asistente_sobre_documentos", "acompanamiento_lanzamiento"):
            assert "QA" not in component.split, component.id


@pytest.mark.parametrize("component", COMPONENTS.values(), ids=lambda c: c.id)
def test_every_component_with_hours_cites_its_sources(component):
    assert all(source in SOURCES for source in component.sources), component.sources
    assert component.basis
    if not component.needs_review:
        assert component.sources, f"{component.id} tiene horas sin fuente"
        assert component.split, f"{component.id} no reparte sus horas entre perfiles"
    assert set(component.split) <= {*ROLES, BUILD}


@pytest.mark.parametrize("component", COMPONENTS.values(), ids=lambda c: c.id)
def test_sizes_grow(component):
    if component.hours_by_size:
        hours = [component.hours_by_size[size] for size in ("S", "M", "L")]
        assert hours == sorted(hours) and hours[0] > 0
        assert component.size_criteria and set(component.size_criteria) == {"S", "M", "L"}
    elif component.base_hours is not None:
        assert component.base_hours > 0


def test_general_rules():
    assert SIZE_FACTORS == {"S": 1.0, "M": 2.0, "L": 3.0}
    assert OVERHEAD_RATE == 0.35


def test_sources_are_documented():
    for source in SOURCES.values():
        assert source.url.startswith("https://") and source.date and source.kind and source.note


def test_product_types_use_existing_components():
    for product in PRODUCT_TYPES.values():
        assert product.components and set(product.components) <= set(COMPONENTS), product.id
        assert product.evidence


def test_sourced_values_match_the_research():
    """Las cifras clave, para que un cambio por error no pase desapercibido."""
    assert COMPONENTS["cuentas_y_roles"].base_hours == 40
    assert COMPONENTS["asistente_sobre_documentos"].base_hours == 180
    assert COMPONENTS["integracion_hris"].hours_by_size == {"S": 80, "M": 180, "L": 320}
    assert COMPONENTS["encuestas"].needs_review
