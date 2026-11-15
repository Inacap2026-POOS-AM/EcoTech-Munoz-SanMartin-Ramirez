from datetime import datetime

from dominio.clima import Clima


class DeserializadorClima:
    """Convierte el diccionario de la API en un objeto Clima validado."""

    def deserializar(self, datos: dict) -> Clima:
        if not isinstance(datos, dict):
            raise ValueError("La respuesta de clima debe ser un diccionario")

        actual = datos.get("current")
        if not isinstance(actual, dict):
            raise ValueError("La respuesta no contiene una sección current válida")

        try:
            temperatura = actual["temperature_2m"]
            humedad = actual["relative_humidity_2m"]
            codigo = actual["weather_code"]
            fecha_texto = actual["time"]
        except KeyError as error:
            raise ValueError("Faltan datos obligatorios en la respuesta de clima") from error

        if not isinstance(fecha_texto, str):
            raise ValueError("La fecha recibida debe ser un texto")

        try:
            fecha = datetime.fromisoformat(fecha_texto)
        except ValueError as error:
            raise ValueError("La fecha recibida no tiene un formato ISO válido") from error

        return Clima(temperatura, humedad, codigo, fecha)
