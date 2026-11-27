"""Los dos informes de cada estimación, en Markdown, escritos por Python con plantillas.

- Informe interno: todo el análisis de costos y rentabilidad de la v6 aplicado al proyecto, más
  lo que hace falta para gestionarlo y seguirlo. Es confidencial.
- Propuesta al cliente: la propuesta de valor y de negocio. Cada cifra ya lleva su costo, sus
  imprevistos y su rentabilidad, nunca se muestran por separado, y todas suman el precio total.

Las cifras salen de app/services/pricing.py y los textos, del borrador del modelo.
"""

from app.context.cost_model import (
    COLLECTION_DAYS,
    CONTINGENCY_RATE,
    CONTRACTOR_PLATFORM_FEE_USD,
    FIRM_ANNUAL_FEES,
    FIRM_BILLABLE_HOURS,
    FIXED_OVERHEAD_PER_HOUR,
    FIXED_OVERHEAD_TOTAL,
    HOURS_PER_WEEK,
    LATIN_AMERICA,
    LOS_ANGELES,
    MARKETING_RATE,
    MAX_BLENDED_RATE_USD,
    PAYMENT_MILESTONES,
    PROPOSAL_VALIDITY_DAYS,
    ROLES,
    TARGET_NET_MARGIN,
    UNITED_STATES,
)
from app.context.catalog import PLATFORM_NAMES
from app.schemas.inventory import ScopeInventory
from app.services.catalog_hours import REVIEW, InventoryHours
from app.services.formatting import hours, number, pct, rate, usd
from app.services.planning import ProjectPlan
from app.services.pricing import INFO, OK, WARNING, ProjectPricing

STATUS_ICON = {OK: "✅", WARNING: "⚠️", INFO: "ℹ️"}
CRITICAL_DEDICATION = 0.90


def _bar(start: int, end: int, duration: int) -> str:
    """Barra de cronograma en texto: una celda por semana."""
    return "`" + "".join("█" if start <= week <= end else "·" for week in range(1, duration + 1)) + "`"


def _weeks(start: int, end: int) -> str:
    return f"{start}" if start == end else f"{start}-{end}"


def _phase_rows(pricing: ProjectPricing, with_proposed: bool) -> list[str]:
    plan = pricing.plan
    rows = []
    for phase in plan.phases:
        cells = [
            f"{phase.number}. {phase.name}",
            _weeks(phase.start_week, phase.end_week),
            f"{phase.weeks} semanas" if phase.weeks != 1 else "1 semana",
        ]
        if with_proposed:
            cells.append("igual" if phase.weeks == phase.proposed_weeks else f"{phase.proposed_weeks} semanas")
        else:
            cells.append("<br>".join(phase.deliverables))
        cells.append(_bar(phase.start_week, phase.end_week, plan.duration_weeks))
        rows.append("| " + " | ".join(cells) + " |")
    return rows


def _statement_rows(pricing: ProjectPricing) -> list[str]:
    s = pricing.statement
    rows = [
        ("Honorarios", s.fees),
        ("Gastos reembolsables, facturados a coste", s.expenses),
        ("**Precio total**", s.price),
        ("− Costo del equipo", -s.labor),
        (f"− Plataforma de contratistas ({pricing.contractors} × {pricing.months} meses × {CONTRACTOR_PLATFORM_FEE_USD} USD)", -s.platform),
        ("− Gastos reembolsables", -s.expenses),
        ("**= Margen bruto**", s.gross_margin),
        (f"− Gastos generales fijos ({FIXED_OVERHEAD_PER_HOUR:.2f} USD por hora del proyecto)", -s.fixed_overhead),
        (f"− Marketing y ventas ({pct(MARKETING_RATE, 0)} de los honorarios)", -s.marketing),
        ("**= Utilidad operativa**", s.operating_profit),
        ("− Impuesto de California para S corporation (1.5 %)", -s.tax),
        ("**= Utilidad neta**", s.net_profit),
    ]
    out = ["| Concepto | USD | % del precio |", "|---|---|---|"]
    for label, value in rows:
        if label.startswith("**"):
            out.append(f"| {label} | **{number(value)}** | **{pct(value / s.price)}** |")
        else:
            out.append(f"| {label} | {number(abs(value))} | {pct(abs(value) / s.price)} |")
    return out


