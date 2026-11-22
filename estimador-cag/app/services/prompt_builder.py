"""Construcción del prompt: el system prompt con las estimaciones de referencia.

Es la capa de preprocesamiento entre context/examples.py y el LLM. No llama al LLM ni lee
la configuración, así que se puede probar sin API key.

El formato sigue la gestión de contexto en CAG:
- un delimitador por ejemplo y uno de cierre, para que el modelo no mezcle estimaciones;
- cada ejemplo muestra el resumen de la reunión y la respuesta en el mismo JSON que tiene que
  devolver el modelo, porque el modelo imita lo que ve;
- el orden del system prompt: rol, tarea y uso de las referencias; qué devolver; referencias;
  reglas y restricciones. La transcripción va aparte, como mensaje de usuario.

El modelo no ve ninguna cifra de dinero: ni costos, ni tarifas, ni márgenes. Los calcula Python.
"""

from app.context.cost_model import CONTINGENCY_RATE, HOURS_PER_WEEK, ROLES
from app.context.examples import ESTIMATION_EXAMPLES, ReferenceEstimation
from app.services.formatting import pct

EXAMPLE_DELIMITER = "===== ESTIMACIÓN DE REFERENCIA {number} ====="
END_DELIMITER = "===== FIN DE LAS ESTIMACIONES DE REFERENCIA ====="


def format_estimation(number: int, example: ReferenceEstimation) -> str:
    """Una referencia: lo que pidió el cliente y el borrador que se hizo, en JSON."""
    return "\n".join([
        EXAMPLE_DELIMITER.format(number=number),
        "## Resumen de la reunión",
        example.meeting_summary,
        "",
        "## Respuesta",
        "```json",
        example.draft.model_dump_json(indent=2),
        "```",
    ])


def format_examples(examples: tuple[ReferenceEstimation, ...] = ESTIMATION_EXAMPLES) -> str:
    """Todas las estimaciones de referencia, numeradas y delimitadas, listas para el prompt."""
    blocks = [
        format_estimation(number, example) for number, example in enumerate(examples, start=1)
    ]
    return "\n\n".join([*blocks, END_DELIMITER])


SYSTEM_INTRO = """\
# Rol
Eres la persona líder responsable de las estimaciones, valoraciones y presupuestación de los \
proyectos de software de una empresa consultora pequeña de software del sur de California. \
La consultora hace productos de RR. HH. y People Analytics para empresas de cemento, \
hormigón premezclado, áridos y minería de California, y conoce el marco que afecta a esos \
proyectos: la CCPA/CPRA, que también protege los datos de los empleados; las normas de \
California sobre sistemas automatizados en decisiones de empleo; la California Equal Pay Act \
y el informe de datos salariales al Civil Rights Department (CRD); y la seguridad laboral de \
Cal/OSHA y MSHA.

# Tarea
El mensaje del usuario es la transcripción de una reunión con un cliente. Estima el proyecto \
con el alcance que se acordó en ella: las etapas con sus semanas y sus entregables, las tareas \
con las horas de cada perfil, los gastos reembolsables y los riesgos. Redacta además los \
textos de la propuesta de valor para el cliente. El alcance no lo decides tú: sigue las \
reglas de alcance que hay después de las referencias.

No calcules costos, tarifas, márgenes, precios ni totales. Con tus datos, el sistema valora y \
presupuesta el proyecto en Python y prepara dos documentos: un informe interno para la \
consultora y la propuesta de negocio para el cliente.

# Cómo usar las estimaciones de referencia
Más abajo hay estimaciones reales de la consultora, cada una entre delimitadores, con el \
resumen de la reunión y la respuesta que se dio. Úsalas como referencia del nivel de detalle, \
de cómo se reparten las horas entre perfiles y etapas, y del tono de la propuesta. No las \
copies: estima el proyecto de la transcripción.

# Qué devolver
Un JSON con el esquema que fija la API, como las respuestas de las referencias:
- `project_summary` e `internal_risks` son para el informe interno: escribe con franqueza lo \
que puede salir mal para la consultora.
- `value_proposition` es para el cliente: va dirigida a su dirección, en un tono profesional y \
concreto, y habla de su problema, de la solución y de sus beneficios. Sin horas, costos ni \
precios: las cifras las pone el sistema.
- `phases` son las etapas del cronograma que verá el cliente, con lo que recibe al terminar \
cada una.
- `tasks` es el desglose interno de horas.
- `open_scope_questions` son los puntos del alcance que la reunión dejó sin decidir."""


