"""Lo que devuelve el modelo en la segunda llamada: el plan del proyecto, sin horas ni dinero.

En la primera llamada el modelo hizo el inventario de alcance y Python calculó las horas de cada
partida de trabajo con el catálogo. En esta, el modelo organiza esas partidas en etapas y redacta
la propuesta. No toca el alcance ni las horas: solo dice en qué etapas se trabaja cada partida.
Python une las dos cosas en un `EstimationDraft` (app/services/plan_service.py), y desde ahí la
planificación, el precio y los informes son los mismos de siempre.
"""

from pydantic import BaseModel, Field

from app.schemas.draft import Expense, Phase, ValueProposition


class WorkAssignment(BaseModel):
    item: int = Field(description="Número de la partida de trabajo, tal como aparece en el inventario")
    first_phase: int = Field(description="Primera etapa en la que se trabaja en la partida (1 = la primera)")
    last_phase: int = Field(description="Última etapa en la que se trabaja en la partida")


class PlanDraft(BaseModel):
    project_name: str
    project_type: str = Field(description="Por ejemplo 'App móvil (iOS y Android) con panel web'")
    project_summary: str = Field(description="Resumen interno del alcance, en 2 o 3 frases")
    value_proposition: ValueProposition
    phases: list[Phase] = Field(description="Etapas consecutivas del proyecto, en orden")
    assignments: list[WorkAssignment] = Field(
        description="Una entrada por cada partida de trabajo numerada: en qué etapas se hace"
    )
    expenses: list[Expense] = Field(description="Gastos reembolsables; lista vacía si no hay")
    internal_risks: list[str] = Field(description="Riesgos para la consultora, solo para el informe interno")
