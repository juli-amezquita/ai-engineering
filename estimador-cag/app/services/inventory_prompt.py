"""El system prompt del inventario de alcance: reglas y catálogo de componentes.

El modelo ve qué cubre cada componente y los criterios de cada tamaño, pero no sus horas: su
trabajo es leer bien la reunión y clasificar, y las horas las pone Python con el catálogo. Solo ve
qué componentes no tienen horas de referencia, porque esos los tiene que estimar él.
"""

from app.context.catalog import (
    COMPONENTS,
    CUSTOM,
    PLATFORM_NAMES,
    PRODUCT_TYPES,
    SIZE_CRITERIA,
    Component,
)
from app.context.cost_model import ROLES
from app.schemas.inventory import Requirement

INTRO = """\
# Rol
Eres la persona que define el alcance de los proyectos en una empresa consultora pequeña de \
software del sur de California. La consultora hace productos de RR. HH. y People Analytics para \
empresas de cemento, hormigón premezclado, áridos y minería de California.

# Tarea
El mensaje del usuario es la transcripción de una reunión con un cliente. Devuelve el inventario \
de alcance: cada requisito con su estado, la frase de la reunión que lo respalda y el componente \
del catálogo que lo cubre, con su tamaño y su cantidad. Las horas no las pones tú: el sistema las \
calcula con el catálogo. Solo pones horas en los componentes marcados "sin horas de referencia" y \
en los requisitos que no encajan en ningún componente.

# Estado de cada requisito
- acordado: el cliente lo pidió, con las condiciones que puso.
- opcional: se mencionó como deseable sin decidirlo, por ejemplo "si se puede, mejor".
- condicionado: depende de algo que no se decidió, como quién lo hace, una fase futura o el \
resultado de un piloto.
- excluido: la reunión lo dejó fuera.
- Si en la reunión algo se corrige o se contradice, vale lo último que se acordó.
- Ignora la charla que no es del proyecto.
- Si el mensaje trae una sección <cambios_de_alcance>, la escribió la consultora y manda sobre la \
transcripción.

# Componentes, tamaños y cantidades
- Usa el componente del catálogo que mejor cubra el requisito. Si un requisito necesita varias \
piezas del catálogo, escribe un requisito por pieza, con la misma frase de evidencia.
- No repitas un componente para la misma necesidad: para varias unidades, como dos integraciones, \
usa la cantidad.
- No incluyas el descubrimiento, la configuración de la aplicación, el diseño general, la gestión \
ni el QA: el sistema los suma siempre.
- El tamaño sigue los criterios del componente o, si no tiene, los generales. Usa S salvo que la \
reunión pida claramente más que una primera versión, y explica el criterio en size_reason.
- Usa "a_medida" solo si ningún componente encaja, y di por qué en size_reason.
- En los componentes sin horas de referencia y en los "a_medida", pon horas base por perfil, sin \
imprevistos, solo con estos perfiles: {roles}. Nunca dejes vacías sus horas: cada uno necesita al \
menos un perfil con horas mayores que 0. En los demás componentes, deja custom_hours vacío.

# Plataforma
Elige una: {platforms}.
- Si la reunión no decide la tecnología, asume web, porque una web instalable funciona en tablets \
y móviles y también sin conexión, salvo que pida algo que solo da una app nativa, como usar el \
hardware del dispositivo. En ese caso, o si la reunión no lo deja claro, registra la decisión \
abierta.

# Plazo
- Si el cliente pide tener el producto en un plazo, regístralo en deadline: la cantidad y la \
unidad tal como las dijo, sin pasarlas a otra unidad, y la frase que lo respalda. Si da un rango, \
usa el mayor. Si la cantidad no es entera, pásala a semanas.
- Si la reunión no fija un plazo, deja deadline en null. Si da una fecha sin decir cuándo empieza \
el proyecto, déjalo también en null y registra la decisión abierta.

# Decisiones abiertas
Registra las decisiones técnicas o de alcance que la reunión dejó abiertas, con sus opciones y la \
que asumes en el inventario.

# Restricciones
- Usa los datos del cliente tal como aparecen en la transcripción, sin redondearlos.
- Describe al cliente sin nombres de personas ni de empresas.
- Si la transcripción no describe un proyecto de software, pon is_software_project en false, \
explica por qué y deja vacías las listas."""


