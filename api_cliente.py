# Consulta de información climática

import logging # Registrar los mensajes sobre los intentos, errores, esperas
import time # Pausar el programa antes de reintentar la consulta, según lo indique el servidor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime # Convertir una fecha HTTP a datetime

import requests


logger = logging.getLogger(__name__)


class ErrorAPI(Exception):
    """La consulta al servicio externo no pudo completarse."""


class ErrorRed(ErrorAPI):
    """Fallo de conexión o timeout que permite reintentar."""


class ErrorHTTP(ErrorAPI):
    """Conserva el código HTTP y la espera indicada por el servidor."""

    def __init__(self, mensaje, codigo, retry_after=None):
        super().__init__(mensaje)
        self.codigo = codigo
        self.retry_after = retry_after


def _calcular_espera(retry_after, espera_base):
    """Interpreta Retry-After como segundos o fecha HTTP."""
    if retry_after is None:
        return espera_base

    valor = retry_after.strip()
    if valor.isascii() and valor.isdigit(): # Para comprobar si el tiempo de espera es un numero
        return int(valor) 

    try: # Para interpretarlo como fecha HTTP
        fecha = parsedate_to_datetime(valor) # Recibe texto y lo pasa a datetime
        if fecha.tzinfo is None: # Contiene la informacion de la zona horaria de la fecha
            return espera_base # Si no tiene zona horaria, se devuelve la espera base
        return max(0, (fecha - datetime.now(timezone.utc)).total_seconds())
    except (ValueError, TypeError, OverflowError): #Overflow supera el rango que python representa
        logger.warning("Retry-After inválido; se utilizará la espera exponencial")
        return espera_base


def consultar_clima():
    """Consulta el clima con un máximo de tres intentos en total."""
    max_intentos = 3

    for intento in range(1, max_intentos + 1):
        logger.info("Consulta de clima: intento %s de %s", intento, max_intentos)
        try:
            return _consultar_clima_una_vez()
        except (ErrorHTTP, ErrorRed) as error:
            retry_after = None
            if isinstance(error, ErrorHTTP):
                logger.warning("Intento %s: error HTTP %s", intento, error.codigo)
                if error.codigo != 429 and not 500 <= error.codigo < 600:
                    raise
                retry_after = error.retry_after
            else:
                logger.warning("Intento %s: fallo de red o timeout", intento)

            if intento == max_intentos:
                logger.warning("Se agotaron los %s intentos de clima", max_intentos)
                raise

            espera = _calcular_espera(retry_after, 2 ** (intento - 1)) # Sin Retry-After válido, espera 1 segundo y luego 2 entre intentos
            logger.warning("Próximo intento en %s segundos", espera)
            time.sleep(espera)


def _consultar_clima_una_vez():
    # Obtiene el JSON del clima actual de Santiago como primera consulta.
    url = "https://api.open-meteo.com/v1/forecast"
    parametros = {
        "latitude": -33.45,
        "longitude": -70.65,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "timezone": "America/Santiago",
    }

    try:
        with requests.get(url, params=parametros, timeout=(3, 10)) as respuesta:
            respuesta.raise_for_status()
            return respuesta.json()
    except requests.exceptions.Timeout as error:
        raise ErrorRed("El servicio de clima tardó demasiado en responder.") from error
    except requests.exceptions.SSLError as error:
        raise ErrorAPI("No se pudo establecer una conexión TLS segura con el servicio de clima.") from error
    except requests.exceptions.ConnectionError as error:
        raise ErrorRed("No se pudo conectar con el servicio de clima.") from error
    except requests.exceptions.HTTPError as error:
        codigo = error.response.status_code

        if codigo == 429:
            retry_after = error.response.headers.get("Retry-After")
            raise ErrorHTTP(
                "Se alcanzó el límite de consultas del servicio de clima.",
                codigo,
                retry_after,
            ) from error

        if 400 <= codigo < 500:
            mensajes = {
                400: "El servicio de clima rechazó los parámetros de la consulta.",
                401: "El servicio de clima requiere credenciales válidas.",
                403: "El servicio de clima no permite el acceso solicitado.",
                404: "No se encontró el endpoint del servicio de clima.",
            }
            mensaje = mensajes.get(codigo, "El servicio de clima rechazó la solicitud.")
            raise ErrorHTTP(mensaje, codigo) from error

        raise ErrorHTTP(
            "El servicio de clima presentó un fallo del servidor.", codigo,
            error.response.headers.get("Retry-After"),
        ) from error
    except requests.exceptions.JSONDecodeError as error:
        raise ErrorAPI("El servicio de clima devolvió una respuesta JSON inválida.") from error
    except requests.exceptions.RequestException as error:
        raise ErrorAPI("No se pudo completar la consulta de clima.") from error
