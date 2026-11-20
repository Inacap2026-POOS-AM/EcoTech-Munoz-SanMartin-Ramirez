from dataclasses import dataclass
from datetime import date
from .persona import Persona
from .excepciones import ErrorNegocio


@dataclass(frozen=True)
class Empleado(Persona):
    inicio: date
    sueldo: int
    departamento: str | None = None

    def __post_init__(self):
        super().__post_init__()
        if type(self.sueldo) is not int or not 0 < self.sueldo <= 10**12:
            raise ErrorNegocio("El sueldo se expresa en pesos enteros positivos.")
        if type(self.inicio) is not date:
            raise ErrorNegocio("Fecha de contrato inválida.")

    def __str__(self):
        return f"{self.nombre} · {self.id} · {self.correo}"