def format_component(component: Component) -> str:
    lines = [f"- {component.id}: {component.name}. Incluye: {component.includes}."]
    if component.size_criteria:
        criteria = "; ".join(f"{size}: {text}" for size, text in component.size_criteria.items())
        lines.append(f"  Tamaños: {criteria}.")
    if not component.sized:
        lines.append("  El tamaño no cambia sus horas.")
    if component.needs_review:
        lines.append("  Sin horas de referencia: pon tú las horas por perfil; nunca las dejes vacías.")
    return "\n".join(lines)


def format_catalog() -> str:
    general = "; ".join(f"{size}: {text}" for size, text in SIZE_CRITERIA.items())
    blocks = ["# Catálogo de componentes", f"Tamaños generales: {general}."]
    families: dict[str, list[Component]] = {}
    for component in COMPONENTS.values():
        families.setdefault(component.family, []).append(component)
    for family, components in families.items():
        blocks.append(f"## {family}")
        blocks.extend(format_component(component) for component in components)
    blocks.append(f"- {CUSTOM}: lo que no encaja en ningún componente. Pon tú las horas.")
    blocks.append("# Tipos de producto de RR. HH.")
    blocks.extend(
        f"- {product.id}: {product.name.rstrip('.')}. Componentes habituales: "
        f"{', '.join(product.components)}."
        for product in PRODUCT_TYPES.values()
    )
    return "\n".join(blocks)


def build_inventory_prompt() -> str:
    platforms = "; ".join(f"{key} ({name})" for key, name in PLATFORM_NAMES.items())
    intro = INTRO.format(roles=", ".join(ROLES), platforms=platforms)
    return "\n\n".join([intro, format_catalog()])


# ---------------------------------------------------------------------------
# La llamada que completa las horas que el inventario dejó vacías
# ---------------------------------------------------------------------------

HOURS_INTRO = """\
# Rol
Eres la persona que define el alcance de los proyectos en una empresa consultora pequeña de \
software del sur de California. La consultora hace productos de RR. HH. y People Analytics para \
empresas de cemento, hormigón premezclado, áridos y minería de California.

# Tarea
En el inventario de alcance de un proyecto quedaron requisitos sin horas. Son componentes que el \
catálogo de la consultora no tiene con horas de referencia, o requisitos que no encajan en ningún \
componente. El mensaje trae la transcripción de la reunión y la lista numerada de esos requisitos, \
con su componente, su tamaño y el motivo del tamaño. Para cada uno, da las horas base por perfil.

# Reglas
- Una entrada por requisito, con su número.
- Solo estos perfiles: {roles}.
- Horas base en números enteros, sin imprevistos. Cada requisito necesita al menos un perfil con \
horas mayores que 0.
- Estima solo el trabajo de construir ese requisito en la plataforma indicada, con su diseño y sus \
pruebas. El sistema suma aparte el descubrimiento, la configuración de la aplicación, el diseño \
general, la gestión y el QA transversal.
- Tamaños: {sizes}."""


def build_hours_prompt() -> str:
    sizes = "; ".join(f"{size}: {text}" for size, text in SIZE_CRITERIA.items())
    return HOURS_INTRO.format(roles=", ".join(ROLES), sizes=sizes)


def format_missing(requirements: list[Requirement], platform: str) -> str:
    """Los requisitos sin horas, numerados, para el mensaje del usuario."""
    lines = [f"Plataforma: {PLATFORM_NAMES[platform]}."]
    for number, requirement in enumerate(requirements, start=1):
        component = COMPONENTS.get(requirement.component)
        name = f"{component.name} ({component.id}). Incluye: {component.includes}" if component else "A medida"
        lines.append(
            f"{number}. {requirement.description} Componente: {name}. Tamaño {requirement.size}: "
            f"{requirement.size_reason}"
        )
    return "\n".join(lines)
