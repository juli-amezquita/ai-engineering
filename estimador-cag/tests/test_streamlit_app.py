"""La interfaz de chat (streamlit_app.py), probada con AppTest de Streamlit y sin llamar al modelo.

El estimador se sustituye por uno falso: aquí solo se prueba lo que hace la interfaz con su
respuesta, no la estimación.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from app.services import estimation_service
from app.services.planning import NotASoftwareProjectError

APP = str(Path(__file__).resolve().parent.parent / "streamlit_app.py")
TRANSCRIPTION = (
    "Cliente: necesitamos una app móvil para que los supervisores registren las inspecciones de "
    "seguridad de las canteras, con fotos y firma, en unos cuatro meses."
)


@pytest.fixture
def calls(monkeypatch):
    """Sustituye el estimador por uno falso y guarda con qué transcripciones lo llamaron."""
    received = []

    async def fake_estimate(transcription, scope_changes=None):
        received.append(transcription)
        return SimpleNamespace(
            internal_report=f"# Informe interno {len(received)}\n\nPrecio: $263,044",
            client_proposal=f"# Propuesta {len(received)}",
        )

    monkeypatch.setattr(estimation_service, "estimate", fake_estimate)
    return received


def start() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=10)
    app.run()
    return app


def send(app: AppTest, text: str) -> AppTest:
    app.chat_input[0].set_value(text).run()
    return app


def test_muestra_la_transcripcion_y_los_dos_informes(calls):
    app = send(start(), TRANSCRIPTION)

    assert not app.exception
    assert calls == [TRANSCRIPTION]
    assert [message.name for message in app.chat_message] == ["user", "assistant"]
    assert [tab.label for tab in app.tabs] == [
        "Informe interno (confidencial)",
        "Propuesta para el cliente",
    ]
    texts = [block.value for block in app.markdown]
    assert r"# Informe interno 1" + "\n\nPrecio: \\$263,044" in texts  # el $ no se lee como LaTeX
    assert "# Propuesta 1" in texts
    assert app.text[0].value == TRANSCRIPTION


def test_solo_deja_pasar_el_html_de_los_saltos_de_linea(monkeypatch):
    """Los entregables de una etapa se separan con <br>; cualquier otro HTML se ve como texto."""
    report = (
        "> Confidencial\n\n"
        "| Etapa | Entregables |\n|---|---|\n"
        "| 1. Descubrimiento | Mapa del proceso<br>Revisión con EHS |\n"
        "| 2. Piloto | <script>alert(1)</script><img src=x onerror=alert(2)><br onclick=alert(3)> |"
    )

    async def with_html(transcription, scope_changes=None):
        return SimpleNamespace(internal_report=report, client_proposal=report)

    monkeypatch.setattr(estimation_service, "estimate", with_html)
    app = send(start(), TRANSCRIPTION)

    blocks = [block for block in app.markdown if "Etapa" in block.value]
    assert len(blocks) == 2
    for block in blocks:
        assert block.proto.allow_html
        assert block.value.startswith("> Confidencial")  # la cita del informe se mantiene
        assert "Mapa del proceso<br>Revisión con EHS" in block.value
        assert block.value.count("<") == 1  # solo el <br> de los entregables
        assert "&lt;script>" in block.value and "&lt;br onclick" in block.value


def test_el_historial_sigue_en_pantalla_despues_de_varias_estimaciones(calls):
    app = send(send(start(), TRANSCRIPTION), TRANSCRIPTION + " Y con un panel web.")

    assert len(calls) == 2
    assert [message.name for message in app.chat_message] == ["user", "assistant"] * 2
    texts = [block.value for block in app.markdown]
    assert "# Propuesta 1" in texts and "# Propuesta 2" in texts


def test_un_texto_corto_no_llama_al_modelo(calls):
    app = send(start(), "hola")

    assert calls == []
    assert "entre 50 y 200,000 caracteres" in app.error[0].value


def test_explica_que_la_transcripcion_no_es_un_proyecto(monkeypatch):
    async def not_a_project(transcription, scope_changes=None):
        raise NotASoftwareProjectError("habla de un evento, no de software")

    monkeypatch.setattr(estimation_service, "estimate", not_a_project)
    app = send(start(), TRANSCRIPTION)

    assert not app.exception
    assert "no describe un proyecto de software" in app.error[0].value


def test_sin_api_key_no_abre_el_chat(monkeypatch, calls):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    app = start()

    assert "Falta ANTHROPIC_API_KEY" in app.error[0].value
    assert len(app.chat_input) == 0
