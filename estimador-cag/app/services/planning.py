"""Planificación: del borrador del modelo a un cronograma que nadie puede incumplir.

El modelo propone etapas con sus semanas y tareas con las horas base de cada perfil. Python:
- valida el borrador (etapas, tareas y gastos coherentes);
- suma el 10 % de imprevistos a cada profesional;
- reparte las horas de cada tarea por igual entre las semanas de sus etapas;
- comprueba la carga semanal de cada perfil (un profesional por perfil, 40 horas por semana con
  los imprevistos incluidos) y, si alguien no cabe, alarga una semana la etapa en la que no cabe
  hasta que quepa. Así ninguna dedicación pasa nunca del 100 %, y no depende del modelo.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.context.cost_model import CONTINGENCY_RATE, HOURS_PER_WEEK, ROLES, round_usd
from app.schemas.draft import EstimationDraft

MAX_EXTRA_WEEKS = 104  # tope de seguridad: más de dos años de alargue es un borrador roto
_TOLERANCE = 1e-9


class NotASoftwareProjectError(ValueError):
    """La transcripción no describe un proyecto de software."""


class InvalidDraftError(ValueError):
    """El borrador del modelo no se puede planificar."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("El borrador del modelo no es válido: " + "; ".join(problems))


@dataclass(frozen=True)
class PhasePlan:
    number: int
    name: str
    proposed_weeks: int
    weeks: int
    start_week: int
    end_week: int
    deliverables: tuple[str, ...]


@dataclass(frozen=True)
class TaskPlan:
    name: str
    first_phase: int
    last_phase: int
    start_week: int
    end_week: int
    hours: dict[str, int]  # horas base por perfil

    @property
    def base_hours(self) -> int:
        return sum(self.hours.values())


@dataclass(frozen=True)
class ExpenseLine:
    description: str
    quantity: float
    unit: str
    unit_cost_usd: float
    amount: int  # cantidad × costo unitario, redondeado al dólar


@dataclass(frozen=True)
class ProjectPlan:
    draft: EstimationDraft
    phases: tuple[PhasePlan, ...]
    tasks: tuple[TaskPlan, ...]
    expenses: tuple[ExpenseLine, ...]
    base_hours_by_role: dict[str, int]  # en el orden en que aparece cada perfil
    weekly_hours: dict[str, tuple[float, ...]]  # horas con imprevistos de cada perfil, semana a semana
    adjustments: tuple[str, ...]  # cambios de Python al cronograma propuesto

    @property
    def duration_weeks(self) -> int:
        return self.phases[-1].end_week

    def total_hours(self, role: str) -> float:
        return self.base_hours_by_role[role] * (1 + CONTINGENCY_RATE)

    def peak_dedication(self, role: str) -> float:
        return max(self.weekly_hours[role]) / HOURS_PER_WEEK

    def average_dedication(self, role: str) -> float:
        return self.total_hours(role) / (self.duration_weeks * HOURS_PER_WEEK)

    def phase_of_week(self, week: int) -> PhasePlan:
        return next(phase for phase in self.phases if phase.start_week <= week <= phase.end_week)


def validate_draft(draft: EstimationDraft) -> None:
    """Rechaza lo que no se puede planificar. Los tipos ya los garantiza el esquema de la API."""
    if not draft.is_software_project:
        raise NotASoftwareProjectError(draft.not_software_reason or "La transcripción no describe un proyecto de software")
    problems: list[str] = []
    if not draft.project_name.strip():
        problems.append("falta el nombre del proyecto")
    if not draft.phases:
        problems.append("no hay etapas")
    for number, phase in enumerate(draft.phases, start=1):
        if phase.weeks < 1:
            problems.append(f"la etapa {number} dura {phase.weeks} semanas")
    if not draft.tasks:
        problems.append("no hay tareas")
    for task in draft.tasks:
        if not 1 <= task.first_phase <= task.last_phase <= len(draft.phases):
            problems.append(f"la tarea {task.name!r} va de la etapa {task.first_phase} a la {task.last_phase}")
        if not task.hours:
            problems.append(f"la tarea {task.name!r} no tiene horas")
        roles = [entry.role for entry in task.hours]
        if len(roles) != len(set(roles)):
            problems.append(f"la tarea {task.name!r} repite un perfil")
        for entry in task.hours:
            if entry.hours <= 0:
                problems.append(f"la tarea {task.name!r} tiene {entry.hours} horas de {entry.role}")
    for expense in draft.expenses:
        if expense.quantity <= 0 or expense.unit_cost_usd <= 0:
            problems.append(f"el gasto {expense.description!r} no tiene cantidad o costo positivos")
    if problems:
        raise InvalidDraftError(problems)


