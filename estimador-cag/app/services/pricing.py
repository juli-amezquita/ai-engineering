"""Valoración y presupuesto: todos los cálculos de dinero del proyecto, en Python.

El precio sale del margen objetivo, como en el análisis v6 del vault: se buscan los honorarios
que dejan una utilidad neta del 30 % sobre el precio total, y la tarifa media resultante
(honorarios ÷ horas con imprevistos) no puede pasar de 150 USD/h. Si para llegar al 30 % hiciera
falta más, se cobra el tope y el informe interno lo marca.

La propuesta al cliente reparte esos mismos honorarios sin mostrar costos ni márgenes:
- cada consultor tiene su tarifa = costo por hora × (1 + imprevistos + recargo de rentabilidad),
  y se factura por sus horas base;
- los gastos generales del proyecto (plataforma de contratistas, gastos fijos asignados y
  marketing) van en una sola línea, con el mismo recargo y los mismos imprevistos;
- el recargo de rentabilidad es el que hace que todo sume exactamente los honorarios;
- los gastos reembolsables van aparte, a coste.
"""

from collections import defaultdict
from dataclasses import dataclass, replace
from decimal import Decimal

from app.context.cost_model import (
    CA_SCORP_TAX_RATE,
    COLLECTION_DAYS,
    CONTINGENCY_RATE,
    CONTRACTOR_PLATFORM_FEE_USD,
    DAYS_PER_MONTH,
    FIRM_ANNUAL_FEES,
    FIRM_BILLABLE_HOURS,
    FIXED_OVERHEAD_PER_HOUR,
    FIXED_OVERHEAD_TOTAL,
    HOURS_PER_WEEK,
    MARKETING_RATE,
    MAX_BLENDED_RATE_USD,
    PAYMENT_MILESTONES,
    ROLES,
    SMALL_AGENCY_NET_MARGIN,
    SMALL_FIRM_RATE_RANGE_USD,
    SPECIALIZED_AGENCY_NET_MARGIN,
    TARGET_NET_MARGIN,
    Role,
    month_of_day,
    project_months,
    round_cents,
    round_usd,
    solve_fees,
)
from app.services.formatting import pct
from app.services.planning import ProjectPlan

NEGOTIATION_MARGINS = (0.25, 0.20, 0.10, 0.0)  # por debajo del objetivo
OK, WARNING, INFO = "ok", "warning", "info"


@dataclass(frozen=True)
class IncomeStatement:
    """Estado de resultados del proyecto, en USD."""

    fees: int
    expenses: int  # gastos reembolsables, que se cobran y se pagan a coste
    labor: int
    platform: int
    fixed_overhead: int
    marketing: int

    @property
    def price(self) -> int:
        return self.fees + self.expenses

    @property
    def gross_margin(self) -> int:
        return self.price - self.labor - self.platform - self.expenses

    @property
    def operating_profit(self) -> int:
        return self.gross_margin - self.fixed_overhead - self.marketing

    @property
    def tax(self) -> int:
        return max(0, round_usd(CA_SCORP_TAX_RATE * self.operating_profit))

    @property
    def net_profit(self) -> int:
        return self.operating_profit - self.tax

    @property
    def net_margin(self) -> float:
        return self.net_profit / self.price


def income_statement(fees: int, expenses: int, labor: int, platform: int, fixed_overhead: int) -> IncomeStatement:
    return IncomeStatement(fees, expenses, labor, platform, fixed_overhead, round_usd(MARKETING_RATE * fees))


@dataclass(frozen=True)
class RoleLine:
    """Un profesional: sus horas, su costo y lo que se le factura al cliente."""

    role: Role
    base_hours: int
    total_hours: float  # con el 10 % de imprevistos
    cost: int  # horas totales × costo por hora
    client_rate: float  # costo por hora × (1 + imprevistos + recargo), lo único que ve el cliente
    client_amount: int  # horas base × tarifa al cliente

    @property
    def contingency_hours(self) -> float:
        return self.total_hours - self.base_hours


