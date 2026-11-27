"""Catálogo de componentes: la fuente de verdad de las horas del estimador.

El modelo no pone horas. En el inventario de alcance (app/schemas/inventory.py) elige qué
componentes hay que construir, de qué tamaño y para qué plataforma, y Python calcula las horas con
este catálogo (app/services/catalog_hours.py). Si el alcance no cambia, las horas tampoco.

El método es el de analogía de la guía de la GAO (GAO-20-195G): partir de lo que cuestan piezas
parecidas y documentar cada ajuste. Cada cifra dice de dónde sale en `basis`, y se separa lo que viene
de una fuente, lo que sale de los datos propios de la consultora y lo que es una convención nuestra:

- Fuente: las horas base de cada funcionalidad son las de una primera versión web (MVP) e incluyen
  su diseño, desarrollo y pruebas (Innovation Insight). De esa misma fuente salen las reglas del
  producto completo (×3), la app móvil (×1.2 por funcionalidad), web y móvil (×1.35), la
  configuración y el diseño de la aplicación, y el 35 % de gestión, QA y lanzamiento.
- Fuente: integraciones con sistemas de RR. HH. (Truto, Kombo e Integrate.io), descubrimiento y
  acompañamiento después del lanzamiento (UpBusinessCo) y reparto de un asistente sobre documentos
  (Lumeor).
- Datos propios: quién construye (backend, frontend o móvil, según la plataforma) y cómo se reparte
  el 35 % entre gestión, liderazgo técnico, QA y DevOps salen de las tres estimaciones de referencia
  de la consultora (app/context/examples.py). Es la analogía con datos propios que prefiere la GAO,
  y tests/test_catalog.py comprueba que las cifras coinciden con las referencias.
- Convención: el tamaño M es el punto medio entre S (MVP, ×1) y L (producto completo, ×3).
- Convención: dentro de cada componente, las horas se reparten entre perfiles con las fases del
  ISBSG (diseño 14.2 %, construcción 41.2 %, pruebas 16.1 %, implantación 9.0 %), normalizadas a
  las fases que tiene ese componente. Las pruebas de cada funcionalidad las hace quien la construye:
  el QA independiente está en el 35 %, como lo define Innovation Insight.

Casi todas las fuentes de horas son agencias de desarrollo que venden ese trabajo; son la semilla
del catálogo. Los componentes sin datos públicos de horas tienen `base_hours=None`: el modelo los
estima y el informe los marca para que una persona los revise (el juicio experto de la GAO). Cuando
la consultora tenga proyectos propios terminados, estas horas se cambian por las suyas.
"""

from dataclasses import dataclass
from typing import Literal

Platform = Literal["web", "movil", "web_y_movil"]
Size = Literal["S", "M", "L"]

# En un reparto, "construcción" es el perfil que construye la interfaz, según la plataforma.
BUILD = "construcción"


@dataclass(frozen=True)
class Source:
    publisher: str
    title: str
    url: str
    date: str  # fecha de publicación o, si la página no la tiene, de la consulta
    kind: str  # estándar, datos independientes, encuesta, agencia de desarrollo o proveedor
    note: str


