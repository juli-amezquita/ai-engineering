"""El prompt de la segunda llamada: organizar en etapas un trabajo cuyas horas ya están fijadas.

El system prompt tiene las instrucciones, las estimaciones de referencia en el mismo formato que la
respuesta y las reglas. Es idéntico en cada llamada, así que va a la caché del proveedor. El
mensaje del usuario lleva la transcripción y el inventario: las partidas de trabajo numeradas con
sus horas, lo que no se acordó, lo que se excluyó y las decisiones abiertas.

El modelo ve las horas de cada partida para dimensionar las etapas, pero no las puede cambiar: el
esquema de la respuesta no tiene horas. Tampoco ve ninguna cifra de dinero.
"""

from app.context.catalog import PLATFORM_NAMES, PRODUCT_TYPES
from app.context.cost_model import CONTINGENCY_RATE, HOURS_PER_WEEK
from app.context.examples import ESTIMATION_EXAMPLES, ReferenceEstimation
from app.schemas.draft import EstimationDraft
from app.schemas.inventory import ScopeInventory
from app.schemas.plan import PlanDraft, WorkAssignment
from app.services.catalog_hours import OVERHEAD, HoursLine, InventoryHours
from app.services.formatting import number, pct
from app.services.prompt_builder import END_DELIMITER, EXAMPLE_DELIMITER

# Horas base que cabe en una semana de una persona, con los imprevistos incluidos.
WEEKLY_BASE_HOURS = int(HOURS_PER_WEEK / (1 + CONTINGENCY_RATE))


def format_item(number_: int, name: str, hours: dict[str, int]) -> str:
    detail = ", ".join(f"{role} {value}" for role, value in hours.items())
    return f"{number_}. {name}: {number(sum(hours.values()))} h ({detail})"


def work_items(hours: InventoryHours) -> list[HoursLine]:
    """Las partidas que el modelo reparte en etapas: todo menos la gestión y el QA transversal,
    que el sistema reparte en todas las etapas, y las líneas sin horas."""
    return [line for line in hours.lines if line.kind != OVERHEAD and line.total > 0]


# ---------------------------------------------------------------------------
# Estimaciones de referencia, en el formato de esta llamada
# ---------------------------------------------------------------------------


def plan_from_draft(draft: EstimationDraft) -> PlanDraft:
    """La respuesta de una referencia: su borrador sin horas, con cada tarea como una partida."""
    return PlanDraft(
        project_name=draft.project_name,
        project_type=draft.project_type,
        project_summary=draft.project_summary,
        value_proposition=draft.value_proposition,
        phases=draft.phases,
        assignments=[
            WorkAssignment(item=number_, first_phase=task.first_phase, last_phase=task.last_phase)
            for number_, task in enumerate(draft.tasks, start=1)
        ],
        expenses=draft.expenses,
        internal_risks=draft.internal_risks,
    )


def format_plan_example(number_: int, example: ReferenceEstimation) -> str:
    items = [
        format_item(item, task.name, {entry.role: entry.hours for entry in task.hours})
        for item, task in enumerate(example.draft.tasks, start=1)
    ]
    return "\n".join([
        EXAMPLE_DELIMITER.format(number=number_),
        "## Resumen de la reunión",
        example.meeting_summary,
        "",
        "## Partidas de trabajo",
        *items,
        "",
        "## Respuesta",
        "```json",
        plan_from_draft(example.draft).model_dump_json(indent=2),
        "```",
    ])


def format_plan_examples(examples: tuple[ReferenceEstimation, ...] = ESTIMATION_EXAMPLES) -> str:
    blocks = [format_plan_example(n, example) for n, example in enumerate(examples, start=1)]
    return "\n\n".join([*blocks, END_DELIMITER])


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

