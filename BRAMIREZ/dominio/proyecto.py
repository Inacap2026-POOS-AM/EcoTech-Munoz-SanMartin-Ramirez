from dataclasses import dataclass
from datetime import date
from .persona import texto
from .excepciones import ErrorNegocio


@dataclass(frozen=True)
class Proyecto:
    id: str
    nombre: str
    descripcion: str
    inicio: date
    estado: str = "ACTIVO"

    def __post_init__(self):
        texto(self.id)
        if type(self.inicio) is not date:
            raise ErrorNegocio("Fecha de proyecto inválida.")
        texto(self.nombre)
        texto(self.descripcion, 400)
        if self.estado not in {"PLANIFICADO", "ACTIVO", "PAUSADO", "FINALIZADO"}:
            raise ErrorNegocio("Estado de proyecto inválido.")

    def __str__(self):
        return f"{self.nombre} · {self.estado}"