SOURCES: dict[str, Source] = {
    "innovation_insight": Source(
        "Innovation Insight",
        "App Development Cost Calculator y desgloses por funcionalidad",
        "https://www.innovation-insight.com/app-development-cost-calculator",
        "2026-10-13",
        "agencia de desarrollo",
        "Horas de sus planes de proyecto, con diseño, desarrollo y pruebas de cada funcionalidad. "
        "Producto completo ×3, móvil ×1.2, web y móvil ×1.35 y 35 % de gestión, QA y lanzamiento. "
        "Equipo sénior fuera de EE. UU.",
    ),
    "rorix": Source(
        "Rorix Technologies",
        "SaaS Development Cost: 2026 Pricing Guide",
        "https://www.rorixtech.com/blogs/saas/saas-development-cost",
        "2026-10-14",
        "agencia de desarrollo",
        "Rangos por funcionalidad: inicio de sesión 40-80 h, roles 60-120 h, paneles 80-160 h. "
        "Se usan para contrastar.",
    ),
    "brocoders": Source(
        "Brocoders",
        "How Much a SaaS MVP Costs in 2026 (A Real 9-Module Build, Hour by Hour)",
        "https://brocoders.com/blog/how-much-saas-mvp-costs-2026/",
        "2026-07-24",
        "agencia de desarrollo",
        "Un MVP real de 9 módulos en unas 600 h: administración 70 h, paneles 40 h. Contraste.",
    ),
    "techsy": Source(
        "Techsy",
        "SaaS Development Cost Calculator",
        "https://techsy.io/en/resources/tools/saas-development-cost-calculator",
        "2026-11-24",
        "agencia de desarrollo",
        "QA 20 % y gestión 15 % sobre el desarrollo. Se usa como contraste del 35 %.",
    ),
    "upbusiness": Source(
        "UpBusinessCo",
        "MVP Development Cost 2026",
        "https://upbusinessco.com/blogs/mvp-development-cost/",
        "2026-10-29",
        "agencia de desarrollo",
        "Supuestos de planificación: descubrimiento de 1 semana con producto, diseño y desarrollo; "
        "arreglos después del lanzamiento de 5 semanas-persona con desarrollo y QA.",
    ),
    "truto": Source(
        "Truto",
        "The 2026 HRIS Unified API Buying Guide",
        "https://truto.one/blog/the-2026-hris-unified-api-buying-guide-cheat-sheet-for-pms/",
        "2026-11-24",
        "proveedor",
        "Una integración nativa con un HRIS: 2-4 semanas de un ingeniero sénior. Vende una API "
        "unificada, así que le conviene que integrar parezca caro.",
    ),
    "kombo": Source(
        "Kombo",
        "Best Unified API Platforms for ATS and HRIS Integrations in 2026",
        "https://www.kombo.dev/blog/best-unified-api-platforms-for-hr-tech-2026",
        "2026-10-19",
        "proveedor",
        "4-5 semanas de desarrollo por integración; varios meses para Workday o SAP SuccessFactors. "
        "Vende una API unificada.",
    ),
    "integrate_io": Source(
        "Integrate.io",
        "Finch API Alternatives: 7 Ways to Pull Payroll and HRIS Data in 2026",
        "https://www.integrate.io/blog/finch-api-alternatives/",
        "2026-10-05",
        "proveedor",
        "4-8 semanas de ingeniería por integración con un HRIS; 2-4 meses o más para Workday.",
    ),
    "lumeor": Source(
        "Lumeor Studio",
        "How much does a RAG knowledge assistant cost?",
        "https://www.lumeor.studio/cost/cost-of-rag-knowledge-assistant/",
        "2026-11-24",
        "agencia de desarrollo",
        "Reparto de un asistente sobre documentos: fuentes 10-15 %, preparación 20-30 %, búsqueda "
        "15-20 %, respuestas 10-15 %, evaluación 15-20 %, interfaz 10-15 %.",
    ),
    "isbsg": Source(
        "ISBSG",
        "Project Planning: Phase Effort Ratios",
        "https://www.isbsg.org/wp-content/uploads/2017/08/Planning-projects-Phase-Effort-Ratios-Aug-2017.pdf",
        "2017-08",
        "datos independientes",
        "86 proyectos nuevos: planificación 8.1 %, especificación 11.5 %, diseño 14.2 %, "
        "construcción 41.2 %, pruebas 16.1 %, implantación 9.0 %.",
    ),
    "gao": Source(
        "U.S. Government Accountability Office",
        "Cost Estimating and Assessment Guide (GAO-20-195G)",
        "https://www.gao.gov/products/gao-20-195g",
        "2020-03-12",
        "estándar",
        "Desglose del producto, analogía con ajustes documentados y juicio experto sin datos.",
    ),
    "sapient": Source(
        "Sapient Insights Group",
        "28th Annual 2025-2026 HR Systems Survey",
        "https://sapientinsights.com/downloads/28th-annual-hr-systems-survey-report/",
        "2025-09",
        "datos independientes",
        "Más de 4,600 organizaciones: clasificación de las aplicaciones de RR. HH. en seis familias.",
    ),
    "hr_com": Source(
        "HR.com HR Research Institute",
        "State of Today's HR Technology and Integrations 2025",
        "https://info.clearcompany.com/hubfs/_RESOURCES/2025/03-20-25-HRdotcom-State-of-Todays-HR-Technology-and-Integrations-2025-Research-Report-ClearCompany.pdf",
        "2025-03",
        "encuesta",
        "153 profesionales de RR. HH., sobre todo de EE. UU.: qué tienen y qué echan en falta.",
    ),
    "crd": Source(
        "California Civil Rights Department",
        "Regulaciones sobre sistemas automatizados de decisión en el empleo",
        "https://calcivilrights.ca.gov/2025/06/30/civil-rights-council-secures-approval-for-regulations-to-protect-against-employment-discrimination-related-to-artificial-intelligence/",
        "2025-06-30",
        "estándar",
        "Vigentes desde el 1 de octubre de 2025: las pruebas contra sesgos cuentan como evidencia y "
        "los datos se guardan cuatro años.",
    ),
    "nyc_ll144": Source(
        "NYC Department of Consumer and Worker Protection",
        "Automated Employment Decision Tools: FAQ",
        "https://www.nyc.gov/site/dca/businesses/faq-automated-employment-decision-tools.page",
        "2026-11-24",
        "estándar",
        "Auditoría de sesgo independiente cada año y aviso a los candidatos.",
    ),
}

