"""Consistencia del inventario de alcance: ¿la misma reunión da siempre los mismos componentes?

Manda la misma transcripción varias veces al modelo, guarda cada inventario y calcula sus horas con
el catálogo. Como los componentes y los tamaños son una lista cerrada, se pueden comparar exactos
entre llamadas: qué componentes aparecen siempre, cuáles solo a veces y con qué tamaño. Las horas
que pone el modelo (componentes sin referencia o a medida) se separan de las del catálogo.

Cada llamada cuesta dinero, así que no corre en los tests ni en el pipeline:

    uv run python -m evals.inventory_consistency run transcripciones/onboarding_seguridad_canteras.txt --runs 10 --label inventario-v1
    uv run python -m evals.inventory_consistency report evals/resultados/<carpeta> [<otra carpeta> ...]
"""

import argparse
import asyncio
import json
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from app.config import get_settings
from app.context.catalog import COMPONENTS, CUSTOM
from app.schemas.inventory import ScopeInventory
from app.services.catalog_hours import CATALOG, REVIEW, InventoryHours, agreed, inventory_hours
from app.services.formatting import number
from app.services.inventory_service import InventoryResult, generate_inventory, get_inventory_prompt
from evals import consistency
from evals.consistency import (
    CONFIG_FILE,
    REPORT_FILE,
    RUN_PATTERN,
    SUMMARY_FILE,
    Spread,
    _num,
    _pct,
    _shown,
    fingerprint,
    git_commit,
    run_many,
)

STATUSES = ("acordado", "opcional", "condicionado", "excluido")


def inventory_record(result: InventoryResult) -> dict:
    """Lo que se guarda de un inventario: sus llamadas, sumadas y una a una, y el inventario."""
    calls = result.calls
    return {
        "model": calls[0].model,
        "input_tokens": sum(call.input_tokens for call in calls),
        "cache_creation_input_tokens": sum(call.cache_creation_input_tokens for call in calls),
        "cache_read_input_tokens": sum(call.cache_read_input_tokens for call in calls),
        "output_tokens": sum(call.output_tokens for call in calls),
        "latency_ms": sum(call.latency_ms for call in calls),
        "estimated_cost_usd": result.estimated_cost_usd,
        "calls": [{**vars(call), "estimated_cost_usd": call.estimated_cost_usd} for call in calls],
        "completed": list(result.completed),
        "inventory": result.inventory.model_dump(mode="json"),
    }


@dataclass(frozen=True)
class InventoryMetrics:
    run: int
    inventory: ScopeInventory
    hours: InventoryHours
    cost_usd: float | None = None
    latency_ms: int = 0
    completed: tuple[str, ...] = ()  # requisitos cuyas horas tuvo que completar una segunda llamada

    @property
    def units(self) -> Counter:
        """Unidades acordadas de cada componente: la suma de sus cantidades."""
        counts: Counter = Counter()
        for requirement in agreed(self.inventory.requirements):
            counts[requirement.component] += max(requirement.quantity, 1)
        return counts

    @property
    def statuses(self) -> Counter:
        return Counter(requirement.status for requirement in self.inventory.requirements)