@dataclass(frozen=True)
class Milestone:
    number: int
    label: str
    week: int  # 0 = a la firma
    amount: int
    collection_month: int


@dataclass(frozen=True)
class CashRow:
    month: int
    collections: int
    payments: int

    @property
    def net(self) -> int:
        return self.collections - self.payments


@dataclass(frozen=True)
class Scenario:
    label: str
    hours: float
    statement: IncomeStatement


@dataclass(frozen=True)
class NegotiationRow:
    margin: float
    fees: int
    price: int
    discount: float  # frente al precio propuesto; negativo si habría que subirlo


@dataclass(frozen=True)
class Check:
    status: str  # ok, warning o info
    text: str


@dataclass(frozen=True)
class ProjectPricing:
    plan: ProjectPlan
    lines: tuple[RoleLine, ...]
    contractors: int
    months: int
    statement: IncomeStatement
    rate_for_target: float  # tarifa media que dejaría exactamente el margen objetivo
    rate: float  # tarifa media aplicada, con el tope de mercado
    factor: float  # 1 + imprevistos + recargo de rentabilidad
    overhead_base: int  # plataforma + gastos fijos asignados + marketing, sin recargo
    overhead_client_amount: int  # la línea de gastos generales de la propuesta
    milestones: tuple[Milestone, ...]
    cash_flow: tuple[CashRow, ...]
    market_alternative: IncomeStatement | None  # a 150 USD/h, si el proyecto queda por debajo
    negotiation: tuple[NegotiationRow, ...]
    sensitivity: tuple[Scenario, ...]
    overrun_to_margin_20: float  # sobrecosto de horas que deja el margen en el 20 %
    overrun_to_break_even: float  # sobrecosto de horas que deja la utilidad en cero
    checks: tuple[Check, ...]

    @property
    def capped(self) -> bool:
        return self.rate < self.rate_for_target

    @property
    def markup(self) -> float:
        return self.factor - 1 - CONTINGENCY_RATE

    @property
    def base_hours(self) -> int:
        return sum(line.base_hours for line in self.lines)

    @property
    def total_hours(self) -> float:
        return sum(line.total_hours for line in self.lines)

    @property
    def contingency_hours(self) -> float:
        return self.total_hours - self.base_hours

    @property
    def max_cash_needed(self) -> int:
        cumulative, lowest = 0, 0
        for row in self.cash_flow:
            cumulative += row.net
            lowest = min(lowest, cumulative)
        return -lowest

    @property
    def hours_share_of_firm(self) -> float:
        return self.total_hours / FIRM_BILLABLE_HOURS

    @property
    def fees_share_of_firm(self) -> float:
        return self.statement.fees / FIRM_ANNUAL_FEES

    @property
    def full_time_equivalents(self) -> float:
        return self.total_hours / (self.plan.duration_weeks * HOURS_PER_WEEK)


def _total_hours(base_hours: int) -> float:
    """Horas con imprevistos, con aritmética decimal para no arrastrar errores de coma flotante."""
    return float(Decimal(base_hours) * (1 + Decimal(str(CONTINGENCY_RATE))))


def _milestone_weeks(plan: ProjectPlan) -> tuple[int, int]:
    """Semanas de los hitos 2 y 3: el fin de la primera etapa y el de la etapa central más larga."""
    phases, duration = plan.phases, plan.duration_weeks
    if len(phases) >= 3:
        longest = max(phases[1:-1], key=lambda phase: phase.weeks)
        return phases[0].end_week, longest.end_week
    second = phases[0].end_week if len(phases) == 2 else max(1, round(duration / 4))
    return second, max(second, round(duration * 3 / 4))


