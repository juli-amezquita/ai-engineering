"""Las horas del inventario, calculadas con el catálogo: el modelo no las pone.

Para cada requisito acordado, el componente da sus horas según el tamaño, la plataforma y la
cantidad, y las reparte entre perfiles. El proyecto suma el descubrimiento, la configuración y el
diseño de la aplicación, y un 35 % transversal (gestión, liderazgo técnico, QA y lanzamiento) sobre
la construcción. Los requisitos que no
están acordados no se estiman: los decide la consultora.

Lo que el catálogo no cubre (componentes sin horas o requisitos a medida) usa las horas del modelo
y queda marcado para revisión. Todas las reglas y sus fuentes están en app/context/catalog.py.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from app.context.catalog import (
    BUILD,
    BUILD_ROLES,
    COMPONENTS,
    CUSTOM,
    DESIGN_HOURS,
    DISCOVERY_HOURS,
    DISCOVERY_SPLIT,
    OVERHEAD_RATE,
    OVERHEAD_SPLIT,
    PLATFORM_FACTORS,
    SETUP_HOURS,
    SETUP_SPLIT,
    SIZE_FACTORS,
    Component,
)
from app.schemas.inventory import Requirement, ScopeInventory

PROJECT, CATALOG, REVIEW, OVERHEAD = "proyecto", "catálogo", "a revisar", "transversal"
OVERHEAD_NAME = "Gestión, liderazgo técnico, QA y lanzamiento"


@dataclass(frozen=True)
class HoursLine:
    kind: str  # proyecto, catálogo, a revisar o transversal
    name: str
    hours: dict[str, int]  # horas base por perfil, sin imprevistos
    basis: str

    @property
    def total(self) -> int:
        return sum(self.hours.values())


@dataclass(frozen=True)
class InventoryHours:
    platform: str
    lines: tuple[HoursLine, ...]

    @property
    def base_hours(self) -> int:
        return sum(line.total for line in self.lines)

    def hours_of(self, kind: str) -> int:
        return sum(line.total for line in self.lines if line.kind == kind)

    @property
    def by_role(self) -> dict[str, int]:
        totals: dict[str, int] = {}
        for line in self.lines:
            for role, hours in line.hours.items():
                totals[role] = totals.get(role, 0) + hours
        return totals


def build_role(platform: str) -> dict[str, float]:
    """Quién construye, según la plataforma, en la proporción de las referencias de la consultora."""
    weights = BUILD_ROLES[platform]
    total = sum(weights.values())
    return {role: weight / total for role, weight in weights.items()}


def distribute(total: float, split: dict[str, float], platform: str) -> dict[str, int]:
    """Reparte las horas entre perfiles según los pesos; 'construcción' depende de la plataforma."""
    weight = sum(split.values())
    shares: dict[str, float] = {}
    for role, share in split.items():
        targets = build_role(platform) if role == BUILD else {role: 1.0}
        for target, part in targets.items():
            shares[target] = shares.get(target, 0) + total * share / weight * part
    # Redondeo por el mayor resto: los perfiles suman exactamente las horas redondeadas de la línea,
    # aunque haya muchos perfiles. Con el redondeo de cada perfil por separado, la suma se desviaba.
    floors = {role: int(hours) for role, hours in shares.items()}
    pending = round(total) - sum(floors.values())
    by_remainder = sorted(shares, key=lambda role: shares[role] - floors[role], reverse=True)
    for role in by_remainder[:max(pending, 0)]:
        floors[role] += 1
    return {role: hours for role, hours in floors.items() if hours > 0}


def component_hours(component: Component, size: str, quantity: int, platform: str) -> float:
    if component.hours_by_size is not None:
        hours = component.hours_by_size[size]
    else:
        hours = component.base_hours * (SIZE_FACTORS[size] if component.sized else 1)
        if component.scales_with_platform:
            hours *= PLATFORM_FACTORS[platform]
    return hours * max(quantity, 1)


def needs_model_hours(requirement: Requirement) -> bool:
    """El catálogo no tiene horas para el requisito: las tiene que poner el modelo."""
    component = COMPONENTS.get(requirement.component)
    return component is None or requirement.component == CUSTOM or component.needs_review


def model_hours(requirement: Requirement) -> dict[str, int]:
    """Las horas que puso el modelo, por perfil: sin las que no son positivas y sumando si repite."""
    hours: dict[str, int] = {}
    for entry in requirement.custom_hours:
        if entry.hours > 0:
            hours[entry.role] = hours.get(entry.role, 0) + entry.hours
    return hours


def missing_hours(inventory: ScopeInventory) -> list[int]:
    """Posición de los requisitos acordados que necesitan horas del modelo y no las tienen."""
    return [
        index
        for index, requirement in enumerate(inventory.requirements)
        if requirement.status == "acordado" and needs_model_hours(requirement) and not model_hours(requirement)
    ]


def _requirement_line(requirement: Requirement, platform: str) -> HoursLine:
    component = COMPONENTS.get(requirement.component)
    label = component.name if component else "A medida"
    name = f"{label} ({requirement.size}): {requirement.description}"
    if requirement.quantity > 1:
        name = f"{label} ({requirement.size}, ×{requirement.quantity}): {requirement.description}"
    if needs_model_hours(requirement):
        return HoursLine(REVIEW, name, model_hours(requirement), "Horas del modelo: el catálogo no tiene referencia")
    total = component_hours(component, requirement.size, requirement.quantity, platform)
    return HoursLine(CATALOG, name, distribute(total, component.split, platform), component.basis)


def agreed(requirements: Iterable[Requirement]) -> list[Requirement]:
    return [requirement for requirement in requirements if requirement.status == "acordado"]


def inventory_hours(inventory: ScopeInventory) -> InventoryHours:
    platform = inventory.platform
    lines = [
        HoursLine(PROJECT, "Descubrimiento", distribute(DISCOVERY_HOURS, DISCOVERY_SPLIT, platform),
                  "UpBusinessCo: 1 semana con producto, diseño y desarrollo"),
        HoursLine(PROJECT, "Configuración, arquitectura y lanzamiento",
                  distribute(SETUP_HOURS[platform], SETUP_SPLIT, platform),
                  f"Innovation Insight: {SETUP_HOURS[platform]} h en {platform}; reparto ISBSG"),
        HoursLine(PROJECT, "Diseño de la interfaz", {"Diseño UX/UI": DESIGN_HOURS[platform]},
                  f"Innovation Insight: diseño personalizado, {DESIGN_HOURS[platform]} h en {platform}"),
    ]
    lines += [_requirement_line(requirement, platform) for requirement in agreed(inventory.requirements)]

    built = sum(line.total for line in lines if line.name != "Descubrimiento")
    overhead = built * OVERHEAD_RATE
    lines.append(
        HoursLine(OVERHEAD, OVERHEAD_NAME, distribute(overhead, OVERHEAD_SPLIT, platform),
                  "Innovation Insight: 35 % de gestión, QA y lanzamiento; reparto con las "
                  "estimaciones de referencia de la consultora")
    )
    return InventoryHours(platform, tuple(lines))