# ---- Reglas generales (fuente: Innovation Insight, salvo M, que es una convención)
SIZE_FACTORS: dict[str, float] = {"S": 1.0, "M": 2.0, "L": 3.0}
SIZE_CRITERIA: dict[str, str] = {
    "S": "Primera versión: el flujo principal que un usuario real ya usaría, sin casos límite",
    "M": "El flujo principal con variantes, configuración o más de un tipo de usuario",
    "L": "Producto completo: casos límite, administración avanzada, escala y pulido",
}
PLATFORM_FACTORS: dict[str, float] = {"web": 1.0, "movil": 1.2, "web_y_movil": 1.35}
PLATFORM_NAMES: dict[str, str] = {
    "web": "Web (también instalable en tablets y móviles)",
    "movil": "App móvil nativa (iOS y Android, un solo código)",
    "web_y_movil": "App móvil nativa y aplicación web",
}

# Proyecto: configuración, arquitectura y lanzamiento, y diseño de la interfaz (Innovation Insight).
SETUP_HOURS: dict[str, int] = {"web": 140, "movil": 220, "web_y_movil": 300}
DESIGN_HOURS: dict[str, int] = {"web": 90, "movil": 108, "web_y_movil": 135}
DISCOVERY_HOURS = 120  # UpBusinessCo: 1 semana × 3 personas (producto, diseño y desarrollo)
OVERHEAD_RATE = 0.35  # Innovation Insight: gestión, QA y lanzamiento

# ---- Reparto entre perfiles con los datos propios de la consultora: sus tres estimaciones de
# referencia (app/context/examples.py). tests/test_catalog.py comprueba estas cifras con ellas.
# Quién construye, según la plataforma, con las horas de las referencias como pesos:
# - web: backend y frontend, como en la referencia 1 (plataforma web con IA);
# - móvil, y web y móvil: backend, frontend y móvil, como en la referencia 2 (app móvil con panel
#   web). Sin panel web, el frontend no está.
BUILD_ROLES: dict[str, dict[str, int]] = {
    "web": {"Backend": 424, "Frontend": 352},
    "movil": {"Backend": 312, "Móvil": 488},
    "web_y_movil": {"Backend": 312, "Frontend": 176, "Móvil": 488},
}
# El 35 % transversal se reparte con el peso medio de cada perfil en las tres referencias, en % de
# sus horas: gestión 7.4, 9.1 y 8.8; liderazgo técnico 11.0, 8.1 y 13.2; QA 8.9, 10.4 y 7.3; DevOps
# 5.0, 4.6 y 4.9.
OVERHEAD_SPLIT: dict[str, float] = {
    "Gestión de proyecto": 8.4,
    "Liderazgo técnico": 10.8,
    "QA": 8.9,
    "DevOps": 4.8,
}