def _hours_origin(inventory: ScopeInventory, breakdown: InventoryHours) -> list[str]:
    """De dónde sale cada hora: el catálogo o, si no tiene referencia, el modelo."""
    w = [
        "**De dónde salen las horas.** Python las calcula con el catálogo de componentes a partir "
        "del inventario de alcance. El modelo solo pone las de los requisitos que el catálogo no "
        f"cubre, marcadas «{REVIEW}». Plataforma: {PLATFORM_NAMES[inventory.platform]}.",
        "",
        "| Partida | Origen | Horas base | Referencia |",
        "|---|---|---:|---|",
    ]
    w += [f"| {line.name} | {line.kind} | {number(line.total)} | {line.basis} |" for line in breakdown.lines]
    w += [f"| **Total, sin imprevistos** | | **{number(breakdown.base_hours)}** | |", ""]
    review = [line for line in breakdown.lines if line.kind == REVIEW]
    if review:
        w += ["**Horas que puso el modelo.** Revísalas antes de enviar la propuesta:", ""]
        w += [
            f"- ⚠️ {line.name}: " + (f"{number(line.total)} h." if line.total else "sin horas; no está en la estimación.")
            for line in review
        ]
        w.append("")
    if inventory.open_decisions:
        w += ["**Decisiones abiertas, estimadas con un supuesto:**", ""]
        w += [
            f"- {decision.question} Se asume: {decision.assumed}. Opciones: {'; '.join(decision.options)}."
            for decision in inventory.open_decisions
        ]
        w.append("")
    excluded = [requirement for requirement in inventory.requirements if requirement.status == "excluido"]
    if excluded:
        w += ["**Excluido en la reunión:**", ""]
        w += [f"- {requirement.description}" for requirement in excluded]
        w.append("")
    return w


def _deadline_lines(plan: ProjectPlan, inventory: ScopeInventory | None) -> list[str]:
    """El plazo que pidió el cliente, si ajustó las etapas del modelo y si el cronograma lo cumple."""
    if plan.deadline_weeks is None:
        return []
    evidence = inventory.deadline.evidence.strip(" .«»\"") if inventory is not None and inventory.deadline else ""
    lines = [f"Plazo que pidió el cliente: {plan.deadline_weeks} semanas" + (f" («{evidence}»)." if evidence else ".")]
    if plan.fitted_to_deadline:
        lines.append(
            f"Las etapas del modelo sumaban {plan.proposed_weeks} semanas: Python las ajustó al plazo en la "
            "misma proporción."
        )
    elif plan.proposed_weeks != plan.deadline_weeks:
        lines.append(
            f"Las etapas del modelo sumaban {plan.proposed_weeks} semanas. Ajustarlas al plazo daba un "
            "cronograma más largo, así que Python parte de las semanas del modelo."
        )
    if plan.meets_deadline:
        lines.append("El cronograma cumple el plazo.")
    else:
        lines.append(f"El cronograma no cabe en el plazo: dura {plan.duration_weeks} semanas.")
    return lines