def _milestones(plan: ProjectPlan, fees: int) -> tuple[Milestone, ...]:
    share = round_usd(fees / PAYMENT_MILESTONES)
    amounts = [share] * (PAYMENT_MILESTONES - 1) + [fees - share * (PAYMENT_MILESTONES - 1)]
    second, third = _milestone_weeks(plan)

    def at_end_of(week: int) -> str:
        phase = plan.phase_of_week(week)
        if phase.end_week == week:
            return f"Al terminar la etapa {phase.number}, «{phase.name}» (semana {week})"
        return f"Al terminar la semana {week}"

    labels_weeks = [
        ("A la firma del contrato", 0),
        (at_end_of(second), second),
        (at_end_of(third), third),
        (f"Al cierre del proyecto (semana {plan.duration_weeks})", plan.duration_weeks),
    ]
    return tuple(
        Milestone(
            number=i + 1,
            label=label,
            week=week,
            amount=amounts[i],
            collection_month=1 if week == 0 else month_of_day(week * 7 + COLLECTION_DAYS),
        )
        for i, (label, week) in enumerate(labels_weeks)
    )


def _cash_flow(plan: ProjectPlan, statement: IncomeStatement, milestones: tuple[Milestone, ...]) -> tuple[CashRow, ...]:
    """Flujo de caja mensual. El equipo se paga según el cronograma; lo demás, por igual cada semana."""
    duration = plan.duration_weeks
    weekly_labor = [
        sum(plan.weekly_hours[role][week] * ROLES[role].cost_per_hour for role in plan.weekly_hours)
        for week in range(duration)
    ]
    scale = statement.labor / sum(weekly_labor)  # para que la suma sea el costo redondeado
    weekly_other = (statement.platform + statement.fixed_overhead + statement.marketing + statement.expenses) / duration
    collections: dict[int, float] = defaultdict(float)
    payments: dict[int, float] = defaultdict(float)
    expenses_by_month: dict[int, float] = defaultdict(float)
    for week in range(1, duration + 1):
        month = month_of_day((week - 0.5) * 7)
        payments[month] += weekly_labor[week - 1] * scale + weekly_other
        expenses_by_month[month] += statement.expenses / duration
    for milestone in milestones:
        collections[milestone.collection_month] += milestone.amount
    for month, amount in expenses_by_month.items():  # se facturan a fin de mes y se cobran a 45 días
        collections[month_of_day(month * DAYS_PER_MONTH + COLLECTION_DAYS)] += amount
    last_month = max([*collections, *payments])
    return tuple(
        CashRow(month, round_usd(collections[month]), round_usd(payments[month])) for month in range(1, last_month + 1)
    )


def _overrun_for_margin(statement: IncomeStatement, margin: float) -> float:
    """Cuánto pueden pasarse las horas del presupuesto (0.1 = un 10 %) antes de bajar a `margin`."""
    variable = statement.labor + statement.fixed_overhead
    operating_needed = margin * statement.price / (1 - CA_SCORP_TAX_RATE)
    factor = ((1 - MARKETING_RATE) * statement.fees - statement.platform - operating_needed) / variable
    return factor - 1