# ---- Repartos con las fases del ISBSG (diseño, construcción, pruebas e implantación). Las
# pruebas de cada funcionalidad las hace quien la construye; el QA independiente está en el 35 %.
DESIGN, BUILDING, TESTING, IMPLEMENTATION = 14.2, 41.2, 16.1, 9.0
FEATURE_SPLIT = {"Diseño UX/UI": DESIGN, BUILD: BUILDING + TESTING}
BACKEND_SPLIT = {"Backend": BUILDING + TESTING}
SETUP_SPLIT = {"Liderazgo técnico": DESIGN, BUILD: BUILDING, "DevOps": IMPLEMENTATION}
DISCOVERY_SPLIT = {"Consultoría de RR. HH.": 1, "Diseño UX/UI": 1, "Liderazgo técnico": 1}


@dataclass(frozen=True)
class Component:
    id: str
    name: str
    family: str
    includes: str  # qué cubre; el modelo lo lee para elegir
    base_hours: int | None  # tamaño S en web; None si no hay datos públicos de horas
    split: dict[str, float]  # perfil (o "construcción") → peso
    sources: tuple[str, ...]
    basis: str  # de dónde salen las horas
    scales_with_platform: bool = True  # las funcionalidades con pantallas cuestan más en móvil
    sized: bool = True  # si el tamaño S, M o L cambia las horas
    hours_by_size: dict[str, int] | None = None  # cuando la fuente da las horas por tamaño
    size_criteria: dict[str, str] | None = None  # criterios propios en lugar de SIZE_CRITERIA

    @property
    def needs_review(self) -> bool:
        return self.base_hours is None and self.hours_by_size is None


def _ii(hours: int, how: str) -> str:
    return f"Innovation Insight: {hours} h en una primera versión web ({how})"


