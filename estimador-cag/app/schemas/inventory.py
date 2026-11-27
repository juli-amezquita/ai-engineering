"""El inventario de alcance: lo que el modelo lee en la reunión, antes de estimar.

Cada requisito dice su estado, la frase de la reunión que lo respalda y qué componente del catálogo
lo cubre, con su tamaño. Las horas no las pone el modelo: las calcula Python con el catálogo
(app/services/catalog_hours.py). Solo pone horas cuando el componente no tiene horas en el catálogo
o el requisito no encaja en ninguno, y esas horas se marcan para que una persona las revise.
También lee el plazo que pidió el cliente, con la cantidad y la unidad que dijo: pasarlo a
semanas es aritmética, y la hace Python.
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.context.catalog import COMPONENTS, CUSTOM, PRODUCT_TYPES
from app.context.cost_model import DAYS_PER_MONTH
from app.schemas.draft import RoleHours

ComponentId = Literal[tuple([*COMPONENTS, CUSTOM])]  # type: ignore[valid-type]
ProductTypeId = Literal[tuple(PRODUCT_TYPES)]  # type: ignore[valid-type]
Status = Literal["acordado", "opcional", "condicionado", "excluido"]


class Requirement(BaseModel):
    description: str = Field(
        description="El requisito en una frase, con los datos del cliente tal como los dijo"
    )
    status: Status = Field(
        description=(
            "acordado: el cliente lo pidió; opcional: lo mencionó como deseable sin decidirlo; "
            "condicionado: depende de algo que no se decidió; excluido: la reunión lo dejó fuera"
        )
    )
    evidence: str = Field(description="Frase literal y breve de la transcripción que lo respalda")
    component: ComponentId = Field(
        description=f"El componente del catálogo que lo cubre, o '{CUSTOM}' si no encaja en ninguno"
    )
    size: Literal["S", "M", "L"] = Field(description="Tamaño del componente según sus criterios")
    quantity: int = Field(
        description="Cuántas unidades del componente, por ejemplo 2 integraciones; normalmente 1"
    )
    size_reason: str = Field(description="Por qué ese tamaño, con el criterio que se cumple")
    custom_hours: list[RoleHours] = Field(
        description=(
            "Obligatorio si el componente no tiene horas en el catálogo o es 'a_medida': horas base "
            "por perfil, sin imprevistos, con al menos un perfil con horas mayores que 0. En los "
            "demás casos, lista vacía"
        )
    )


class OpenDecision(BaseModel):
    question: str = Field(description="La decisión que la reunión dejó abierta")
    options: list[str] = Field(description="Las opciones posibles")
    assumed: str = Field(description="La opción que se asume en el inventario mientras no se decida")
    evidence: str = Field(description="Frase literal y breve de la transcripción que la origina")


class Deadline(BaseModel):
    """El plazo que pidió el cliente, tal como lo dijo. Python lo pasa a semanas."""

    amount: int = Field(description="La cantidad que dijo el cliente, por ejemplo 4 en 'en unos cuatro meses'")
    unit: Literal["semanas", "meses"] = Field(description="La unidad que dijo el cliente")
    evidence: str = Field(description="Frase literal y breve de la transcripción que lo respalda")

    @property
    def weeks(self) -> int:
        if self.unit == "semanas":
            return self.amount
        return round(self.amount * DAYS_PER_MONTH / 7)


class RequirementHours(BaseModel):
    item: int = Field(description="Número del requisito en la lista del mensaje")
    hours: list[RoleHours] = Field(
        description="Horas base por perfil, sin imprevistos, con al menos un perfil con horas mayores que 0"
    )


class MissingHours(BaseModel):
    """La respuesta de la llamada que completa las horas que el inventario dejó vacías."""

    requirements: list[RequirementHours] = Field(description="Una entrada por cada requisito de la lista")


class ScopeInventory(BaseModel):
    is_software_project: bool = Field(
        description="false si la transcripción no describe un proyecto de software"
    )
    not_software_reason: str = Field(
        description="Si no es un proyecto de software, por qué, en una frase; si no, vacío"
    )
    product_types: list[ProductTypeId] = Field(
        description="Los tipos de producto de RR. HH. que describe la reunión"
    )
    platform: Literal["web", "movil", "web_y_movil"] = Field(
        description="La plataforma del producto, según las reglas de plataforma"
    )
    platform_reason: str = Field(description="Por qué esa plataforma, con la frase que la respalda")
    requirements: list[Requirement] = Field(description="Todos los requisitos, en cualquier estado")
    open_decisions: list[OpenDecision] = Field(
        description="Decisiones técnicas o de alcance que la reunión dejó abiertas; lista vacía si no hay"
    )
    deadline: Deadline | None = Field(
        description="El plazo que pidió el cliente para tener el producto, según las reglas de plazo; null si no fija ninguno"
    )

    @property
    def deadline_weeks(self) -> int | None:
        return self.deadline.weeks if self.deadline is not None else None
