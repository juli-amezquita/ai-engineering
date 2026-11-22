"""Estimaciones de referencia: el conocimiento que se inyecta en cada llamada al LLM (CAG).

Son tres proyectos ficticios de RR. HH. y People Analytics para empresas de cemento,
hormigón premezclado, áridos y minería de California. Son de tipos distintos para que el
modelo vea variedad sin redundancia: una plataforma web con IA, una app móvil y una
integración de datos interna.

Los datos ya vienen preparados, como pide la gestión de contexto en CAG:
- una sola moneda y unidad de tarifa (USD por hora), igual en todos los ejemplos;
- la consultora es pequeña y trabaja con un equipo mixto: gestión, liderazgo técnico y
  consultoría de RR. HH. en Los Ángeles; backend, datos, IA/ML y DevOps en otras zonas de
  EE. UU.; diseño, frontend, full-stack, móvil y QA en Latinoamérica;
- cada proyecto tiene una sola tarifa media para todo el equipo, la que le deja a la
  consultora un 30 % de utilidad neta, y nunca pasa de 150 USD/h, el precio de mercado de
  una consultora pequeña (análisis v6 del vault);
- las horas salen de un desglose por tarea y perfil, y cada profesional suma un 10 % de
  imprevistos;
- la dedicación de cada profesional se calcula con sus horas y la duración, y no puede
  pasar del 100 %;
- importes y totales calculados en Python, no escritos a mano ni dejados al modelo;
- clientes descritos por su sector y su tamaño, sin nombres reales.

El texto que llega al prompt lo genera app/services/prompt_builder.py.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

# Perfiles del equipo y desde dónde trabaja cada uno.
ROLE_LOCATIONS: dict[str, str] = {
    "Gestión de proyecto": "Los Ángeles",
    "Consultoría de RR. HH.": "Los Ángeles",
    "Liderazgo técnico": "Los Ángeles",
    "Backend": "EE. UU.",
    "Ingeniería de datos": "EE. UU.",
    "Ciencia de datos": "EE. UU.",
    "IA / ML": "EE. UU.",
    "DevOps": "EE. UU.",
    "Diseño UX/UI": "Latinoamérica",
    "Frontend": "Latinoamérica",
    "Full-stack": "Latinoamérica",
    "Móvil": "Latinoamérica",
    "QA": "Latinoamérica",
}

# Precio de mercado de una consultora pequeña: tope de la tarifa media de un proyecto.
MAX_HOURLY_RATE_USD = Decimal("150")

# Imprevistos: un 10 % sobre las horas de cada profesional.
CONTINGENCY_RATE = Decimal("0.10")

# Jornada de referencia para calcular la dedicación de cada profesional.
HOURS_PER_WEEK = 40


@dataclass(frozen=True)
class Task:
    """Una línea del desglose: qué se hace y cuántas horas pone cada perfil."""

    name: str
    hours_by_role: dict[str, int]

    def __post_init__(self) -> None:
        if not self.hours_by_role:
            raise ValueError(f"La tarea {self.name!r} no tiene horas asignadas")
        for role, hours in self.hours_by_role.items():
            if role not in ROLE_LOCATIONS:
                raise ValueError(f"El perfil {role!r} no está en ROLE_LOCATIONS")
            if not isinstance(hours, int) or hours <= 0:
                raise ValueError(f"Las horas de {role!r} en {self.name!r} deben ser un entero positivo")

    @property
    def total_hours(self) -> int:
        return sum(self.hours_by_role.values())


@dataclass(frozen=True)
class Expense:
    """Un gasto reembolsable del proyecto, que se factura a coste (viajes, traducción...)."""

    name: str
    amount: int  # USD

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError(f"El gasto {self.name!r} debe ser positivo")


@dataclass(frozen=True)
class RoleBudget:
    """El presupuesto de horas de un profesional: horas base, imprevistos y su importe."""

    role: str
    base_hours: int
    rate: Decimal  # tarifa media del proyecto, en USD por hora

    @property
    def location(self) -> str:
        return ROLE_LOCATIONS[self.role]

    @property
    def contingency_hours(self) -> Decimal:
        return self.base_hours * CONTINGENCY_RATE

    @property
    def total_hours(self) -> Decimal:
        return self.base_hours + self.contingency_hours

    @property
    def amount(self) -> int:
        """Importe en USD (horas totales × tarifa), redondeado al dólar."""
        return int((self.total_hours * self.rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class ReferenceEstimation:
    """Una estimación pasada: lo que pidió el cliente y lo que se le presupuestó."""

    title: str
    project_type: str
    meeting_summary: str  # qué pedía el cliente en la reunión original
    project_summary: str  # el alcance que propuso la estimación, en 2 o 3 frases
    tasks: tuple[Task, ...]
    hourly_rate: Decimal  # tarifa media para todo el equipo, en USD por hora
    expenses: tuple[Expense, ...]
    duration_weeks: int
    phases: str  # cómo se reparten las semanas
    risks: tuple[str, ...]  # riesgos y supuestos clave

    def __post_init__(self) -> None:
        if self.duration_weeks <= 0:
            raise ValueError(f"La duración de {self.title!r} debe ser positiva")
        if not 0 < self.hourly_rate <= MAX_HOURLY_RATE_USD:
            raise ValueError(
                f"La tarifa de {self.title!r} debe ser positiva y no pasar de {MAX_HOURLY_RATE_USD} USD/h"
            )
        for budget in self.role_budgets:
            if self.dedication(budget) > 1:
                raise ValueError(
                    f"{budget.role} en {self.title!r} necesita más de una persona a tiempo "
                    f"completo durante {self.duration_weeks} semanas"
                )

    @property
    def role_budgets(self) -> tuple[RoleBudget, ...]:
        """Un presupuesto por profesional, en el orden en que aparece cada perfil."""
        hours: dict[str, int] = {}
        for task in self.tasks:
            for role, role_hours in task.hours_by_role.items():
                hours[role] = hours.get(role, 0) + role_hours
        return tuple(RoleBudget(role, base_hours, self.hourly_rate) for role, base_hours in hours.items())

    def dedication(self, budget: RoleBudget) -> Decimal:
        """Fracción de jornada completa que ocupa el profesional durante todo el proyecto."""
        return budget.total_hours / (self.duration_weeks * HOURS_PER_WEEK)

    @property
    def base_hours(self) -> int:
        return sum(budget.base_hours for budget in self.role_budgets)

    @property
    def contingency_hours(self) -> Decimal:
        return sum((budget.contingency_hours for budget in self.role_budgets), Decimal(0))

    @property
    def total_hours(self) -> Decimal:
        return self.base_hours + self.contingency_hours

    @property
    def fees(self) -> int:
        """Honorarios: la suma de los importes de cada profesional."""
        return sum(budget.amount for budget in self.role_budgets)

    @property
    def expenses_total(self) -> int:
        return sum(expense.amount for expense in self.expenses)

    @property
    def total_price(self) -> int:
        return self.fees + self.expenses_total


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
            "Plataforma web, usable en tablet en planta, que extrae habilidades y certificaciones "
            "de los registros de formación y de las órdenes de trabajo con un LLM, las mapea a la "
            "taxonomía O*NET del Departamento de Trabajo de EE. UU. y permite buscar candidatos "
            "internos para puestos críticos. Cada persona valida su perfil, RR. HH. ve las brechas "
            "por planta y el buscador se prueba contra sesgos. Termina con un piloto en una planta, "
            "el despliegue a toda la plantilla y dos semanas de hipercuidado."
        ),
        tasks=(
            Task(
                "Descubrimiento con RR. HH., operaciones, mantenimiento y seguridad, con visitas a una planta y una cantera",
                {"Gestión de proyecto": 32, "Liderazgo técnico": 24, "Diseño UX/UI": 24, "Consultoría de RR. HH.": 24},
            ),
            Task("Adaptación de O*NET a unos 60 puestos de planta y cantera", {"Consultoría de RR. HH.": 64, "IA / ML": 16}),
            Task(
                "Diseño UX/UI para tablet: perfil, validación, buscador y panel, con pruebas con 8 usuarios",
                {"Diseño UX/UI": 152},
            ),
            Task("Arquitectura, modelo de datos y API", {"Liderazgo técnico": 80, "Backend": 80}),
            Task("Inicio de sesión con Microsoft (SSO) y roles", {"Backend": 40}),
            Task("Integración con el HRIS y el sistema de formación", {"Backend": 96}),
            Task("Importación de las órdenes de trabajo del sistema de mantenimiento", {"Backend": 48}),
            Task(
                "Extracción de habilidades con un LLM: pipeline, conjunto de evaluación y revisión humana",
                {"IA / ML": 168},
            ),
            Task("Mapeo de habilidades y certificaciones a O*NET", {"IA / ML": 64}),
            Task("Buscador semántico de candidatos internos", {"IA / ML": 96, "Backend": 24}),
            Task(
                "Pruebas de sesgo del buscador y registro de sus resultados durante 4 años",
                {"IA / ML": 48, "Consultoría de RR. HH.": 16},
            ),
            Task("Frontend para tablet: perfil, validación por la persona y buscador", {"Frontend": 216}),
            Task(
                "Panel de brechas por planta y de puestos críticos con jubilaciones próximas",
                {"Frontend": 88, "Backend": 24},
            ),
            Task(
                "Privacidad y seguridad: aviso a empleados, derechos CCPA/CPRA y registro de accesos",
                {"Backend": 56, "Liderazgo técnico": 24},
            ),
            Task("Infraestructura en la nube, entornos, CI/CD y monitorización", {"DevOps": 96}),
            Task("Plan de pruebas y pruebas funcionales, de regresión y de accesibilidad", {"QA": 168}),
            Task(
                "Piloto en una planta: validación de la extracción con 50 perfiles y ajustes",
                {"Gestión de proyecto": 16, "IA / ML": 40, "QA": 32, "Consultoría de RR. HH.": 16, "Frontend": 24, "Liderazgo técnico": 16},
            ),
            Task(
                "Despliegue a toda la plantilla, formación a RR. HH. y supervisores, documentación y traspaso",
                {"Gestión de proyecto": 24, "Liderazgo técnico": 24, "Backend": 16, "DevOps": 16, "Consultoría de RR. HH.": 8},
            ),
            Task("Hipercuidado durante las dos semanas siguientes al lanzamiento", {"Backend": 40, "Frontend": 24, "IA / ML": 16}),
            Task("Liderazgo técnico: revisiones de código, decisiones de arquitectura y seguridad", {"Liderazgo técnico": 80}),
            Task("Gestión del proyecto: planificación, seguimiento semanal, comité mensual y riesgos", {"Gestión de proyecto": 96}),
        ),
        hourly_rate=Decimal("146.79"),
        expenses=(
            Expense("Viajes a una planta, una cantera y la planta piloto (3 viajes de 240 millas a 0.725 USD/milla)", 522),
            Expense("API de modelos de lenguaje y embeddings durante el desarrollo y la evaluación", 400),
            Expense("Entornos de desarrollo y pruebas en la nube durante 4 meses", 1600),
        ),
        duration_weeks=16,
        phases=(
            "3 de descubrimiento y diseño, 9 de construcción, 2 de piloto en una planta y 2 de "
            "despliegue e hipercuidado."
        ),
        risks=(
            "Muchos operadores no tienen un CV actualizado: la fuente principal son los registros de "
            "formación y las órdenes de trabajo. La extracción se valida en el piloto con 50 "
            "perfiles antes de procesar toda la plantilla.",
            "El buscador apoya decisiones de movilidad y promoción. En California, usar un sistema "
            "automatizado en decisiones de empleo exige poder demostrar que no discrimina, por eso "
            "se incluyen pruebas de sesgo y se conservan sus registros.",
            "Los perfiles de habilidades son información personal protegida por la CCPA/CPRA, que "
            "en California también cubre a los empleados: cada persona ve y corrige el suyo, y "
            "RR. HH. solo ve agregados por planta salvo consentimiento.",
            "La formación de seguridad MSHA (Parte 46, que cubre el cemento y los áridos) incluye un "
            "reciclaje anual: el perfil muestra su vigencia, pero la fuente oficial sigue siendo el "
            "sistema de formación. Las visitas a la cantera requieren la formación sobre los riesgos "
            "del lugar que MSHA exige a los visitantes, y la imparte el cliente.",
            "Si las plantas están sindicadas, las vacantes y las promociones siguen el convenio "
            "colectivo (publicación de puestos y antigüedad): el buscador sugiere candidatos y "
            "orienta la formación, pero no sustituye ese proceso.",
            "Existen plataformas SaaS de habilidades. Este desarrollo se justifica si las fuentes "
            "propias del sector (órdenes de trabajo y registros de MSHA) pesan más que lo que ofrece "
            "una plataforma estándar; conviene compararlo durante el descubrimiento. El soporte "
            "después del hipercuidado se presupuesta aparte.",
            "Se asume que el HRIS y el sistema de formación exponen una API. Si solo exportan "
            "ficheros, hay que sumar unas 40 horas de backend. El consumo de la API del LLM y la "
            "nube en producción se facturan aparte.",
        ),
    ),
    ReferenceEstimation(
        title="App de escucha continua para conductores y personal de planta",
        project_type="App móvil (iOS y Android) con panel web",
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
        project_summary=(
            "App móvil multiplataforma con encuestas de pulso semanales, reconocimientos y un canal "
            "anónimo para avisos de seguridad y otros problemas, en inglés y español, con acceso "
            "por número de teléfono y modo sin conexión para canteras sin cobertura. Un panel "
            "web muestra a RR. HH. los resultados por planta, solo en grupos de 10 respuestas o "
            "más, y alerta de tendencias de desgaste y fatiga. Incluye un piloto en 3 plantas, el "
            "despliegue en las 30 y dos semanas de hipercuidado."
        ),
        tasks=(
            Task(
                "Descubrimiento con RR. HH., seguridad y operaciones, con visitas a 2 plantas y una reunión con representantes de los Teamsters",
                {"Gestión de proyecto": 32, "Consultoría de RR. HH.": 24, "Diseño UX/UI": 24, "Liderazgo técnico": 16},
            ),
            Task(
                "Diseño de las encuestas de pulso (preguntas validadas de compromiso, carga de trabajo y fatiga) y su versión en español",
                {"Consultoría de RR. HH.": 72},
            ),
            Task(
                "Diseño UX/UI móvil y del panel web: responder en menos de un minuto, también con guantes y a pleno sol",
                {"Diseño UX/UI": 168},
            ),
            Task("Arquitectura, modelo de datos y API", {"Liderazgo técnico": 64, "Backend": 64}),
            Task(
                "Programación de encuestas y notificaciones push según el turno, nunca en pausas ni fuera del turno",
                {"Backend": 80},
            ),
            Task("Acceso con número de teléfono y código SMS", {"Backend": 40}),
            Task(
                "Anonimato: umbral mínimo de 10 respuestas por grupo y separación de identidades",
                {"Backend": 48, "Liderazgo técnico": 16},
            ),
            Task("App multiplataforma: encuestas, reconocimientos y canal anónimo", {"Móvil": 320}),
            Task("Modo sin conexión y sincronización para canteras sin cobertura", {"Móvil": 64}),
            Task("Soporte en inglés y español", {"Móvil": 24}),
            Task("Envío de los avisos de seguridad del canal anónimo a su responsable, con plazos", {"Backend": 32}),
            Task("Panel web de RR. HH. con resultados por planta", {"Frontend": 176}),
            Task("Alertas de tendencia de desgaste y fatiga por planta", {"Ingeniería de datos": 80}),
            Task("Infraestructura, CI/CD móvil y publicación en App Store y Google Play", {"DevOps": 96}),
            Task(
                "Pruebas en dispositivos reales, también Android de gama baja, en planta y en cantera",
                {"QA": 216},
            ),
            Task(
                "Piloto en 3 plantas: soporte, análisis de la participación y ajustes",
                {"Gestión de proyecto": 24, "Consultoría de RR. HH.": 24, "Móvil": 40, "Backend": 24, "Ingeniería de datos": 16},
            ),
            Task(
                "Despliegue en las 30 plantas: materiales en inglés y español, y formación a jefes de planta y RR. HH.",
                {"Gestión de proyecto": 24, "Consultoría de RR. HH.": 16},
            ),
            Task("Hipercuidado durante las dos semanas siguientes al lanzamiento", {"Móvil": 40, "Backend": 24}),
            Task("Liderazgo técnico: revisiones de código, decisiones de arquitectura y seguridad", {"Liderazgo técnico": 72}),
            Task("Gestión del proyecto: planificación, seguimiento semanal, comité mensual y riesgos", {"Gestión de proyecto": 108}),
        ),
        hourly_rate=Decimal("114.75"),
        expenses=(
            Expense("Viajes a 2 plantas en el descubrimiento y a 3 en el piloto (5 viajes de 120 millas a 0.725 USD/milla)", 435),
            Expense("Traducción profesional al español de la app, las encuestas y los materiales (unas 12,000 palabras a 0.14 USD)", 1680),
            Expense("Registro de la marca y la campaña de SMS (10DLC) y cuota de la campaña durante el proyecto", 101),
            Expense("Dispositivos de prueba: dos Android de gama baja y uno resistente", 900),
            Expense("Entornos de desarrollo y pruebas en la nube durante 4.5 meses", 1800),
        ),
        duration_weeks=18,
        phases=(
            "3 de descubrimiento y diseño, 9 de construcción, 1 de revisión en las tiendas de apps, "
            "3 de piloto en 3 plantas y 2 de despliegue e hipercuidado."
        ),
        risks=(
            "Las encuestas se responden durante el turno y nunca en las pausas de comida o descanso, "
            "que en California deben quedar libres de toda tarea; responder fuera del turno puede "
            "considerarse tiempo de trabajo pagado. Los conductores solo responden con el camión "
            "detenido, porque la ley prohíbe usar el móvil en la mano al conducir.",
            "Las respuestas sobre bienestar y fatiga pueden ser información personal sensible según "
            "la CPRA: se usan solo de forma agregada y se declaran en el aviso de privacidad para "
            "empleados.",
            "El canal anónimo recibirá avisos de seguridad: no sustituye los procedimientos formales "
            "ante Cal/OSHA o MSHA, y la empresa debe definir quién los atiende y en qué plazo.",
            "La app afecta a las condiciones de trabajo de conductores representados por los "
            "Teamsters: conviene acordarla con el sindicato antes del piloto, y el calendario puede "
            "ajustarse.",
            "Los SMS a números de EE. UU. exigen registrar la marca y la campaña (10DLC), lo que "
            "lleva unas semanas. El coste de los SMS y la nube en producción se facturan aparte.",
            "Las cuentas de desarrollador de Apple (99 USD al año) y Google Play (25 USD) se abren a "
            "nombre del cliente, que es quien publica la app.",
            "Existen plataformas SaaS de escucha al empleado. Este desarrollo se justifica por el "
            "acceso sin correo corporativo, el modo sin conexión y el acuerdo con el sindicato; "
            "conviene compararlo durante el descubrimiento. El soporte después del hipercuidado se "
            "presupuesta aparte.",
        ),
    ),
    ReferenceEstimation(
        title="Pipeline de equidad salarial y reporte al CRD de California",
        project_type="Integración de datos interna con dashboard",
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
        project_summary=(
            "Pipeline mensual que une HRIS, nóminas y valoración de puestos en un almacén de datos, "
            "con los datos personales seudonimizados. Separa horas extra, pluses y salario "
            "prevaleciente; calcula la brecha bruta y ajustada por categoría, sexo y raza o etnia; "
            "genera los informes anuales para el CRD; avisa de las brechas no explicadas por encima "
            "del 5 % y ofrece un simulador de ajustes con presupuesto. La puesta en marcha incluye "
            "un primer cierre mensual en paralelo con el proceso manual."
        ),
        tasks=(
            Task(
                "Descubrimiento: inventario de fuentes, sesión con la asesoría legal y propuesta de categorías de trabajo similar en planta, cantera, transporte y oficinas",
                {"Gestión de proyecto": 32, "Consultoría de RR. HH.": 40, "Liderazgo técnico": 24, "Ciencia de datos": 16},
            ),
            Task("Conectores con el HRIS y los dos sistemas de nómina", {"Ingeniería de datos": 128}),
            Task(
                "Unificación de los códigos de nómina, separación de horas extra, pluses y salario prevaleciente, y modelo de datos",
                {"Ingeniería de datos": 144, "Consultoría de RR. HH.": 32},
            ),
            Task("Seudonimización de los datos personales y permisos por rol", {"Liderazgo técnico": 40}),
            Task("Reglas de calidad de datos y conciliación con la nómina", {"Ingeniería de datos": 64}),
            Task(
                "Modelo de brecha ajustada por factores legítimos, con tratamiento de los grupos pequeños",
                {"Ciencia de datos": 160, "Consultoría de RR. HH.": 24},
            ),
            Task(
                "Generación de los informes anuales para el CRD, incluido el de trabajadores de agencias",
                {"Liderazgo técnico": 64, "Consultoría de RR. HH.": 16},
            ),
            Task("Alertas de brechas no explicadas por encima del 5 %", {"Ingeniería de datos": 24, "Ciencia de datos": 16}),
            Task("Simulador de escenarios de ajuste salarial con presupuesto", {"Ciencia de datos": 56, "Full-stack": 56}),
            Task("Dashboard de brechas para RR. HH.", {"Full-stack": 144, "Diseño UX/UI": 56}),
            Task("Orquestación mensual, monitorización y alertas del pipeline", {"DevOps": 80}),
            Task("Validación de las cifras contra la nómina y QA", {"QA": 120, "Consultoría de RR. HH.": 24}),
            Task(
                "Primer cierre mensual en paralelo con el proceso manual, formación a RR. HH. y documentación de la metodología para la asesoría legal",
                {"Gestión de proyecto": 16, "Ciencia de datos": 32, "Liderazgo técnico": 24, "Consultoría de RR. HH.": 16},
            ),
            Task("Hipercuidado durante el primer cierre mensual", {"Ingeniería de datos": 32}),
            Task("Liderazgo técnico: revisiones, decisiones de arquitectura y seguridad de los datos", {"Liderazgo técnico": 64}),
            Task("Gestión del proyecto: planificación, seguimiento semanal, comité mensual y riesgos", {"Gestión de proyecto": 96}),
        ),
        hourly_rate=Decimal("149.94"),
        expenses=(
            Expense("Viajes a las oficinas centrales (2 viajes de 100 millas a 0.725 USD/milla)", 145),
            Expense("Entorno de datos de desarrollo y pruebas en la nube durante 4 meses", 2000),
        ),
        duration_weeks=16,
        phases=(
            "3 de descubrimiento y modelo de datos, 9 de construcción, 2 de validación y 2 de "
            "primer cierre mensual en paralelo con el proceso manual."
        ),
        risks=(
            "Qué puestos hacen un trabajo sustancialmente similar lo decide la empresa con su "
            "asesoría legal: el proyecto lo implementa, no lo decide. El análisis se hace bajo la "
            "dirección de esa asesoría, para proteger la confidencialidad entre abogado y cliente.",
            "Los dos sistemas de nómina usan códigos de concepto distintos. Se asume un máximo de "
            "tres años de histórico; con más, la limpieza crece.",
            "En los puestos con convenio, el salario base lo fija la escala por categoría y "
            "antigüedad, así que las brechas suelen aparecer en el reparto de horas extra y en los "
            "puestos fuera de convenio (supervisión, ventas y oficinas): el modelo los analiza por "
            "separado.",
            "Desde 2016 (ley AB 219), los conductores que entregan hormigón en obra pública cobran "
            "salario prevaleciente según la ubicación de la planta: hay que separarlo del salario "
            "base para no confundirlo con una brecha.",
            "Hay pocas mujeres en planta, cantera y transporte, así que muchas categorías tienen "
            "grupos pequeños: los resultados se muestran con un tamaño mínimo de grupo y se "
            "interpretan con cautela.",
            "Los datos de los trabajadores de agencias dependen de que las agencias los entreguen a "
            "tiempo. Si el CRD cambia la plantilla del informe, la adaptación se presupuesta aparte.",
            "Los salarios individuales solo los ve RR. HH., con permisos por rol. Las licencias del "
            "almacén de datos no están incluidas.",
            "Existen plataformas SaaS de equidad salarial. Este desarrollo se justifica por las dos "
            "nóminas heredadas, los convenios y el salario prevaleciente; conviene compararlo durante "
            "el descubrimiento. El soporte después del primer cierre se presupuesta aparte.",
        ),
    ),
)