def _checks(pricing: "ProjectPricing") -> tuple[Check, ...]:
    plan, statement = pricing.plan, pricing.statement
    checks: list[Check] = []
    if pricing.capped:
        checks.append(Check(WARNING, (
            f"Para dejar un margen neto del {pct(TARGET_NET_MARGIN, 0)} haría falta una tarifa media de "
            f"{pricing.rate_for_target:,.2f} USD/h, por encima del tope de mercado de {MAX_BLENDED_RATE_USD:.0f} "
            f"USD/h. Con el tope, el margen neto queda en un {pct(statement.net_margin)}."
        )))
    else:
        checks.append(Check(OK, f"El margen neto es del {pct(statement.net_margin)}, el objetivo de la empresa."))
    checks.append(Check(OK, (
        f"La tarifa media, {pricing.rate:,.2f} USD por hora con imprevistos, no pasa de "
        f"{MAX_BLENDED_RATE_USD:.0f} USD/h."
    )))
    if pricing.market_alternative is not None:
        gap = 1 - pricing.rate / MAX_BLENDED_RATE_USD
        if gap >= 0.05:
            alternative = pricing.market_alternative
            checks.append(Check(WARNING, (
                f"La tarifa media queda un {pct(gap)} por debajo del mercado. Cobrando {MAX_BLENDED_RATE_USD:.0f} "
                f"USD/h, la utilidad neta subiría a {alternative.net_profit:,} USD (margen del "
                f"{pct(alternative.net_margin)}): fijar el precio por el margen objetivo deja ese dinero en la mesa."
            )))
    peak_role = max(plan.weekly_hours, key=plan.peak_dedication)
    checks.append(Check(OK, (
        f"Nadie pasa del 100 % de dedicación en ninguna semana. La más alta es la de {peak_role}, "
        f"con un {pct(plan.peak_dedication(peak_role), 0)}."
    )))
    for adjustment in plan.adjustments:
        checks.append(Check(WARNING, f"Python alargó el cronograma propuesto: {adjustment}"))
    open_questions = len(plan.draft.open_scope_questions)
    if open_questions:
        if open_questions == 1:
            what = "un punto de alcance sin decidir, que no está estimado"
        else:
            what = f"{open_questions} puntos de alcance sin decidir, que no están estimados"
        checks.append(Check(WARNING, (
            f"La reunión dejó {what} (sección 2). Decide qué entra y vuelve a estimar indicando "
            "los cambios de alcance."
        )))
    proposal_total = sum(line.client_amount for line in pricing.lines) + pricing.overhead_client_amount + statement.expenses
    assert proposal_total == statement.price, "la propuesta tiene que sumar el precio total"
    checks.append(Check(OK, f"La propuesta al cliente suma exactamente el precio total: {statement.price:,} USD."))
    assert sum(milestone.amount for milestone in pricing.milestones) == statement.fees
    checks.append(Check(OK, "Los cuatro hitos de pago suman exactamente los honorarios."))
    below_cost = [line.role.name for line in pricing.lines if line.client_rate < line.role.cost_per_hour * (1 + CONTINGENCY_RATE)]
    if below_cost:
        checks.append(Check(WARNING, f"Se facturan por debajo de su costo con imprevistos: {', '.join(below_cost)}."))
    else:
        checks.append(Check(OK, "Todas las tarifas al cliente cubren el costo de su perfil y sus imprevistos."))
    low, high = SMALL_FIRM_RATE_RANGE_USD
    outside = [line for line in pricing.lines if not low <= line.client_rate <= high]
    if outside:
        detail = ", ".join(f"{line.role.name} {line.client_rate:,.2f}" for line in outside)
        checks.append(Check(WARNING, (
            f"Tarifas fuera del rango de {low}-{high} USD/h de las consultoras pequeñas (Cleveroad): {detail}. "
            "Las más bajas pueden dejar ver que ese perfil trabaja desde un país de menor costo; las más altas "
            "invitan a negociar."
        )))
    low_margin, high_margin = SPECIALIZED_AGENCY_NET_MARGIN
    checks.append(Check(WARNING, (
        f"Un margen neto del {pct(TARGET_NET_MARGIN, 0)} es alto: más del doble de la media de las agencias pequeñas "
        f"({pct(SMALL_AGENCY_NET_MARGIN, 0)}), aunque dentro del {low_margin * 100:.0f}-{high_margin * 100:.0f} % de las especializadas "
        "(Promethean, vía Haus Advisors). Es alcanzable sobre todo porque los contratistas solo cobran las horas trabajadas."
    )))
    checks.append(Check(INFO, (
        f"La empresa adelanta hasta {pricing.max_cash_needed:,} USD de caja antes de cobrar los hitos que faltan."
    )))
    return tuple(checks)


