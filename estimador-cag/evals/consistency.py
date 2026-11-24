"""Evaluador de consistencia: ¿la misma reunión da siempre la misma estimación?

Manda la misma transcripción varias veces al modelo real, guarda cada borrador y mide cuánto
cambian las cifras que Python calcula con ellos: horas base, precio, semanas, horas de cada perfil
y los puntos de alcance que el modelo deja por confirmar.

Sirve para juzgar con números cualquier cambio del prompt, de los ejemplos o del preprocesamiento:
se mide una línea base, se hace el cambio y se vuelve a medir con la misma transcripción.

Cada llamada cuesta dinero (unos 0.01 USD con claude-haiku-5-5) y tarda cerca de un minuto, así
que no se ejecuta en los tests ni en el pipeline: se lanza a mano desde estimador-cag/.

    uv run python -m evals.consistency run transcripciones/onboarding_seguridad_canteras.txt --runs 5 --label linea-base
    uv run python -m evals.consistency report evals/resultados/<carpeta> [<otra carpeta> ...]

`run` guarda en evals/resultados/<fecha>_<etiqueta>/ un JSON por llamada, la configuración y el
informe. `report` vuelve a calcular el informe con los borradores guardados, sin llamar al modelo;
con varias carpetas, las compara.

La carpeta guarda los borradores, que no llevan nombres (lo exigen las reglas del prompt), y una
huella de la transcripción, nunca su texto.
"""

import argparse
import asyncio
import hashlib
import json
import re
import statistics
import subprocess
import sys
import time
import unicodedata
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import anthropic
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.draft import EstimationDraft
from app.services.formatting import number, pct
from app.services.llm_service import DraftResult, generate_draft, get_system_prompt
from app.services.planning import build_plan
from app.services.pricing import price_project

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = Path(__file__).resolve().parent / "resultados"
CONFIG_FILE = "config.json"
REPORT_FILE = "informe.md"
SUMMARY_FILE = "resumen.json"
RUN_PATTERN = "llamada_*.json"

# Errores de configuración: si la clave o el modelo están mal, fallarán todas las llamadas.
FATAL_ERRORS = (
    anthropic.AuthenticationError,
    anthropic.PermissionDeniedError,
    anthropic.NotFoundError,
    anthropic.BadRequestError,
    NotImplementedError,
)

Generator = Callable[[str, str | None], Awaitable[DraftResult]]

# Las cifras que se comparan entre llamadas: (atributo de RunMetrics, nombre en el informe).
FIGURES = (("base_hours", "Horas base"), ("price", "Precio (USD)"), ("weeks", "Semanas"))


# ---------------------------------------------------------------------------
# Lanzar las llamadas
# ---------------------------------------------------------------------------


