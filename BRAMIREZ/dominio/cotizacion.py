from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

MONEDAS = frozenset({"CLP", "USD", "EUR", "BRL", "ARS", "GBP", "JPY", "CAD"})


@dataclass(frozen=True)
class CotizacionMonetaria:
    fecha_fuente: datetime
    base: str
    destino: str
    tasa: Decimal

    def __post_init__(self):
        if not isinstance(self.fecha_fuente, datetime) or self.fecha_fuente.utcoffset() is None:
            raise ValueError("La fecha de cotización requiere zona horaria.")
        if self.base not in MONEDAS or self.destino not in MONEDAS:
            raise ValueError("Moneda no disponible.")
        if (not isinstance(self.tasa, Decimal) or not self.tasa.is_finite()
                or not Decimal("1e-12") <= self.tasa <= Decimal("1e12")):
            raise ValueError("Tasa inválida.")

    def a_dict(self):
        return {"fecha_fuente": self.fecha_fuente.isoformat(), "base": self.base,
                "destino": self.destino, "tasa": str(self.tasa)}
