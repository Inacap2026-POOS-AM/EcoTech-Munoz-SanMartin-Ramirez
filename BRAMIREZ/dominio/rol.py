from dataclasses import dataclass
from .permiso import Permiso

CONSULTAR = Permiso("consultar_servicios", "Consultar clima y cambio")
REGISTRAR = Permiso("registrar_tiempo", "Registrar tiempo propio")
ADMINISTRAR = Permiso("administrar", "Gestionar entidades y cuentas")


@dataclass(frozen=True)
class Rol:
    """Perfil fijo para esta aplicación local."""
    nombre: str

    @property
    def permisos(self):
        catalogo = {
            "admin": (CONSULTAR, REGISTRAR, ADMINISTRAR),
            "consulta": (CONSULTAR, REGISTRAR),
        }
        return catalogo.get(self.nombre, ())

    def permite(self, permiso):
        return any(item.codigo == permiso for item in self.permisos)