COMPONENTS: dict[str, Component] = {
    component.id: component
    for component in (
        # ---- Base de la aplicación
        Component(
            "cuentas_y_roles", "Cuentas de usuario y roles", "Base de la aplicación",
            "Registro, inicio de sesión, recuperación de contraseña y permisos por rol",
            40, FEATURE_SPLIT, ("innovation_insight", "rorix"),
            _ii(40, "48 h en móvil ÷ 1.2") + ". Rorix da 40-80 h el inicio de sesión y 60-120 h los roles",
        ),
        Component(
            "inicio_sesion_unico", "Inicio de sesión único (SSO)", "Base de la aplicación",
            "Entrar con la cuenta corporativa (Microsoft 365, Google Workspace u otro proveedor)",
            12, FEATURE_SPLIT, ("innovation_insight",), _ii(12, "14 h en móvil ÷ 1.2"),
        ),
        Component(
            "busqueda_y_filtros", "Búsqueda y filtros", "Base de la aplicación",
            "Buscar y filtrar registros, por ejemplo personas, sedes o cursos",
            36, FEATURE_SPLIT, ("innovation_insight",), _ii(36, "43 h en móvil ÷ 1.2"),
        ),
        Component(
            "archivos", "Carga de archivos y multimedia", "Base de la aplicación",
            "Subir, guardar y mostrar documentos, fotos o videos",
            28, FEATURE_SPLIT, ("innovation_insight",), _ii(28, "34 h en móvil ÷ 1.2"),
        ),
        Component(
            "notificaciones", "Notificaciones y recordatorios", "Base de la aplicación",
            "Avisos push y por correo, incluidos recordatorios programados, como un vencimiento",
            24, FEATURE_SPLIT, ("innovation_insight",), _ii(24, "29 h en móvil ÷ 1.2"),
        ),
        Component(
            "panel_administracion", "Panel de administración", "Base de la aplicación",
            "Pantallas para que el cliente gestione usuarios, contenidos y configuración",
            70, FEATURE_SPLIT, ("innovation_insight", "brocoders"),
            _ii(70, "84 h en móvil ÷ 1.2") + ". Brocoders: 70 h en un MVP real",
        ),
        Component(
            "varios_idiomas", "Varios idiomas", "Base de la aplicación",
            "La interfaz en más de un idioma, por ejemplo inglés y español",
            24, FEATURE_SPLIT, ("innovation_insight",),
            "Innovation Insight publica su costo (900-1,000 USD), en el mismo tramo que las "
            "notificaciones, que son 24 h; las horas se deducen de ese costo",
        ),
        Component(
            "modo_sin_conexion", "Modo sin conexión y sincronización", "Base de la aplicación",
            "Usar la aplicación sin cobertura y sincronizar los datos al recuperarla",
            56, FEATURE_SPLIT, ("innovation_insight",), _ii(56, "67 h en móvil ÷ 1.2"),
        ),
        Component(
            "agenda", "Agenda y reservas", "Base de la aplicación",
            "Calendario, citas o turnos, por ejemplo entrevistas o turnos de trabajo",
            64, FEATURE_SPLIT, ("innovation_insight",), _ii(64, "86 h en web y móvil ÷ 1.35"),
        ),
        Component(
            "chat", "Chat dentro de la aplicación", "Base de la aplicación",
            "Mensajes entre usuarios dentro de la aplicación",
            72, FEATURE_SPLIT, ("innovation_insight",), _ii(72, "86 h en móvil ÷ 1.2"),
        ),
        Component(
            "lecciones_y_cuestionarios", "Lecciones, cuestionarios y progreso", "Formación",
            "Módulos de formación con contenidos, cuestionarios y seguimiento del avance de cada persona",
            96, FEATURE_SPLIT, ("innovation_insight",), _ii(96, "115 h en móvil ÷ 1.2"),
        ),
        # ---- Integraciones
        Component(
            "integracion_servicio_externo", "Integración con un servicio externo", "Integraciones",
            "Conectar con una API documentada de terceros, como firma electrónica, correo o un "
            "portal de empleo. Una unidad por servicio",
            36, BACKEND_SPLIT, ("innovation_insight",),
            "Innovation Insight: 36 h por integración, igual en web y en móvil",
            scales_with_platform=False, sized=False,
        ),
        Component(
            "integracion_hris", "Integración con un sistema de RR. HH. o nómina", "Integraciones",
            "Leer o escribir empleados, estructura o nómina en un HRIS con API estándar, como "
            "BambooHR, Rippling, Gusto, UKG o ADP. Una unidad por sistema",
            None, BACKEND_SPLIT, ("truto", "kombo", "integrate_io"),
            "S: 2 semanas de un ingeniero (Truto, 2-4 semanas); M: 4.5 semanas (Kombo, 4-5 "
            "semanas); L: 8 semanas (Integrate.io, 4-8 semanas). Semanas de 40 h",
            scales_with_platform=False,
            hours_by_size={"S": 80, "M": 180, "L": 320},
            size_criteria={
                "S": "API sencilla y solo lectura de empleados, como BambooHR",
                "M": "Lectura y escritura, o datos de nómina, en una API estándar",
                "L": "Requiere acuerdo de partner o certificados, como ADP, o sincroniza muchos objetos",
            },
        ),
        Component(
            "integracion_hris_empresarial", "Integración con un HRIS empresarial", "Integraciones",
            "Integrar con Workday o SAP SuccessFactors, con modelos de datos propios de cada empresa "
            "y fechas efectivas. Una unidad por sistema",
            None, BACKEND_SPLIT, ("integrate_io", "kombo", "truto"),
            "Integrate.io: 2-4 meses o más para Workday. S: 2 meses, M: 3, L: 4 (meses de 160 h). "
            "Kombo y Truto también hablan de varios meses",
            scales_with_platform=False,
            hours_by_size={"S": 320, "M": 480, "L": 640},
            size_criteria={
                "S": "Solo lectura de un objeto, como los empleados",
                "M": "Lectura de varios objetos, como empleados, puestos y estructura",
                "L": "Lectura y escritura, o configuraciones distintas por empresa",
            },
        ),
        # ---- Datos y analítica
        Component(
            "paneles_y_reportes", "Paneles y reportes", "Datos y analítica",
            "Indicadores, gráficos y reportes con filtros, por ejemplo por sede o por equipo",
            48, FEATURE_SPLIT, ("innovation_insight", "rorix", "brocoders"),
            _ii(48, "58 h en móvil ÷ 1.2") + ". Rorix: 80-160 h; Brocoders: 40 h en un MVP real",
        ),
        Component(
            "analitica_de_personas", "Analítica de personas con historial", "Datos y analítica",
            "Modelo de datos con la historia de cada persona (altas, bajas, cambios de puesto y de "
            "jefe) e indicadores como rotación o antigüedad, cruzados con otras fuentes",
            None, {}, ("sapient",),
            "Sin datos públicos de horas: lo estima el modelo y se revisa",
        ),
        Component(
            "modelo_predictivo", "Modelo predictivo", "Datos y analítica",
            "Un modelo estadístico o de aprendizaje automático, como el riesgo de rotación, con su "
            "validación y su explicación para los usuarios",
            None, {}, ("crd",),
            "Sin datos públicos de horas: lo estima el modelo y se revisa",
        ),
        Component(
            "encuestas", "Encuestas a empleados", "Datos y analítica",
            "Encuestas programadas o puntuales, su envío y sus resultados agregados sin identificar "
            "a las personas",
            None, {}, ("hr_com",),
            "Sin datos públicos de horas: lo estima el modelo y se revisa",
        ),
        # ---- Inteligencia artificial
        Component(
            "asistente_ia", "Asistente con IA", "Inteligencia artificial",
            "Un chat o asistente con un modelo de lenguaje, sin documentos propios de la empresa",
            130, {"Diseño UX/UI": DESIGN, "IA / ML": BUILDING + TESTING},
            ("innovation_insight",), _ii(130, "su calculadora"),
        ),
        Component(
            "asistente_sobre_documentos", "Asistente con IA sobre documentos propios (RAG)",
            "Inteligencia artificial",
            "Respuestas con IA a partir de manuales o políticas de la empresa, citando la fuente y "
            "diciendo que no sabe cuando no hay respuesta, con su conjunto de preguntas de evaluación",
            180,
            {
                "Consultoría de RR. HH.": 12.5,  # revisar y acotar las fuentes
                "Ingeniería de datos": 25,  # preparar y dividir los documentos
                "IA / ML": 30,  # búsqueda (17.5) y respuestas (12.5)
                "QA": 17.5,  # evaluación
                BUILD: 12.5,  # interfaz
            },
            ("innovation_insight", "lumeor"),
            _ii(180, "su calculadora") + ". Reparto con los puntos medios de Lumeor",
        ),
        # ---- Cumplimiento
        Component(
            "privacidad_datos", "Privacidad de los datos personales", "Cumplimiento",
            "Consentimiento, exportación, borrado y conservación de los datos personales "
            "(CCPA/CPRA en California)",
            24, BACKEND_SPLIT, ("innovation_insight", "crd"),
            "Innovation Insight: 24 h para los requisitos del RGPD europeo (consentimiento, "
            "exportación, borrado y conservación), que se toman como análogos de la CCPA/CPRA",
            scales_with_platform=False, sized=False,
        ),
        Component(
            "documentos_y_firmas", "Documentos generados y firmas en pantalla", "Cumplimiento",
            "Generar documentos, como certificados o formularios en PDF, y firmarlos en la pantalla",
            None, {}, (),
            "Sin datos públicos de horas: lo estima el modelo y se revisa. Si la firma usa un "
            "proveedor externo, como DocuSign, es una integración con un servicio externo",
        ),
        Component(
            "prueba_de_sesgo", "Prueba de sesgo de decisiones automatizadas", "Cumplimiento",
            "Medir si un sistema que apoya decisiones de empleo trata distinto a grupos protegidos "
            "y documentarlo, como piden las normas de California y Nueva York",
            None, {}, ("crd", "nyc_ll144"),
            "Sin datos públicos de horas: lo estima el modelo y se revisa",
        ),
        # ---- Puesta en marcha
        Component(
            "acompanamiento_lanzamiento", "Acompañamiento después del lanzamiento",
            "Puesta en marcha",
            "Arreglos y soporte en las semanas siguientes al lanzamiento o a un piloto",
            200, {BUILD: 1, "QA": 1}, ("upbusiness",),
            "UpBusinessCo: 5 semanas-persona de desarrollo y QA después del lanzamiento de un SaaS "
            "de 48 semanas-persona; mitad y mitad por convención",
            scales_with_platform=False, sized=False,
        ),
        Component(
            "formacion_y_cambio", "Formación de usuarios y gestión del cambio", "Puesta en marcha",
            "Formar a los usuarios, acompañar un piloto en sus sedes y preparar el despliegue",
            None, {}, (),
            "Sin datos públicos de horas: lo estima el modelo y se revisa",
        ),
    )
}