def fingerprint(text: str) -> str:
    """Huella corta de un texto: dice si dos ejecuciones usaron el mismo, sin guardarlo."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def git_commit() -> str | None:
    """El commit del código, y si `app/` tiene cambios sin guardar (por ejemplo, en el prompt)."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        changes = subprocess.run(
            ["git", "status", "--porcelain", "--", "app"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return f"{commit} con cambios sin commit en app/" if changes else commit


def run_path(folder: Path, run: int) -> Path:
    return folder / f"llamada_{run:02d}.json"


async def call_once(
    run: int, transcription: str, scope_changes: str | None, generate: Generator, folder: Path
) -> dict:
    """Una llamada. Si falla, el error se guarda como un resultado más: también cuenta."""
    start = time.perf_counter()
    try:
        result = await generate(transcription, scope_changes)
    except FATAL_ERRORS:
        raise
    except Exception as error:  # noqa: BLE001
        record = {
            "run": run,
            "ok": False,
            "error": f"{type(error).__name__}: {error}",
            "latency_ms": round((time.perf_counter() - start) * 1000),
        }
        print(f"  Llamada {run}: falló ({record['error']})", flush=True)
    else:
        record = {
            "run": run,
            "ok": True,
            "model": result.model,
            "provider": result.provider,
            "input_tokens": result.input_tokens,
            "cache_creation_input_tokens": result.cache_creation_input_tokens,
            "cache_read_input_tokens": result.cache_read_input_tokens,
            "output_tokens": result.output_tokens,
            "latency_ms": result.latency_ms,
            "estimated_cost_usd": result.estimated_cost_usd,
            "draft": result.draft.model_dump(mode="json"),
        }
        print(f"  Llamada {run}: lista en {result.latency_ms / 1000:.0f} s", flush=True)
    run_path(folder, run).write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return record


async def run_many(
    transcription: str,
    *,
    runs: int,
    folder: Path,
    scope_changes: str | None = None,
    concurrency: int = 4,
    generate: Generator = generate_draft,
) -> list[dict]:
    """Lanza `runs` llamadas con la misma transcripción y guarda cada una en `folder`.

    La primera va sola: escribe el system prompt en la caché del proveedor, y las demás lo leen
    a una décima parte del precio. Las demás van en paralelo, como mucho `concurrency` a la vez.
    """
    records = [await call_once(1, transcription, scope_changes, generate, folder)]
    semaphore = asyncio.Semaphore(concurrency)

    async def limited(run: int) -> dict:
        async with semaphore:
            return await call_once(run, transcription, scope_changes, generate, folder)

    records += await asyncio.gather(*(limited(run) for run in range(2, runs + 1)))
    return records


# ---------------------------------------------------------------------------
# Medir
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunMetrics:
    """Las cifras de una llamada, calculadas con el mismo código que usa el servicio."""

    run: int
    base_hours: int
    price: int
    weeks: int  # duración final, después de los ajustes de Python
    proposed_weeks: int  # lo que propuso el modelo
    tasks: int
    hours_by_role: dict[str, int]
    open_scope_questions: tuple[str, ...]
    adjustments: int  # etapas que Python alargó porque alguien no cabía
    cost_usd: float | None = None
    latency_ms: int = 0


def measure(
    run: int, draft: EstimationDraft, *, cost_usd: float | None = None, latency_ms: int = 0
) -> RunMetrics:
    pricing = price_project(build_plan(draft))
    plan = pricing.plan
    return RunMetrics(
        run=run,
        base_hours=pricing.base_hours,
        price=pricing.statement.price,
        weeks=plan.duration_weeks,
        proposed_weeks=sum(phase.weeks for phase in draft.phases),
        tasks=len(draft.tasks),
        hours_by_role=dict(plan.base_hours_by_role),
        open_scope_questions=tuple(draft.open_scope_questions),
        adjustments=len(plan.adjustments),
        cost_usd=cost_usd,
        latency_ms=latency_ms,
    )


@dataclass(frozen=True)
class Spread:
    """Cuánto cambia una cifra de una llamada a otra."""

    values: tuple[float, ...]

    @property
    def mean(self) -> float:
        return statistics.fmean(self.values)

    @property
    def median(self) -> float:
        return statistics.median(self.values)

    @property
    def minimum(self) -> float:
        return min(self.values)

    @property
    def maximum(self) -> float:
        return max(self.values)

    @property
    def stdev(self) -> float | None:
        return statistics.stdev(self.values) if len(self.values) > 1 else None

    @property
    def amplitude(self) -> float | None:
        """Cuánto más alta es la llamada más alta que la más baja: 0.35 es un 35 % más."""
        if len(self.values) < 2 or self.minimum <= 0:
            return None
        return self.maximum / self.minimum - 1

    @property
    def cv(self) -> float | None:
        """Coeficiente de variación: la desviación estándar sobre la media. Más bajo, más estable."""
        if self.stdev is None or self.mean <= 0:
            return None
        return self.stdev / self.mean

    def as_dict(self) -> dict:
        return {
            "media": self.mean,
            "mediana": self.median,
            "minimo": self.minimum,
            "maximo": self.maximum,
            "desviacion_estandar": self.stdev,
            "amplitud": self.amplitude,
            "cv": self.cv,
        }


@dataclass(frozen=True)
class Summary:
    """Todas las llamadas de una carpeta: las que dieron un borrador válido y las que no."""

    label: str
    config: dict
    metrics: tuple[RunMetrics, ...]
    failures: tuple[dict, ...]  # {"run": n, "error": "..."}

    @property
    def attempts(self) -> int:
        return len(self.metrics) + len(self.failures)

    def spread(self, figure: str) -> Spread:
        return Spread(tuple(getattr(metrics, figure) for metrics in self.metrics))

    @property
    def roles(self) -> list[str]:
        """Los perfiles que aparecen en alguna llamada, en el orden en que salen."""
        seen: dict[str, None] = {}
        for metrics in self.metrics:
            seen.update(dict.fromkeys(metrics.hours_by_role))
        return list(seen)

    def role_spread(self, role: str) -> Spread:
        """Las horas del perfil en cada llamada; si no aparece en una, cuenta como 0."""
        return Spread(tuple(metrics.hours_by_role.get(role, 0) for metrics in self.metrics))

    def role_presence(self, role: str) -> int:
        return sum(1 for metrics in self.metrics if metrics.hours_by_role.get(role, 0) > 0)

    @property
    def partial_roles(self) -> list[str]:
        """Perfiles que el modelo incluye en unas llamadas y en otras no."""
        return [role for role in self.roles if self.role_presence(role) < len(self.metrics)]

    @property
    def total_cost_usd(self) -> float | None:
        costs = [metrics.cost_usd for metrics in self.metrics]
        return round(sum(costs), 4) if costs and None not in costs else None

    def as_dict(self) -> dict:
        return {
            "etiqueta": self.label,
            "config": self.config,
            "llamadas": self.attempts,
            "validas": len(self.metrics),
            "fallidas": list(self.failures),
            "cifras": {figure: self.spread(figure).as_dict() for figure, _ in FIGURES}
            if self.metrics
            else {},
            "perfiles": {
                role: {"llamadas": self.role_presence(role), **self.role_spread(role).as_dict()}
                for role in self.roles
            },
            "costo_total_usd": self.total_cost_usd,
        }


def load_summary(folder: Path) -> Summary:
    """Lee una carpeta de resultados y vuelve a calcular cada borrador con el código actual."""
    config_path = folder / CONFIG_FILE
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    metrics: list[RunMetrics] = []
    failures: list[dict] = []
    for path in sorted(folder.glob(RUN_PATTERN)):
        record = json.loads(path.read_text(encoding="utf-8"))
        if not record.get("ok"):
            failures.append({"run": record["run"], "error": record.get("error", "sin detalle")})
            continue
        try:
            draft = EstimationDraft.model_validate(record["draft"])
            metrics.append(
                measure(
                    record["run"],
                    draft,
                    cost_usd=record.get("estimated_cost_usd"),
                    latency_ms=record.get("latency_ms", 0),
                )
            )
        except (ValidationError, ValueError) as error:
            failures.append({"run": record["run"], "error": f"Python no pudo usar el borrador: {error}"})
    return Summary(
        label=config.get("label", folder.name),
        config=config,
        metrics=tuple(metrics),
        failures=tuple(failures),
    )


# ---------------------------------------------------------------------------
# Informes
# ---------------------------------------------------------------------------


def _num(value: float) -> str:
    return number(round(value))


def _pct(value: float | None) -> str:
    return "—" if value is None else pct(value, 0)


def render_report(summary: Summary) -> str:
    """El informe de una carpeta, en Markdown."""
    config = summary.config
    lines = [f"# Consistencia: {summary.label}", ""]
    if config:
        lines += [
            f"- Transcripción: `{config.get('transcription')}` (huella {config.get('transcription_fingerprint')})",
            f"- Cambios de alcance: {'sí, huella ' + config['scope_changes_fingerprint'] if config.get('scope_changes_fingerprint') else 'no'}",
            f"- Modelo: {config.get('model')} · system prompt {config.get('system_prompt_fingerprint')} · commit {config.get('git_commit')}",
            f"- Fecha: {config.get('started_at')}",
        ]
    cost = summary.total_cost_usd
    lines += [
        f"- Llamadas válidas: {len(summary.metrics)} de {summary.attempts}"
        + (f" · costo total {cost:.4f} USD" if cost is not None else ""),
        "",
    ]
    if len(summary.metrics) < 2:
        lines += ["Hacen falta al menos dos llamadas válidas para medir la variación.", ""]
        return "\n".join(lines + _failures(summary))

    lines += [
        "## Cifras",
        "",
        "| | Media | Mediana | Mínimo | Máximo | Amplitud | CV |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for figure, name in FIGURES:
        spread = summary.spread(figure)
        lines.append(
            f"| {name} | {_num(spread.mean)} | {_num(spread.median)} | {_num(spread.minimum)} | "
            f"{_num(spread.maximum)} | {_pct(spread.amplitude)} | {_pct(spread.cv)} |"
        )
    lines += [
        "",
        "La amplitud dice cuánto más alta es la llamada más alta que la más baja. El CV "
        "(coeficiente de variación) es la desviación estándar dividida por la media: cuanto más "
        "bajo, más estable. La mediana es la cifra que daría quedarse con la llamada del medio.",
        "",
        "## Dónde está la variación: horas base por perfil",
        "",
        "Ordenados de más a menos variación. Si un perfil no aparece en una llamada, cuenta como 0 horas.",
        "",
        "| Perfil | Llamadas en las que aparece | Media | Mínimo | Máximo | Desviación estándar |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    roles = sorted(summary.roles, key=lambda role: summary.role_spread(role).stdev or 0, reverse=True)
    for role in roles:
        spread = summary.role_spread(role)
        lines.append(
            f"| {role} | {summary.role_presence(role)} de {len(summary.metrics)} | {_num(spread.mean)} | "
            f"{_num(spread.minimum)} | {_num(spread.maximum)} | {_num(spread.stdev or 0)} |"
        )
    lines += [
        "",
        "## Cada llamada",
        "",
        "| Llamada | Horas base | Precio (USD) | Semanas (propuestas) | Tareas | Puntos por confirmar | Etapas alargadas por Python |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for metrics in summary.metrics:
        lines.append(
            f"| {metrics.run} | {number(metrics.base_hours)} | {number(metrics.price)} | "
            f"{metrics.weeks} ({metrics.proposed_weeks}) | {metrics.tasks} | "
            f"{len(metrics.open_scope_questions)} | {metrics.adjustments} |"
        )
    lines += [
        "",
        "## Puntos de alcance por confirmar",
        "",
        "Los redacta el modelo, así que el mismo punto puede salir con palabras distintas: hay que "
        "leerlos para ver si coinciden.",
        "",
    ]
    for metrics in summary.metrics:
        lines.append(f"**Llamada {metrics.run}**")
        lines += [f"- {question}" for question in metrics.open_scope_questions] or ["- Ninguno"]
        lines.append("")
    return "\n".join(lines + _failures(summary))


def _failures(summary: Summary) -> list[str]:
    if not summary.failures:
        return []
    lines = ["## Llamadas que fallaron", ""]
    lines += [f"- Llamada {failure['run']}: {failure['error']}" for failure in summary.failures]
    return lines + [""]


def render_comparison(summaries: list[Summary]) -> str:
    """Varias carpetas lado a lado, por ejemplo la línea base y la versión con un cambio."""
    header = "| | " + " | ".join(summary.label for summary in summaries) + " |"
    lines = [
        "# Comparación de consistencia",
        "",
        header,
        "|---|" + "---:|" * len(summaries),
    ]

    def row(name: str, cell: Callable[[Summary], str]) -> None:
        lines.append(f"| {name} | " + " | ".join(cell(summary) for summary in summaries) + " |")

    def figure_cell(figure: str, stat: str) -> Callable[[Summary], str]:
        def cell(summary: Summary) -> str:
            if not summary.metrics:
                return "—"
            value = getattr(summary.spread(figure), stat)
            return _pct(value) if stat in ("amplitude", "cv") else _num(value)

        return cell

    row("Llamadas válidas", lambda s: f"{len(s.metrics)} de {s.attempts}")
    for figure, name in FIGURES:
        row(f"{name}: mediana", figure_cell(figure, "median"))
        row(f"{name}: amplitud", figure_cell(figure, "amplitude"))
        row(f"{name}: CV", figure_cell(figure, "cv"))
    row("Perfiles que no salen en todas las llamadas", lambda s: str(len(s.partial_roles)))
    row(
        "Puntos por confirmar por llamada",
        lambda s: "—" if not s.metrics else "{}-{}".format(
            min(len(m.open_scope_questions) for m in s.metrics),
            max(len(m.open_scope_questions) for m in s.metrics),
        ),
    )
    row(
        "Costo de las llamadas",
        lambda s: "—" if s.total_cost_usd is None else f"{s.total_cost_usd:.4f} USD",
    )
    return "\n".join(lines + [""])


def write_report(folder: Path, summary: Summary) -> str:
    report = render_report(summary)
    (folder / REPORT_FILE).write_text(report, encoding="utf-8")
    (folder / SUMMARY_FILE).write_text(
        json.dumps(summary.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


# ---------------------------------------------------------------------------
# Línea de comandos
# ---------------------------------------------------------------------------


def _slug(text: str) -> str:
    """'Línea base' → 'linea-base', para el nombre de la carpeta."""
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-") or "ejecucion"


def new_folder(label: str) -> Path:
    folder = RESULTS_DIR / f"{datetime.now():%Y-%m-%d_%H%M%S}_{_slug(label)}"
    folder.mkdir(parents=True)
    return folder


def _shown(folder: Path) -> str:
    try:
        return str(folder.relative_to(ROOT))
    except ValueError:
        return str(folder)


def command_run(args: argparse.Namespace) -> int:
    if args.runs < 2:
        print("Hacen falta al menos 2 llamadas para medir la variación.", file=sys.stderr)
        return 2
    if args.concurrency < 1:
        print("--concurrency tiene que ser 1 o más.", file=sys.stderr)
        return 2
    transcription = args.transcription.read_text(encoding="utf-8")
    scope_changes = args.scope_changes.read_text(encoding="utf-8") if args.scope_changes else None
    try:
        settings = get_settings()
    except ValidationError as error:
        print(f"La configuración no es válida: {error}", file=sys.stderr)
        return 2

    label = args.label or args.transcription.stem
    folder = new_folder(label)
    config = {
        "label": label,
        "transcription": str(args.transcription),
        "transcription_fingerprint": fingerprint(transcription),
        "scope_changes_fingerprint": fingerprint(scope_changes) if scope_changes else None,
        "model": settings.LLM_MODEL,
        "provider": settings.LLM_PROVIDER,
        "system_prompt_fingerprint": fingerprint(get_system_prompt()),
        "git_commit": git_commit(),
        "runs": args.runs,
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }
    (folder / CONFIG_FILE).write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"{args.runs} llamadas reales a {settings.LLM_MODEL} (unos {0.01 * args.runs:.2f} USD). "
        f"Resultados en {_shown(folder)}",
        flush=True,
    )
    asyncio.run(
        run_many(
            transcription,
            runs=args.runs,
            folder=folder,
            scope_changes=scope_changes,
            concurrency=args.concurrency,
            generate=generate_draft,
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
    summaries = []
    for folder in args.folders:
        summary = load_summary(folder)
        summaries.append(summary)
        report = write_report(folder, summary)
        if len(args.folders) == 1:
            print(report)
    if len(summaries) > 1:
        print(render_comparison(summaries))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m evals.consistency",
        description="Mide cuánto cambia la estimación de una misma transcripción entre llamadas.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="lanza la transcripción varias veces contra el modelo real (cuesta dinero)")
    run.add_argument("transcription", type=Path, help="archivo .txt con la transcripción")
    run.add_argument("--runs", type=int, default=5, help="número de llamadas (5 por defecto)")
    run.add_argument("--label", help="nombre de la ejecución, por ejemplo linea-base")
    run.add_argument("--scope-changes", type=Path, help="archivo con los cambios de alcance de la consultora")
    run.add_argument("--concurrency", type=int, default=4, help="llamadas en paralelo después de la primera")
    run.set_defaults(handler=command_run)

    report = commands.add_parser("report", help="recalcula el informe de una o varias carpetas, sin llamar al modelo")
    report.add_argument("folders", type=Path, nargs="+", help="carpetas de evals/resultados/")
    report.set_defaults(handler=command_report)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
