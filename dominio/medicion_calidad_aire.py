
from datetime import datetime
from decimal import Decimal, InvalidOperation


class MedicionCalidadAire:
    """Representa una medición ambiental obtenida desde una API."""

    def __init__(
        self,
        pm2_5,
        pm10,
        us_aqi,
        fecha_hora: datetime,
        latitud,
        longitud,
    ):
        self.__pm2_5 = self.__validar_decimal(pm2_5, "PM2.5")
        self.__pm10 = self.__validar_decimal(pm10, "PM10")
        self.__us_aqi = self.__validar_aqi(us_aqi)
        self.__fecha_hora = self.__validar_fecha_hora(fecha_hora)
        self.__latitud = self.__validar_coordenada(
            latitud, "La latitud", -90, 90
        )
        self.__longitud = self.__validar_coordenada(
            longitud, "La longitud", -180, 180
        )

    @staticmethod
    def __validar_decimal(valor, campo):
        if isinstance(valor, bool):
            raise ValueError(campo + " debe ser un número")

        try:
            numero = Decimal(str(valor))
        except (InvalidOperation, ValueError) as error:
            raise ValueError(campo + " debe ser un número") from error

        if not numero.is_finite() or numero < 0:
            raise ValueError(campo + " debe ser un número no negativo")

        return numero

    @staticmethod
    def __validar_aqi(valor):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ValueError("US AQI debe ser un número entero")

        if not 0 <= valor <= 500:
            raise ValueError("US AQI debe estar entre 0 y 500")

        return valor

    @staticmethod
    def __validar_fecha_hora(valor):
        if not isinstance(valor, datetime):
            raise ValueError("La fecha debe ser un objeto datetime")

        if valor.tzinfo is None or valor.utcoffset() is None:
            raise ValueError("La fecha debe incluir una zona horaria")

        return valor

    @staticmethod
    def __validar_coordenada(valor, campo, minimo, maximo):
        if isinstance(valor, bool):
            raise ValueError(campo + " debe ser un número")

        try:
            numero = Decimal(str(valor))
        except (InvalidOperation, ValueError) as error:
            raise ValueError(campo + " debe ser un número") from error

        if not numero.is_finite():
            raise ValueError(campo + " debe ser un número finito")

        if numero < Decimal(str(minimo)) or numero > Decimal(str(maximo)):
            raise ValueError(campo + " fuera del rango permitido")

        return numero


    @property
    def pm2_5(self):
        return self.__pm2_5

    @property
    def pm10(self):
        return self.__pm10

    @property
    def us_aqi(self):
        return self.__us_aqi

    @property
    def fecha_hora(self):
        return self.__fecha_hora

    @property
    def latitud(self):
        return self.__latitud

    @property
    def longitud(self):
        return self.__longitud
