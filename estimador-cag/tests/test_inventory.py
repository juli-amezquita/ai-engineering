"""El inventario de alcance: el prompt, la llamada al modelo y las horas que calcula Python."""

import asyncio
import json
import re

import pytest
from anthropic import transform_schema

from app.context.catalog import COMPONENTS, PRODUCT_TYPES
from app.schemas.draft import RoleHours
from app.schemas.inventory import (
    Deadline,
    MissingHours,
    OpenDecision,
    Requirement,
    RequirementHours,
    ScopeInventory,
)
from app.services.catalog_hours import CATALOG, OVERHEAD, REVIEW, distribute, inventory_hours, missing_hours
from app.services.inventory_service import (
    fill_hours,
    generate_inventory,
    get_hours_format,
    get_hours_prompt,
    get_inventory_format,
    get_inventory_prompt,
)
from app.services.llm_service import EstimationError

from .conftest import model_response


def requirement(component, size="S", status="acordado", quantity=1, custom=()):
    return Requirement(
        description=f"Requisito de {component}",
        status=status,
        evidence="frase de la reunión",
        component=component,
        size=size,
        quantity=quantity,
        size_reason="primera versión",
        custom_hours=[RoleHours(role=role, hours=hours) for role, hours in custom],
    )


FOUR_MONTHS = Deadline(amount=4, unit="meses", evidence="en unos cuatro meses")


def inventory(requirements, platform="web", deadline=FOUR_MONTHS):
    return ScopeInventory(
        is_software_project=True,
        not_software_reason="",
        product_types=["formacion"],
        platform=platform,
        platform_reason="la reunión no lo decidió",
        requirements=requirements,
        open_decisions=[
            OpenDecision(question="¿App nativa o web?", options=["web", "movil"], assumed="web",
                         evidence="una app para tablet")
        ],
        deadline=deadline,
    )


SAMPLE = inventory([
    requirement("cuentas_y_roles"),
    requirement("integracion_hris", size="M"),
    requirement("lecciones_y_cuestionarios", status="opcional"),
    requirement("encuestas", custom=[("Full-stack", 30)]),
])


def test_hours_follow_the_catalog():
    hours = inventory_hours(SAMPLE)
    names = [line.name for line in hours.lines]
    assert names[:3] == ["Descubrimiento", "Configuración, arquitectura y lanzamiento", "Diseño de la interfaz"]
    # cuentas S en web: 40 h; HRIS M: 180 h; la opcional no se estima; las encuestas, del modelo
    assert hours.hours_of(CATALOG) == 40 + 180
    assert hours.hours_of(REVIEW) == 30
    assert not any("lecciones" in name.lower() for name in names)
    # 35 % transversal sobre todo lo construido (sin el descubrimiento), con el peso de cada perfil
    # en las estimaciones de referencia
    built = hours.base_hours - 120 - hours.hours_of(OVERHEAD)
    overhead = hours.hours_of(OVERHEAD)
    assert overhead == pytest.approx(built * 0.35, abs=1)
    assert hours.by_role["Gestión de proyecto"] == pytest.approx(overhead * 8.4 / 32.9, abs=1)
    assert hours.by_role["DevOps"] > 0 and hours.by_role["Liderazgo técnico"] > 0
    assert hours.base_hours == 768


def test_each_line_keeps_its_total_when_split_among_roles():
    for line in inventory_hours(SAMPLE).lines:
        assert sum(line.hours.values()) == line.total
    assert distribute(100, {"A": 1, "B": 1, "C": 1}, "web") == {"A": 34, "B": 33, "C": 33}


def test_the_same_inventory_always_gives_the_same_hours():
    assert inventory_hours(SAMPLE) == inventory_hours(SAMPLE.model_copy(deep=True))


@pytest.mark.parametrize(
    ("platform", "size", "expected"),
    [("web", "S", 40), ("web", "L", 120), ("movil", "S", 48), ("web_y_movil", "M", 108)],
)
def test_size_and_platform_factors(platform, size, expected):
    hours = inventory_hours(inventory([requirement("cuentas_y_roles", size=size)], platform))
    assert hours.hours_of(CATALOG) == pytest.approx(expected, abs=1)


def test_build_roles_depend_on_the_platform():
    web = inventory_hours(inventory([requirement("cuentas_y_roles")], "web")).by_role
    mobile = inventory_hours(inventory([requirement("cuentas_y_roles")], "movil")).by_role
    both = inventory_hours(inventory([requirement("cuentas_y_roles")], "web_y_movil")).by_role
    assert {"Backend", "Frontend"} <= set(web) and not {"Móvil", "Full-stack"} & set(web)
    assert {"Backend", "Móvil"} <= set(mobile) and "Frontend" not in mobile
    assert {"Backend", "Frontend", "Móvil"} <= set(both)
    # Las pruebas de cada funcionalidad las hace quien construye: el QA solo sale del 35 %
    feature = [line for line in inventory_hours(SAMPLE).lines if line.name.startswith("Cuentas")][0]
    assert "QA" not in feature.hours


def test_integrations_do_not_scale_with_platform_and_use_quantity():
    hours = inventory_hours(inventory([requirement("integracion_hris", size="L", quantity=2)], "movil"))
    assert hours.hours_of(CATALOG) == 640