@dataclass(frozen=True)
class InventorySummary:
    label: str
    config: dict
    metrics: tuple[InventoryMetrics, ...]
    failures: tuple[dict, ...]

    @property
    def attempts(self) -> int:
        return len(self.metrics) + len(self.failures)

    def spread(self, value: Callable[[InventoryMetrics], float]) -> Spread:
        return Spread(tuple(value(metrics) for metrics in self.metrics))

    @property
    def components(self) -> list[str]:
        """Los componentes acordados en alguna llamada, en el orden del catálogo."""
        seen = {component for metrics in self.metrics for component in metrics.units}
        return [component for component in [*COMPONENTS, CUSTOM] if component in seen]

    def presence(self, component: str) -> int:
        return sum(1 for metrics in self.metrics if metrics.units[component] > 0)

    def sizes(self, component: str) -> Counter:
        return Counter(
            requirement.size
            for metrics in self.metrics
            for requirement in agreed(metrics.inventory.requirements)
            if requirement.component == component
        )

    @property
    def partial_components(self) -> list[str]:
        return [c for c in self.components if self.presence(c) < len(self.metrics)]

    @property
    def platforms(self) -> Counter:
        return Counter(metrics.inventory.platform for metrics in self.metrics)

    @property
    def total_cost_usd(self) -> float | None:
        costs = [metrics.cost_usd for metrics in self.metrics]
        return round(sum(costs), 4) if costs and None not in costs else None

    def as_dict(self) -> dict:
        figures = {
            name: self.spread(value).as_dict() for name, value in FIGURES.items()
        } if self.metrics else {}
        return {
            "etiqueta": self.label,
            "config": self.config,
            "llamadas": self.attempts,
            "validas": len(self.metrics),
            "fallidas": list(self.failures),
            "cifras": figures,
            "plataformas": dict(self.platforms),
            "componentes": {
                component: {"llamadas": self.presence(component), "tamanos": dict(self.sizes(component))}
                for component in self.components
            },
            "costo_total_usd": self.total_cost_usd,
        }


FIGURES: dict[str, Callable[[InventoryMetrics], float]] = {
    "Horas base": lambda m: m.hours.base_hours,
    "Horas del catálogo": lambda m: m.hours.hours_of(CATALOG),
    "Horas a revisar (del modelo)": lambda m: m.hours.hours_of(REVIEW),
    "Requisitos acordados": lambda m: m.statuses["acordado"],
    "Requisitos no acordados": lambda m: sum(m.statuses[s] for s in STATUSES[1:]),
}


def load_summary(folder: Path) -> InventorySummary:
    config_path = folder / CONFIG_FILE
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    metrics: list[InventoryMetrics] = []
    failures: list[dict] = []
    for path in sorted(folder.glob(RUN_PATTERN)):
        record = json.loads(path.read_text(encoding="utf-8"))
        if not record.get("ok"):
            failures.append({"run": record["run"], "error": record.get("error", "sin detalle")})
            continue
        try:
            # Los inventarios anteriores al plazo no traen el campo: se leen sin plazo.
            inventory = ScopeInventory.model_validate({"deadline": None, **record["inventory"]})
        except ValidationError as error:
            failures.append({"run": record["run"], "error": f"El inventario no es válido: {error}"})
            continue
        metrics.append(
            InventoryMetrics(
                record["run"], inventory, inventory_hours(inventory),
                record.get("estimated_cost_usd"), record.get("latency_ms", 0),
                tuple(record.get("completed", ())),
            )
        )
    return InventorySummary(config.get("label", folder.name), config, tuple(metrics), tuple(failures))


def _name(component: str) -> str:
    return COMPONENTS[component].name if component in COMPONENTS else "A medida"


