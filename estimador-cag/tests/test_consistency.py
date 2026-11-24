"""El evaluador de consistencia, con un generador simulado: nunca llama al modelo."""

import asyncio
import json

import pytest

from app.context.examples import ESTIMATION_EXAMPLES
from app.services.llm_service import DraftResult, EstimationError
from app.services.planning import build_plan
from app.services.pricing import price_project
from evals import consistency
from evals.consistency import (
    Spread,
    load_summary,
    measure,
    render_comparison,
    render_report,
    run_many,
)

DRAFTS = [example.draft for example in ESTIMATION_EXAMPLES]


class FakeGenerator:
    """Devuelve por turnos los borradores de las referencias; la llamada `fail_on` lanza `error`."""

    def __init__(self, fail_on: int | None = None, error: Exception | None = None):
        self.fail_on = fail_on
        self.error = error
        self.calls = 0
        self.events: list[tuple[str, int]] = []

    async def __call__(self, transcription: str, scope_changes: str | None) -> DraftResult:
        self.calls += 1
        number = self.calls
        self.events.append(("empieza", number))
        await asyncio.sleep(0.01)
        self.events.append(("termina", number))
        if number == self.fail_on:
            raise self.error
        draft = DRAFTS[(number - 1) % len(DRAFTS)]
        return DraftResult(draft, "claude-haiku-5-5", "anthropic", 1_656, 0, 20_639, 9_000, 60_000)


def run_into(folder, runs=4, generator=None):
    generator = generator or FakeGenerator(fail_on=3, error=EstimationError("se cortó"))
    asyncio.run(run_many("Transcripción de prueba", runs=runs, folder=folder, generate=generator))
    return generator


def test_spread():
    spread = Spread((1_544, 2_078))
    assert spread.amplitude == pytest.approx(2_078 / 1_544 - 1)  # un 35 % más
    assert spread.cv == pytest.approx(spread.stdev / 1_811)
    assert spread.median == 1_811
    single = Spread((1_544,))
    assert single.amplitude is None and single.cv is None


def test_measure_uses_the_service_calculations():
    pricing = price_project(build_plan(DRAFTS[0]))
    metrics = measure(1, DRAFTS[0])
    assert metrics.base_hours == pricing.base_hours
    assert metrics.price == pricing.statement.price
    assert metrics.weeks == pricing.plan.duration_weeks
    assert metrics.hours_by_role == pricing.plan.base_hours_by_role
    assert metrics.open_scope_questions == tuple(DRAFTS[0].open_scope_questions)


def test_every_call_is_saved_and_the_first_goes_alone(tmp_path):
    generator = run_into(tmp_path)
    # la primera termina antes de que empiece otra: así las demás leen el prompt de la caché
    assert generator.events[:2] == [("empieza", 1), ("termina", 1)]
    saved = sorted(path.name for path in tmp_path.glob("llamada_*.json"))
    assert saved == ["llamada_01.json", "llamada_02.json", "llamada_03.json", "llamada_04.json"]
    failed = json.loads((tmp_path / "llamada_03.json").read_text(encoding="utf-8"))
    assert failed["ok"] is False and failed["error"] == "EstimationError: se cortó"
    ok = json.loads((tmp_path / "llamada_01.json").read_text(encoding="utf-8"))
    assert ok["ok"] is True and ok["draft"]["project_name"] == DRAFTS[0].project_name


def test_a_configuration_error_stops_the_run(tmp_path):
    generator = FakeGenerator(fail_on=1, error=NotImplementedError("LLM_PROVIDER=openai"))
    with pytest.raises(NotImplementedError):
        run_into(tmp_path, generator=generator)
    assert generator.calls == 1


def test_summary_and_report(tmp_path):
    run_into(tmp_path)
    summary = load_summary(tmp_path)
    # llamadas 1, 2 y 4 válidas (borradores 0, 1 y 0); la 3 falló
    expected = [measure(1, DRAFTS[0]).base_hours, measure(2, DRAFTS[1]).base_hours, measure(4, DRAFTS[0]).base_hours]
    assert summary.spread("base_hours").values == tuple(expected)
    assert [failure["run"] for failure in summary.failures] == [3]
    assert summary.attempts == 4
    assert summary.total_cost_usd == pytest.approx(3 * DraftResult(DRAFTS[0], "claude-haiku-5-5", "anthropic", 1_656, 0, 20_639, 9_000, 1).estimated_cost_usd, abs=1e-4)

    report = render_report(summary)
    assert "Llamadas válidas: 3 de 4" in report
    assert "## Cifras" in report and "## Dónde está la variación" in report
    assert "- Llamada 3: EstimationError: se cortó" in report
    for role in summary.partial_roles:
        assert f"| {role} | " in report


def test_a_draft_python_cannot_plan_counts_as_a_failure(tmp_path):
    run_into(tmp_path, runs=2, generator=FakeGenerator())
    path = tmp_path / "llamada_02.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["draft"]["phases"] = []
    path.write_text(json.dumps(record), encoding="utf-8")
    summary = load_summary(tmp_path)
    assert len(summary.metrics) == 1
    assert "Python no pudo usar el borrador" in summary.failures[0]["error"]
    assert "Hacen falta al menos dos llamadas válidas" in render_report(summary)


def test_comparison(tmp_path):
    base, change = tmp_path / "base", tmp_path / "cambio"
    for folder in (base, change):
        folder.mkdir()
        run_into(folder)
    (change / "config.json").write_text(json.dumps({"label": "inventario"}), encoding="utf-8")
    comparison = render_comparison([load_summary(base), load_summary(change)])
    assert "| | base | inventario |" in comparison
    assert "| Horas base: CV |" in comparison and "| Llamadas válidas | 3 de 4 | 3 de 4 |" in comparison


def test_run_command(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(consistency, "RESULTS_DIR", tmp_path / "resultados")
    monkeypatch.setattr(consistency, "generate_draft", FakeGenerator())
    transcription = tmp_path / "reunion.txt"
    transcription.write_text("Transcripción de prueba con suficiente texto.", encoding="utf-8")

    assert consistency.main(["run", str(transcription), "--runs", "3", "--label", "Línea base"]) == 0

    (folder,) = (tmp_path / "resultados").iterdir()
    assert folder.name.endswith("_linea-base")
    config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
    assert config["label"] == "Línea base" and config["runs"] == 3
    assert "Transcripción de prueba" not in json.dumps(config)  # solo la huella, nunca el texto
    assert len(config["transcription_fingerprint"]) == 12
    summary = json.loads((folder / "resumen.json").read_text(encoding="utf-8"))
    assert summary["validas"] == 3
    assert (folder / "informe.md").read_text(encoding="utf-8").startswith("# Consistencia: Línea base")
    assert "3 llamadas reales" in capsys.readouterr().out


def test_run_command_needs_two_calls(tmp_path, capsys):
    transcription = tmp_path / "reunion.txt"
    transcription.write_text("Transcripción", encoding="utf-8")
    assert consistency.main(["run", str(transcription), "--runs", "1"]) == 2
    assert "al menos 2 llamadas" in capsys.readouterr().err


def test_report_command_recalculates_without_calling_the_model(tmp_path, capsys):
    run_into(tmp_path)
    assert consistency.main(["report", str(tmp_path)]) == 0
    assert (tmp_path / "informe.md").exists() and (tmp_path / "resumen.json").exists()
    assert "# Consistencia:" in capsys.readouterr().out
