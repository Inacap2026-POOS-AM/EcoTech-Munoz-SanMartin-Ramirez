from datetime import datetime
from math import isfinite


class Clima:
    """Representa los datos validados de una condición meteorológica."""

    def __init__(self, temperatura: float, humedad: float, codigo: int, fecha: datetime):
        if (
            isinstance(temperatura, bool)
            or not isinstance(temperatura, (int, float))
            or not isfinite(temperatura)
        ):
            raise ValueError("La temperatura debe ser un número finito")

        if (
            isinstance(humedad, bool)
            or not isinstance(humedad, (int, float))
            or not isfinite(humedad)
            or not 0 <= humedad <= 100
        ):
            raise ValueError("La humedad debe ser un número entre 0 y 100")

        codigos_validos = {
            0, 1, 2, 3, 45, 48, 51, 53, 55, 56, 57,
            61, 63, 65, 66, 67, 71, 73, 75, 77,
            80, 81, 82, 85, 86, 95, 96, 99,
        }
        if isinstance(codigo, bool) or not isinstance(codigo, int) or codigo not in codigos_validos:
            raise ValueError("El código meteorológico no es válido")

        if not isinstance(fecha, datetime):
            raise ValueError("La fecha del clima debe ser un objeto datetime")

        self.__temperatura = float(temperatura)
        self.__humedad = float(humedad)
        self.__codigo = codigo
        self.__fecha = fecha

    def get_temperatura(self) -> float:
        return self.__temperatura

    def get_humedad(self) -> float:
        return self.__humedad

    def get_codigo(self) -> int:
        return self.__codigo

    def get_fecha(self) -> datetime:
        return self.__fecha
