"""Construcción del prompt: convierte las estimaciones de referencia en texto para el modelo.

Es la capa de preprocesamiento entre context/examples.py y el prompt. No llama al LLM ni
lee la configuración, así que se puede probar sin API key. En el paso 4 añadirá el system
prompt completo.

El formato sigue la gestión de contexto en CAG:
- Markdown, el formato por defecto del proyecto y el más parecido al output esperado;
- un delimitador por ejemplo y uno de cierre, para que el modelo no mezcle estimaciones;
- las mismas secciones que tendrá la respuesta, porque el modelo imita lo que ve.
"""

from app.context.examples import ESTIMATION_EXAMPLES, ReferenceEstimation

EXAMPLE_DELIMITER = "===== ESTIMACIÓN DE REFERENCIA {number} ====="
END_DELIMITER = "===== FIN DE LAS ESTIMACIONES DE REFERENCIA ====="


def format_number(value: int) -> str:
    """Un solo formato numérico en todo el contexto: coma para los miles, como en EE. UU. (12600 -> 12,600)."""
    return f"{value:,}"


def format_usd(amount: int) -> str:
    """'USD' explícito en vez de '$', que en Latinoamérica también usan otras monedas."""
    return f"{format_number(amount)} USD"


def format_estimation(number: int, example: ReferenceEstimation) -> str:
    """Formatea una estimación: lo que pidió el cliente y el presupuesto que se le dio."""
    task_rows = [
        f"| {task.name} | {task.role} | {task.hours} | {task.rate} USD/h | {format_usd(task.cost)} |"
        for task in example.tasks
    ]
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
        "| Tarea | Perfil | Horas | Tarifa | Coste |",
        "|---|---|---|---|---|",
        *task_rows,
        f"| **Total** | | **{format_number(example.total_hours)}** | | **{format_usd(example.total_cost)}** |",
        "",
        "### Equipo recomendado",
        example.team,
        "",
        "### Duración estimada",
        example.duration,
        "",
        "### Riesgos y supuestos",
        *(f"- {risk}" for risk in example.risks),
    ]
    return "\n".join(lines)


def format_examples(examples: tuple[ReferenceEstimation, ...] = ESTIMATION_EXAMPLES) -> str:
    """Todas las estimaciones de referencia, numeradas y delimitadas, listas para el prompt."""
    blocks = [format_estimation(number, example) for number, example in enumerate(examples, start=1)]
    return "\n\n".join([*blocks, END_DELIMITER])
