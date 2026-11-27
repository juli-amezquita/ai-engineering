# Estimador CAG

Servicio FastAPI que estima proyectos de software a partir de la transcripción de una reunión con un cliente, con arquitectura **CAG** (*Cache-Augmented Generation*): el catálogo de componentes y las estimaciones de referencia de la consultora viajan en el system prompt de cada llamada al LLM.

Es el entregable de la sesión 2 del Máster en AI Engineering de LIDR, con la interfaz de chat de la sesión 3 en curso. La consultora, los clientes y las cifras son ficticios: una consultora pequeña del sur de California que hace productos de RR. HH. y People Analytics para empresas de cemento, hormigón premezclado, áridos y minería.

## Cómo funciona

```
transcripción ─► LLM 1 (system prompt: reglas + catálogo de componentes, sin horas)
                  │  devuelve el inventario de alcance: requisitos, estado, componente, tamaño y plazo
                  ▼
               Python ─► horas de cada partida con el catálogo y el plazo en semanas
                  │
transcripción ─► LLM 2 (system prompt: rol + 3 estimaciones de referencia + reglas)
 + inventario     │  devuelve el plan: etapas, en qué etapas va cada partida y los textos
                  ▼
               Python ─► borrador: las partidas con las horas del catálogo
                      ─► cronograma: en el plazo del cliente y sin pasar del 100 % de dedicación
                      ─► costos, precio y márgenes (margen neto del 30 %, tope de 150 USD/h)
                      ─► informe interno + propuesta para el cliente
```

1. **El modelo hace el inventario de alcance.** Con la transcripción y el catálogo, `claude-haiku-5-5` devuelve cada requisito con su estado (acordado, opcional, condicionado o excluido), la frase de la reunión que lo respalda, el componente del catálogo que lo cubre y su tamaño, la plataforma, las decisiones que quedaron abiertas y el plazo que pidió el cliente, con la cantidad y la unidad que dijo (`app/schemas/inventory.py`). La API garantiza que el JSON cumple el esquema.
   - **El alcance es el de la reunión.** Solo se estima lo acordado: no se añade ni se quita nada.
   - **Lo que quedó sin decidir no se estima.** Los requisitos opcionales o condicionados salen como puntos por confirmar.
   - **Solo el usuario cambia el alcance**, con el campo `scope_changes` del request.
2. **Python pone las horas y el plazo.** Pasa el plazo a semanas («en unos cuatro meses» son 17) y calcula las horas de cada partida con el catálogo (`app/context/catalog.py`), según el componente, el tamaño, la cantidad y la plataforma. El modelo solo pone horas a lo que el catálogo no cubre, y esas partidas quedan marcadas para revisarlas. Si el modelo deja alguna sin horas, una llamada corta pide solo esas horas; si aun así faltan, la estimación falla con un 502 en vez de salir incompleta (ver **Inventario de alcance y catálogo de horas**).
3. **El modelo organiza el proyecto y redacta.** En una segunda llamada recibe la transcripción y el inventario con las partidas numeradas y sus horas, y devuelve el plan (`app/schemas/plan.py`): las etapas con sus semanas, que suman el plazo del cliente si pidió uno, y sus entregables, en qué etapas se trabaja cada partida, los gastos reembolsables, los textos de la propuesta de valor y los riesgos internos. El esquema del plan no tiene horas, así que no las puede cambiar.
4. **Python calcula.** Une el inventario y el plan en el borrador de la estimación. Si las etapas no suman el plazo del cliente, las ajusta en la misma proporción. Suma un 10 % de imprevistos, reparte las horas por semana y alarga las etapas en las que algún perfil pasaría de 40 horas, aunque eso pase del plazo: el informe lo avisa (ver **El plazo del cliente**). Después calcula el precio que deja un 30 % de utilidad neta sobre el precio, sin pasar de 150 USD/h, con el estado de resultados, la caja, el margen de negociación, la sensibilidad y los controles.
5. **Python escribe dos informes en Markdown:**
   - el **informe interno**, confidencial, con los costos, los márgenes, la línea base de seguimiento, las alertas y de dónde sale cada hora;
   - la **propuesta para el cliente**, con la propuesta de valor, el cronograma de implementación por etapa, la inversión y la forma de pago. Cada tarifa y la línea de gastos generales ya incluyen su costo, sus imprevistos y la rentabilidad. Nunca se muestran por separado, y todo suma el precio al dólar.

