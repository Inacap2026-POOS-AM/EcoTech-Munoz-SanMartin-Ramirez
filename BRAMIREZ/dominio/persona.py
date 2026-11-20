from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import re

from .excepciones import ErrorNegocio
from .validaciones import validar_rut


def texto(valor, limite=100):
    if not isinstance(valor, str) or not 0 < len(valor.strip()) <= limite:
        raise ErrorNegocio(f"Se requiere texto de 1 a {limite} caracteres.")
    return valor.strip()


@dataclass(frozen=True)
class Persona(ABC):
    id: str
    nombre: str
    correo: str
    direccion: str
    telefono: str
    rut: str | None = field(default=None, kw_only=True, repr=False)

    def __post_init__(self):
        for valor in (self.id, self.nombre, self.direccion):
            texto(valor)
        if not isinstance(self.correo, str) or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", self.correo):
            raise ErrorNegocio("Correo inválido.")
        if not isinstance(self.telefono, str) or not re.fullmatch(r"[+\d ()-]{6,22}", self.telefono):
            raise ErrorNegocio("Teléfono inválido.")
        if self.rut is not None:
            object.__setattr__(self, "rut", validar_rut(self.rut))

    @abstractmethod
    def __str__(self):
        """Representación pública."""