def build_internal_report(
    pricing: ProjectPricing,
    scope_changes: str | None = None,
    inventory: ScopeInventory | None = None,
    breakdown: InventoryHours | None = None,
) -> str:
    plan, s = pricing.plan, pricing.statement
    draft = plan.draft
    duration = plan.duration_weeks
    w: list[str] = []
    add = w.append

    add(f"# Informe interno: {draft.project_name}")
    add("")
    add("> [!warning] Confidencial")
    add("> Solo para la consultora: incluye costos, márgenes y tarifas internas. Al cliente se le envía la propuesta.")
    add("")
    add(f"- **Tipo de proyecto:** {draft.project_type}")
    add(f"- **Cliente:** {draft.value_proposition.client_profile}")
    add("")

    # 1. Resumen
    add("## 1. Resumen")
    add("")
    add("| Concepto | Valor |")
    add("|---|---|")
    for label, value in (
        ("Duración", f"{duration} semanas ({len(plan.phases)} etapas)"),
        ("Horas base / imprevistos / totales", f"{number(pricing.base_hours)} / {hours(pricing.contingency_hours)} / {hours(pricing.total_hours)}"),
        ("Equipo", f"{len(pricing.lines)} profesionales, {pricing.full_time_equivalents:.1f} personas a tiempo completo de media"),
        ("Precio total", usd(s.price)),
        ("Honorarios / gastos reembolsables", f"{usd(s.fees)} / {usd(s.expenses)}"),
        ("Tarifa media (honorarios ÷ horas totales)", f"{rate(pricing.rate)} USD/h"),
        ("Costo del equipo", usd(s.labor)),
        ("Utilidad neta / margen neto", f"{usd(s.net_profit)} / {pct(s.net_margin)}"),
        ("Recargo de rentabilidad sobre el costo", pct(pricing.markup)),
        ("Caja máxima que hay que adelantar", usd(pricing.max_cash_needed)),
    ):
        add(f"| {label} | {value} |")
    add("")
    warnings = [check for check in pricing.checks if check.status == WARNING]
    if warnings:
        add("**Alertas:**")
        for check in warnings:
            add(f"- ⚠️ {check.text}")
        add("")

    # 2. Alcance
    add("## 2. Alcance")
    add("")
    add(draft.project_summary)
    add("")
    if scope_changes:
        add("**Cambios de alcance indicados por la consultora**, que mandan sobre la transcripción:")
        add("")
        add("> " + scope_changes.replace("\n", "\n> "))
        add("")
    if draft.open_scope_questions:
        add(
            "**Puntos que la reunión dejó sin decidir.** No están estimados ni incluidos en la "
            "propuesta: decídelos y vuelve a estimar indicando los cambios de alcance."
        )
        add("")
        w.extend(f"- {question}" for question in draft.open_scope_questions)
    else:
        add("La reunión no dejó puntos de alcance sin decidir.")
    add("")
    if inventory is not None and breakdown is not None:
        w.extend(_hours_origin(inventory, breakdown))

    # 3. Cronograma
    add("## 3. Cronograma por etapa")
    add("")
    add("| Etapa | Semanas | Duración | Propuesta del modelo | Cronograma |")
    add("|---|---|---|---|---|")
    w.extend(_phase_rows(pricing, with_proposed=True))
    add("")
    deadline = _deadline_lines(plan, inventory)
    for line in [*deadline, *plan.adjustments]:
        add(f"- {line}")
    if deadline or plan.adjustments:
        add("")

    # 4. Tareas
    add("## 4. Desglose de tareas")
    add("")
    add("Horas base, sin imprevistos. Las horas de cada tarea se reparten por igual entre las semanas de sus etapas.")
    add("")
    add("| Tarea | Etapas | Semanas | Horas por perfil | Horas | Cronograma |")
    add("|---|---|---|---|---|---|")
    for task in plan.tasks:
        detail = ", ".join(f"{role} {value}" for role, value in task.hours.items())
        add(
            f"| {task.name} | {_weeks(task.first_phase, task.last_phase)} | {_weeks(task.start_week, task.end_week)} "
            f"| {detail} | {number(task.base_hours)} | {_bar(task.start_week, task.end_week, duration)} |"
        )
    add(f"| **Total, sin imprevistos** | | | | **{number(pricing.base_hours)}** | |")
    add("")

    # 5. Costo por hora
    add("## 5. Costo por hora de cada perfil")
    add("")
    add("| Perfil | Ubicación | Modalidad | Base del costo | Costo por hora |")
    add("|---|---|---|---|---|")
    for line in pricing.lines:
        role = line.role
        add(f"| {role.name} | {role.location} | {role.modality} | {role.cost_basis} | {rate(role.cost_per_hour)} |")
    add("")
    add("- **Plantilla de Los Ángeles:** el salario es el 70 % de la compensación total (BLS ECEC), y su costo se reparte entre las horas facturables del año (el 66.4 % de SPI).")
    add(f"- **Contratistas:** cobran solo las horas trabajadas, más {CONTRACTOR_PLATFORM_FEE_USD} USD al mes de Deel.")
    add("")

    # 6. Costos laborales
    add("## 6. Costos laborales y facturación por profesional")
    add("")
    add(f"Imprevistos del {pct(CONTINGENCY_RATE, 0)} sobre las horas de cada profesional. La dedicación máxima es la de la semana más cargada, con un tope de {HOURS_PER_WEEK} horas.")
    add("")
    add("| Perfil | Ubicación | Horas base | Imprevistos | Horas totales | Dedicación media | Dedicación máxima | Costo/h | Costo | Tarifa al cliente | Facturado |")
    add("|---|---|---|---|---|---|---|---|---|---|---|")
    for line in pricing.lines:
        name = line.role.name
        add(
            f"| {name} | {line.role.location} | {number(line.base_hours)} | {hours(line.contingency_hours)} | {hours(line.total_hours)} "
            f"| {pct(plan.average_dedication(name), 0)} | {pct(plan.peak_dedication(name), 0)} | {rate(line.role.cost_per_hour)} "
            f"| {number(line.cost)} | {rate(line.client_rate)} | {number(line.client_amount)} |"
        )
    add(
        f"| **Total** | | **{number(pricing.base_hours)}** | **{hours(pricing.contingency_hours)}** | **{hours(pricing.total_hours)}** "
        f"| | | **{rate(s.labor / pricing.total_hours)}** | **{number(s.labor)}** | | **{number(sum(line.client_amount for line in pricing.lines))}** |"
    )
    add("")
    add(f"El resto de los honorarios, {usd(pricing.overhead_client_amount)}, es la línea de gastos generales de la propuesta (sección 9).")
    add("")

    # 7. Estado de resultados
    add("## 7. Estado de resultados del proyecto")
    add("")
    w.extend(_statement_rows(pricing))
    add("")
    add("**Gastos reembolsables, a coste:**")
    add("")
    add("| Gasto | Cantidad | Costo unitario | Importe |")
    add("|---|---|---|---|")
    for expense in plan.expenses:
        add(f"| {expense.description} | {expense.quantity:,g} {expense.unit} | {expense.unit_cost_usd:,g} USD | {number(expense.amount)} |")
    add(f"| **Total** | | | **{number(s.expenses)}** |")
    add("")

    # 8. Mercado
    add("## 8. Precio frente al mercado")
    add("")
    gap = 1 - pricing.rate / MAX_BLENDED_RATE_USD
    if gap > 0.0005:
        add(
            f"La tarifa media del proyecto es de {rate(pricing.rate)} USD por hora con imprevistos, un {pct(gap)} por debajo de "
            f"los {MAX_BLENDED_RATE_USD:.0f} USD/h que cobra una consultora pequeña."
        )
    else:
        add(f"La tarifa media del proyecto es de {rate(pricing.rate)} USD por hora con imprevistos, el tope de mercado de una consultora pequeña.")
    add("")
    if pricing.capped:
        add(
            f"Para dejar el {pct(TARGET_NET_MARGIN, 0)} haría falta una tarifa media de {rate(pricing.rate_for_target)} USD/h. "
            f"Se aplica el tope de mercado y el margen neto queda en un {pct(s.net_margin)}."
        )
        add("")
    elif pricing.market_alternative is not None:
        alternative = pricing.market_alternative
        add(f"| Concepto | Precio con margen del {pct(TARGET_NET_MARGIN, 0)} | Precio de mercado ({MAX_BLENDED_RATE_USD:.0f} USD/h) |")
        add("|---|---|---|")
        add(f"| Precio total | {number(s.price)} | {number(alternative.price)} |")
        add(f"| Utilidad neta | {number(s.net_profit)} | {number(alternative.net_profit)} |")
        add(f"| Margen neto | {pct(s.net_margin)} | {pct(alternative.net_margin)} |")
        add("")

    # 9. Conciliación
    add("## 9. Conciliación con la propuesta al cliente")
    add("")
    add(
        f"Cada concepto de la propuesta lleva su costo, un {pct(CONTINGENCY_RATE, 0)} de imprevistos y un recargo de rentabilidad "
        f"del {pct(pricing.markup)} sobre el costo, el que hace que el proyecto deje un margen neto del {pct(s.net_margin)} "
        f"sobre el precio. Es decir, costo × {pricing.factor:.4f}. El cliente solo ve el valor final de cada concepto."
    )
    add("")
    add(f"| Concepto | Costo base | Imprevistos ({pct(CONTINGENCY_RATE, 0)}) | Rentabilidad ({pct(pricing.markup)}) | Valor en la propuesta |")
    add("|---|---|---|---|---|")
    totals = [0, 0, 0, 0]
    for line in pricing.lines:
        base_cost = round(line.base_hours * line.role.cost_per_hour)
        contingency = round(base_cost * CONTINGENCY_RATE)
        profit = line.client_amount - base_cost - contingency
        add(f"| {line.role.name}: {number(line.base_hours)} h × {rate(line.client_rate)} USD/h | {number(base_cost)} | {number(contingency)} | {number(profit)} | {number(line.client_amount)} |")
        totals = [a + b for a, b in zip(totals, (base_cost, contingency, profit, line.client_amount))]
    overhead_contingency = round(pricing.overhead_base * CONTINGENCY_RATE)
    overhead_profit = pricing.overhead_client_amount - pricing.overhead_base - overhead_contingency
    add(f"| Gastos generales del proyecto | {number(pricing.overhead_base)} | {number(overhead_contingency)} | {number(overhead_profit)} | {number(pricing.overhead_client_amount)} |")
    totals = [a + b for a, b in zip(totals, (pricing.overhead_base, overhead_contingency, overhead_profit, pricing.overhead_client_amount))]
    add(f"| Gastos reembolsables, a coste | {number(s.expenses)} | 0 | 0 | {number(s.expenses)} |")
    totals = [a + b for a, b in zip(totals, (s.expenses, 0, 0, s.expenses))]
    add(f"| **Total** | **{number(totals[0])}** | **{number(totals[1])}** | **{number(totals[2])}** | **{number(totals[3])}** |")
    add("")
    add(
        f"Los gastos generales del proyecto son la plataforma de contratistas ({number(s.platform)}), los gastos fijos asignados "
        f"({number(s.fixed_overhead)}) y el marketing ({number(s.marketing)}). Su valor en la propuesta absorbe el redondeo al "
        "dólar de las tarifas, para que todo sume exactamente el precio."
    )
    add("")

    # 10. Negociación
    add("## 10. Margen de negociación")
    add("")
    add("| Margen neto | Honorarios | Precio total | Descuento sobre el precio propuesto |")
    add("|---|---|---|---|")
    add(f"| {pct(s.net_margin)} (propuesta) | {number(s.fees)} | {number(s.price)} | — |")
    for row in pricing.negotiation:
        label = f"{pct(row.margin, 0)}" + (" (equilibrio)" if row.margin == 0 else "")
        add(f"| {label} | {number(row.fees)} | {number(row.price)} | {pct(row.discount)} |")
    add("")
    break_even = next((row for row in pricing.negotiation if row.margin == 0), None)
    if break_even is not None:
        add(f"Por debajo de {usd(break_even.price)}, un descuento del {pct(break_even.discount)}, el proyecto pierde dinero.")
        add("")

    # 11. Sensibilidad
    add("## 11. Sensibilidad a las horas")
    add("")
    add("El precio es cerrado: si se trabajan más horas, se pagan del margen. Los gastos fijos asignados crecen con las horas.")
    add("")
    add("| Escenario | Horas | Costo del equipo | Utilidad neta | Margen neto |")
    add("|---|---|---|---|---|")
    for scenario in pricing.sensitivity:
        st = scenario.statement
        add(f"| {scenario.label} | {hours(scenario.hours)} | {number(st.labor)} | {number(st.net_profit)} | {pct(st.net_margin)} |")
    add("")
    add(
        f"Si las horas superan el presupuesto en más de un {pct(pricing.overrun_to_margin_20)}, el margen baja del 20 %; con un "
        f"{pct(pricing.overrun_to_break_even)} más, la utilidad llega a cero."
    )
    add("")

    # 12. Facturación
    add("## 12. Plan de facturación y cobro")
    add("")
    add("| Hito | Momento | % de los honorarios | Importe | Mes en que se espera el cobro |")
    add("|---|---|---|---|---|")
    for milestone in pricing.milestones:
        add(f"| {milestone.number} | {milestone.label} | {pct(1 / PAYMENT_MILESTONES, 0)} | {number(milestone.amount)} | {milestone.collection_month} |")
    add("")
    add(f"El anticipo se cobra al firmar; el resto de los hitos y los gastos reembolsables, que se facturan a fin de mes, se cobran a {COLLECTION_DAYS} días.")
    add("")

    # 13. Caja
    add("## 13. Flujo de caja mensual")
    add("")
    add("| Mes | Cobros | Pagos | Neto | Acumulado |")
    add("|---|---|---|---|---|")
    cumulative = 0
    for row in pricing.cash_flow:
        cumulative += row.net
        add(f"| {row.month} | {number(row.collections)} | {number(row.payments)} | {number(row.net)} | {number(cumulative)} |")
    add(f"| **Caja máxima que hay que adelantar** | | | | **{number(pricing.max_cash_needed)}** |")
    add("")
    add("- **Pagos:** el equipo se paga según el cronograma semanal (sección 14); la plataforma, los gastos fijos, el marketing y los gastos reembolsables, por igual cada semana.")
    add("- **Impuesto:** el de California se paga una vez al año y no entra en el flujo mensual.")
    add("")

    # 14. Línea base
    add("## 14. Línea base de seguimiento semanal")
    add("")
    add("Horas planificadas de cada perfil, con imprevistos, y costo acumulado del equipo. Sirve para comparar cada semana lo real con lo previsto.")
    add("")
    roles = list(plan.weekly_hours)
    add("| Semana | Etapa | " + " | ".join(roles) + " | Horas | Costo del equipo | Acumulado | % del costo |")
    add("|---|---|" + "---|" * len(roles) + "---|---|---|---|")
    weekly_costs = [sum(plan.weekly_hours[role][i] * ROLES[role].cost_per_hour for role in roles) for i in range(duration)]
    scale = s.labor / sum(weekly_costs)
    accumulated = 0.0
    for i in range(duration):
        week_hours = [plan.weekly_hours[role][i] for role in roles]
        cost = weekly_costs[i] * scale
        accumulated += cost
        add(
            f"| {i + 1} | {plan.phase_of_week(i + 1).number} | " + " | ".join(hours(value) for value in week_hours)
            + f" | {hours(sum(week_hours))} | {number(round(cost))} | {number(round(accumulated))} | {pct(accumulated / s.labor, 0)} |"
        )
    add("")

    # 15. Alertas de seguimiento
    add("## 15. Alertas para el seguimiento")
    add("")
    contingency_cost = s.labor - round(s.labor / (1 + CONTINGENCY_RATE))
    half = (duration + 1) // 2
    add(
        f"- **Reserva de imprevistos:** {hours(pricing.contingency_hours)} horas, unos {usd(contingency_cost)} de costo. "
        f"Si en la semana {half} ya se ha consumido más de la mitad, hay que revisar el alcance con el cliente."
    )
    add("- **Horas por perfil:** avisar cuando un perfil supere sus horas base (sección 6): desde ahí consume imprevistos, y al pasar sus horas totales consume margen.")
    add("- **Costo acumulado:** si el costo real supera en más de un 5 % al de la línea base dos semanas seguidas, hay que replanificar.")
    add(
        f"- **Margen:** con un {pct(pricing.overrun_to_margin_20)} más de horas que el presupuesto, el margen baja del 20 %; "
        f"con un {pct(pricing.overrun_to_break_even)} más, el proyecto pierde dinero."
    )
    add(f"- **Cobros:** si un hito no se cobra a los {COLLECTION_DAYS} días, la caja que hay que adelantar crece en su importe.")
    critical = [name for name in roles if plan.peak_dedication(name) >= CRITICAL_DEDICATION]
    if critical:
        detail = ", ".join(f"{name} ({pct(plan.peak_dedication(name), 0)})" for name in critical)
        add(f"- **Perfiles críticos:** {detail} llegan casi a tiempo completo en su semana más cargada: una baja o un retraso mueven el calendario.")
    add("")

    # 16. Peso en la empresa
    add("## 16. Peso del proyecto en la empresa")
    add("")
    add("| Concepto | Proyecto | Empresa en un año | % |")
    add("|---|---|---|---|")
    add(f"| Horas facturables | {hours(pricing.total_hours)} | {number(round(FIRM_BILLABLE_HOURS))} | {pct(pricing.hours_share_of_firm)} |")
    add(f"| Gastos generales fijos absorbidos | {number(s.fixed_overhead)} | {number(FIXED_OVERHEAD_TOTAL)} | {pct(s.fixed_overhead / FIXED_OVERHEAD_TOTAL)} |")
    add(f"| Honorarios | {number(s.fees)} | {number(FIRM_ANNUAL_FEES)} | {pct(pricing.fees_share_of_firm)} |")
    add("")
    add("**Mezcla del equipo por ubicación:**")
    add("")
    add("| Ubicación | Horas totales | % de las horas | Costo | % del costo |")
    add("|---|---|---|---|---|")
    for location in (LOS_ANGELES, UNITED_STATES, LATIN_AMERICA):
        group = [line for line in pricing.lines if line.role.location == location]
        if not group:
            continue
        group_hours = sum(line.total_hours for line in group)
        group_cost = sum(line.cost for line in group)
        add(f"| {location} | {hours(group_hours)} | {pct(group_hours / pricing.total_hours)} | {number(group_cost)} | {pct(group_cost / s.labor)} |")
    add("")

    # 17. Controles
    add("## 17. Controles de coherencia")
    add("")
    for check in pricing.checks:
        add(f"- {STATUS_ICON[check.status]} {check.text}")
    add("")

    # 18. Riesgos
    add("## 18. Riesgos para la consultora")
    add("")
    for risk in draft.internal_risks:
        add(f"- {risk}")
    return "\n".join(w).rstrip() + "\n"


