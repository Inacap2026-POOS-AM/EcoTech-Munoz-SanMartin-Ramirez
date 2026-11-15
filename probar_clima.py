"""Prueba manual de la consulta y deserialización durante el desarrollo."""

import logging

from api_cliente import ErrorAPI, consultar_clima
from deserializador_clima import DeserializadorClima


def main():
    try:
        datos = consultar_clima()
        deserializador = DeserializadorClima()
        clima = deserializador.deserializar(datos)

        print("Clima de Santiago")
        print("Temperatura:", clima.get_temperatura(), "°C")
        print("Humedad:", clima.get_humedad(), "%")
        print("Código meteorológico:", clima.get_codigo())
        print("Fecha del clima:", clima.get_fecha())
    except ErrorAPI as error:
        print("No se pudo consultar el clima:", error)
    except ValueError as error:
        print("Los datos del clima no son válidos:", error)


if __name__ == "__main__": #Se ejecuta si este archivo es el que iniciamos directamente
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
