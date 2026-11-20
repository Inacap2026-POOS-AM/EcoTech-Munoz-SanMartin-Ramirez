from dataclasses import dataclass
from .persona import texto


@dataclass(frozen=True)
class Departamento:
    id: str
    nombre: str
    gerente: str | None = None

    def __post_init__(self):
        texto(self.nombre)
        texto(self.id)

    def __str__(self):
        return f"{self.nombre} ({self.id})"