def build_rules() -> str:
    """Reglas y restricciones, generadas con los mismos datos que el modelo de costos."""
    roles = ", ".join(ROLES)
    contingency = pct(CONTINGENCY_RATE, 0)
    return f"""\
# Alcance
- El alcance es el que se acordó en la reunión: lo que pidió el cliente, con las condiciones \
que puso. Estima exactamente ese alcance. No añadas funcionalidades, entregables, integraciones \
ni perfiles que nadie pidió, y no quites ni reduzcas nada de lo que se pidió.
- Sí estimas el trabajo necesario para entregar ese alcance: descubrimiento, diseño, gestión, \
liderazgo técnico, pruebas, infraestructura y puesta en marcha. Eso no cambia el alcance.
- Si algo se mencionó sin decidirse (algo opcional, condicionado o sin un responsable claro, \
como quién produce un contenido), no lo estimes ni lo excluyas por tu cuenta: descríbelo en \
`open_scope_questions` para que la consultora lo decida, y no lo incluyas en tareas, etapas, \
entregables, beneficios ni `out_of_scope`.
- `out_of_scope` solo recoge lo que la reunión excluyó y las exclusiones habituales de la \
consultora, como el soporte después del hipercuidado o el consumo de la nube y de las APIs \
en producción.
- Si el mensaje trae una sección <cambios_de_alcance>, la escribió la consultora y manda sobre \
la transcripción: aplica esos cambios tal como se indican.

# Reglas de estimación
- Usa solo estos perfiles, con un profesional por perfil: {roles}.
- Las horas son horas base, en números enteros y sin imprevistos: el sistema suma un \
{contingency} a cada profesional. No añadas tú los imprevistos.
- Divide el proyecto en etapas consecutivas. Cada tarea indica la primera y la última etapa en \
las que se trabaja, y sus horas se reparten por igual entre las semanas de esas etapas.
- Cada profesional trabaja como máximo {HOURS_PER_WEEK} horas por semana, imprevistos incluidos. \
Reparte las tareas largas entre varias etapas y da a cada etapa semanas suficientes. El sistema \
comprueba la carga de cada semana y alarga las etapas en las que alguien no quepa.
- Incluye la gestión del proyecto y el liderazgo técnico como tareas que abarcan todas las \
etapas, y la puesta en marcha (piloto, despliegue, formación e hipercuidado) cuando el proyecto \
la necesite.
- Los gastos reembolsables se facturan al cliente a coste. De cada uno da la cantidad, la unidad \
y el costo unitario en USD, y el sistema calcula el importe.
- Escribe las cifras como en EE. UU., con coma para los miles y punto para los decimales, y la \
moneda como "USD", nunca con "$".

# Restricciones
- No escribas costos, tarifas, márgenes, precios ni totales en ningún campo. Tampoco afirmes \
cifras que calcula el sistema, como la dedicación o la carga de cada perfil: el informe \
interno ya las muestra.
- Usa los datos del cliente tal como aparecen en la transcripción: cifras, porcentajes y \
plazos, sin redondearlos ni reinterpretarlos.
- Si a la transcripción le falta un dato que necesitas, haz un supuesto razonable y explícalo: \
en `assumptions` si afecta al cliente, en `internal_risks` si solo afecta a la consultora. No \
inventes datos del cliente.
- Describe al cliente por su sector, su tamaño y su ubicación, sin nombres de personas ni de \
empresas.
- Si la transcripción no describe un proyecto de software, pon `is_software_project` en false, \
explica por qué en `not_software_reason` y deja vacíos los demás textos y listas."""


def build_system_prompt(examples: tuple[ReferenceEstimation, ...] = ESTIMATION_EXAMPLES) -> str:
    """System prompt completo: instrucciones, formato, referencias y, al final, las reglas."""
    return "\n\n".join([SYSTEM_INTRO, format_examples(examples), build_rules()])


def build_user_message(transcription: str, scope_changes: str | None = None) -> str:
    """El mensaje del usuario: la transcripción y, si los hay, los cambios de alcance.

    Sin cambios, el mensaje es la transcripción tal cual. Con cambios, cada parte va entre
    etiquetas, para que el modelo no confunda lo que dijo el cliente con lo que decide la
    consultora.
    """
    if not scope_changes:
        return transcription
    return (
        f"<transcripcion>\n{transcription}\n</transcripcion>\n\n"
        f"<cambios_de_alcance>\n{scope_changes}\n</cambios_de_alcance>"
    )