def price_project(plan: ProjectPlan) -> ProjectPricing:
    """Valora el proyecto planificado: costos, precio, propuesta, caja, sensibilidad y controles."""
    roles = [ROLES[name] for name in plan.base_hours_by_role]
    total_hours = {role.name: _total_hours(plan.base_hours_by_role[role.name]) for role in roles}
    labor_costs = {role.name: round_usd(total_hours[role.name] * role.cost_per_hour) for role in roles}
    hours = sum(total_hours.values())
    contractors = sum(1 for role in roles if role.is_contractor)
    months = project_months(plan.duration_weeks)
    labor = sum(labor_costs.values())
    platform = contractors * months * CONTRACTOR_PLATFORM_FEE_USD
    fixed_overhead = round_usd(FIXED_OVERHEAD_PER_HOUR * hours)
    expenses = sum(expense.amount for expense in plan.expenses)

    # El precio: la tarifa media que deja el 30 %, con el tope de mercado. Se factura por perfil
    # y se redondea al dólar, como en la v6.
    rate_for_target = round(solve_fees(labor + platform + fixed_overhead, expenses) / hours, 2)
    rate = min(rate_for_target, MAX_BLENDED_RATE_USD)
    fees = sum(round_usd(total_hours[role.name] * rate) for role in roles)
    statement = income_statement(fees, expenses, labor, platform, fixed_overhead)

    # La propuesta: un mismo factor (imprevistos + recargo) sobre el costo de cada concepto.
    overhead_base = platform + fixed_overhead + statement.marketing
    base_labor_cost = sum(plan.base_hours_by_role[role.name] * role.cost_per_hour for role in roles)
    factor = fees / (base_labor_cost + overhead_base)
    lines = []
    for role in roles:
        client_rate = round_cents(role.cost_per_hour * factor)
        base = plan.base_hours_by_role[role.name]
        lines.append(RoleLine(role, base, total_hours[role.name], labor_costs[role.name], client_rate, round_usd(base * client_rate)))
    overhead_client_amount = fees - sum(line.client_amount for line in lines)  # absorbe el redondeo

    milestones = _milestones(plan, fees)
    market_alternative = None
    if rate < MAX_BLENDED_RATE_USD:
        market_fees = sum(round_usd(total_hours[role.name] * MAX_BLENDED_RATE_USD) for role in roles)
        market_alternative = income_statement(market_fees, expenses, labor, platform, fixed_overhead)
    cost_before_marketing = labor + platform + fixed_overhead
    negotiation = []
    for margin in (m for m in NEGOTIATION_MARGINS if m < statement.net_margin - 0.005):
        margin_fees = round_usd(solve_fees(cost_before_marketing, expenses, margin))
        negotiation.append(NegotiationRow(margin, margin_fees, margin_fees + expenses, 1 - (margin_fees + expenses) / statement.price))
    sensitivity = []
    for label, factor_hours in (
        ("Sin usar los imprevistos", 1 / (1 + CONTINGENCY_RATE)),
        ("Presupuesto, con todos los imprevistos", 1.0),
        ("Un 10 % más de horas que el presupuesto", 1.1),
        ("Un 20 % más de horas que el presupuesto", 1.2),
    ):
        scenario = income_statement(fees, expenses, round_usd(labor * factor_hours), platform, round_usd(fixed_overhead * factor_hours))
        sensitivity.append(Scenario(label, hours * factor_hours, scenario))

    pricing = ProjectPricing(
        plan=plan,
        lines=tuple(lines),
        contractors=contractors,
        months=months,
        statement=statement,
        rate_for_target=rate_for_target,
        rate=rate,
        factor=factor,
        overhead_base=overhead_base,
        overhead_client_amount=overhead_client_amount,
        milestones=milestones,
        cash_flow=_cash_flow(plan, statement, milestones),
        market_alternative=market_alternative,
        negotiation=tuple(negotiation),
        sensitivity=tuple(sensitivity),
        overrun_to_margin_20=_overrun_for_margin(statement, 0.20),
        overrun_to_break_even=_overrun_for_margin(statement, 0.0),
        checks=(),
    )
    return replace(pricing, checks=_checks(pricing))


def fixed_overhead_share(pricing: ProjectPricing) -> float:
    return pricing.statement.fixed_overhead / FIXED_OVERHEAD_TOTAL
