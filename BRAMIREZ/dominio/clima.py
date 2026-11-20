"""Dato meteorológico seleccionado, tipado y validado."""
from dataclasses import dataclass
from datetime import datetime
import math


@dataclass(frozen=True)
class CondicionClimatica:
    fecha_fuente: datetime
    temperatura_C: float
    humedad_pct: float
    estado: str

    def __post_init__(self):
        if not isinstance(self.fecha_fuente, datetime) or self.fecha_fuente.utcoffset() is None:
            raise ValueError("La fecha meteorológica requiere zona horaria.")
        for valor, minimo, maximo in [(self.temperatura_C, -100, 70),
                                      (self.humedad_pct, 0, 100)]:
            if type(valor) is not float or not math.isfinite(valor) or not minimo <= valor <= maximo:
                raise ValueError("Dato meteorológico inválido.")
        if not isinstance(self.estado, str) or not 0 < len(self.estado.strip()) <= 120:
            raise ValueError("Estado meteorológico inválido.")

    def a_dict(self):
        return {"fecha_fuente": self.fecha_fuente.isoformat(),
                "temperatura_C": self.temperatura_C, "humedad_pct": self.humedad_pct,
                "estado": self.estado}
