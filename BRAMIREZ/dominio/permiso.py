from dataclasses import dataclass


@dataclass(frozen=True)
class Permiso:
    """Operación que puede autorizar un rol."""
    codigo: str
    descripcion: str