def test_prompt_lists_the_catalog_without_hours():
    prompt = get_inventory_prompt()
    for component in COMPONENTS:
        assert f"- {component}:" in prompt
    for product in PRODUCT_TYPES:
        assert f"- {product}:" in prompt
    assert not re.search(r"\d+ h\b", prompt), "el modelo no debe ver las horas del catálogo"
    assert "Innovation Insight" not in prompt
    assert "Sin horas de referencia" in prompt and "a_medida" in prompt


def test_schema_is_strict():
    schema = get_inventory_format()["schema"]
    text = json.dumps(schema, ensure_ascii=False)
    assert '"additionalProperties": false' in text and "integracion_hris" in text
    assert transform_schema(ScopeInventory) == schema


def test_generate_inventory(fake_anthropic):
    messages = fake_anthropic(model_response(text=SAMPLE.model_dump_json()))
    result = asyncio.run(generate_inventory("Transcripción de prueba"))
    call = messages.calls[0]
    assert call["system"][0]["text"] == get_inventory_prompt()
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert call["output_config"]["format"] == get_inventory_format()
    assert result.inventory == SAMPLE
    assert result.hours.base_hours == 768
    assert len(result.calls) == 1 and result.completed == ()  # SAMPLE trae todas sus horas
    assert result.estimated_cost_usd is not None


# Las encuestas no tienen horas en el catálogo y aquí el modelo las dejó vacías.
WITHOUT_HOURS = inventory([
    requirement("cuentas_y_roles"),
    requirement("encuestas"),
    requirement("analitica_de_personas", status="opcional"),  # no acordado: no hacen falta horas
])
FILLED = MissingHours(requirements=[RequirementHours(item=1, hours=[RoleHours(role="Full-stack", hours=25)])])


def test_missing_hours_only_counts_agreed_requirements_without_catalog_hours():
    assert missing_hours(WITHOUT_HOURS) == [1]
    assert missing_hours(SAMPLE) == []
    zero = inventory([requirement("encuestas", custom=[("Full-stack", 0)])])
    assert missing_hours(zero) == [0]


def test_fill_hours_uses_the_list_numbers_and_ignores_the_rest():
    answer = MissingHours(requirements=[*FILLED.requirements, RequirementHours(item=5, hours=[])])
    filled = fill_hours(WITHOUT_HOURS, [1], answer)
    assert filled.requirements[1].custom_hours == FILLED.requirements[0].hours
    assert filled.requirements[0] == WITHOUT_HOURS.requirements[0]
    assert missing_hours(filled) == []


def test_generate_inventory_asks_for_the_missing_hours(fake_anthropic):
    messages = fake_anthropic(
        model_response(text=WITHOUT_HOURS.model_dump_json()), model_response(text=FILLED.model_dump_json())
    )
    result = asyncio.run(generate_inventory("Transcripción de prueba"))
    _, hours_call = messages.calls
    assert hours_call["system"][0]["text"] == get_hours_prompt()
    assert hours_call["output_config"]["format"] == get_hours_format()
    content = hours_call["messages"][0]["content"]
    assert content.startswith("Transcripción de prueba\n\n<requisitos_sin_horas>")
    assert "1. Requisito de encuestas Componente: Encuestas a empleados (encuestas)" in content
    assert "analitica" not in content  # el opcional no se estima
    assert len(result.calls) == 2 and result.completed == ("Requisito de encuestas",)
    assert result.hours.hours_of(REVIEW) == 25


def test_generate_inventory_fails_if_the_hours_are_still_missing(fake_anthropic):
    empty = MissingHours(requirements=[RequirementHours(item=1, hours=[RoleHours(role="QA", hours=0)])])
    fake_anthropic(model_response(text=WITHOUT_HOURS.model_dump_json()), model_response(text=empty.model_dump_json()))
    with pytest.raises(EstimationError, match="no puso horas a: Requisito de encuestas"):
        asyncio.run(generate_inventory("Transcripción de prueba"))


def test_prompts_require_hours_where_the_catalog_has_none():
    assert "Nunca dejes vacías sus horas" in get_inventory_prompt()
    assert "nunca las dejes vacías" in get_inventory_prompt()
    hours_prompt = get_hours_prompt()
    assert "al menos un perfil con horas mayores que 0" in hours_prompt
    assert not re.search(r"\d+ h\b", hours_prompt), "tampoco ve las horas del catálogo"


@pytest.mark.parametrize(
    ("amount", "unit", "weeks"), [(4, "meses", 17), (6, "meses", 26), (12, "semanas", 12), (1, "meses", 4)]
)
def test_the_model_reads_the_deadline_and_python_converts_it(amount, unit, weeks):
    assert Deadline(amount=amount, unit=unit, evidence="frase").weeks == weeks
    assert inventory([], deadline=Deadline(amount=amount, unit=unit, evidence="frase")).deadline_weeks == weeks
    assert inventory([], deadline=None).deadline_weeks is None


def test_deadline_is_required_but_can_be_null():
    schema = get_inventory_format()["schema"]
    assert "deadline" in schema["required"]
    assert {"type": "null"} in schema["properties"]["deadline"]["anyOf"]
    prompt = get_inventory_prompt()
    assert "# Plazo" in prompt and "sin pasarlas a otra unidad" in prompt
