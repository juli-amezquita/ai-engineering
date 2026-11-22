"""Punto de entrada: crea la app, registra los routers y expone /health (paso 6).

Arranque: `uv run uvicorn app.main:app --reload`, con Swagger en /docs y ReDoc en /redoc.

Decisiones:
- La configuración se carga al arrancar (lifespan), no en la primera petición: si falta la API
  key del proveedor elegido, el servidor no arranca, como promete config.py.
- Importar este módulo no carga la configuración, así que los tests pueden crear la app sin
  API key mientras no la arranquen.
- LOG_LEVEL se aplica a los logs de la aplicación (`app.*`). Las librerías solo muestran
  advertencias, para que en DEBUG el SDK del proveedor no vuelque las transcripciones al log.
- GET / redirige a /docs, para que abrir el servidor en el navegador lleve a la documentación.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.routers import estimations
from app.schemas.health import HealthResponse

APP_VERSION = "0.1.0"  # la de pyproject.toml

DESCRIPTION = """\
Estima proyectos de software a partir de la transcripción de una reunión con el cliente, con \
arquitectura **CAG** (*Cache-Augmented Generation*): las estimaciones de referencia viajan en el \
system prompt de cada llamada al LLM.

**Cómo funciona**

1. El modelo lee la transcripción con las referencias y devuelve un borrador estructurado: \
etapas, tareas con las horas de cada perfil, gastos y los textos de la propuesta. No calcula \
ninguna cifra de dinero.
2. Python comprueba que nadie pasa del 100 % de dedicación, calcula los costos, el precio y los \
márgenes, y escribe dos informes.

**La respuesta de `POST /api/v1/estimate`**

- `estimation`: el informe interno de la consultora, con costos y márgenes. Es confidencial.
- `client_proposal`: la propuesta de valor y de negocio para el cliente.
"""

TAGS = [
    {"name": "Estimaciones", "description": "Estimación, valoración y presupuesto de un proyecto"},
    {"name": "Salud", "description": "Estado del servicio"},
]

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()  # si falta la API key, el arranque se detiene aquí
    logging.basicConfig(
        level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    logging.getLogger("app").setLevel(settings.LOG_LEVEL)
    logger.info(
        "Estimador listo: entorno=%s proveedor=%s modelo=%s",
        settings.APP_ENV,
        settings.LLM_PROVIDER,
        settings.LLM_MODEL,
    )
    yield


app = FastAPI(
    title="Estimador de proyectos de software (CAG)",
    description=DESCRIPTION,
    version=APP_VERSION,
    openapi_tags=TAGS,
    lifespan=lifespan,
)
app.include_router(estimations.router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse, tags=["Salud"], summary="Estado del servicio")
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        environment=settings.APP_ENV,
        provider=settings.LLM_PROVIDER,
        model=settings.LLM_MODEL,
    )


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")
