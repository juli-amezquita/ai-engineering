"""Construcción del prompt: convierte las estimaciones de referencia en texto para el modelo.

Es la capa de preprocesamiento entre context/examples.py y el prompt. No llama al LLM ni
lee la configuración, así que se puede probar sin API key. En el paso 4 añadirá el system
prompt completo.

El formato sigue la gestión de contexto en CAG:
- Markdown, el formato por defecto del proyecto y el más parecido al output esperado;
- un delimitador por ejemplo y uno de cierre, para que el modelo no mezcle estimaciones;
- las mismas secciones que tendrá la respuesta, porque el modelo imita lo que ve.
"""

from decimal import ROUND_HALF_UP, Decimal

from app.context.examples import CONTINGENCY_RATE, ESTIMATION_EXAMPLES, ReferenceEstimation

EXAMPLE_DELIMITER = "===== ESTIMACIÓN DE REFERENCIA {number} ====="
END_DELIMITER = "===== FIN DE LAS ESTIMACIONES DE REFERENCIA ====="


def format_number(value: int) -> str:
    """Un solo formato numérico en todo el contexto: coma para los miles, como en EE. UU. (12600 -> 12,600)."""
    return f"{value:,}"


def format_hours(value: Decimal) -> str:
    """Horas con un decimal, porque los imprevistos del 10 % pueden dejar décimas (42.4)."""
    return f"{value:,.1f}"


def format_percent(fraction: Decimal) -> str:
    return f"{(fraction * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)} %"


def format_usd(amount: int) -> str:
    """'USD' explícito en vez de '$', que en Latinoamérica también usan otras monedas."""
    return f"{format_number(amount)} USD"


def format_estimation(number: int, example: ReferenceEstimation) -> str:
    """Formatea una estimación: lo que pidió el cliente y el presupuesto que se le dio."""
    task_rows = [
        f"| {task.name} | "
        + ", ".join(f"{role} {hours}" for role, hours in task.hours_by_role.items())
        + f" | {format_number(task.total_hours)} |"
        for task in example.tasks
    ]
    budget_rows = [
        f"| {budget.role} | {budget.location} | {format_number(budget.base_hours)} "
        f"| {format_hours(budget.contingency_hours)} | {format_hours(budget.total_hours)} "
        f"| {format_percent(example.dedication(budget))} | {format_usd(budget.amount)} |"
        for budget in example.role_budgets
    ]
    expense_rows = [f"| {expense.name} | {format_usd(expense.amount)} |" for expense in example.expenses]
    lines = [
        EXAMPLE_DELIMITER.format(number=number),
        f"Proyecto: {example.title}",
        f"Tipo de proyecto: {example.project_type}",
        "",
        "## Resumen de la reunión",
        example.meeting_summary,
        "",
        "## Estimación",
        "",
        "### Resumen del proyecto",
        example.project_summary,
        "",
        "### Desglose de tareas",
        "| Tarea | Horas por perfil | Horas |",
        "|---|---|---|",
        *task_rows,
        f"| **Total, sin imprevistos** | | **{format_number(example.base_hours)}** |",
        "",
        "### Equipo y presupuesto por profesional",
        f"Un profesional por perfil. Cada uno suma un {format_percent(CONTINGENCY_RATE)} de horas de "
        f"imprevistos. La dedicación es la media sobre las {example.duration_weeks} semanas del proyecto. "
        f"Tarifa media del proyecto, igual para todo el equipo: {example.hourly_rate:.2f} USD/h.",
        "",
        f"| Profesional | Ubicación | Horas base | Imprevistos ({format_percent(CONTINGENCY_RATE)}) "
        "| Horas totales | Dedicación media | Importe |",
        "|---|---|---|---|---|---|---|",
        *budget_rows,
        f"| **Total** | | **{format_number(example.base_hours)}** | **{format_hours(example.contingency_hours)}** "
        f"| **{format_hours(example.total_hours)}** | | **{format_usd(example.fees)}** |",
        "",
        "### Gastos reembolsables, facturados a coste",
        "| Gasto | Importe |",
        "|---|---|",
        *expense_rows,
        f"| **Total** | **{format_usd(example.expenses_total)}** |",
        "",
        "### Precio total",
        f"Honorarios {format_usd(example.fees)} + gastos reembolsables {format_usd(example.expenses_total)} "
        f"= **{format_usd(example.total_price)}**",
        "",
        "### Duración estimada",
        f"{example.duration_weeks} semanas: {example.phases}",
        "",
        "### Riesgos y supuestos",
        *(f"- {risk}" for risk in example.risks),
    ]
    return "\n".join(lines)


def format_examples(examples: tuple[ReferenceEstimation, ...] = ESTIMATION_EXAMPLES) -> str:
    """Todas las estimaciones de referencia, numeradas y delimitadas, listas para el prompt."""
    blocks = [format_estimation(number, example) for number, example in enumerate(examples, start=1)]
    return "\n\n".join([*blocks, END_DELIMITER])
