# Consulta de información climática

import logging # Registrar los mensajes sobre los intentos, errores, esperas
import time # Pausar el programa antes de reintentar la consulta, según lo indique el servidor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime # Convertir una fecha HTTP a datetime
from math import isfinite

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


def _validar_coordenadas(latitud, longitud):
    """Rechaza coordenadas incorrectas antes de consultar el servicio."""
    if (
        isinstance(latitud, bool) # Rechaza booleanos
        or not isinstance(latitud, (int, float)) # Rechaza si no es int o float
        or not -90 <= latitud <= 90 # Rechaza numeros fuera del rango geografico permitido
        or not isfinite(latitud) # Rechaza numeros infinitos
    ):
        raise ValueError("La latitud debe ser un número finito entre -90 y 90")

    if (
        isinstance(longitud, bool)
        or not isinstance(longitud, (int, float))
        or not -180 <= longitud <= 180
        or not isfinite(longitud)
    ):
        raise ValueError("La longitud debe ser un número finito entre -180 y 180")


def consultar_clima(latitud: float, longitud: float):
    """Consulta el clima de las coordenadas indicadas."""
    _validar_coordenadas(latitud, longitud)
    url = "https://api.open-meteo.com/v1/forecast"
    parametros = {
        "latitude": latitud,
        "longitude": longitud,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "timezone": "America/Santiago",
    }
    return _consultar_json(url, parametros)


def buscar_lugares(nombre: str):
    """Busca ciudades y devuelve hasta cinco coincidencias validadas."""
    if not isinstance(nombre, str):
        raise ValueError("El nombre del lugar debe ser un texto")
    nombre = nombre.strip()
    if not 2 <= len(nombre) <= 100 or not nombre.isprintable() or not any(letra.isalpha() for letra in nombre):
        raise ValueError("Ingresa un nombre de lugar de 2 a 100 caracteres, sin caracteres de control")

    datos = _consultar_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": nombre, "count": 5, "language": "es", "format": "json"},
    )
    if not isinstance(datos, dict):
        raise ValueError("La respuesta de lugares debe ser un diccionario")
    resultados = datos.get("results", [])
    if not isinstance(resultados, list):
        raise ValueError("La respuesta de lugares debe contener una lista de resultados")

    lugares = []
    for resultado in resultados:
        if not isinstance(resultado, dict):
            raise ValueError("El servicio devolvió un lugar con estructura inválida")
        try:
            latitud = resultado["latitude"]
            longitud = resultado["longitude"]
            nombre_lugar = resultado["name"]
        except KeyError as error:
            raise ValueError("Faltan datos obligatorios de un lugar") from error
        _validar_coordenadas(latitud, longitud)
        region = resultado.get("admin1", "Región no informada") # admin1 es la clave de la API para guardar la region
        pais = resultado.get("country", "País no informado")
        for texto in (nombre_lugar, region, pais):
            if not isinstance(texto, str) or not texto.strip() or not texto.isprintable() or len(texto) > 200:
                raise ValueError("El servicio devolvió un nombre de lugar inválido")
        lugares.append({
            "nombre": nombre_lugar,
            "region": region,
            "pais": pais,
            "latitud": latitud,
            "longitud": longitud,
        })
    return lugares


def _consultar_json(url, parametros):
    """Comparte el manejo de errores y los tres intentos entre ambos servicios."""
    max_intentos = 3

    for intento in range(1, max_intentos + 1):
        logger.info("Consulta a servicio externo: intento %s de %s", intento, max_intentos)
        try:
            return _consultar_json_una_vez(url, parametros)
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
                logger.warning("Se agotaron los %s intentos de consulta", max_intentos)
                raise

            espera = _calcular_espera(retry_after, 2 ** (intento - 1)) # Sin Retry-After válido, espera 1 segundo y luego 2 entre intentos
            logger.warning("Próximo intento en %s segundos", espera)
            time.sleep(espera)


def _consultar_json_una_vez(url, parametros):
    """Realiza una petición para clima o búsqueda de lugares."""
    try:
        with requests.get(url, params=parametros, timeout=(3, 10)) as respuesta:
            respuesta.raise_for_status()
            return respuesta.json()
    except requests.exceptions.Timeout as error:
        raise ErrorRed("El servicio externo tardó demasiado en responder.") from error
    except requests.exceptions.SSLError as error:
        raise ErrorAPI("No se pudo establecer una conexión TLS segura con el servicio externo.") from error
    except requests.exceptions.ConnectionError as error:
        raise ErrorRed("No se pudo conectar con el servicio externo.") from error
    except requests.exceptions.HTTPError as error:
        codigo = error.response.status_code

        if codigo == 429:
            retry_after = error.response.headers.get("Retry-After")
            raise ErrorHTTP(
                "Se alcanzó el límite de consultas del servicio externo.",
                codigo,
                retry_after,
            ) from error

        if 400 <= codigo < 500:
            mensajes = {
                400: "El servicio externo rechazó los parámetros de la consulta.",
                401: "El servicio externo requiere credenciales válidas.",
                403: "El servicio externo no permite el acceso solicitado.",
                404: "No se encontró el endpoint del servicio externo.",
            }
            mensaje = mensajes.get(codigo, "El servicio externo rechazó la solicitud.")
            raise ErrorHTTP(mensaje, codigo) from error

        raise ErrorHTTP(
            "El servicio externo presentó un fallo del servidor.", codigo,
            error.response.headers.get("Retry-After"),
        ) from error
    except requests.exceptions.JSONDecodeError as error:
        raise ErrorAPI("El servicio externo devolvió una respuesta JSON inválida.") from error
    except requests.exceptions.RequestException as error:
        raise ErrorAPI("No se pudo completar la consulta de clima.") from error
