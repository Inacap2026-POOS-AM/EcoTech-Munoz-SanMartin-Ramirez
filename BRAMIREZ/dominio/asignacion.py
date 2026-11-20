from dataclasses import dataclass
from datetime import date
from .persona import texto
from .excepciones import ErrorNegocio


@dataclass(frozen=True)
class AsignacionProyecto:
    empleado: str
    proyecto: str
    rol: str
    inicio: date

    def __post_init__(self):
        texto(self.empleado)
        texto(self.proyecto)
        if type(self.inicio) is not date:
            raise ErrorNegocio("Fecha de asignación inválida.")
        texto(self.rol)

    def __str__(self):
        return f"{self.empleado} — {self.rol} en {self.proyecto}"
