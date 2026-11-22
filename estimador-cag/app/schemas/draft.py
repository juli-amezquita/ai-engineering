"""Lo que devuelve el modelo: un borrador estructurado de la estimación, sin ninguna cifra de dinero.

El modelo estima alcance, etapas, tareas, horas y gastos, y redacta los textos. Los costos,
tarifas, márgenes, precios y totales los calcula Python (app/services/pricing.py) con estos
datos. La API garantiza que la respuesta cumple este esquema (structured outputs), y las
descripciones de cada campo viajan con el esquema y le dicen al modelo qué poner.
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.context.cost_model import ROLES

RoleName = Literal[tuple(ROLES)]  # type: ignore[valid-type]  # los 13 perfiles del modelo de costos


class RoleHours(BaseModel):
    role: RoleName = Field(description="Perfil del equipo")
    hours: int = Field(description="Horas base de este perfil en la tarea, sin imprevistos: el sistema suma el 10 %")


class Phase(BaseModel):
    name: str = Field(description="Nombre corto de la etapa, por ejemplo 'Descubrimiento y diseño'")
    weeks: int = Field(description="Semanas que dura la etapa")
    deliverables: list[str] = Field(description="Lo que el cliente recibe al terminar la etapa, una frase por entregable")


class Task(BaseModel):
    name: str = Field(description="Qué se hace, en una frase")
    first_phase: int = Field(description="Número de la primera etapa en la que se trabaja en la tarea (1 = la primera)")
    last_phase: int = Field(description="Número de la última etapa en la que se trabaja en la tarea")
    hours: list[RoleHours] = Field(description="Horas base de cada perfil que trabaja en la tarea")


class Expense(BaseModel):
    description: str = Field(description="Gasto reembolsable, que se factura al cliente a coste")
    quantity: float = Field(description="Cantidad, por ejemplo 720 millas o 4 meses")
    unit: str = Field(description="Unidad de la cantidad, por ejemplo 'millas', 'meses' o 'global'")
    unit_cost_usd: float = Field(description="Costo de cada unidad, en USD")


class ValueProposition(BaseModel):
    """La propuesta de negocio para el cliente: textos sin horas, costos ni precios."""

    client_profile: str = Field(description="El cliente por su sector, su tamaño y su ubicación, sin nombres")
    current_situation: str = Field(description="La situación actual y el problema que hay que resolver")
    objectives: list[str] = Field(description="Objetivos del cliente con el proyecto")
    solution: str = Field(description="La solución propuesta, en un párrafo")
    benefits: list[str] = Field(description="Beneficios concretos para el cliente")
    out_of_scope: list[str] = Field(description="Lo que no incluye la propuesta")
    assumptions: list[str] = Field(description="Supuestos y condiciones que el cliente debe conocer, incluidos los legales")


class EstimationDraft(BaseModel):
    is_software_project: bool = Field(description="false si la transcripción no describe un proyecto de software")
    not_software_reason: str = Field(description="Si no es un proyecto de software, por qué, en una frase; si no, vacío")
    project_name: str
    project_type: str = Field(description="Por ejemplo 'App móvil (iOS y Android) con panel web'")
    project_summary: str = Field(description="Resumen interno del alcance, en 2 o 3 frases")
    value_proposition: ValueProposition
    phases: list[Phase] = Field(description="Etapas consecutivas del proyecto, en orden")
    tasks: list[Task] = Field(description="Desglose de tareas con las horas de cada perfil")
    expenses: list[Expense] = Field(description="Gastos reembolsables; lista vacía si no hay")
    open_scope_questions: list[str] = Field(
        description=(
            "Puntos del alcance que la reunión dejó sin decidir (opcionales, condicionados o sin "
            "responsable claro). No se estiman: los decide la consultora. Lista vacía si no hay"
        )
    )
    internal_risks: list[str] = Field(description="Riesgos para la consultora, solo para el informe interno")