CUSTOM = "a_medida"  # para lo que no encaja en ningún componente


@dataclass(frozen=True)
class ProductType:
    id: str
    name: str
    family: str  # la familia de Sapient Insights
    evidence: str  # cuánto se usa o se pide, con su fuente
    components: tuple[str, ...]


PRODUCT_TYPES: dict[str, ProductType] = {
    product.id: product
    for product in (
        ProductType("incorporacion", "Incorporación (onboarding)", "Talento",
                    "HR.com: el 62 % lo tiene",
                    ("cuentas_y_roles", "archivos", "notificaciones", "panel_administracion",
                     "paneles_y_reportes", "integracion_hris")),
        ProductType("reclutamiento", "Reclutamiento y seguimiento de candidatos", "Talento",
                    "HR.com: el 74 % lo tiene",
                    ("cuentas_y_roles", "busqueda_y_filtros", "archivos", "notificaciones", "agenda",
                     "integracion_servicio_externo", "paneles_y_reportes", "prueba_de_sesgo")),
        ProductType("desempeno", "Gestión del desempeño", "Talento", "HR.com: el 65 % lo tiene",
                    ("cuentas_y_roles", "notificaciones", "paneles_y_reportes",
                     "panel_administracion")),
        ProductType("formacion", "Formación y certificaciones", "Talento",
                    "Sapient: aplicación de formación y desarrollo",
                    ("lecciones_y_cuestionarios", "cuentas_y_roles", "notificaciones",
                     "paneles_y_reportes", "archivos")),
        ProductType("tiempo", "Control horario, ausencias y turnos", "Gestión del tiempo",
                    "Sapient: el 88 % tiene control horario",
                    ("agenda", "modo_sin_conexion", "notificaciones", "integracion_hris",
                     "paneles_y_reportes")),
        ProductType("autoservicio", "Autoservicio y portal del empleado",
                    "Gestión y servicio de RR. HH.", "Sapient: autoservicio de empleados y jefes",
                    ("cuentas_y_roles", "inicio_sesion_unico", "busqueda_y_filtros", "archivos",
                     "integracion_hris")),
        ProductType("encuestas", "Encuestas de clima y escucha", "Gestión y servicio de RR. HH.",
                    "HR.com: el 56 % echa en falta herramientas de clima",
                    ("encuestas", "notificaciones", "paneles_y_reportes", "privacidad_datos")),
        ProductType("asistente_rrhh", "Asistente y mesa de ayuda de RR. HH.",
                    "Gestión y servicio de RR. HH.", "Sapient: mesa de ayuda y portales de RR. HH.",
                    ("asistente_sobre_documentos", "inicio_sesion_unico", "panel_administracion")),
        ProductType("seguridad_salud", "Seguridad y salud laboral", "Gestión y servicio de RR. HH.",
                    "Sapient: aplicación de seguridad y salud",
                    ("lecciones_y_cuestionarios", "modo_sin_conexion", "notificaciones",
                     "paneles_y_reportes", "documentos_y_firmas")),
        ProductType("analitica_personas", "Analítica de personas", "Analítica",
                    "HR.com: el 65 % la echa en falta",
                    ("integracion_hris", "analitica_de_personas", "paneles_y_reportes",
                     "modelo_predictivo", "prueba_de_sesgo")),
        ProductType("compensacion", "Compensación y equidad salarial", "Talento",
                    "HR.com: el 40 % tiene compensación total y el 47 % la echa en falta",
                    ("integracion_hris", "analitica_de_personas", "paneles_y_reportes",
                     "privacidad_datos")),
        ProductType("habilidades_sucesion", "Habilidades, carrera y sucesión", "Talento",
                    "HR.com: el 68 % echa en falta la sucesión y el 53 % las habilidades",
                    ("busqueda_y_filtros", "paneles_y_reportes", "analitica_de_personas")),
    )
}
