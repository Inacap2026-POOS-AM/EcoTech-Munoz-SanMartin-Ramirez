"""Traduce JSON de proveedor o caché a objetos propios validados."""
from datetime import datetime, timezone
from decimal import Decimal
import math
from dominio.clima import CondicionClimatica
from dominio.cotizacion import CotizacionMonetaria

CODIGOS = {0: 'Despejado',
 1: 'Mayormente despejado',
 2: 'Parcialmente nublado',
 3: 'Cubierto',
 45: 'Niebla',
 48: 'Niebla con escarcha',
 51: 'Llovizna leve',
 53: 'Llovizna',
 55: 'Llovizna intensa',
 56: 'Llovizna helada leve',
 57: 'Llovizna helada intensa',
 61: 'Lluvia leve',
 63: 'Lluvia',
 65: 'Lluvia intensa',
 66: 'Lluvia helada leve',
 67: 'Lluvia helada intensa',
 71: 'Nieve leve',
 73: 'Nieve',
 75: 'Nieve intensa',
 77: 'Granos de nieve',
 80: 'Chubascos leves',
 81: 'Chubascos',
 82: 'Chubascos violentos',
 85: 'Chubascos de nieve leves',
 86: 'Chubascos de nieve intensos',
 95: 'Tormenta',
 96: 'Tormenta con granizo',
 99: 'Tormenta con granizo intenso'}


def numero(valor, minimo, maximo):
    if (type(valor) not in (int, float) or not math.isfinite(valor)
            or not minimo <= valor <= maximo):
        raise ValueError("Valor numérico fuera de rango.")
    return float(valor)


class Deserializador:
    @staticmethod
    def clima(datos) -> CondicionClimatica:
        actual, unidades = datos["current"], datos["current_units"]
        if unidades["temperature_2m"] != "°C" or unidades["relative_humidity_2m"] != "%":
            raise ValueError("Unidades inesperadas.")
        fecha = datetime.fromisoformat(actual["time"])
        fecha = fecha.replace(tzinfo=timezone.utc) if fecha.tzinfo is None else fecha.astimezone(timezone.utc)
        codigo = actual["weather_code"]
        if type(codigo) is not int or codigo not in CODIGOS:
            raise ValueError("Código meteorológico inválido.")
        return CondicionClimatica(fecha, numero(actual["temperature_2m"], -100, 70),
                                 numero(actual["relative_humidity_2m"], 0, 100), CODIGOS[codigo])

    @staticmethod
    def clima_con_clave(datos) -> CondicionClimatica:
        actual = datos["current"]
        estado = actual["condition"]["text"]
        if not isinstance(estado, str):
            raise ValueError("Estado meteorológico inválido.")
        fecha = datetime.fromtimestamp(numero(actual["last_updated_epoch"], 1, 4102444800), timezone.utc)
        return CondicionClimatica(fecha, numero(actual["temp_c"], -100, 70),
                                 numero(actual["humidity"], 0, 100), estado.strip())

    @staticmethod
    def cambio(datos, base, destino) -> CotizacionMonetaria:
        if datos["result"] != "success" or datos["base_code"] != base:
            raise ValueError("Moneda de origen inesperada.")
        fecha = datetime.fromtimestamp(numero(datos["time_last_update_unix"], 1, 4102444800), timezone.utc)
        tasa = numero(datos["rates"][destino], 1e-12, 1e12)
        return CotizacionMonetaria(fecha, base, destino, Decimal(str(tasa)))

    @staticmethod
    def clima_guardado(datos) -> CondicionClimatica:
        return CondicionClimatica(datetime.fromisoformat(datos["fecha_fuente"]),
                                 numero(datos["temperatura_C"], -100, 70),
                                 numero(datos["humedad_pct"], 0, 100), datos["estado"])

    @staticmethod
    def cambio_guardado(datos) -> CotizacionMonetaria:
        return CotizacionMonetaria(datetime.fromisoformat(datos["fecha_fuente"]),
                                   datos["base"], datos["destino"], Decimal(str(datos["tasa"])))
