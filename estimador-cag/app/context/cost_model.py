"""Modelo de costos de la consultora: los datos con los que Python valora cada proyecto.

Son las premisas del análisis v6 del vault ("Precios, costos y márgenes v6: escenario 2 con
margen neto del 30 %"):
- una consultora pequeña de 17 personas con un equipo mixto: gestión, liderazgo técnico y
  consultoría de RR. HH. en plantilla en Los Ángeles; backend, datos, IA/ML y DevOps como
  contratistas de otras zonas de EE. UU.; diseño, frontend, full-stack, móvil y QA como
  contratistas de Latinoamérica;
- margen = utilidad neta después de impuestos ÷ precio total (honorarios + gastos
  reembolsables), con un objetivo del 30 %;
- la tarifa media de un proyecto (honorarios ÷ horas con imprevistos) no pasa de 150 USD/h,
  el precio de mercado de una consultora pequeña.

El modelo de lenguaje nunca ve estas cifras: solo estima horas y redacta textos.
"""

import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

# ---- Política comercial
TARGET_NET_MARGIN = 0.30
MAX_BLENDED_RATE_USD = 150.0  # tope de la tarifa media del proyecto
CONTINGENCY_RATE = 0.10  # imprevistos: un 10 % sobre las horas de cada profesional
HOURS_PER_WEEK = 40  # jornada de un profesional, imprevistos incluidos
PAYMENT_MILESTONES = 4  # honorarios en 4 hitos del 25 %
PROPOSAL_VALIDITY_DAYS = 30

# ---- Supuestos de costos (fuentes en el análisis v6)
PAYROLL_LOAD = 1 / 0.70  # BLS ECEC jun-2026: el salario es el 70 % de la compensación total
WORKED_HOURS_PER_YEAR = 1880  # 2,080 h pagadas menos 200 h de vacaciones y festivos
BILLABLE_HOURS_PER_YEAR = 0.664 * 2080  # SPI 2026: 66.4 % de utilización, 1,381.1 h al año
HOURS_PER_MONTH = 2080 / 12  # 173.3 h por mes completo de un contratista
CONTRACTOR_PLATFORM_FEE_USD = 49  # Deel: por contratista y mes
COLLECTION_DAYS = 45  # cobro real a 45 días (SMB Compass)
CA_SCORP_TAX_RATE = 0.015  # FTB: impuesto de California para una S corporation
MARKETING_RATE = 0.08  # Hinge 2026: marketing y ventas, el 8 % de los honorarios
DAYS_PER_MONTH = 30.44

# ---- Referencias de mercado
SMALL_FIRM_RATE_RANGE_USD = (75, 175)  # Cleveroad 2026: consultoras de TI pequeñas
SMALL_AGENCY_NET_MARGIN = 0.12  # Promethean, vía Haus Advisors
SPECIALIZED_AGENCY_NET_MARGIN = (0.25, 0.40)  # la misma fuente

LOS_ANGELES, UNITED_STATES, LATIN_AMERICA = "Los Ángeles", "EE. UU.", "Latinoamérica"


