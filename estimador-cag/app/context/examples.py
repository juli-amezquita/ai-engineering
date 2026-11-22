"""Estimaciones de referencia: el conocimiento que se inyecta en cada llamada al LLM (CAG).

Son tres proyectos ficticios de RR. HH. y People Analytics para empresas de cemento,
hormigón premezclado, áridos y minería de California. Son de tipos distintos para que el
modelo vea variedad sin redundancia: una plataforma web con IA, una app móvil y una
integración de datos interna.

Cada referencia tiene dos partes:
- lo que pidió el cliente en la reunión;
- el borrador que se hizo con esa reunión (`EstimationDraft`), el mismo formato que tiene que
  devolver el modelo: etapas, tareas con las horas base de cada perfil, gastos reembolsables,
  textos de la propuesta de valor y riesgos internos.

Las referencias no llevan tarifas, costos ni precios: los calcula Python con el modelo de
costos (app/context/cost_model.py). Con sus horas, Python reproduce los precios del análisis
v6 del vault: 366,797, 265,951 y 272,637 USD.

El texto que llega al prompt lo genera app/services/prompt_builder.py.
"""

from dataclasses import dataclass

from app.schemas.draft import EstimationDraft, Expense, Phase, RoleHours, Task, ValueProposition

IRS_MILEAGE_RATE_USD = 0.725  # tarifa de kilometraje del IRS, USD por milla


def _task(name: str, first_phase: int, last_phase: int, hours: dict[str, int]) -> Task:
    return Task(
        name=name,
        first_phase=first_phase,
        last_phase=last_phase,
        hours=[RoleHours(role=role, hours=role_hours) for role, role_hours in hours.items()],
    )


def _phase(name: str, weeks: int, *deliverables: str) -> Phase:
    return Phase(name=name, weeks=weeks, deliverables=list(deliverables))


def _expense(description: str, quantity: float, unit: str, unit_cost_usd: float) -> Expense:
    return Expense(description=description, quantity=quantity, unit=unit, unit_cost_usd=unit_cost_usd)


@dataclass(frozen=True)
class ReferenceEstimation:
    """Una estimación pasada: lo que pidió el cliente y el borrador que se hizo con eso."""

    meeting_summary: str
    draft: EstimationDraft