INTRO = """\
# Rol
Eres la persona líder responsable de las estimaciones, valoraciones y presupuestación de los \
proyectos de software de una empresa consultora pequeña de software del sur de California. \
La consultora hace productos de RR. HH. y People Analytics para empresas de cemento, \
hormigón premezclado, áridos y minería de California, y conoce el marco que afecta a esos \
proyectos: la CCPA/CPRA, que también protege los datos de los empleados; las normas de \
California sobre sistemas automatizados en decisiones de empleo; la California Equal Pay Act \
y el informe de datos salariales al Civil Rights Department (CRD); y la seguridad laboral de \
Cal/OSHA y MSHA.

# Tarea
El mensaje del usuario trae la transcripción de una reunión con un cliente y el inventario de \
alcance que ya se hizo con ella. El inventario tiene las partidas de trabajo numeradas, con las \
horas de cada perfil que calculó el sistema con su catálogo. El alcance y las horas ya están \
decididos: tu trabajo es organizar el proyecto y redactar la propuesta.
- Divide el proyecto en etapas, con sus semanas y sus entregables.
- Di en qué etapas se trabaja cada partida.
- Añade los gastos reembolsables y los riesgos para la consultora.
- Redacta los textos de la propuesta de valor para el cliente.

No calcules costos, tarifas, márgenes, precios ni totales. Con tus datos, el sistema arma el \
cronograma, valora y presupuesta el proyecto en Python y prepara dos documentos: un informe \
interno para la consultora y la propuesta de negocio para el cliente.

# Cómo usar las estimaciones de referencia
Más abajo hay estimaciones reales de la consultora, cada una entre delimitadores, con el \
resumen de la reunión, sus partidas de trabajo y la respuesta que se dio. Úsalas como \
referencia de cómo se agrupan las partidas en etapas, de cuántas semanas dura cada etapa y del \
tono de la propuesta. No las copies: organiza el proyecto de la transcripción.

# Qué devolver
Un JSON con el esquema que fija la API, como las respuestas de las referencias:
- `assignments` tiene una entrada por cada partida numerada del inventario, con su número y la \
primera y la última etapa en las que se trabaja en ella.
- `project_summary` e `internal_risks` son para el informe interno: escribe con franqueza lo \
que puede salir mal para la consultora.
- `value_proposition` es para el cliente: va dirigida a su dirección, en un tono profesional y \
concreto, y habla de su problema, de la solución y de sus beneficios. Sin horas, costos ni \
precios: las cifras las pone el sistema.
- `phases` son las etapas del cronograma que verá el cliente, con lo que recibe al terminar \
cada una."""


def build_rules() -> str:
    contingency = pct(CONTINGENCY_RATE, 0)
    return f"""\
# Alcance
- El alcance es el del inventario. No añadas funcionalidades, entregables, integraciones ni \
perfiles que no estén en sus partidas, y no quites ninguna partida.
- Los requisitos sin acordar del inventario no se estiman: el sistema los presenta como puntos \
por confirmar. No los incluyas en etapas, entregables, beneficios ni `out_of_scope`.
- `out_of_scope` recoge lo que el inventario marca como excluido y las exclusiones habituales de \
la consultora, como el soporte después del hipercuidado o el consumo de la nube y de las APIs \
en producción.
- `assumptions` recoge, entre otros supuestos, la opción que el inventario asume en cada \
decisión abierta, para que el cliente la conozca.
- `project_type` describe la plataforma del inventario.
- Si el mensaje trae una sección <cambios_de_alcance>, la escribió la consultora y ya está \
aplicada en el inventario: tenla en cuenta en los textos.

# Reglas del cronograma
- Cada partida aparece una sola vez en `assignments`, con el número que tiene en el inventario.
- Las etapas son consecutivas. Las horas de cada partida se reparten por igual entre las \
semanas de las etapas en las que se trabaja en ella.
- Si el inventario trae el plazo que pidió el cliente, las semanas de las etapas suman \
exactamente ese plazo: reparte el trabajo para terminar en él. Si no lo suman, el sistema ajusta \
las etapas en la misma proporción. Si el inventario no trae plazo, da a cada etapa las semanas \
que necesite el equipo.
- Cada profesional trabaja como máximo {HOURS_PER_WEEK} horas por semana, con un {contingency} \
de imprevistos incluido: unas {WEEKLY_BASE_HOURS} horas base por semana. Da a cada etapa semanas \
suficientes para las horas de cada perfil y reparte las partidas largas entre varias etapas. \
El sistema comprueba la carga de cada semana y alarga las etapas en las que alguien no quepa, \
aunque eso pase del plazo del cliente, y se lo avisa a la consultora.
- La gestión de proyecto y el QA transversal no son partidas: el sistema los reparte en todas \
las etapas. Ten en cuenta sus horas al dar las semanas.
- Los gastos reembolsables se facturan al cliente a coste. De cada uno da la cantidad, la unidad \
y el costo unitario en USD, y el sistema calcula el importe.
- Escribe las cifras como en EE. UU., con coma para los miles y punto para los decimales, y la \
moneda como "USD", nunca con "$".

# Restricciones
- No escribas costos, tarifas, márgenes, precios ni totales en ningún campo. Tampoco afirmes \
cifras que calcula el sistema, como las horas, la dedicación o la carga de cada perfil, ni \
digas si el cronograma cumple el plazo del cliente: lo comprueba el sistema.
- Usa los datos del cliente tal como aparecen en la transcripción: cifras, porcentajes y \
plazos, sin redondearlos ni reinterpretarlos.
- Si a la transcripción le falta un dato que necesitas, haz un supuesto razonable y explícalo: \
en `assumptions` si afecta al cliente, en `internal_risks` si solo afecta a la consultora. No \
inventes datos del cliente.
- Describe al cliente por su sector, su tamaño y su ubicación, sin nombres de personas ni de \
empresas."""


