from dataclasses import dataclass
from datetime import date
from .excepciones import ErrorNegocio
from .persona import texto


@dataclass(frozen=True)
class RegistroTiempo:
    empleado: str
    proyecto: str
    fecha: date
    minutos: int
    descripcion: str

    def __post_init__(self):
        if type(self.fecha) is not date or type(self.minutos) is not int:
            raise ErrorNegocio("Use una fecha y un número entero de minutos.")
        if self.fecha > date.today() or not 1 <= self.minutos <= 1440:
            raise ErrorNegocio("Fecha futura o duración fuera de 1 a 1440 minutos.")
        texto(self.descripcion, 400)

    def __str__(self):
        return f"{self.fecha} · {self.minutos} min · {self.descripcion}"