def round_usd(value: float | Decimal) -> int:
    """Redondeo al dólar, siempre hacia arriba en el medio (0.5 -> 1), como en la v6."""
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def round_cents(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class Role:
    """Un perfil del equipo: desde dónde trabaja, cómo se le paga y cuánto cuesta cada hora."""

    name: str
    location: str
    modality: str
    cost_per_hour: float  # USD por hora de proyecto
    cost_basis: str  # de dónde sale el costo

    @property
    def is_contractor(self) -> bool:
        return self.location != LOS_ANGELES


def _los_angeles(name: str, median_wage: float) -> Role:
    """Plantilla W-2: salario con cargas, repartido entre las horas facturables del año."""
    cost = median_wage * PAYROLL_LOAD * WORKED_HOURS_PER_YEAR / BILLABLE_HOURS_PER_YEAR
    basis = f"BLS LA, mediana {median_wage:.2f} USD/h × 1.43 × 1,880 h ÷ 1,381 h facturables"
    return Role(name, LOS_ANGELES, "Plantilla W-2", cost, basis)


def _united_states(name: str, hourly_pay: float, basis: str | None = None) -> Role:
    basis = basis or f"KORE1, punto medio del pago al contratista: {hourly_pay:.2f} USD/h"
    return Role(name, UNITED_STATES, "Contratista por hora", hourly_pay, basis)


def _latin_america(name: str, monthly_pay: int) -> Role:
    basis = f"HiresLink, nivel medio: {monthly_pay:,} USD/mes ÷ 173.3 h"
    return Role(name, LATIN_AMERICA, "Contratista por hora", monthly_pay / HOURS_PER_MONTH, basis)


ROLES: dict[str, Role] = {
    role.name: role
    for role in (
        _los_angeles("Gestión de proyecto", 52.07),
        _los_angeles("Consultoría de RR. HH.", 46.78),
        _los_angeles("Liderazgo técnico", 77.37),
        _united_states("Backend", 65.00),
        _united_states("Ingeniería de datos", 97.50),
        _united_states("Ciencia de datos", 57.80, "BLS nacional, mediana: 57.80 USD/h"),
        _united_states("IA / ML", 127.50),
        _united_states("DevOps", 77.50),
        _latin_america("Diseño UX/UI", 3200),
        _latin_america("Frontend", 4000),
        _latin_america("Full-stack", 4200),
        _latin_america("Móvil", 4400),
        _latin_america("QA", 3400),
    )
}

# ---- La empresa: 17 personas en el escenario 2
FIRM_TEAM = (
    "Gestión de proyecto", "Liderazgo técnico", "Liderazgo técnico", "Consultoría de RR. HH.",
    "Backend", "Backend", "Ingeniería de datos", "Ciencia de datos", "IA / ML", "DevOps",
    "Frontend", "Full-stack", "Móvil", "QA", "QA", "Diseño UX/UI",
)  # más la dirección, que no factura
FIRM_HEADCOUNT = 17
FIRM_W2_HEADCOUNT = 5
FIRM_ATTRITION = 0.114
CEO_MEDIAN_WAGE = 60.50

FIXED_OVERHEAD: dict[str, int] = {
    "Dirección: fundador/a y CEO, no facturable (BLS LA 11-1021, mediana 60.50 USD/h, con cargas)":
        round_usd(CEO_MEDIAN_WAGE * PAYROLL_LOAD * WORKED_HOURS_PER_YEAR),
    "Software y herramientas: 3,200 USD por persona y año (Productiv, 10-49 empleados)": 3200 * FIRM_HEADCOUNT,
    "Oficina: 5 puestos de coworking en LA a 340 USD/mes (Statista)": 5 * 340 * 12,
    "Contabilidad externa: 1,000 USD/mes (NerdWallet, servicio premium)": 12_000,
    "Asesoría legal: contratos con clientes y contratistas (estimación propia)": 10_000,
    "Seguros: E&O con ciberriesgo 111 USD/mes y responsabilidad general 32 USD/mes (Insureon)": (111 + 32) * 12,
    "Nómina de la plantilla: Gusto Plus, 80 USD/mes + 12 USD por persona": 80 * 12 + 12 * FIRM_W2_HEADCOUNT * 12,
    "Contratación: 1.9 bajas al año (11.4 %) × 1,300 USD por contratación (SHRM 2026)":
        round_usd(FIRM_HEADCOUNT * FIRM_ATTRITION * 1300),
    "Equipos de la plantilla: portátil de 2,000 USD cada 3 años (estimación propia)":
        round_usd(FIRM_W2_HEADCOUNT * 2000 / 3),
}
FIXED_OVERHEAD_TOTAL = sum(FIXED_OVERHEAD.values())
FIRM_BILLABLE_HOURS = BILLABLE_HOURS_PER_YEAR * len(FIRM_TEAM)
# Los gastos generales fijos se reparten entre los proyectos según sus horas.
FIXED_OVERHEAD_PER_HOUR = FIXED_OVERHEAD_TOTAL / FIRM_BILLABLE_HOURS


def solve_fees(cost_before_marketing: float, expenses: float, margin: float = TARGET_NET_MARGIN) -> float:
    """Honorarios F que dejan una utilidad neta igual a `margin` × precio (F + gastos reembolsables).

    Utilidad neta = (1 - t) · ((1 - m) · F - C) y precio = F + X, así que
    F = ((1 - t) · C + M · X) / ((1 - t) · (1 - m) - M),
    con C = costo del equipo + plataforma + gastos generales fijos, X = gastos reembolsables,
    t = impuesto, m = marketing y M = margen objetivo.
    """
    t, m = CA_SCORP_TAX_RATE, MARKETING_RATE
    return ((1 - t) * cost_before_marketing + margin * expenses) / ((1 - t) * (1 - m) - margin)


def _firm_annual_fees() -> int:
    """Ingresos anuales de la empresa si toda ella vendiera a la tarifa que deja el 30 %."""
    delivery = 0.0
    for name in FIRM_TEAM:
        role = ROLES[name]
        if role.is_contractor:
            delivery += BILLABLE_HOURS_PER_YEAR * role.cost_per_hour + 12 * CONTRACTOR_PLATFORM_FEE_USD
        else:
            delivery += role.cost_per_hour * BILLABLE_HOURS_PER_YEAR
    rate = round(solve_fees(delivery + FIXED_OVERHEAD_TOTAL, 0) / FIRM_BILLABLE_HOURS, 2)
    return round_usd(rate * FIRM_BILLABLE_HOURS)


FIRM_ANNUAL_FEES = _firm_annual_fees()


def project_months(duration_weeks: int) -> int:
    """Meses de calendario que ocupa el proyecto, para la cuota de la plataforma de contratistas."""
    return math.ceil(duration_weeks * 7 / DAYS_PER_MONTH)


def month_of_day(day: float) -> int:
    """Mes del proyecto (1, 2...) en el que cae un día contado desde la firma."""
    return int(day // DAYS_PER_MONTH) + 1
