from dataclasses import dataclass
from decimal import Decimal
from .cotizacion import CotizacionMonetaria


@dataclass(frozen=True)
class PagoEstimado:
    cotizacion: CotizacionMonetaria
    importe_origen: Decimal
    pago_estimado: Decimal

    def __post_init__(self):
        if not isinstance(self.cotizacion, CotizacionMonetaria):
            raise ValueError("Cotización inválida.")
        for valor in (self.importe_origen, self.pago_estimado):
            if not isinstance(valor, Decimal) or not valor.is_finite() or valor < 0:
                raise ValueError("Importe inválido.")

    def a_dict(self):
        return dict(self.cotizacion.a_dict(), importe_origen=str(self.importe_origen),
                    pago_estimado=str(self.pago_estimado))
