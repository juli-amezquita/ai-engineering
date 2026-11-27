"""Planificación: del borrador del modelo a un cronograma que nadie puede incumplir.

El modelo propone etapas con sus semanas y tareas con las horas base de cada perfil. Python:
- valida el borrador (etapas, tareas y gastos coherentes);
- si el cliente pidió un plazo, ajusta las semanas de las etapas para que sumen ese plazo, en la
  misma proporción que propuso el modelo;
- suma el 10 % de imprevistos a cada profesional;
- reparte las horas de cada tarea por igual entre las semanas de sus etapas;
- comprueba la carga semanal de cada perfil (un profesional por perfil, 40 horas por semana con
  los imprevistos incluidos) y, si alguien no cabe, alarga una semana la etapa en la que no cabe
  hasta que quepa. Así ninguna dedicación pasa nunca del 100 %, y no depende del modelo. Si
  para eso hay que pasar del plazo del cliente, el cronograma pasa del plazo y los controles lo
  avisan: el plazo nunca se cumple a costa de sobrecargar a nadie.
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
    adjustments: tuple[str, ...]  # etapas que Python alargó porque alguien no cabía
    deadline_weeks: int | None = None  # el plazo que pidió el cliente, si pidió alguno
    fitted_to_deadline: bool = False  # si Python ajustó las semanas del modelo a ese plazo

    @property
    def duration_weeks(self) -> int:
        return self.phases[-1].end_week

    @property
    def proposed_weeks(self) -> int:
        """Lo que sumaban las etapas que propuso el modelo."""
        return sum(phase.proposed_weeks for phase in self.phases)

    @property
    def meets_deadline(self) -> bool | None:
        if self.deadline_weeks is None:
            return None
        return self.duration_weeks <= self.deadline_weeks

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


def fit_to_deadline(weeks: list[int], deadline: int) -> list[int]:
    """Las semanas de cada etapa, en la proporción que propuso el modelo, para que sumen el plazo.

    Redondea por el mayor resto, como el reparto de horas entre perfiles, y deja al menos una
    semana por etapa. Si hay más etapas que semanas de plazo, no las toca.
    """
    total = sum(weeks)
    if total == deadline or deadline < len(weeks):
        return list(weeks)
    shares = [phase_weeks * deadline / total for phase_weeks in weeks]
    fitted = [max(1, int(share)) for share in shares]
    by_remainder = sorted(range(len(weeks)), key=lambda i: shares[i] - int(shares[i]), reverse=True)
    for i in by_remainder[: max(deadline - sum(fitted), 0)]:
        fitted[i] += 1
    while sum(fitted) > deadline:  # el mínimo de una semana puede pasarse: se quita a la más larga
        fitted[fitted.index(max(fitted))] -= 1
    return fitted


def _extend(draft: EstimationDraft, planned: list[int]) -> tuple[list[int], dict[int, set[str]], dict[str, list[float]]]:
    """Alarga una semana la etapa de la primera semana en la que alguien no cabe, hasta que quepan todos."""
    weeks = list(planned)
    overloaded_roles: dict[int, set[str]] = {}
    for _ in range(MAX_EXTRA_WEEKS + 1):
        load = _weekly_hours(draft, weeks)
        overload = _first_overload(load)
        if overload is None:
            return weeks, overloaded_roles, load
        week, roles = overload
        phase_index = next(i for i, (start, end) in enumerate(_phase_bounds(weeks)) if start <= week <= end)
        weeks[phase_index] += 1
        overloaded_roles.setdefault(phase_index, set()).update(roles)
    raise InvalidDraftError([f"hacen falta más de {MAX_EXTRA_WEEKS} semanas extra para que el equipo quepa"])


def build_plan(draft: EstimationDraft, deadline_weeks: int | None = None) -> ProjectPlan:
    """Valida el borrador y devuelve un cronograma en el que nadie pasa del 100 % de dedicación.

    Con `deadline_weeks`, las etapas se ajustan primero al plazo que pidió el cliente. Si así el
    equipo no cabe en el plazo y partir de las semanas del modelo da un cronograma más corto, se
    parte de las semanas del modelo: el alargue va etapa por etapa y, con las etapas apretadas,
    puede alargar más de la cuenta.
    """
    validate_draft(draft)
    proposed = [phase.weeks for phase in draft.phases]
    planned = fit_to_deadline(proposed, deadline_weeks) if deadline_weeks is not None else proposed
    weeks, overloaded_roles, load = _extend(draft, planned)
    if deadline_weeks is not None and sum(weeks) > deadline_weeks and planned != proposed:
        alternative = _extend(draft, proposed)
        if sum(alternative[0]) < sum(weeks):
            planned = proposed
            weeks, overloaded_roles, load = alternative

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
        f"La etapa {phases[i].number}, «{phases[i].name}», pasa de {planned[i]} a "
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
        deadline_weeks=deadline_weeks,
        fitted_to_deadline=planned != proposed,
    )