## Requisitos

- Git, Python 3.11 y [uv](https://docs.astral.sh/uv/).
- Una API key de Anthropic.

## Instalación

Esta versión está en la rama `entregable-session-3`. Un `git clone` sin rama descarga `mis-entregables`, que tiene la última versión ya entregada y no la de esta sesión. Descarga directamente la rama:

```bash
git clone -b entregable-session-3 https://github.com/juli-amezquita/ai-engineering.git
cd ai-engineering/estimador-cag
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
| `LLM_TIMEOUT_SECONDS` | `180` | Segundos sin recibir datos del proveedor antes de dar la llamada por colgada y responder 504 |
| `APP_ENV` | `development` | `development`, `staging` o `production` |
| `LOG_LEVEL` | `DEBUG` | Nivel de los logs de la aplicación |

El `.env` nunca entra en git. Si falta la clave del proveedor elegido, el servidor no arranca.

## Arrancar

```bash
uv run uvicorn app.main:app --reload
```

- Swagger: <http://localhost:8000/docs> (también ReDoc en `/redoc`).
- Estado del servicio: `GET /health`.

## Interfaz de chat (sesión 3)

```bash
uv run streamlit run streamlit_app.py
```

Se abre en <http://localhost:8501>. Pega la transcripción de la reunión en el chat: en alrededor de un minuto, la respuesta trae dos pestañas, el informe interno y la propuesta para el cliente. Cada mensaje es una estimación nueva e independiente, y las anteriores siguen en pantalla hasta que se recarga la página. Mientras se estima, la caja de texto se desactiva.

No hace falta arrancar FastAPI: la interfaz llama al mismo servicio que el endpoint, así que el system prompt, el catálogo, las referencias y los cálculos son los mismos, y lee la API key del mismo `.env`. Valida la transcripción con las mismas reglas (de 50 a 200,000 caracteres) y explica los errores en el chat.

`.streamlit/config.toml` hace que la interfaz escuche solo en `localhost`, para que nadie de la red local la use con tu API key, y desactiva las estadísticas de uso de Streamlit.

## Probar

Sin API key puedes ver la salida de una llamada real en [`ejemplos-de-salida/`](ejemplos-de-salida/): la respuesta completa, el informe interno y la propuesta para el cliente.

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
| `summary` | Las cifras clave calculadas en Python (precio, honorarios, gastos, tarifa media, margen, caja), las semanas del cronograma y las que pidió el cliente (`requested_weeks`), los ajustes al cronograma, los puntos de alcance sin decidir, las alertas y las horas que puso el modelo, que hay que revisar (`review_hours` y `review_items`) |
| `usage` | Tokens de entrada, de caché escrita y leída, y de salida, sumando todas las llamadas |
| `estimated_cost_usd` | Costo estimado de todas las llamadas al modelo |
| `latency_ms`, `created_at` | Duración de todas las llamadas y momento de la estimación |

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
│   │   ├── draft.py               # el borrador de la estimación, con tareas y horas
│   │   ├── inventory.py           # el inventario de alcance: requisitos, componentes y tamaños
│   │   ├── plan.py                # el plan de la segunda llamada: etapas y partidas, sin horas
│   │   └── health.py              # respuesta de /health
│   ├── services/
│   │   ├── estimation_service.py  # encadena modelo → planificación → precio → informes
│   │   ├── llm_service.py         # llamada a Anthropic con structured outputs y prompt caching
│   │   ├── inventory_service.py   # primera llamada: el inventario de alcance
│   │   ├── inventory_prompt.py    # system prompt del inventario: reglas y catálogo sin horas
│   │   ├── catalog_hours.py       # las horas del inventario, calculadas con el catálogo
│   │   ├── plan_service.py        # segunda llamada: el plan, y la unión con el inventario
│   │   ├── plan_prompt.py         # system prompt del plan y el inventario en el mensaje
│   │   ├── prompt_builder.py      # system prompt de la estimación en una sola llamada (línea base)
│   │   ├── planning.py            # valida el borrador y arma el cronograma semanal
│   │   ├── pricing.py             # costos, precio, márgenes, caja, sensibilidad y controles
│   │   ├── report_builder.py      # informe interno y propuesta al cliente
│   │   └── formatting.py          # formato de las cifras
│   └── context/
│       ├── examples.py            # las 3 estimaciones de referencia (el contexto CAG)
│       ├── catalog.py             # catálogo de componentes: la fuente de verdad de las horas
│       └── cost_model.py          # costos por perfil, gastos generales y política comercial
├── evals/
│   ├── consistency.py             # evaluador de consistencia: la misma transcripción varias veces
│   └── inventory_consistency.py   # lo mismo para el inventario: componentes y horas del catálogo
├── tests/                         # pytest: estructura, cálculos, servicio del LLM, API, evaluador e interfaz
├── transcripciones/               # transcripción de prueba
├── ejemplos-de-salida/            # respuesta, informe interno y propuesta de una llamada real
├── streamlit_app.py               # interfaz de chat (sesión 3)
├── .streamlit/config.toml         # la interfaz solo escucha en localhost y sin estadísticas de uso
├── .env.example
└── pyproject.toml / uv.lock
```

## Evaluador de consistencia

El modelo no da siempre la misma estimación para la misma reunión (ver **Limitaciones conocidas**). El evaluador mide cuánto cambia: manda la misma transcripción varias veces al modelo real, calcula cada borrador con el mismo código del servicio y compara las horas base, el precio, las semanas frente al plazo que pidió el cliente, las horas de cada perfil y los puntos de alcance que quedan por confirmar.

Mide los dos recorridos con `--pipeline`: `inventario` (por defecto) es el del servicio, con las dos llamadas; `directo` es la estimación en una sola llamada, con las horas del modelo, que se mantiene como línea base.

Sirve para juzgar un cambio del prompt, de los ejemplos o del preprocesamiento con números: se mide una línea base, se hace el cambio y se vuelve a medir con la misma transcripción.

```bash
uv run python -m evals.consistency run transcripciones/onboarding_seguridad_canteras.txt --runs 10 --label con-inventario
uv run python -m evals.consistency run transcripciones/onboarding_seguridad_canteras.txt --runs 5 --pipeline directo --label linea-base
```

Usa la API key del `.env` y cuesta dinero, unos 0.01 USD y entre uno y dos minutos por estimación, así que no corre en los tests ni en el pipeline. La primera llamada va sola, para que las demás lean el system prompt de la caché, y las demás van en paralelo (`--concurrency`, 4 por defecto). Con `--scope-changes archivo.txt` se mide con cambios de alcance.

Cada ejecución queda en `evals/resultados/<fecha>_<etiqueta>/`:

| Archivo | Qué lleva |
|---|---|
| `llamada_NN.json` | El borrador, el inventario si lo hubo, los tokens, el costo y la latencia de cada llamada, o el error si falló |
| `config.json` | El recorrido, el modelo, el commit, una huella de los system prompts y una huella de la transcripción (nunca su texto) |
| `informe.md` | Media, mediana, mínimo, máximo, amplitud y coeficiente de variación de cada cifra; las horas de cada perfil, de más a menos variación; cada llamada y sus puntos por confirmar |
| `resumen.json` | Las mismas cifras, para guardarlas o compararlas |

Para recalcular el informe con los borradores guardados, sin llamar al modelo, o comparar dos ejecuciones lado a lado:

```bash
uv run python -m evals.consistency report evals/resultados/<línea base> evals/resultados/<con el cambio>
```

## Inventario de alcance y catálogo de horas

Es la respuesta a la variabilidad: el modelo deja de poner horas, igual que ya no calcula dinero. En la primera llamada, el modelo lee la reunión y devuelve el inventario de alcance: cada requisito con su estado (acordado, opcional, condicionado o excluido), la frase de la reunión que lo respalda, el componente del catálogo que lo cubre y su tamaño (S, M o L), la plataforma y las decisiones que quedaron abiertas. Después Python calcula las horas con el catálogo (`app/context/catalog.py`).

El catálogo sigue el método por analogía de la guía de costos de la GAO (GAO-20-195G): cada componente dice de qué fuente salen sus horas y qué es una convención propia.

- Las horas base son las de una primera versión web e incluyen diseño, desarrollo y pruebas (Innovation Insight, octubre de 2026). Esa misma fuente da las reglas para el producto completo (×3), la app móvil (×1.2), web y móvil (×1.35) y el 35 % de gestión, QA y lanzamiento.
- Las integraciones con sistemas de RR. HH. salen de Truto, Kombo e Integrate.io; el descubrimiento y el acompañamiento después del lanzamiento, de UpBusinessCo.
- El reparto entre perfiles sale de los datos propios de la consultora, sus tres estimaciones de referencia: en web construyen backend y frontend, como en la referencia 1; en móvil, backend y móvil, como en la referencia 2; y el 35 % se reparte entre gestión, liderazgo técnico, QA y DevOps con el peso medio que tienen en las tres. Las pruebas de cada funcionalidad las hace quien la construye, y el QA independiente está en el 35 %. Dentro de cada componente, las horas se reparten con las fases del ISBSG.
- El tamaño M es el punto medio entre S y L, por convención.
- Los componentes sin datos públicos de horas, como las encuestas o la analítica con historial, los estima el modelo, y el informe los marca para revisarlos.

El modelo no ve las horas del catálogo: solo clasifica. Si el inventario no cambia, las horas tampoco.

Los componentes sin referencia tienen que llevar horas del modelo, y a veces el modelo deja esa lista vacía. El esquema no puede exigir que tenga elementos, porque *structured outputs* no admite esa restricción, así que lo comprueba Python. Si a un requisito acordado le faltan horas, una segunda llamada, corta, recibe la transcripción y solo esos requisitos, y devuelve sus horas por perfil. Si siguen faltando, el inventario lanza un error y el endpoint responde 502.

El inventario alimenta la estimación del endpoint (ver **Cómo funciona**), y el informe interno dice de dónde sale cada hora: el catálogo, con su fuente, o el modelo, marcada «a revisar». El evaluador del inventario lo mide por separado y compara listas exactas de componentes y tamaños entre llamadas:

```bash
uv run python -m evals.inventory_consistency run transcripciones/onboarding_seguridad_canteras.txt --runs 10 --label inventario-v1
```

Cuesta menos de 0.01 USD por llamada y guarda los resultados igual que el otro evaluador.

## El plazo del cliente

Con las horas fijas del catálogo, lo que más variaba entre estimaciones eran las semanas: el modelo proponía etapas distintas en cada llamada, de 13 a 20 semanas, aunque el cliente había pedido el producto «en unos cuatro meses». La regla del plazo reparte el trabajo así:

1. **El modelo lee el plazo** en el inventario, con la cantidad y la unidad que dijo el cliente (4 meses) y la frase que lo respalda. Si la reunión no fija un plazo, o da una fecha sin decir cuándo empieza el proyecto, lo deja vacío.
2. **Python lo pasa a semanas**, con 30.44 días por mes: 4 meses son 17 semanas.
3. **El modelo organiza las etapas para que sumen ese plazo.** Si no lo suman, Python las ajusta en la misma proporción, con el redondeo por el mayor resto y al menos una semana por etapa.
4. **Python comprueba la carga de cada semana**, como antes. Si alguien no cabe, alarga la etapa, aunque eso pase del plazo, y los controles del informe lo avisan. Si al apretar las etapas el cronograma termina más tarde que el que propuso el modelo, Python se queda con el del modelo, porque el alargue va etapa por etapa y con las etapas apretadas puede alargar de más.

El informe interno dice en el cronograma qué plazo pidió el cliente, si Python ajustó las etapas y si el cronograma lo cumple. El endpoint devuelve el plazo en `summary.requested_weeks`.

En diez estimaciones reales (`evals/resultados/2026-11-25_133236_estimacion-con-plazo`), el modelo leyó el mismo plazo en las diez y propuso etapas que sumaban exactamente 17 semanas, así que Python no tuvo que ajustar ni alargar ninguna. Las semanas dejaron de variar:

| | Línea base, una llamada | Reparto calibrado | Con la regla del plazo |
|---|---:|---:|---:|
| Semanas | 16 a 17 (CV 3 %) | 13 a 23 (CV 15 %) | 17 en las diez (CV 0 %) |
| Horas base, mediana | 1,848 (CV 11 %) | 1,826 (CV 5 %) | 1,792 (CV 6 %) |
| Precio mediano (USD) | 278,681 (CV 7 %) | 266,722 (CV 5 %) | 263,044 (CV 6 %) |

## Tests y pipeline

```bash
uv run pytest
```

Los tests no usan la clave real ni llaman a la API: fijan una clave falsa, no leen el `.env` y sustituyen el cliente de Anthropic o el estimador con `app.dependency_overrides`. Comprueban:

- la estructura de carpetas, que `.env` esté ignorado y que no haya claves en el código;
- que Python reproduzca los precios del análisis de la consultora y que la propuesta sume el precio sin revelar costos ni márgenes;
- la forma de la llamada al modelo, su tiempo de espera, el reintento cuando la respuesta deja de llegar y el rechazo de respuestas cortadas, rechazadas o fuera del esquema;
- `/health`, Swagger, el endpoint, cada código de error, también el 504 cuando la respuesta deja de llegar dos veces, y que el servidor no arranque sin la clave;
- el inventario y las horas del catálogo, la llamada que completa las horas que faltan y el error si siguen faltando, y la unión del inventario con el plan: cada partida en sus etapas, la gestión y el QA en todas, y el rechazo de un plan que deja partidas fuera;
- el plazo: el paso de meses a semanas, el ajuste de las etapas, el aviso cuando el equipo no cabe y que apretar las etapas nunca dé un cronograma más largo que el del modelo;
- los evaluadores de consistencia, con un generador simulado en lugar del modelo;
- la interfaz de chat, con `AppTest` de Streamlit y un estimador simulado: los dos informes, que del HTML del informe solo pasen los `<br>` del cronograma, el historial después de varias estimaciones, que un texto corto no llegue al modelo, el mensaje cuando la transcripción no es un proyecto y que sin clave no se abra el chat.

El workflow `.github/workflows/estimador-cag.yml` lo ejecuta en GitHub Actions en cada push a `mis-entregables` o a una rama `entregable-session-*`. Instala las dependencias exactas de `uv.lock`, pasa los tests y arranca el servidor de verdad para comprobar `/health` y `/docs`.

## Decisiones de diseño

- **`claude-haiku-5-5`** en vez del `claude-haiku-4-5` del enunciado: es más nuevo, más barato y tiene 1M de contexto.
- **Los cálculos no los hace el modelo.** Con *structured outputs*, el modelo clasifica el alcance, organiza las etapas y redacta; las horas salen del catálogo y Python valida y calcula, así que las cifras siempre cuadran.
- **Dos llamadas en vez de una.** Clasificar el alcance y organizar el proyecto son tareas distintas, y separarlas deja ver qué varía en cada una. Cuesta una llamada más y algo más de latencia. La estimación en una sola llamada sigue en `llm_service.generate_draft`, como línea base del evaluador.
- **El plazo del cliente fija la duración.** Si la reunión da un plazo, el cronograma dura ese plazo: es la fecha que el cliente necesita, y repartir el trabajo en todo el plazo deja más holgura que terminar antes con más carga por semana. El modelo lee el plazo tal como lo dijo el cliente y Python lo pasa a semanas, igual que con las horas. El plazo nunca se cumple a costa de sobrecargar a alguien: si el equipo no cabe, el cronograma se alarga y el informe lo avisa.
- **Contexto sin dinero.** El system prompt no lleva tarifas, costos, márgenes ni ubicaciones: el modelo no los necesita y así no pueden llegar a la propuesta.
- **Prompt caching** en los dos system prompts (unos 7,200 tokens el del inventario y 18,500 el del plan): las llamadas siguientes pagan esa entrada a una décima parte.
- **`AsyncAnthropic`** con `await`, para no bloquear el event loop de FastAPI.
- **La interfaz de chat importa el servicio en vez de llamar al endpoint.** Basta un `streamlit run`, y el system prompt es el del endpoint por construcción. Es además lo que pide el ejercicio de la sesión 3: conectar Streamlit sin wrapper, para ver el acoplamiento antes de resolverlo. El servicio es asíncrono y Streamlit no, así que cada estimación corre con `asyncio.run`. La interfaz no tiene lógica de negocio: cuando exista un endpoint con streaming, podrá consumirlo, y cambiarla por otra solo tocará `streamlit_app.py`.
- **Tres minutos sin datos y la llamada se da por colgada.** El SDK espera 600 segundos sin recibir datos, y en una tanda del evaluador cuatro de diez llamadas tardaron 10 minutos en fallar (`evals/resultados/2026-11-25_131801_estimacion-con-plazo`). El tiempo de espera tampoco puede ser corto, porque mientras el modelo piensa la API no envía nada: en una estimación medida, ese silencio duró 23 y 25 segundos, y en la llamada más larga de las tandas (16,700 tokens en 68 segundos) rondaría el minuto. Con 180 segundos (`LLM_TIMEOUT_SECONDS`), una llamada colgada falla a los 3 minutos y cabe incluso una respuesta que gaste pensando los 32,000 tokens de `max_tokens`. Si la respuesta deja de llegar a mitad, el SDK no la reintenta y deja pasar el error de su librería HTTP. Por eso `llm_service` repite la llamada una vez, y si vuelve a colgarse, convierte el error en el de tiempo de espera del SDK para que el endpoint responda 504 y no 500. En la tanda en la que se colgaron cuatro de diez llamadas, las cuatro ya habían empezado a responder: es justo el caso que el SDK no cubre. Cada llamada registra cuántas veces se repitió (`retries`), y el evaluador lo guarda con el resto de la llamada.
- **El cliente y la configuración se cargan tarde:** importar la app no necesita clave, pero el servidor no arranca sin ella.
- **Logs:** `LOG_LEVEL` solo afecta a la aplicación; las librerías solo muestran advertencias, para que las transcripciones, con datos de empleados, no acaben en el log.

## Limitaciones conocidas

- **Variabilidad:** con el inventario, el catálogo y la regla del plazo, la misma transcripción dio entre 1,725 y 2,077 horas base en diez estimaciones reales (CV del 6 %), frente a 1,640 a 2,200 en la línea base de una sola llamada (CV del 11 %), y 17 semanas en las diez. Lo que todavía varía es la lectura del alcance, sobre todo los tamaños: la estimación más cara, de 311,052 USD, es la única que clasificó el asistente sobre documentos como L, y las cuentas y roles salen como S en unas llamadas y como M en otras. Y en 3 de las 10, el plan llama «piloto» a una etapa aunque el inventario deja el piloto sin acordar. `claude-haiku-5-5` no permite bajar la `temperature`.
- **Un plazo largo estira el cronograma:** si el cliente da mucho más plazo del que hace falta, el cronograma dura ese plazo con menos horas por semana. El informe lo deja ver en la dedicación media de cada perfil, pero no lo avisa.
- **Una llamada colgada alarga la estimación:** con el reintento, cada llamada que se cuelga suma 3 minutos de espera, y si se cuelga dos veces seguidas el endpoint responde 504 a los 6 minutos. El intento cortado no devuelve el uso de tokens, así que su costo no entra en `estimated_cost_usd`.
- **El reparto entre perfiles mueve el precio:** con la primera versión del catálogo, que daba casi toda la construcción y las pruebas a full-stack y QA de Latinoamérica, el precio mediano bajó a 221,882 USD con las mismas horas. Con el reparto calibrado con las referencias de la consultora quedó en 266,722 USD, un 4 % por debajo de la línea base de una sola llamada (278,681 USD). Quedan dos diferencias con las referencias: el diseño pesa un 13 % de las horas, frente al 3 a 9 % de las referencias, y la gestión de proyecto un 6 %, frente al 7 a 9 %.
- **Revisión humana:** la propuesta debe revisarse antes de enviarse. El modelo puede leer mal un dato de la transcripción.
- **OpenAI** está declarado en la configuración, pero no implementado: llega con el wrapper multiproveedor de la sesión 3.
