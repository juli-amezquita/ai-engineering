"""Estimaciones de referencia: el conocimiento que se inyecta en cada llamada al LLM (CAG).

Son tres proyectos ficticios de RR. HH. y People Analytics para empresas de cemento,
hormigón premezclado, áridos y minería de California. Son de tipos distintos para que el
modelo vea variedad sin redundancia: una plataforma web con IA, una app móvil y una
integración de datos interna.

Los datos ya vienen preparados, como pide la gestión de contexto en CAG:
- una sola moneda y unidad de tarifa (USD por hora), igual en todos los ejemplos;
- tarifas de referencia del mercado de California;
- horas en múltiplos de 5;
- costes y totales calculados en Python, no escritos a mano ni dejados al modelo;
- clientes descritos por su sector y su tamaño, sin nombres reales.

El texto que llega al prompt lo genera app/services/prompt_builder.py.
"""

from dataclasses import dataclass

# Tarifas de la empresa por perfil, en USD por hora, para clientes de California.
# Son la referencia de precios que el modelo necesita para no inventar cifras.
HOURLY_RATES_USD: dict[str, int] = {
    "Gestión de proyecto": 140,
    "Diseño UX/UI": 130,
    "Frontend": 145,
    "Backend": 155,
    "Móvil": 155,
    "Ingeniería de datos": 165,
    "IA / ML": 190,
    "QA": 105,
    "DevOps": 160,
}


@dataclass(frozen=True)
class Task:
    """Una línea del desglose: qué se hace, qué perfil lo hace y cuántas horas lleva."""

    name: str
    role: str
    hours: int

    def __post_init__(self) -> None:
        if self.role not in HOURLY_RATES_USD:
            raise ValueError(f"El perfil {self.role!r} no tiene tarifa en HOURLY_RATES_USD")
        if self.hours <= 0 or self.hours % 5 != 0:
            raise ValueError(f"Las horas de {self.name!r} deben ser positivas y múltiplo de 5")

    @property
    def rate(self) -> int:
        """Tarifa del perfil, en USD por hora."""
        return HOURLY_RATES_USD[self.role]

    @property
    def cost(self) -> int:
        """Coste de la tarea en USD, calculado: horas × tarifa."""
        return self.hours * self.rate


@dataclass(frozen=True)
class ReferenceEstimation:
    """Una estimación pasada: lo que pidió el cliente y lo que se le presupuestó."""

    title: str
    project_type: str
    meeting_summary: str  # qué pedía el cliente en la reunión original
    project_summary: str  # el alcance que propuso la estimación, en 2 o 3 frases
    tasks: tuple[Task, ...]
    team: str
    duration: str
    risks: tuple[str, ...]  # riesgos y supuestos clave

    @property
    def total_hours(self) -> int:
        return sum(task.hours for task in self.tasks)

    @property
    def total_cost(self) -> int:
        return sum(task.cost for task in self.tasks)