def render_report(summary: InventorySummary) -> str:
    config = summary.config
    lines = [f"# Consistencia del inventario: {summary.label}", ""]
    if config:
        lines += [
            f"- Transcripción: `{config.get('transcription')}` (huella {config.get('transcription_fingerprint')})",
            f"- Modelo: {config.get('model')} · prompt {config.get('system_prompt_fingerprint')} · commit {config.get('git_commit')}",
            f"- Fecha: {config.get('started_at')}",
        ]
    cost = summary.total_cost_usd
    lines += [
        f"- Llamadas válidas: {len(summary.metrics)} de {summary.attempts}"
        + (f" · costo total {cost:.4f} USD" if cost is not None else ""),
        "",
    ]
    n = len(summary.metrics)
    if n < 2:
        lines += ["Hacen falta al menos dos llamadas válidas para medir la variación.", ""]
        return "\n".join(lines + consistency._failures(summary))

    lines += [
        "## Cifras",
        "",
        "Las horas son base, sin el 10 % de imprevistos. Las del catálogo las calcula Python; las "
        "que quedan a revisar las pone el modelo.",
        "",
        "| | Media | Mediana | Mínimo | Máximo | Amplitud | CV |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, value in FIGURES.items():
        s = summary.spread(value)
        lines.append(
            f"| {name} | {_num(s.mean)} | {_num(s.median)} | {_num(s.minimum)} | {_num(s.maximum)} "
            f"| {_pct(s.amplitude)} | {_pct(s.cv)} |"
        )
    platforms = ", ".join(f"{p} en {c} de {n}" for p, c in summary.platforms.most_common())
    deadlines = Counter(m.inventory.deadline_weeks for m in summary.metrics).most_common()
    deadline = ", ".join(f"{f'{w} semanas' if w else 'sin plazo'} en {c} de {n}" for w, c in deadlines)
    completed = sum(1 for m in summary.metrics if m.completed)
    without_hours = sum(1 for m in summary.metrics for line in m.hours.lines if line.kind == REVIEW and not line.total)
    lines += [
        "",
        f"**Plataforma:** {platforms}.",
        "",
        f"**Plazo pedido:** {deadline}.",
        "",
        f"**Horas que faltaban:** {completed} de {n} inventarios necesitaron una segunda llamada para "
        f"completar horas; quedan {without_hours} partidas sin horas.",
        "",
        "## Componentes acordados",
        "",
              "| Componente | Llamadas en las que aparece | Tamaños | Unidades por llamada |",
              "|---|---:|---|---:|"]
    for component in summary.components:
        sizes = ", ".join(f"{size} ×{count}" for size, count in sorted(summary.sizes(component).items()))
        units = [metrics.units[component] for metrics in summary.metrics]
        lines.append(
            f"| {_name(component)} | {summary.presence(component)} de {n} | {sizes} | "
            f"{min(units)}-{max(units)} |"
        )
    lines += ["", "## Cada llamada", "",
              "| Llamada | Plataforma | Horas base | Catálogo | A revisar | Acordados | Opcionales | "
              "Condicionados | Excluidos | Decisiones abiertas |",
              "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for m in summary.metrics:
        st = m.statuses
        lines.append(
            f"| {m.run} | {m.inventory.platform} | {number(m.hours.base_hours)} | "
            f"{number(m.hours.hours_of(CATALOG))} | {number(m.hours.hours_of(REVIEW))} | "
            f"{st['acordado']} | {st['opcional']} | {st['condicionado']} | {st['excluido']} | "
            f"{len(m.inventory.open_decisions)} |"
        )
    lines += ["", "## Lo que no se acordó y las decisiones abiertas", ""]
    for m in summary.metrics:
        lines.append(f"**Llamada {m.run}**")
        pending = [r for r in m.inventory.requirements if r.status != "acordado"]
        lines += [f"- {r.status}: {r.description}" for r in pending] or ["- Todo acordado"]
        lines += [f"- Decisión abierta: {d.question} (se asume: {d.assumed})" for d in m.inventory.open_decisions]
        lines.append("")
    lines += ["## Horas que puso el modelo", "", "Son las que hay que revisar: el catálogo no tiene referencia.", ""]
    for m in summary.metrics:
        review = [line for line in m.hours.lines if line.kind == REVIEW]
        lines.append(f"**Llamada {m.run}:** {number(m.hours.hours_of(REVIEW))} h")
        lines += [f"- {line.name}: {number(line.total)} h" for line in review]
        lines += [f"- Completada en una segunda llamada: {description}" for description in m.completed]
        lines.append("")
    return "\n".join(lines + consistency._failures(summary))


def render_comparison(summaries: list[InventorySummary]) -> str:
    lines = [
        "# Comparación de consistencia del inventario",
        "",
        "| | " + " | ".join(s.label for s in summaries) + " |",
        "|---|" + "---:|" * len(summaries),
    ]

    def row(name: str, cell: Callable[[InventorySummary], str]) -> None:
        lines.append(f"| {name} | " + " | ".join(cell(s) for s in summaries) + " |")

    row("Llamadas válidas", lambda s: f"{len(s.metrics)} de {s.attempts}")
    for name, value in FIGURES.items():
        row(f"{name}: mediana", lambda s, v=value: _num(s.spread(v).median) if s.metrics else "—")
        row(f"{name}: CV", lambda s, v=value: _pct(s.spread(v).cv) if s.metrics else "—")
    row("Componentes que no salen en todas las llamadas", lambda s: str(len(s.partial_components)))
    row("Costo de las llamadas", lambda s: "—" if s.total_cost_usd is None else f"{s.total_cost_usd:.4f} USD")
    return "\n".join(lines + [""])


def write_report(folder: Path, summary: InventorySummary) -> str:
    report = render_report(summary)
    (folder / REPORT_FILE).write_text(report, encoding="utf-8")
    (folder / SUMMARY_FILE).write_text(json.dumps(summary.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def command_run(args: argparse.Namespace) -> int:
    if args.runs < 2:
        print("Hacen falta al menos 2 llamadas para medir la variación.", file=sys.stderr)
        return 2
    transcription = args.transcription.read_text(encoding="utf-8")
    scope_changes = args.scope_changes.read_text(encoding="utf-8") if args.scope_changes else None
    try:
        settings = get_settings()
    except ValidationError as error:
        print(f"La configuración no es válida: {error}", file=sys.stderr)
        return 2
    label = args.label or f"inventario-{args.transcription.stem}"
    folder = consistency.new_folder(label)
    config = {
        "label": label,
        "kind": "inventario",
        "transcription": str(args.transcription),
        "transcription_fingerprint": fingerprint(transcription),
        "scope_changes_fingerprint": fingerprint(scope_changes) if scope_changes else None,
        "model": settings.LLM_MODEL,
        "provider": settings.LLM_PROVIDER,
        "system_prompt_fingerprint": fingerprint(get_inventory_prompt()),
        "git_commit": git_commit(),
        "runs": args.runs,
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }
    (folder / CONFIG_FILE).write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{args.runs} inventarios con {settings.LLM_MODEL}. Resultados en {_shown(folder)}", flush=True)
    asyncio.run(
        run_many(
            transcription, runs=args.runs, folder=folder, scope_changes=scope_changes,
            concurrency=args.concurrency, generate=generate_inventory, serialize=inventory_record,
        )
    )
    print()
    print(write_report(folder, load_summary(folder)))
    return 0


def command_report(args: argparse.Namespace) -> int:
    missing = [folder for folder in args.folders if not folder.is_dir()]
    if missing:
        print(f"No existe la carpeta: {', '.join(map(str, missing))}", file=sys.stderr)
        return 2
    summaries = [load_summary(folder) for folder in args.folders]
    for folder, summary in zip(args.folders, summaries):
        report = write_report(folder, summary)
        if len(summaries) == 1:
            print(report)
    if len(summaries) > 1:
        print(render_comparison(summaries))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m evals.inventory_consistency",
        description="Mide cuánto cambia el inventario de alcance de una misma transcripción.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="lanza el inventario varias veces contra el modelo real (cuesta dinero)")
    run.add_argument("transcription", type=Path)
    run.add_argument("--runs", type=int, default=10)
    run.add_argument("--label")
    run.add_argument("--scope-changes", type=Path)
    run.add_argument("--concurrency", type=int, default=4)
    run.set_defaults(handler=command_run)
    report = commands.add_parser("report", help="recalcula el informe de una o varias carpetas")
    report.add_argument("folders", type=Path, nargs="+")
    report.set_defaults(handler=command_report)
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
