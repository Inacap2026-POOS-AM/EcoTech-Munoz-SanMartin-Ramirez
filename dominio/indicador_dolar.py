from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


class IndicadorDolar:
    """Valor del dólar observado: pesos chilenos por un dólar estadounidense."""

    def __init__(self, valor: Decimal, fecha: date):
        if not isinstance(valor, Decimal) or not valor.is_finite() or not Decimal("0.0001") <= valor <= Decimal("1000000"):
            raise ValueError("El valor del dólar debe ser positivo, finito y estar en el rango admitido")
        if not isinstance(fecha, date) or isinstance(fecha, datetime):
            raise ValueError("La fecha del indicador debe ser una fecha válida")
        self.__valor = valor
        self.__fecha = fecha

    def get_valor(self):
        return self.__valor

    def get_fecha(self):
        return self.__fecha

    def convertir_a_usd(self, importe):
        if isinstance(importe, bool) or not isinstance(importe, (str, int, Decimal)):
            raise ValueError("El importe debe ser un número decimal válido")
        try:
            pesos = Decimal(importe)
        except InvalidOperation as error:
            raise ValueError("El importe debe ser un número decimal válido") from error
        if not pesos.is_finite() or not Decimal("0") < pesos <= Decimal("9999999999.99"):
            raise ValueError("El importe debe ser positivo y no superar 9999999999.99 CLP")
        if pesos != pesos.quantize(Decimal("0.01")):
            raise ValueError("El importe admite hasta dos decimales")
        return (pesos / self.__valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
