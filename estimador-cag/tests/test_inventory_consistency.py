"""El evaluador de consistencia del inventario, con un generador simulado."""

import asyncio
import json

from app.services.inventory_service import InventoryResult
from app.services.llm_service import CallUsage, EstimationError
from evals import consistency, inventory_consistency
from evals.consistency import run_many
from evals.inventory_consistency import (
    inventory_record,
    load_summary,
    render_comparison,
    render_report,
)

from .test_inventory import SAMPLE, inventory, requirement

WITHOUT_HRIS = inventory([requirement("cuentas_y_roles"), requirement("panel_administracion", size="M")])
CALL = CallUsage("claude-haiku-5-5", 1_000, 0, 3_000, 4_000, 30_000)


class FakeInventories:
    """Devuelve por turnos SAMPLE y WITHOUT_HRIS; la llamada `fail_on` falla."""

    def __init__(self, fail_on=None):
        self.fail_on = fail_on
        self.calls = 0

    async def __call__(self, transcription, scope_changes):
        self.calls += 1
        if self.calls == self.fail_on:
            raise EstimationError("se cortó")
        chosen = SAMPLE if self.calls % 2 else WITHOUT_HRIS
        return InventoryResult(chosen, (CALL,), scope_changes)


def run_into(folder, runs=5, generator=None):
    asyncio.run(run_many("Transcripción", runs=runs, folder=folder,
                         generate=generator or FakeInventories(fail_on=4), serialize=inventory_record))


def test_summary_compares_exact_components(tmp_path):
    run_into(tmp_path)
    summary = load_summary(tmp_path)
    assert summary.attempts == 5 and len(summary.metrics) == 4  # la 4 falló
    # SAMPLE en las llamadas 1, 3 y 5; WITHOUT_HRIS en la 2
    assert summary.presence("cuentas_y_roles") == 4
    assert summary.presence("integracion_hris") == 3
    assert summary.sizes("panel_administracion") == {"M": 1}
    assert "integracion_hris" in summary.partial_components
    assert "cuentas_y_roles" not in summary.partial_components
    assert summary.platforms == {"web": 4}


def test_report_and_comparison(tmp_path):
    run_into(tmp_path)
    report = render_report(load_summary(tmp_path))
    assert "Llamadas válidas: 4 de 5" in report
    assert "| Integración con un sistema de RR. HH. o nómina | 3 de 4 | M ×3 | 0-1 |" in report
    assert "- opcional: Requisito de lecciones_y_cuestionarios" in report
    assert "- Llamada 4: EstimationError: se cortó" in report
    assert "Encuestas a empleados" in report  # horas que puso el modelo
    assert "**Plazo pedido:** 17 semanas en 4 de 4." in report
    comparison = render_comparison([load_summary(tmp_path), load_summary(tmp_path)])
    assert "| Horas base: CV |" in comparison


def test_run_command(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(consistency, "RESULTS_DIR", tmp_path / "resultados")
    monkeypatch.setattr(inventory_consistency, "generate_inventory", FakeInventories())
    transcription = tmp_path / "reunion.txt"
    transcription.write_text("Transcripción de prueba con suficiente texto.", encoding="utf-8")

    assert inventory_consistency.main(["run", str(transcription), "--runs", "3"]) == 0

    (folder,) = (tmp_path / "resultados").iterdir()
    assert folder.name.endswith("_inventario-reunion")
    config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
    assert config["kind"] == "inventario" and "Transcripción de prueba" not in json.dumps(config)
    summary = json.loads((folder / "resumen.json").read_text(encoding="utf-8"))
    assert summary["validas"] == 3 and summary["componentes"]["cuentas_y_roles"]["llamadas"] == 3
    assert "3 inventarios" in capsys.readouterr().out


def test_inventories_saved_before_the_deadline_still_load(tmp_path):
    run_into(tmp_path, runs=2, generator=FakeInventories())
    path = tmp_path / "llamada_01.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    del record["inventory"]["deadline"]
    path.write_text(json.dumps(record), encoding="utf-8")
    assert "**Plazo pedido:** sin plazo en 1 de 2, 17 semanas en 1 de 2." in render_report(load_summary(tmp_path))
