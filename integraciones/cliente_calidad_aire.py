from datetime import datetime
from zoneinfo import ZoneInfo
from dominio.medicion_calidad_aire import MedicionCalidadAire
import logging
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests


logger = logging.getLogger(__name__)


class ErrorCalidadAire(Exception):
    """Error controlado al consultar el servicio de calidad del aire."""


class ClienteCalidadAire:
    """Cliente HTTP para consultar la API de Open-Meteo."""

    URL_API = "https://air-quality-api.open-meteo.com/v1/air-quality"

    LATITUD = -33.4489
    LONGITUD = -70.6693
    ZONA_HORARIA = "America/Santiago"

    MAX_INTENTOS = 4
    TIMEOUT = 10

    def obtener_condiciones_actuales(self):
        """Obtiene PM2.5, PM10 y US AQI para Santiago."""

        parametros = {
            "latitude": self.LATITUD,
            "longitude": self.LONGITUD,
            "current": "pm2_5,pm10,us_aqi",
            "timezone": self.ZONA_HORARIA,
        }

        for intento in range(1, self.MAX_INTENTOS + 1):
            logger.info(
                "Consulta de calidad del aire. Intento %s de %s",
                intento,
                self.MAX_INTENTOS,
            )

            try:
                respuesta = requests.get(
                    self.URL_API,
                    params=parametros,
                    timeout=self.TIMEOUT,
                )

            except requests.exceptions.RequestException as error:
                if intento == self.MAX_INTENTOS:
                    raise ErrorCalidadAire(
                        "No fue posible conectar con Open-Meteo."
                    ) from error

                espera = 2 ** (intento - 1)

                logger.warning(
                    "Error de conexión. Nuevo intento en %s segundos.",
                    espera,
                )
                time.sleep(espera)
                continue

            if respuesta.status_code == 429:
                if intento == self.MAX_INTENTOS:
                    raise ErrorCalidadAire(
                        "Open-Meteo mantuvo el límite de solicitudes."
                    )

                espera = self._obtener_espera_retry_after(
                    respuesta.headers.get("Retry-After")
                )

                logger.warning(
                    "Límite de solicitudes (429). Esperando %s segundos.",
                    espera,
                )
                time.sleep(espera)
                continue

            if 500 <= respuesta.status_code <= 599:
                if intento == self.MAX_INTENTOS:
                    raise ErrorCalidadAire(
                        "Open-Meteo no está disponible temporalmente."
                    )

                espera = 2 ** (intento - 1)

                logger.warning(
                    "Error del servidor (%s). Nuevo intento en %s segundos.",
                    respuesta.status_code,
                    espera,
                )
                time.sleep(espera)
                continue

            if 400 <= respuesta.status_code <= 499:
                raise ErrorCalidadAire(
                    "Open-Meteo rechazó la solicitud: HTTP "
                    + str(respuesta.status_code)
                )

            try:
                datos = respuesta.json()
            except ValueError as error:
                raise ErrorCalidadAire(
                    "Open-Meteo devolvió una respuesta JSON inválida."
                ) from error

            if not isinstance(datos, dict):
                raise ErrorCalidadAire(
                    "La respuesta de Open-Meteo no tiene el formato esperado."
                )

            if not isinstance(datos.get("current"), dict):
                raise ErrorCalidadAire(
                    "La respuesta no contiene las condiciones actuales."
                )

            return datos

        raise ErrorCalidadAire(
            "Se agotaron los intentos de consulta."
        )

    def obtener_medicion_actual(self):
        """Convierte la respuesta JSON en una entidad del dominio."""

        datos = self.obtener_condiciones_actuales()

        try:
            actual = datos["current"]

            fecha_hora = datetime.fromisoformat(actual["time"])

            if fecha_hora.tzinfo is None:
                fecha_hora = fecha_hora.replace(
                    tzinfo=ZoneInfo(self.ZONA_HORARIA)
                )

            return MedicionCalidadAire(
                pm2_5=actual["pm2_5"],
                pm10=actual["pm10"],
                us_aqi=actual["us_aqi"],
                fecha_hora=fecha_hora,
                latitud=self.LATITUD,
                longitud=self.LONGITUD,
            )

        except (KeyError, TypeError, ValueError) as error:
            raise ErrorCalidadAire(
                "No fue posible interpretar los datos de calidad del aire."
            ) from error

    @staticmethod
    def _obtener_espera_retry_after(valor):
        """Interpreta Retry-After como segundos o fecha HTTP."""

        if not valor:
            return 2

        try:
            return max(0, float(valor))
        except ValueError:
            pass

        try:
            fecha = parsedate_to_datetime(valor)

            if fecha.tzinfo is None:
                fecha = fecha.replace(tzinfo=timezone.utc)

            espera = (fecha - datetime.now(timezone.utc)).total_seconds()
            return max(0, espera)

        except (TypeError, ValueError, OverflowError):
            return 2
