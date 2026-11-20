from dataclasses import dataclass
from .rol import Rol
from .excepciones import ErrorNegocio


@dataclass(frozen=True)
class Usuario:
    """Identidad autenticada para la sesión local."""
    nombre: str
    rol: Rol
    empleado: str | None = None

    def exigir(self, permiso):
        if not self.rol.permite(permiso):
            raise ErrorNegocio("El perfil no tiene permiso para esta operación.")