ESTIMATION_EXAMPLES: tuple[ReferenceEstimation, ...] = (
    ReferenceEstimation(
        title="Plataforma de inteligencia de habilidades para movilidad interna",
        project_type="Plataforma web SaaS con IA",
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
        project_summary=(
            "MVP de una plataforma web, usable en tablet en planta, que extrae habilidades y "
            "certificaciones de los registros de formación y de las órdenes de trabajo con un LLM, "
            "las mapea a la taxonomía O*NET del Departamento de Trabajo de EE. UU. y permite buscar "
            "candidatos internos para puestos críticos. Cada persona valida su perfil, RR. HH. ve "
            "las brechas por planta y el buscador se prueba contra sesgos."
        ),
        tasks=(
            Task("Descubrimiento con RR. HH. y operaciones, y adaptación de O*NET a los puestos de planta y cantera", "Gestión de proyecto", 30),
            Task("Diseño UX/UI del perfil de habilidades y del buscador", "Diseño UX/UI", 50),
            Task("API, modelo de datos e inicio de sesión con Microsoft (SSO)", "Backend", 80),
            Task("Integración con el HRIS y el sistema de formación: puestos y certificaciones", "Backend", 40),
            Task("Extracción de habilidades de formación y órdenes de trabajo con un LLM, mapeadas a O*NET", "IA / ML", 90),
            Task("Buscador semántico de candidatos internos para puestos críticos", "IA / ML", 60),
            Task("Pruebas de sesgo del buscador y registro de sus resultados", "IA / ML", 30),
            Task("Frontend adaptado a tablet: perfil, validación por la persona y buscador", "Frontend", 90),
            Task("Panel de brechas por planta y de puestos críticos con jubilaciones próximas", "Frontend", 40),
            Task("Privacidad: aviso a empleados, derechos CCPA/CPRA y registro de accesos", "Backend", 30),
            Task("Pruebas funcionales y validación de la extracción con 50 perfiles", "QA", 50),
            Task("Despliegue en la nube y CI/CD", "DevOps", 25),
        ),
        team=(
            "1 backend, 1 frontend y 1 especialista en IA/ML a tiempo completo; diseño UX/UI y "
            "gestión de proyecto a tiempo parcial; QA en las últimas cuatro semanas."
        ),
        duration="8-10 semanas",
        risks=(
            "Muchos operadores no tienen un CV actualizado: la fuente principal son los registros de "
            "formación y las órdenes de trabajo. La extracción se valida con una muestra de 50 "
            "perfiles antes de procesar toda la plantilla.",
            "El buscador apoya decisiones de movilidad y promoción. En California, usar un sistema "
            "automatizado en decisiones de empleo exige poder demostrar que no discrimina, por eso "
            "se incluyen pruebas de sesgo y se conservan sus registros.",
            "Los perfiles de habilidades son información personal protegida por la CCPA/CPRA, que "
            "en California también cubre a los empleados: cada persona ve y corrige el suyo, y "
            "RR. HH. solo ve agregados por planta salvo consentimiento.",
            "Las certificaciones de seguridad (formación MSHA) se muestran con su vigencia, pero la "
            "fuente oficial sigue siendo el sistema de formación.",
            "Se asume que el HRIS y el sistema de formación exponen una API. Si solo exportan "
            "ficheros, hay que sumar unas 30 horas de backend. El consumo de la API del LLM se "
            "factura aparte.",
        ),
    ),
    ReferenceEstimation(
        title="App de escucha continua para conductores y personal de planta",
        project_type="App móvil (iOS y Android) con panel web",
        meeting_summary=(
            "Una concretera de California, con unos 3.000 empleados entre conductores de camiones "
            "hormigonera, operadores de planta y personal de canteras, quiere saber cómo está su "
            "plantilla antes de que la rotación se dispare: le cuesta mucho retener conductores. "
            "Este personal no tiene correo corporativo ni ordenador, así que las encuestas anuales "
            "apenas llegan. Piden una app para el móvil con encuestas de pulso de tres preguntas a "
            "la semana, reconocimientos entre compañeros y un canal anónimo para avisar de "
            "problemas, incluidos los de seguridad. RR. HH. quiere un panel con los resultados por "
            "planta y alertas cuando una planta empeore varias semanas seguidas. Les preocupa mucho "
            "el anonimato: los jefes de planta no deben poder identificar a nadie. Buena parte de "
            "la plantilla habla español, y algunos conductores, punyabí."
        ),
        project_summary=(
            "App móvil multiplataforma con encuestas de pulso semanales, reconocimientos y un canal "
            "anónimo para avisos de seguridad y otros problemas, en inglés, español y punyabí, con "
            "acceso por número de teléfono y modo sin conexión para canteras sin cobertura. Un panel "
            "web muestra a RR. HH. los resultados por planta, solo en grupos de 10 respuestas o "
            "más, y alerta de tendencias de desgaste y fatiga."
        ),
        tasks=(
            Task("Descubrimiento y diseño de las encuestas con RR. HH. y seguridad", "Gestión de proyecto", 25),
            Task("Diseño UX/UI móvil: responder en menos de un minuto, también con guantes y a pleno sol", "Diseño UX/UI", 60),
            Task("App multiplataforma: encuestas, reconocimientos y canal anónimo", "Móvil", 160),
            Task("Soporte en inglés, español y punyabí, y modo sin conexión para canteras sin cobertura", "Móvil", 30),
            Task("API, programación de encuestas y notificaciones push", "Backend", 90),
            Task("Acceso con número de teléfono y código SMS", "Backend", 30),
            Task("Anonimato: umbral mínimo de 10 respuestas por grupo", "Backend", 30),
            Task("Panel web de RR. HH. con resultados por planta", "Frontend", 80),
            Task("Alertas de tendencia de desgaste y fatiga por planta", "Ingeniería de datos", 40),
            Task("Pruebas en dispositivos reales, también en planta y cantera, y QA", "QA", 60),
            Task("Publicación en App Store y Google Play, y CI/CD", "DevOps", 30),
        ),
        team=(
            "2 perfiles móviles, 1 backend y 1 frontend; diseño UX/UI, datos y gestión de proyecto "
            "a tiempo parcial; QA desde la mitad del proyecto."
        ),
        duration="10-12 semanas, incluida la revisión de las tiendas de apps",
        risks=(
            "Las encuestas se responden durante el turno y, en el caso de los conductores, solo con "
            "el camión detenido: en California, responder fuera del turno puede considerarse tiempo "
            "de trabajo pagado. Se propone un piloto en 3 plantas antes de desplegar en toda la "
            "empresa.",
            "Las respuestas sobre bienestar y fatiga pueden ser información personal sensible según "
            "la CPRA: se usan solo de forma agregada y se declaran en el aviso de privacidad para "
            "empleados.",
            "El canal anónimo recibirá avisos de seguridad: no sustituye los procedimientos formales "
            "ante Cal/OSHA o MSHA, y la empresa debe definir quién los atiende y en qué plazo.",
            "Si los conductores o el personal de planta están sindicados, conviene informar al "
            "sindicato antes del piloto, y el calendario puede ajustarse.",
            "Los SMS a números de EE. UU. exigen registrar la marca y la campaña (10DLC), lo que "
            "lleva unas semanas. El coste de los SMS se factura aparte.",
        ),
    ),
    ReferenceEstimation(
        title="Pipeline de equidad salarial y reporte al CRD de California",
        project_type="Integración de datos interna con dashboard",
        meeting_summary=(
            "Un grupo de materiales de construcción (cemento, áridos y hormigón premezclado) con "
            "unos 2.500 empleados en cinco plantas y canteras de California presenta cada año el "
            "informe de datos salariales al California Civil Rights Department (CRD), además del "
            "informe aparte de los trabajadores que contrata a través de agencias. Quiere "
            "adelantarse a reclamaciones bajo la California Equal Pay Act, que exige igual salario "
            "por trabajo sustancialmente similar sin distinguir por sexo, raza o etnia. Los datos "
            "están repartidos entre el HRIS, la nómina de cada planta y un Excel con la valoración "
            "de puestos, y la paga incluye muchas horas extra, pluses de turno y obras públicas con "
            "salario prevaleciente (prevailing wage). Hoy el informe se hace a mano y lleva un mes. "
            "Piden automatizarlo: unificar los datos cada mes, calcular la brecha por categoría de "
            "puesto, explicar qué parte se debe a factores legítimos como la antigüedad y avisar "
            "cuando una brecha no explicada pase del 5 %. RR. HH. quiere además simular cuánto "
            "costaría cerrar las brechas con un presupuesto dado."
        ),
        project_summary=(
            "Pipeline mensual que une HRIS, nóminas y valoración de puestos en un almacén de datos, "
            "con los datos personales seudonimizados. Separa horas extra, pluses y salario "
            "prevaleciente; calcula la brecha bruta y ajustada por categoría, sexo y raza o etnia; "
            "genera los informes anuales para el CRD; avisa de las brechas no explicadas por encima "
            "del 5 % y ofrece un simulador de ajustes con presupuesto."
        ),
        tasks=(
            Task("Descubrimiento: inventario de fuentes y categorías de trabajo similar en planta, cantera, transporte y oficinas", "Gestión de proyecto", 40),
            Task("Conectores con el HRIS y las nóminas de las cinco plantas y canteras", "Ingeniería de datos", 80),
            Task("Limpieza y normalización de conceptos salariales (horas extra, pluses de turno y salario prevaleciente) y modelo de datos", "Ingeniería de datos", 90),
            Task("Seudonimización de los datos personales en el pipeline", "Ingeniería de datos", 30),
            Task("Modelo de brecha ajustada por factores legítimos", "IA / ML", 60),
            Task("Generación de los informes anuales para el CRD, incluido el de trabajadores de agencias", "Ingeniería de datos", 40),
            Task("Simulador de escenarios de ajuste salarial", "Backend", 40),
            Task("Dashboard de brechas para RR. HH.", "Frontend", 60),
            Task("Orquestación mensual, monitorización y alertas del pipeline", "DevOps", 40),
            Task("Validación de las cifras contra nómina y QA", "QA", 50),
        ),
        team=(
            "2 perfiles de ingeniería de datos y 1 especialista en IA/ML con base estadística; "
            "frontend, backend y gestión de proyecto a tiempo parcial; QA en la fase de validación."
        ),
        duration="9-11 semanas",
        risks=(
            "Qué puestos hacen un trabajo sustancialmente similar lo decide la empresa con su "
            "asesoría legal: el proyecto lo implementa, no lo decide.",
            "Cada planta usa códigos de concepto salarial distintos, y el salario prevaleciente "
            "cambia por condado y por obra. Se asume un máximo de tres años de histórico; con más, "
            "la limpieza crece.",
            "Hay pocas mujeres en planta, cantera y transporte, así que muchas categorías tienen "
            "grupos pequeños: los resultados se muestran con un tamaño mínimo de grupo y se "
            "interpretan con cautela.",
            "Los datos de los trabajadores de agencias dependen de que las agencias los entreguen a "
            "tiempo. Si el CRD cambia la plantilla del informe, la adaptación se presupuesta aparte.",
            "Los salarios individuales solo los ve RR. HH., con permisos por rol. Las licencias del "
            "almacén de datos no están incluidas.",
        ),
    ),
)
