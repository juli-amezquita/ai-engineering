# Estimador CAG

Servicio FastAPI que estima proyectos de software a partir de la transcripción de una reunión con un cliente, con arquitectura **CAG** (*Cache-Augmented Generation*): las estimaciones de referencia de la consultora viajan en el system prompt de cada llamada al LLM.

Es el entregable de la sesión 2 del Máster en AI Engineering de LIDR. La consultora, los clientes y las cifras son ficticios: una consultora pequeña del sur de California que hace productos de RR. HH. y People Analytics para empresas de cemento, hormigón premezclado, áridos y minería.

## Cómo funciona

```
transcripción ─► LLM (system prompt: rol + 3 estimaciones de referencia + reglas)
                  │  devuelve un borrador en JSON (structured outputs), sin cifras de dinero
                  ▼
               Python ─► cronograma: nadie pasa del 100 % de dedicación
                      ─► costos, precio y márgenes (margen neto del 30 %, tope de 150 USD/h)
                      ─► informe interno + propuesta para el cliente
```

1. **El modelo estima y redacta.** Con la transcripción y las referencias, `claude-haiku-5-5` devuelve un JSON con el esquema de `app/schemas/draft.py`: etapas con sus semanas y entregables, tareas con las horas de cada perfil, gastos reembolsables, los textos de la propuesta de valor y los riesgos internos. La API garantiza que el JSON cumple el esquema.
   - **El alcance es el de la reunión.** El modelo estima exactamente lo que pidió el cliente: no añade ni quita nada.
   - **Lo que quedó sin decidir no se estima.** Lo devuelve como punto por confirmar.
   - **Solo el usuario cambia el alcance**, con el campo `scope_changes` del request.
2. **Python calcula.** Suma un 10 % de imprevistos, reparte las horas por semana y alarga las etapas en las que algún perfil pasaría de 40 horas. Después calcula el precio que deja un 30 % de utilidad neta sobre el precio, sin pasar de 150 USD/h, con el estado de resultados, la caja, el margen de negociación, la sensibilidad y los controles.
3. **Python escribe dos informes en Markdown:**
   - el **informe interno**, confidencial, con los costos, los márgenes, la línea base de seguimiento y las alertas;
   - la **propuesta para el cliente**, con la propuesta de valor, el cronograma de implementación por etapa, la inversión y la forma de pago. Cada tarifa y la línea de gastos generales ya incluyen su costo, sus imprevistos y la rentabilidad. Nunca se muestran por separado, y todo suma el precio al dólar.

## Requisitos

