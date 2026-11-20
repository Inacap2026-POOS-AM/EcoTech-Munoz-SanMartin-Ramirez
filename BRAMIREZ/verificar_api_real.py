"""Comprobación opcional: llamadas reales únicamente a los dos proveedores públicos."""
import json
from pathlib import Path
from api_cliente import ClienteAPI, ServicioExternoError
from deserializador import Deserializador
from infraestructura.log_api import configurar_log


def verificar():
    configurar_log()
    resultados = []
    consultas = [
        ('Open-Meteo', 'https://api.open-meteo.com/v1/forecast?latitude=-36.84&longitude=-73.1&current=temperature_2m,relative_humidity_2m,weather_code&timezone=GMT', Deserializador.clima),
        ('ExchangeRate-API', 'https://open.er-api.com/v6/latest/USD',
         lambda d: Deserializador.cambio(d, 'USD', 'CLP')),
    ]
    for nombre, url, parsear in consultas:
        try:
            dato = parsear(ClienteAPI().obtener(url))
            resultados.append({'proveedor': nombre, 'verificado': True, 'datos': dato.a_dict()})
        except (ServicioExternoError, ValueError, TypeError, KeyError, OverflowError) as exc:
            detalle = str(exc) if isinstance(exc, ServicioExternoError) else 'Respuesta inválida'
            resultados.append({'proveedor': nombre, 'verificado': False, 'detalle': detalle})
    return resultados


if __name__ == '__main__':
    print(json.dumps(verificar(), ensure_ascii=False, indent=2))
