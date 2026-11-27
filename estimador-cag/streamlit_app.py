"""Interfaz de chat del estimador (sesión 3, nivel 1).

Arranque, desde `estimador-cag/`: `uv run streamlit run streamlit_app.py`.

Es solo la capa de presentación. Se pega la transcripción, la interfaz llama al mismo servicio que
usa el endpoint (`estimation_service.estimate`) y muestra los dos informes. Por eso el system
prompt, el catálogo de horas, las estimaciones de referencia y los cálculos son los del endpoint
por construcción, y la API key se lee del `.env` con `config.py`, igual que en FastAPI.

Decisiones:
- Cada mensaje es una transcripción nueva y una estimación independiente. El historial se ve en
  pantalla, pero no se reenvía al modelo: el estimador es single-turn.
- La transcripción se valida con `EstimateRequest`, el mismo esquema del endpoint.
- El servicio es asíncrono y el script de Streamlit no: cada estimación corre con `asyncio.run`.
- Una estimación tarda alrededor de un minuto. Mientras tanto, la caja de texto se desactiva
  para que un segundo mensaje no interrumpa la llamada en curso.
- Los errores se explican en el chat con el mismo criterio que los códigos HTTP del endpoint.
"""

import asyncio
import logging

import anthropic
import streamlit as st
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.estimation import EstimateRequest
from app.services.estimation_service import estimate
from app.services.llm_service import EstimationError
from app.services.planning import InvalidDraftError, NotASoftwareProjectError

logger = logging.getLogger("app.streamlit")

SATURATED = (
    anthropic.RateLimitError,
    anthropic.OverloadedError,
    anthropic.ServiceUnavailableError,
)
REJECTED_KEY = (anthropic.AuthenticationError, anthropic.PermissionDeniedError)


def error_message(error: Exception) -> str:
    """Traduce un fallo de la estimación a un mensaje para el chat. Lo inesperado se relanza."""
    if isinstance(error, NotASoftwareProjectError):
        return f"La transcripción no describe un proyecto de software: {error}"
    if isinstance(error, (EstimationError, InvalidDraftError)):
        return f"El modelo devolvió algo que no sirve como estimación. Inténtalo de nuevo. ({error})"
    if isinstance(error, NotImplementedError):
        return str(error)
    if isinstance(error, REJECTED_KEY):
        return "El proveedor rechazó la API key. Revisa ANTHROPIC_API_KEY en el archivo .env."
    if isinstance(error, SATURATED):
        return "El proveedor del LLM está saturado. Inténtalo de nuevo en unos minutos."
    if isinstance(error, anthropic.APITimeoutError):  # antes que APIConnectionError, su clase madre
        return "El proveedor del LLM tardó demasiado en responder."
    if isinstance(error, anthropic.APIConnectionError):
        return "No se pudo conectar con el proveedor del LLM."
    if isinstance(error, anthropic.APIStatusError):
        return f"El proveedor del LLM respondió con un error ({error.status_code})."
    raise error


def estimate_reply(transcription: str) -> dict:
    """Valida la transcripción, pide la estimación y devuelve el mensaje del asistente."""
    try:
        request = EstimateRequest(transcription=transcription)
    except ValidationError:
        return {"kind": "error", "text": "La transcripción debe tener entre 50 y 200,000 caracteres."}
    try:
        with st.spinner("Estimando. Tarda alrededor de un minuto…"):
            result = asyncio.run(estimate(request.transcription))
    except Exception as error:
        logger.warning("La estimación falló: %s", type(error).__name__)
        return {"kind": "error", "text": error_message(error)}
    return {
        "kind": "estimation",
        "internal_report": result.internal_report,
        "client_proposal": result.client_proposal,
    }


def markdown(text: str) -> str:
    """Prepara un informe para `st.markdown(..., unsafe_allow_html=True)`.

    - En las tablas, los entregables de cada etapa van separados por `<br>`, y Streamlit solo lo
      convierte en salto de línea si se le permite HTML. Pero el texto del informe sale del modelo
      a partir de la transcripción, así que antes se escapa todo `<`: el único HTML que pasa es
      `<br>`. El `>` no se escapa porque abre las citas del informe, y sin `<` no hay etiqueta.
    - Streamlit lee `$...$` como LaTeX; un signo de dólar en un informe debe verse tal cual.
    """
    text = text.replace("<", "&lt;").replace("&lt;br>", "<br>")
    return text.replace("$", r"\$")


def show(message: dict) -> None:
    if message["kind"] == "transcription":
        words = len(message["text"].split())
        with st.expander(f"Transcripción · {words:,} palabras"):
            st.text(message["text"])
    elif message["kind"] == "error":
        st.error(message["text"])
    else:
        internal, proposal = st.tabs(["Informe interno (confidencial)", "Propuesta para el cliente"])
        with internal:
            st.markdown(markdown(message["internal_report"]), unsafe_allow_html=True)
        with proposal:
            st.markdown(markdown(message["client_proposal"]), unsafe_allow_html=True)


st.set_page_config(page_title="Estimador de software", layout="wide")
st.title("Estimador de proyectos de software")
st.caption(
    "Pega la transcripción de la reunión con el cliente. Recibes el informe interno, "
    "con costos y márgenes, y la propuesta para el cliente."
)

try:
    get_settings()  # si falta la API key, la interfaz no se abre, como el servidor
except ValidationError as error:
    st.error(error.errors()[0]["msg"].removeprefix("Value error, "))
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        show(message)

transcription = st.chat_input(
    "Pega aquí la transcripción de la reunión", max_chars=200_000, submit_mode="disable"
)
if transcription:
    question = {"role": "user", "kind": "transcription", "text": transcription}
    st.session_state.messages.append(question)
    with st.chat_message("user"):
        show(question)
    with st.chat_message("assistant"):
        answer = {"role": "assistant", **estimate_reply(transcription)}
        show(answer)
    st.session_state.messages.append(answer)