def build_client_proposal(pricing: ProjectPricing) -> str:
    plan, s = pricing.plan, pricing.statement
    draft = plan.draft
    value = draft.value_proposition
    w: list[str] = []
    add = w.append

    add(f"# Propuesta: {draft.project_name}")
    add("")
    add(f"**Preparada para:** {value.client_profile}")
    add("")

    add("## 1. Resumen")
    add("")
    add(f"- **Qué proponemos:** {draft.project_type}.")
    add(f"- **Plazo:** {plan.duration_weeks} semanas, en {len(plan.phases)} etapas.")
    add(f"- **Inversión total:** {usd(s.price)}, con los gastos reembolsables incluidos.")
    add("")

    add("## 2. Situación actual")
    add("")
    add(value.current_situation)
    add("")
    add("## 3. Objetivos")
    add("")
    w.extend(f"- {item}" for item in value.objectives)
    add("")
    add("## 4. Solución propuesta")
    add("")
    add(value.solution)
    add("")
    add("## 5. Beneficios")
    add("")
    w.extend(f"- {item}" for item in value.benefits)
    add("")

    add("## 6. Cronograma de implementación")
    add("")
    add("| Etapa | Semanas | Duración | Entregables | Cronograma |")
    add("|---|---|---|---|---|")
    w.extend(_phase_rows(pricing, with_proposed=False))
    add("")

    add("## 7. Inversión")
    add("")
    add("### Honorarios profesionales")
    add("")
    add("| Consultor | Horas | Tarifa (USD/h) | Importe (USD) |")
    add("|---|---|---|---|")
    for line in pricing.lines:
        add(f"| {line.role.name} | {number(line.base_hours)} | {rate(line.client_rate)} | {number(line.client_amount)} |")
    add(f"| Gastos generales del proyecto | | | {number(pricing.overhead_client_amount)} |")
    add(f"| **Total honorarios** | **{number(pricing.base_hours)}** | | **{number(s.fees)}** |")
    add("")
    add("### Gastos reembolsables, facturados a coste")
    add("")
    if plan.expenses:
        add("| Gasto | Importe (USD) |")
        add("|---|---|")
        for expense in plan.expenses:
            add(f"| {expense.description} | {number(expense.amount)} |")
        add(f"| **Total gastos reembolsables** | **{number(s.expenses)}** |")
    else:
        add("No se prevén gastos reembolsables.")
    add("")
    add("### Inversión total")
    add("")
    add(f"Honorarios {usd(s.fees)} + gastos reembolsables {usd(s.expenses)} = **{usd(s.price)}**")
    add("")

    add("## 8. Forma de pago")
    add("")
    add("| Hito | Momento | % de los honorarios | Importe (USD) |")
    add("|---|---|---|---|")
    for milestone in pricing.milestones:
        add(f"| {milestone.number} | {milestone.label} | {pct(1 / PAYMENT_MILESTONES, 0)} | {number(milestone.amount)} |")
    add(f"| **Total** | | **100 %** | **{number(s.fees)}** |")
    add("")
    add("Los gastos reembolsables se facturan a coste al final de cada mes, con sus comprobantes.")
    add("")

    add("## 9. Fuera del alcance")
    add("")
    w.extend(f"- {item}" for item in value.out_of_scope)
    add("")
    section = 10
    if draft.open_scope_questions:
        add(f"## {section}. Puntos por confirmar")
        add("")
        add(
            "Estos puntos se mencionaron en la reunión, pero no quedaron decididos. No están "
            "incluidos en esta propuesta: si se incluyen, se actualizan el alcance, el cronograma y "
            "la inversión."
        )
        add("")
        w.extend(f"- {question}" for question in draft.open_scope_questions)
        add("")
        section += 1
    add(f"## {section}. Supuestos y condiciones")
    add("")
    w.extend(f"- {item}" for item in value.assumptions)
    add("")
    add(f"## {section + 1}. Validez")
    add("")
    add(f"Esta propuesta es válida durante {PROPOSAL_VALIDITY_DAYS} días desde su envío.")
    return "\n".join(w).rstrip() + "\n"