def build_plan_prompt(examples: tuple[ReferenceEstimation, ...] = ESTIMATION_EXAMPLES) -> str:
    return "\n\n".join([INTRO, format_plan_examples(examples), build_rules()])


# ---------------------------------------------------------------------------
# Mensaje del usuario
# ---------------------------------------------------------------------------


def _deadline(inventory: ScopeInventory) -> str:
    if inventory.deadline is None:
        return "La reunión no fija un plazo: da a cada etapa las semanas que necesite el equipo."
    weeks = inventory.deadline.weeks
    evidence = inventory.deadline.evidence.strip(" .«»\"")
    return f"El cliente pidió el producto en {weeks} semanas («{evidence}»): las etapas suman {weeks} semanas."


def format_inventory(inventory: ScopeInventory, hours: InventoryHours) -> str:
    products = ", ".join(PRODUCT_TYPES[product].name.rstrip(".") for product in inventory.product_types)
    lines = [
        f"Plataforma: {PLATFORM_NAMES[inventory.platform]}. {inventory.platform_reason}",
        f"Tipos de producto: {products or 'ninguno del catálogo'}.",
        "",
        "## Plazo",
        _deadline(inventory),
        "",
        "## Partidas de trabajo",
        "Horas base por perfil, sin imprevistos, calculadas por el sistema. No se cambian.",
    ]
    lines += [format_item(n, line.name, line.hours) for n, line in enumerate(work_items(hours), start=1)]
    for line in hours.lines:
        if line.kind == OVERHEAD:
            detail = ", ".join(f"{role} {value}" for role, value in line.hours.items())
            lines.append(
                f"Además, el sistema reparte en todas las etapas «{line.name}»: "
                f"{number(line.total)} h ({detail})."
            )
    pending = [r for r in inventory.requirements if r.status in ("opcional", "condicionado")]
    excluded = [r for r in inventory.requirements if r.status == "excluido"]
    if pending:
        lines += ["", "## Requisitos sin acordar: no se estiman"]
        lines += [f"- {r.description} ({r.status})" for r in pending]
    if excluded:
        lines += ["", "## Excluido en la reunión"]
        lines += [f"- {r.description}" for r in excluded]
    if inventory.open_decisions:
        lines += ["", "## Decisiones abiertas"]
        lines += [
            f"- {d.question} Opciones: {'; '.join(d.options)}. Se asume: {d.assumed}."
            for d in inventory.open_decisions
        ]
    return "\n".join(lines)


def build_plan_message(
    transcription: str,
    inventory: ScopeInventory,
    hours: InventoryHours,
    scope_changes: str | None = None,
) -> str:
    """La transcripción, el inventario y, si los hay, los cambios de alcance, cada uno entre etiquetas."""
    message = (
        f"<transcripcion>\n{transcription}\n</transcripcion>\n\n"
        f"<inventario>\n{format_inventory(inventory, hours)}\n</inventario>"
    )
    if scope_changes:
        message += f"\n\n<cambios_de_alcance>\n{scope_changes}\n</cambios_de_alcance>"
    return message