ESTIMATION_EXAMPLES: tuple[ReferenceEstimation, ...] = (
    ReferenceEstimation(
        meeting_summary=(
            "Un productor de cemento y áridos con unas 800 personas en dos plantas de cemento y "
            "cuatro canteras de California quiere cubrir sus puestos críticos con talento interno "
            "antes de contratar fuera: en los próximos cinco años se jubila buena parte de sus "
            "operadores de horno y técnicos de mantenimiento. Hoy las habilidades y certificaciones "
            "están repartidas entre el sistema de formación, las órdenes de trabajo de mantenimiento "
            "y la memoria de los supervisores, y RR. HH. tarda semanas en encontrar a alguien con un "
            "perfil concreto. Piden una plataforma que construya el perfil de habilidades de cada "
            "persona a partir de su formación, sus certificaciones y su historial de trabajo, que "
            "cada empleado pueda revisar y corregir, y un buscador de candidatos internos para un "
            "puesto. Dirección quiere además ver qué habilidades faltan por planta para orientar la "
            "formación. Usan Microsoft 365 y su HRIS tiene API."
        ),
        draft=EstimationDraft(
            is_software_project=True,
            not_software_reason="",
            project_name="Plataforma de inteligencia de habilidades para movilidad interna",
            project_type="Plataforma web SaaS con IA",
            project_summary=(
                "Plataforma web, usable en tablet en planta, que extrae habilidades y certificaciones "
                "de los registros de formación y de las órdenes de trabajo con un LLM, las mapea a la "
                "taxonomía O*NET del Departamento de Trabajo de EE. UU. y permite buscar candidatos "
                "internos para puestos críticos. Cada persona valida su perfil, RR. HH. ve las brechas "
                "por planta y el buscador se prueba contra sesgos. Termina con un piloto en una planta, "
                "el despliegue a toda la plantilla y dos semanas de hipercuidado."
            ),
            value_proposition=ValueProposition(
                client_profile=(
                    "Productor de cemento y áridos de California, con unas 800 personas en dos "
                    "plantas de cemento y cuatro canteras."
                ),
                current_situation=(
                    "En los próximos cinco años se jubila buena parte de los operadores de horno y de "
                    "los técnicos de mantenimiento. Las habilidades y certificaciones de la plantilla "
                    "están repartidas entre el sistema de formación, las órdenes de trabajo de "
                    "mantenimiento y la memoria de los supervisores, y RR. HH. tarda semanas en "
                    "encontrar a alguien con un perfil concreto para un puesto crítico."
                ),
                objectives=[
                    "Cubrir los puestos críticos con talento interno antes de buscar fuera.",
                    "Tener un perfil de habilidades y certificaciones actualizado de cada persona, revisado por ella misma.",
                    "Saber qué habilidades faltan en cada planta para orientar la formación.",
                ],
                solution=(
                    "Una plataforma web, usable en tablet en planta, que construye el perfil de "
                    "habilidades de cada persona a partir de sus registros de formación, sus "
                    "certificaciones y sus órdenes de trabajo, con un modelo de lenguaje y la "
                    "taxonomía O*NET del Departamento de Trabajo de EE. UU. Cada persona revisa y "
                    "corrige su perfil, RR. HH. busca candidatos internos para cada puesto y dirección "
                    "ve las brechas de habilidades por planta."
                ),
                benefits=[
                    "Encontrar candidatos internos en minutos en lugar de semanas.",
                    "Preparar con tiempo el relevo de las jubilaciones, sabiendo quién puede cubrir cada puesto crítico.",
                    "Orientar el presupuesto de formación a las brechas reales de cada planta.",
                    "Un buscador probado contra sesgos, con registros que permiten demostrar que no discrimina, como exige California a los sistemas automatizados en decisiones de empleo.",
                ],
                out_of_scope=[
                    "El soporte y el mantenimiento después de las dos semanas de hipercuidado, que se presupuestan aparte.",
                    "El consumo de la API del modelo de lenguaje y de la nube en producción.",
                    "La formación de seguridad que MSHA exige a los visitantes de la cantera, que imparte el cliente.",
                ],
                assumptions=[
                    "El HRIS y el sistema de formación exponen una API. Si solo exportan ficheros, se revisan el alcance y la inversión.",
                    "Los perfiles de habilidades son información personal protegida por la CCPA/CPRA, que en California también cubre a los empleados: cada persona ve y corrige el suyo, y RR. HH. solo ve agregados por planta salvo consentimiento.",
                    "La formación de seguridad MSHA (Parte 46, que cubre el cemento y los áridos) incluye un reciclaje anual: la plataforma muestra su vigencia, pero la fuente oficial sigue siendo el sistema de formación.",
                    "Si las plantas están sindicadas, las vacantes y las promociones siguen el convenio colectivo: el buscador sugiere candidatos y orienta la formación, pero no sustituye ese proceso.",
                ],
            ),
            phases=[
                _phase(
                    "Descubrimiento y diseño", 3,
                    "Mapa de las fuentes de datos y de los unos 60 puestos críticos de planta y cantera",
                    "Taxonomía O*NET adaptada a los puestos del cliente",
                    "Primeros prototipos del perfil y del buscador, revisados con usuarios",
                ),
                _phase(
                    "Construcción", 9,
                    "Integración con el HRIS, el sistema de formación y las órdenes de trabajo",
                    "Extracción de habilidades con IA, con su conjunto de evaluación",
                    "Perfil con validación por la persona, buscador de candidatos y panel de brechas",
                    "Pruebas de sesgo del buscador",
                ),
                _phase(
                    "Piloto en una planta", 2,
                    "Extracción validada con 50 perfiles reales",
                    "Ajustes a partir de lo aprendido en el piloto",
                ),
                _phase(
                    "Despliegue e hipercuidado", 2,
                    "Plataforma en producción para toda la plantilla",
                    "Formación a RR. HH. y supervisores, documentación y traspaso",
                    "Dos semanas de hipercuidado",
                ),
            ],
            tasks=[
                _task(
                    "Descubrimiento con RR. HH., operaciones, mantenimiento y seguridad, con visitas a una planta y una cantera",
                    1, 1, {"Gestión de proyecto": 32, "Liderazgo técnico": 24, "Diseño UX/UI": 24, "Consultoría de RR. HH.": 24},
                ),
                _task("Adaptación de O*NET a unos 60 puestos de planta y cantera", 1, 1, {"Consultoría de RR. HH.": 64, "IA / ML": 16}),
                _task("Diseño UX/UI para tablet: perfil, validación, buscador y panel, con pruebas con 8 usuarios", 1, 2, {"Diseño UX/UI": 152}),
                _task("Arquitectura, modelo de datos y API", 1, 2, {"Liderazgo técnico": 80, "Backend": 80}),
                _task("Inicio de sesión con Microsoft (SSO) y roles", 2, 2, {"Backend": 40}),
                _task("Integración con el HRIS y el sistema de formación", 2, 2, {"Backend": 96}),
                _task("Importación de las órdenes de trabajo del sistema de mantenimiento", 2, 3, {"Backend": 48}),
                _task("Extracción de habilidades con un LLM: pipeline, conjunto de evaluación y revisión humana", 1, 2, {"IA / ML": 168}),
                _task("Mapeo de habilidades y certificaciones a O*NET", 2, 2, {"IA / ML": 64}),
                _task("Buscador semántico de candidatos internos", 2, 2, {"IA / ML": 96, "Backend": 24}),
                _task("Pruebas de sesgo del buscador y registro de sus resultados durante 4 años", 2, 3, {"IA / ML": 48, "Consultoría de RR. HH.": 16}),
                _task("Frontend para tablet: perfil, validación por la persona y buscador", 2, 2, {"Frontend": 216}),
                _task("Panel de brechas por planta y de puestos críticos con jubilaciones próximas", 2, 3, {"Frontend": 88, "Backend": 24}),
                _task(
                    "Privacidad y seguridad: aviso a empleados, derechos CCPA/CPRA y registro de accesos",
                    2, 3, {"Backend": 56, "Liderazgo técnico": 24},
                ),
                _task("Infraestructura en la nube, entornos, CI/CD y monitorización", 1, 2, {"DevOps": 96}),
                _task("Plan de pruebas y pruebas funcionales, de regresión y de accesibilidad", 2, 2, {"QA": 168}),
                _task(
                    "Piloto en una planta: validación de la extracción con 50 perfiles y ajustes",
                    3, 3, {"Gestión de proyecto": 16, "IA / ML": 40, "QA": 32, "Consultoría de RR. HH.": 16, "Frontend": 24, "Liderazgo técnico": 16},
                ),
                _task(
                    "Despliegue a toda la plantilla, formación a RR. HH. y supervisores, documentación y traspaso",
                    4, 4, {"Gestión de proyecto": 24, "Liderazgo técnico": 24, "Backend": 16, "DevOps": 16, "Consultoría de RR. HH.": 8},
                ),
                _task("Hipercuidado durante las dos semanas siguientes al lanzamiento", 4, 4, {"Backend": 40, "Frontend": 24, "IA / ML": 16}),
                _task("Liderazgo técnico: revisiones de código, decisiones de arquitectura y seguridad", 1, 4, {"Liderazgo técnico": 80}),
                _task("Gestión del proyecto: planificación, seguimiento semanal, comité mensual y riesgos", 1, 4, {"Gestión de proyecto": 96}),
            ],
            expenses=[
                _expense("Viajes a una planta, una cantera y la planta piloto: 3 viajes de 240 millas a la tarifa del IRS", 720, "millas", IRS_MILEAGE_RATE_USD),
                _expense("API de modelos de lenguaje y embeddings durante el desarrollo y la evaluación", 1, "global", 400),
                _expense("Entornos de desarrollo y pruebas en la nube", 4, "meses", 400),
            ],
            internal_risks=[
                "Muchos operadores no tienen un CV actualizado: la fuente principal son los registros de formación y las órdenes de trabajo. Si la extracción no llega a la calidad esperada en el piloto con 50 perfiles, hay que dedicar más horas de IA/ML antes de procesar toda la plantilla.",
                "Si el HRIS y el sistema de formación solo exportan ficheros, hacen falta unas 40 horas más de backend.",
                "Las integraciones con el HRIS, el sistema de formación y el de mantenimiento dependen de que el cliente dé acceso a tiempo: un retraso mueve todo el calendario.",
                "Existen plataformas SaaS de habilidades. El desarrollo se justifica si las fuentes propias del sector (órdenes de trabajo y registros de MSHA) pesan más que lo que ofrece una plataforma estándar: conviene compararlo en el descubrimiento para no perder el proyecto más adelante.",
            ],
        ),
    ),
    ReferenceEstimation(
        meeting_summary=(
            "Una concretera del sur de California, con unas 1,200 personas entre conductores de "
            "camiones hormigonera (la mayoría, con unos 500 camiones), operadores de sus 30 plantas "
            "y personal de canteras, quiere saber cómo está su plantilla antes de que la rotación se "
            "dispare: le cuesta mucho retener conductores, que se quejan de los horarios irregulares "
            "y de cuándo pueden hacer sus pausas. Este personal no tiene correo corporativo ni "
            "ordenador, así que las encuestas anuales apenas llegan. Piden una app para el móvil con "
            "encuestas de pulso de tres preguntas a la semana, reconocimientos entre compañeros y un "
            "canal anónimo para avisar de problemas, incluidos los de seguridad. RR. HH. quiere un "
            "panel con los resultados por planta y alertas cuando una planta empeore varias semanas "
            "seguidas. Les preocupa mucho el anonimato: los jefes de planta no deben poder "
            "identificar a nadie. Los conductores están representados por los Teamsters, y buena "
            "parte de la plantilla prefiere el español."
        ),
        draft=EstimationDraft(
            is_software_project=True,
            not_software_reason="",
            project_name="App de escucha continua para conductores y personal de planta",
            project_type="App móvil (iOS y Android) con panel web",
            project_summary=(
                "App móvil multiplataforma con encuestas de pulso semanales, reconocimientos y un canal "
                "anónimo para avisos de seguridad y otros problemas, en inglés y español, con acceso "
                "por número de teléfono y modo sin conexión para canteras sin cobertura. Un panel "
                "web muestra a RR. HH. los resultados por planta, solo en grupos de 10 respuestas o "
                "más, y alerta de tendencias de desgaste y fatiga. Incluye un piloto en 3 plantas, el "
                "despliegue en las 30 y dos semanas de hipercuidado."
            ),
            value_proposition=ValueProposition(
                client_profile=(
                    "Concretera del sur de California con unas 1,200 personas: conductores de camiones "
                    "hormigonera, la mayoría, operadores de 30 plantas y personal de canteras."
                ),
                current_situation=(
                    "La rotación de conductores es alta, y se quejan de los horarios irregulares y de "
                    "cuándo pueden hacer sus pausas. La plantilla no tiene correo corporativo ni "
                    "ordenador, así que las encuestas anuales apenas llegan y la empresa se entera de "
                    "los problemas cuando la persona ya se ha ido. Buena parte de la plantilla "
                    "prefiere el español."
                ),
                objectives=[
                    "Saber cada semana cómo está la plantilla de cada planta.",
                    "Detectar a tiempo las plantas en las que empeoran el desgaste y la fatiga.",
                    "Dar a conductores y operadores un canal anónimo para avisar de problemas, también de seguridad.",
                    "Reconocer el buen trabajo entre compañeros.",
                ],
                solution=(
                    "Una app para iOS y Android, en inglés y español, con encuestas de pulso de tres "
                    "preguntas a la semana, reconocimientos entre compañeros y un canal anónimo. Se "
                    "entra con el número de teléfono, funciona sin conexión en las canteras y solo "
                    "envía encuestas durante el turno. Un panel web muestra a RR. HH. los resultados "
                    "por planta, siempre en grupos de 10 respuestas o más, y avisa cuando una planta "
                    "empeora varias semanas seguidas."
                ),
                benefits=[
                    "Llegar a toda la plantilla, también a quien no tiene correo ni ordenador.",
                    "Actuar sobre la rotación antes de perder conductores.",
                    "Anonimato garantizado: ningún jefe de planta puede identificar a nadie.",
                    "Avisos de seguridad que llegan a su responsable, con plazos de respuesta.",
                ],
                out_of_scope=[
                    "El costo de los SMS y de la nube en producción.",
                    "El soporte y el mantenimiento después de las dos semanas de hipercuidado, que se presupuestan aparte.",
                    "Las cuentas de desarrollador de Apple (99 USD al año) y Google Play (25 USD), que se abren a nombre del cliente porque es quien publica la app.",
                ],
                assumptions=[
                    "Las encuestas se responden durante el turno y nunca en las pausas de comida o descanso, que en California deben quedar libres de toda tarea. Los conductores solo responden con el camión detenido, porque la ley prohíbe usar el móvil en la mano al conducir.",
                    "Las respuestas sobre bienestar y fatiga pueden ser información personal sensible según la CPRA: se usan solo de forma agregada y se declaran en el aviso de privacidad para empleados.",
                    "El canal anónimo no sustituye los procedimientos formales ante Cal/OSHA o MSHA, y el cliente define quién atiende los avisos y en qué plazo.",
                    "La app afecta a las condiciones de trabajo de conductores representados por los Teamsters: conviene acordarla con el sindicato antes del piloto, y el calendario puede ajustarse.",
                    "Los SMS a números de EE. UU. exigen registrar la marca y la campaña (10DLC), lo que lleva unas semanas.",
                ],
            ),
            phases=[
                _phase(
                    "Descubrimiento y diseño", 3,
                    "Mapa de turnos, pausas y canales de comunicación por tipo de puesto",
                    "Encuestas de pulso validadas, en inglés y español",
                    "Primeros prototipos de la app y del panel",
                ),
                _phase(
                    "Construcción", 9,
                    "App para iOS y Android con encuestas, reconocimientos y canal anónimo, también sin conexión",
                    "Acceso por número de teléfono y notificaciones según el turno",
                    "Panel web de RR. HH. con alertas de desgaste y fatiga",
                ),
                _phase("Revisión en las tiendas de apps", 1, "App publicada en App Store y Google Play"),
                _phase(
                    "Piloto en 3 plantas", 3,
                    "Análisis de la participación en el piloto",
                    "Ajustes a partir de lo aprendido",
                ),
                _phase(
                    "Despliegue e hipercuidado", 2,
                    "App en las 30 plantas, con materiales en inglés y español",
                    "Formación a jefes de planta y RR. HH.",
                    "Dos semanas de hipercuidado",
                ),
            ],
            tasks=[
                _task(
                    "Descubrimiento con RR. HH., seguridad y operaciones, con visitas a 2 plantas y una reunión con representantes de los Teamsters",
                    1, 1, {"Gestión de proyecto": 32, "Consultoría de RR. HH.": 24, "Diseño UX/UI": 24, "Liderazgo técnico": 16},
                ),
                _task(
                    "Diseño de las encuestas de pulso (preguntas validadas de compromiso, carga de trabajo y fatiga) y su versión en español",
                    1, 2, {"Consultoría de RR. HH.": 72},
                ),
                _task(
                    "Diseño UX/UI móvil y del panel web: responder en menos de un minuto, también con guantes y a pleno sol",
                    1, 2, {"Diseño UX/UI": 168},
                ),
                _task("Arquitectura, modelo de datos y API", 1, 2, {"Liderazgo técnico": 64, "Backend": 64}),
                _task("Programación de encuestas y notificaciones push según el turno, nunca en pausas ni fuera del turno", 2, 2, {"Backend": 80}),
                _task("Acceso con número de teléfono y código SMS", 2, 2, {"Backend": 40}),
                _task("Anonimato: umbral mínimo de 10 respuestas por grupo y separación de identidades", 2, 2, {"Backend": 48, "Liderazgo técnico": 16}),
                _task("App multiplataforma: encuestas, reconocimientos y canal anónimo", 1, 3, {"Móvil": 320}),
                _task("Modo sin conexión y sincronización para canteras sin cobertura", 2, 3, {"Móvil": 64}),
                _task("Soporte en inglés y español", 2, 3, {"Móvil": 24}),
                _task("Envío de los avisos de seguridad del canal anónimo a su responsable, con plazos", 2, 2, {"Backend": 32}),
                _task("Panel web de RR. HH. con resultados por planta", 2, 2, {"Frontend": 176}),
                _task("Alertas de tendencia de desgaste y fatiga por planta", 2, 2, {"Ingeniería de datos": 80}),
                _task("Infraestructura, CI/CD móvil y publicación en App Store y Google Play", 2, 3, {"DevOps": 96}),
                _task("Pruebas en dispositivos reales, también Android de gama baja, en planta y en cantera", 2, 4, {"QA": 216}),
                _task(
                    "Piloto en 3 plantas: soporte, análisis de la participación y ajustes",
                    4, 4, {"Gestión de proyecto": 24, "Consultoría de RR. HH.": 24, "Móvil": 40, "Backend": 24, "Ingeniería de datos": 16},
                ),
                _task(
                    "Despliegue en las 30 plantas: materiales en inglés y español, y formación a jefes de planta y RR. HH.",
                    5, 5, {"Gestión de proyecto": 24, "Consultoría de RR. HH.": 16},
                ),
                _task("Hipercuidado durante las dos semanas siguientes al lanzamiento", 5, 5, {"Móvil": 40, "Backend": 24}),
                _task("Liderazgo técnico: revisiones de código, decisiones de arquitectura y seguridad", 1, 5, {"Liderazgo técnico": 72}),
                _task("Gestión del proyecto: planificación, seguimiento semanal, comité mensual y riesgos", 1, 5, {"Gestión de proyecto": 108}),
            ],
            expenses=[
                _expense("Viajes a 2 plantas en el descubrimiento y a 3 en el piloto: 5 viajes de 120 millas a la tarifa del IRS", 600, "millas", IRS_MILEAGE_RATE_USD),
                _expense("Traducción profesional al español de la app, las encuestas y los materiales", 12_000, "palabras", 0.14),
                _expense("Registro de la marca y la campaña de SMS (10DLC) y cuota de la campaña durante el proyecto", 1, "global", 101),
                _expense("Dispositivos de prueba: dos Android de gama baja y uno resistente", 3, "dispositivos", 300),
                _expense("Entornos de desarrollo y pruebas en la nube", 4.5, "meses", 400),
            ],
            internal_risks=[
                "Si la empresa no acuerda la app con los Teamsters antes del piloto, el calendario se alarga y el precio cerrado no cubre las semanas de más.",
                "La revisión en las tiendas de apps puede rechazar la primera versión y retrasar el piloto.",
                "Los Android de gama baja pueden dar problemas de rendimiento que solo aparecen en el piloto, cuando ya no queda holgura en el calendario.",
                "Existen plataformas SaaS de escucha al empleado. El desarrollo se justifica por el acceso sin correo corporativo, el modo sin conexión y el acuerdo con el sindicato: conviene compararlo en el descubrimiento.",
            ],
        ),
    ),
    ReferenceEstimation(
        meeting_summary=(
            "Un grupo de materiales de construcción (cemento, áridos y hormigón premezclado) con "
            "unas 2,500 personas en California, repartidas en dos cementeras, una docena de canteras "
            "y unas 40 plantas de hormigón, presenta cada año el informe de datos salariales al "
            "California Civil Rights Department (CRD), además del informe aparte de los trabajadores "
            "que contrata a través de agencias. Quiere adelantarse a reclamaciones bajo la "
            "California Equal Pay Act, que exige igual salario por trabajo sustancialmente similar "
            "sin distinguir por sexo, raza o etnia. Los datos están repartidos entre el HRIS, dos "
            "sistemas de nómina heredados de adquisiciones y un Excel con la valoración de puestos. "
            "Buena parte de la plantilla de planta y transporte tiene convenio colectivo, y la paga "
            "incluye muchas horas extra, pluses de turno y el salario prevaleciente de los "
            "conductores que entregan en obra pública. Hoy el informe se hace a mano y lleva un mes. "
            "Piden automatizarlo: unificar los datos cada mes, calcular la brecha por categoría de "
            "puesto, explicar qué parte se debe a factores legítimos como la antigüedad o las "
            "escalas del convenio y avisar cuando una brecha no explicada pase del 5 %. RR. HH. "
            "quiere además simular cuánto costaría cerrar las brechas con un presupuesto dado."
        ),
        draft=EstimationDraft(
            is_software_project=True,
            not_software_reason="",
            project_name="Pipeline de equidad salarial y reporte al CRD de California",
            project_type="Integración de datos interna con dashboard",
            project_summary=(
                "Pipeline mensual que une HRIS, nóminas y valoración de puestos en un almacén de datos, "
                "con los datos personales seudonimizados. Separa horas extra, pluses y salario "
                "prevaleciente; calcula la brecha bruta y ajustada por categoría, sexo y raza o etnia; "
                "genera los informes anuales para el CRD; avisa de las brechas no explicadas por encima "
                "del 5 % y ofrece un simulador de ajustes con presupuesto. La puesta en marcha incluye "
                "un primer cierre mensual en paralelo con el proceso manual."
            ),
            value_proposition=ValueProposition(
                client_profile=(
                    "Grupo de materiales de construcción de California (cemento, áridos y hormigón "
                    "premezclado) con unas 2,500 personas en dos cementeras, una docena de canteras y "
                    "unas 40 plantas de hormigón."
                ),
                current_situation=(
                    "Cada año la empresa presenta al California Civil Rights Department (CRD) el informe "
                    "de datos salariales y el de los trabajadores contratados por agencias. Hoy lo "
                    "prepara a mano en un mes, con datos repartidos entre el HRIS, dos nóminas heredadas "
                    "de adquisiciones y un Excel con la valoración de puestos. La paga incluye muchas "
                    "horas extra, pluses de turno y el salario prevaleciente de los conductores de obra "
                    "pública, y buena parte de la plantilla tiene convenio colectivo."
                ),
                objectives=[
                    "Automatizar los informes anuales para el CRD.",
                    "Adelantarse a reclamaciones bajo la California Equal Pay Act.",
                    "Separar las brechas que explican factores legítimos, como la antigüedad o las escalas del convenio, de las que no.",
                    "Saber cuánto costaría cerrar las brechas con un presupuesto dado.",
                ],
                solution=(
                    "Un pipeline mensual que une el HRIS, las dos nóminas y la valoración de puestos en "
                    "un almacén de datos, con los datos personales seudonimizados. Separa horas extra, "
                    "pluses y salario prevaleciente; calcula la brecha bruta y ajustada por categoría de "
                    "puesto, sexo y raza o etnia; genera los informes para el CRD; avisa cuando una "
                    "brecha no explicada supera el 5 %, y ofrece a RR. HH. un dashboard y un simulador "
                    "de ajustes salariales."
                ),
                benefits=[
                    "Pasar de un mes de trabajo manual a unos informes que se generan solos.",
                    "Ver las brechas cada mes, en lugar de una vez al año.",
                    "Decidir los ajustes salariales sabiendo cuánto cuestan.",
                    "Una metodología documentada que la asesoría legal puede revisar.",
                ],
                out_of_scope=[
                    "Las licencias del almacén de datos.",
                    "La adaptación a una nueva plantilla del informe si el CRD la cambia.",
                    "El soporte después del primer cierre mensual, que se presupuesta aparte.",
                ],
                assumptions=[
                    "Qué puestos hacen un trabajo sustancialmente similar lo decide el cliente con su asesoría legal: el proyecto lo implementa, no lo decide. El análisis se hace bajo la dirección de esa asesoría, para proteger la confidencialidad entre abogado y cliente.",
                    "Se trabaja con un máximo de tres años de histórico de nómina.",
                    "Desde 2016 (ley AB 219), los conductores que entregan hormigón en obra pública cobran salario prevaleciente según la ubicación de la planta: se separa del salario base para no confundirlo con una brecha.",
                    "Hay pocas mujeres en planta, cantera y transporte, así que muchas categorías tienen grupos pequeños: los resultados se muestran con un tamaño mínimo de grupo y se interpretan con cautela.",
                    "Los datos de los trabajadores de agencias dependen de que las agencias los entreguen a tiempo.",
                    "Los salarios individuales solo los ve RR. HH., con permisos por rol.",
                ],
            ),
            phases=[
                _phase(
                    "Descubrimiento y modelo de datos", 3,
                    "Inventario de las fuentes y de los códigos de nómina",
                    "Propuesta de categorías de trabajo similar para la asesoría legal",
                    "Modelo de datos del almacén",
                ),
                _phase(
                    "Construcción", 9,
                    "Conectores con el HRIS y las dos nóminas, con los datos personales seudonimizados",
                    "Modelo de brecha ajustada y alertas por encima del 5 %",
                    "Informes anuales para el CRD, simulador de ajustes y dashboard",
                ),
                _phase("Validación", 2, "Cifras validadas contra la nómina"),
                _phase(
                    "Primer cierre mensual en paralelo", 2,
                    "Primer cierre mensual en paralelo con el proceso manual",
                    "Formación a RR. HH. y metodología documentada para la asesoría legal",
                ),
            ],
            tasks=[
                _task(
                    "Descubrimiento: inventario de fuentes, sesión con la asesoría legal y propuesta de categorías de trabajo similar en planta, cantera, transporte y oficinas",
                    1, 1, {"Gestión de proyecto": 32, "Consultoría de RR. HH.": 40, "Liderazgo técnico": 24, "Ciencia de datos": 16},
                ),
                _task("Conectores con el HRIS y los dos sistemas de nómina", 2, 2, {"Ingeniería de datos": 128}),
                _task(
                    "Unificación de los códigos de nómina, separación de horas extra, pluses y salario prevaleciente, y modelo de datos",
                    1, 2, {"Ingeniería de datos": 144, "Consultoría de RR. HH.": 32},
                ),
                _task("Seudonimización de los datos personales y permisos por rol", 2, 2, {"Liderazgo técnico": 40}),
                _task("Reglas de calidad de datos y conciliación con la nómina", 2, 3, {"Ingeniería de datos": 64}),
                _task("Modelo de brecha ajustada por factores legítimos, con tratamiento de los grupos pequeños", 2, 2, {"Ciencia de datos": 160, "Consultoría de RR. HH.": 24}),
                _task("Generación de los informes anuales para el CRD, incluido el de trabajadores de agencias", 2, 2, {"Liderazgo técnico": 64, "Consultoría de RR. HH.": 16}),
                _task("Alertas de brechas no explicadas por encima del 5 %", 2, 2, {"Ingeniería de datos": 24, "Ciencia de datos": 16}),
                _task("Simulador de escenarios de ajuste salarial con presupuesto", 2, 2, {"Ciencia de datos": 56, "Full-stack": 56}),
                _task("Dashboard de brechas para RR. HH.", 2, 2, {"Full-stack": 144, "Diseño UX/UI": 56}),
                _task("Orquestación mensual, monitorización y alertas del pipeline", 2, 2, {"DevOps": 80}),
                _task("Validación de las cifras contra la nómina y QA", 2, 3, {"QA": 120, "Consultoría de RR. HH.": 24}),
                _task(
                    "Primer cierre mensual en paralelo con el proceso manual, formación a RR. HH. y documentación de la metodología para la asesoría legal",
                    4, 4, {"Gestión de proyecto": 16, "Ciencia de datos": 32, "Liderazgo técnico": 24, "Consultoría de RR. HH.": 16},
                ),
                _task("Hipercuidado durante el primer cierre mensual", 4, 4, {"Ingeniería de datos": 32}),
                _task("Liderazgo técnico: revisiones, decisiones de arquitectura y seguridad de los datos", 1, 4, {"Liderazgo técnico": 64}),
                _task("Gestión del proyecto: planificación, seguimiento semanal, comité mensual y riesgos", 1, 4, {"Gestión de proyecto": 96}),
            ],
            expenses=[
                _expense("Viajes a las oficinas centrales: 2 viajes de 100 millas a la tarifa del IRS", 200, "millas", IRS_MILEAGE_RATE_USD),
                _expense("Entorno de datos de desarrollo y pruebas en la nube", 4, "meses", 500),
            ],
            internal_risks=[
                "Los dos sistemas de nómina usan códigos de concepto distintos: con más de tres años de histórico la limpieza crece, y el precio cerrado no la cubre.",
                "En los puestos con convenio, el salario base lo fija la escala por categoría y antigüedad, así que las brechas suelen aparecer en el reparto de horas extra y en los puestos fuera de convenio. Si el modelo no los analiza por separado, el resultado pierde credibilidad ante la asesoría legal.",
                "El acceso a las dos nóminas heredadas depende de sus proveedores: un retraso en las credenciales o en las exportaciones mueve todo el calendario.",
                "Existen plataformas SaaS de equidad salarial. El desarrollo se justifica por las dos nóminas heredadas, los convenios y el salario prevaleciente: conviene compararlo en el descubrimiento.",
            ],
        ),
    ),
)
