# Consulta de información climática

import requests


class ErrorAPI(Exception):
    """La consulta al servicio externo no pudo completarse."""


def consultar_clima():
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
        raise ErrorAPI("El servicio de clima tardó demasiado en responder.") from error
    except requests.exceptions.ConnectionError as error:
        raise ErrorAPI("No se pudo conectar con el servicio de clima.") from error
    except requests.exceptions.HTTPError as error:
        raise ErrorAPI("El servicio de clima respondió con un error HTTP.") from error
    except requests.exceptions.JSONDecodeError as error:
        raise ErrorAPI("El servicio de clima devolvió una respuesta JSON inválida.") from error
    except requests.exceptions.RequestException as error:
        raise ErrorAPI("No se pudo completar la consulta de clima.") from error