def _phase_bounds(weeks: list[int]) -> list[tuple[int, int]]:
    bounds, start = [], 1
    for phase_weeks in weeks:
        bounds.append((start, start + phase_weeks - 1))
        start += phase_weeks
    return bounds


def _weekly_hours(draft: EstimationDraft, weeks: list[int]) -> dict[str, list[float]]:
    bounds = _phase_bounds(weeks)
    duration = bounds[-1][1]
    load: dict[str, list[float]] = {}
    for task in draft.tasks:
        start, end = bounds[task.first_phase - 1][0], bounds[task.last_phase - 1][1]
        span = end - start + 1
        for entry in task.hours:
            per_week = entry.hours * (1 + CONTINGENCY_RATE) / span
            role_load = load.setdefault(entry.role, [0.0] * duration)
            for week in range(start, end + 1):
                role_load[week - 1] += per_week
    return load


def _first_overload(load: dict[str, list[float]]) -> tuple[int, list[str]] | None:
    """La primera semana en la que algún perfil pasa de su jornada, y qué perfiles."""
    duration = len(next(iter(load.values())))
    for week in range(1, duration + 1):
        over = [role for role, hours in load.items() if hours[week - 1] > HOURS_PER_WEEK + _TOLERANCE]
        if over:
            return week, over
    return None


def build_plan(draft: EstimationDraft) -> ProjectPlan:
    """Valida el borrador y devuelve un cronograma en el que nadie pasa del 100 % de dedicación."""
    validate_draft(draft)
    weeks = [phase.weeks for phase in draft.phases]
    overloaded_roles: dict[int, set[str]] = {}
    for _ in range(MAX_EXTRA_WEEKS + 1):
        load = _weekly_hours(draft, weeks)
        overload = _first_overload(load)
        if overload is None:
            break
        week, roles = overload
        phase_index = next(i for i, (start, end) in enumerate(_phase_bounds(weeks)) if start <= week <= end)
        weeks[phase_index] += 1
        overloaded_roles.setdefault(phase_index, set()).update(roles)
    else:
        raise InvalidDraftError([f"hacen falta más de {MAX_EXTRA_WEEKS} semanas extra para que el equipo quepa"])

    bounds = _phase_bounds(weeks)
    phases = tuple(
        PhasePlan(
            number=i + 1,
            name=phase.name,
            proposed_weeks=phase.weeks,
            weeks=weeks[i],
            start_week=bounds[i][0],
            end_week=bounds[i][1],
            deliverables=tuple(phase.deliverables),
        )
        for i, phase in enumerate(draft.phases)
    )
    adjustments = tuple(
        f"La etapa {phases[i].number}, «{phases[i].name}», pasa de {phases[i].proposed_weeks} a "
        f"{phases[i].weeks} semanas para que {', '.join(sorted(roles))} no pase de "
        f"{HOURS_PER_WEEK} horas por semana."
        for i, roles in sorted(overloaded_roles.items())
    )
    tasks = tuple(
        TaskPlan(
            name=task.name,
            first_phase=task.first_phase,
            last_phase=task.last_phase,
            start_week=bounds[task.first_phase - 1][0],
            end_week=bounds[task.last_phase - 1][1],
            hours={entry.role: entry.hours for entry in task.hours},
        )
        for task in draft.tasks
    )
    base_hours: dict[str, int] = {}
    for task in tasks:
        for role, hours in task.hours.items():
            base_hours[role] = base_hours.get(role, 0) + hours
    expenses = tuple(
        ExpenseLine(
            description=expense.description,
            quantity=expense.quantity,
            unit=expense.unit,
            unit_cost_usd=expense.unit_cost_usd,
            amount=round_usd(Decimal(str(expense.quantity)) * Decimal(str(expense.unit_cost_usd))),
        )
        for expense in draft.expenses
    )
    # Perfiles en el orden del modelo de costos, para que los informes sean estables.
    ordered = {role: base_hours[role] for role in ROLES if role in base_hours}
    return ProjectPlan(
        draft=draft,
        phases=phases,
        tasks=tasks,
        expenses=expenses,
        base_hours_by_role=ordered,
        weekly_hours={role: tuple(load[role]) for role in ordered},
        adjustments=adjustments,
    )