- Python 3.11 y [uv](https://docs.astral.sh/uv/).
- Una API key de Anthropic.

## Instalación

```bash
cd estimador-cag
uv sync
cp .env.example .env
```

Rellena `ANTHROPIC_API_KEY` en `.env`. Las demás variables tienen un valor por defecto:

| Variable | Por defecto | Para qué |
|---|---|---|
| `ANTHROPIC_API_KEY` | (obligatoria con Anthropic) | Clave del proveedor |
| `OPENAI_API_KEY` | vacía | Declarada para la sesión 3; OpenAI todavía no está implementado |
| `LLM_PROVIDER` | `anthropic` | `anthropic` u `openai` |
| `LLM_MODEL` | `claude-haiku-5-5` | Modelo del proveedor |
| `APP_ENV` | `development` | `development`, `staging` o `production` |
| `LOG_LEVEL` | `DEBUG` | Nivel de los logs de la aplicación |

El `.env` nunca entra en git. Si falta la clave del proveedor elegido, el servidor no arranca.

## Arrancar

```bash
uv run uvicorn app.main:app --reload
```

- Swagger: <http://localhost:8000/docs> (también ReDoc en `/redoc`).
- Estado del servicio: `GET /health`.

## Probar

Con la transcripción de prueba del repositorio, que describe un productor ficticio de áridos que quiere una app de incorporación y formación MSHA para sus canteras:

```bash
curl -s http://localhost:8000/health
```

```bash
python3 -c 'import json; print(json.dumps({"transcription": open("transcripciones/onboarding_seguridad_canteras.txt", encoding="utf-8").read()}))' | curl -s -X POST http://localhost:8000/api/v1/estimate -H "Content-Type: application/json" --data-binary @- -o respuesta.json
```

La llamada tarda entre 50 y 75 segundos y cuesta alrededor de 0.01 USD (menos si el system prompt ya está en la caché). Para cambiar o aclarar el alcance, añade `scope_changes` al body; manda sobre la transcripción:

```json
{"transcription": "...", "scope_changes": "Incluir la producción de los contenidos de la Parte 46 en inglés y español."}
```

Para leer los dos informes:

```bash
python3 -c 'import json; r = json.load(open("respuesta.json")); open("informe_interno.md", "w").write(r["estimation"]); open("propuesta.md", "w").write(r["client_proposal"]); print(r["summary"])'
```

### Request de `POST /api/v1/estimate`

| Campo | Qué lleva |
|---|---|
| `transcription` | La transcripción de la reunión, de 50 a 200,000 caracteres (obligatoria) |
| `scope_changes` | Cambios o aclaraciones de alcance que decide la consultora (opcional, hasta 20,000 caracteres). Mandan sobre la transcripción |

### Respuesta de `POST /api/v1/estimate`

| Campo | Qué lleva |
|---|---|
| `estimation` | El informe interno, en Markdown. Confidencial: no se envía al cliente |
| `client_proposal` | La propuesta de valor y de negocio para el cliente, en Markdown |
| `model`, `provider` | El modelo y el proveedor que respondieron |
| `summary` | Las cifras clave calculadas en Python (precio, honorarios, gastos, tarifa media, margen, caja), los ajustes al cronograma, los puntos de alcance sin decidir y las alertas |
| `usage` | Tokens de entrada, de caché escrita y leída, y de salida |
| `estimated_cost_usd` | Costo estimado de la llamada al modelo |
| `latency_ms`, `created_at` | Duración de la llamada y momento de la estimación |

| Código | Cuándo |
|---|---|
| 200 | La estimación se generó |
| 422 | La transcripción falta, mide menos de 50 o más de 200,000 caracteres, o no describe un proyecto de software |
| 500 | La API key no es válida (sin dar detalles) |
| 501 | `LLM_PROVIDER` todavía no está implementado |
| 502 | El modelo devolvió algo que no sirve como estimación, o el proveedor respondió con un error |
| 503 | El proveedor está saturado o no hay conexión |
| 504 | El proveedor tardó demasiado |

## Estructura

```
estimador-cag/
├── app/
│   ├── main.py                    # app FastAPI, /health, Swagger y carga de la configuración al arrancar
│   ├── config.py                  # variables de entorno con Pydantic BaseSettings
│   ├── routers/
│   │   └── estimations.py         # POST /api/v1/estimate y los códigos de error
│   ├── schemas/
│   │   ├── estimation.py          # request y response del endpoint
│   │   ├── draft.py               # el JSON que devuelve el modelo
│   │   └── health.py              # respuesta de /health
│   ├── services/
│   │   ├── estimation_service.py  # encadena modelo → planificación → precio → informes
│   │   ├── llm_service.py         # llamada a Anthropic con structured outputs y prompt caching
│   │   ├── prompt_builder.py      # system prompt: rol, tarea, referencias, reglas y restricciones
│   │   ├── planning.py            # valida el borrador y arma el cronograma semanal
│   │   ├── pricing.py             # costos, precio, márgenes, caja, sensibilidad y controles
│   │   ├── report_builder.py      # informe interno y propuesta al cliente
│   │   └── formatting.py          # formato de las cifras
│   └── context/
│       ├── examples.py            # las 3 estimaciones de referencia (el contexto CAG)
│       └── cost_model.py          # costos por perfil, gastos generales y política comercial
├── tests/                         # pytest: estructura, cálculos, servicio del LLM y API
├── transcripciones/               # transcripción de prueba
├── .env.example
└── pyproject.toml / uv.lock
```

## Tests y pipeline

```bash
uv run pytest
```

Los tests no usan la clave real ni llaman a la API: fijan una clave falsa, no leen el `.env` y sustituyen el cliente de Anthropic o el estimador con `app.dependency_overrides`. Comprueban:

- la estructura de carpetas, que `.env` esté ignorado y que no haya claves en el código;
- que Python reproduzca los precios del análisis de la consultora y que la propuesta sume el precio sin revelar costos ni márgenes;
- la forma de la llamada al modelo y el rechazo de respuestas cortadas, rechazadas o fuera del esquema;
- `/health`, Swagger, el endpoint, cada código de error y que el servidor no arranque sin la clave.

El workflow `.github/workflows/estimador-cag.yml` lo ejecuta en GitHub Actions en cada push a `mis-entregables` o a una rama `entregable-session-*`. Instala las dependencias exactas de `uv.lock`, pasa los tests y arranca el servidor de verdad para comprobar `/health` y `/docs`.

## Decisiones de diseño

- **`claude-haiku-5-5`** en vez del `claude-haiku-4-5` del enunciado: es más nuevo, más barato y tiene 1M de contexto.
- **Los cálculos no los hace el modelo.** Con *structured outputs*, el modelo solo estima horas y redacta; Python valida y calcula, así que las cifras siempre cuadran.
- **Contexto sin dinero.** El system prompt no lleva tarifas, costos, márgenes ni ubicaciones: el modelo no los necesita y así no pueden llegar a la propuesta.
- **Prompt caching** en el system prompt (unos 20,600 tokens): las llamadas siguientes pagan la entrada a una décima parte.
- **`AsyncAnthropic`** con `await`, para no bloquear el event loop de FastAPI.
- **El cliente y la configuración se cargan tarde:** importar la app no necesita clave, pero el servidor no arranca sin ella.
- **Logs:** `LOG_LEVEL` solo afecta a la aplicación; las librerías solo muestran advertencias, para que las transcripciones, con datos de empleados, no acaben en el log.

## Limitaciones conocidas

- **Variabilidad:** la misma transcripción dio entre 1,544 y 2,078 horas base en cuatro llamadas reales (de 231,801 a 335,903 USD). Con las reglas de alcance, los puntos claramente abiertos (la formación de contratistas y quién produce los contenidos) se marcan por confirmar en todas las llamadas. Pero las horas de cada tarea siguen variando, y un punto límite, como desplegar en todas las canteras después del piloto, se marca en una llamada y no en otra. `claude-haiku-5-5` no permite bajar la `temperature`.
- **Revisión humana:** la propuesta debe revisarse antes de enviarse. El modelo puede leer mal un dato de la transcripción.
- **OpenAI** está declarado en la configuración, pero no implementado: llega con el wrapper multiproveedor de la sesión 3.
