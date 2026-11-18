from datetime import datetime
from math import isfinite


class Clima:
    """Representa los datos validados de una condición meteorológica."""

    # Interpretación de los códigos WMO utilizados por Open-Meteo:
    # https://open-meteo.com/en/docs
    DESCRIPCIONES = {
        0: "Despejado",
        1: "Mayormente despejado",
        2: "Parcialmente nublado",
        3: "Cubierto",
        45: "Niebla",
        48: "Niebla con escarcha",
        51: "Llovizna ligera",
        53: "Llovizna moderada",
        55: "Llovizna intensa",
        56: "Llovizna helada ligera",
        57: "Llovizna helada intensa",
        61: "Lluvia ligera",
        63: "Lluvia moderada",
        65: "Lluvia intensa",
        66: "Lluvia helada ligera",
        67: "Lluvia helada intensa",
        71: "Nevada ligera",
        73: "Nevada moderada",
        75: "Nevada intensa",
        77: "Granos de nieve",
        80: "Chubascos ligeros",
        81: "Chubascos moderados",
        82: "Chubascos violentos",
        85: "Chubascos de nieve ligeros",
        86: "Chubascos de nieve intensos",
        95: "Tormenta eléctrica ligera o moderada",
        96: "Tormenta eléctrica con granizo ligero",
        99: "Tormenta eléctrica con granizo fuerte",
    }

    def __init__(self, temperatura: float, humedad: float, codigo: int, fecha: datetime):
        if (
            isinstance(temperatura, bool) # Para comprobar si es un booleano y rechazarlo
            or not isinstance(temperatura, (int, float)) # Para comprobar si no es un int o float y rechazarlo
            or not isfinite(temperatura) # Para comprobar si no es un número finito y rechazarlo
        ):
            raise ValueError("La temperatura debe ser un número finito")

        if (
            isinstance(humedad, bool)
            or not isinstance(humedad, (int, float))
            or not isfinite(humedad)
            or not 0 <= humedad <= 100
        ):
            raise ValueError("La humedad debe ser un número entre 0 y 100")

        if isinstance(codigo, bool) or not isinstance(codigo, int) or codigo not in self.DESCRIPCIONES:
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

    def get_descripcion(self) -> str:
        return self.DESCRIPCIONES[self.__codigo]

    def get_fecha(self) -> datetime:
        return self.__fecha
