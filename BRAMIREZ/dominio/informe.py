from dataclasses import dataclass


@dataclass(frozen=True)
class Informe:
    tipo: str
    columnas: tuple
    filas: list


