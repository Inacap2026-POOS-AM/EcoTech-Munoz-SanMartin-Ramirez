"""Prueba manual de la consulta y deserialización durante el desarrollo."""

import logging

from api_cliente import ErrorAPI, buscar_lugares, consultar_clima
from deserializador_clima import DeserializadorClima


def main():
    try:
        while True:
            nombre = input("Nombre del lugar (Enter para salir): ")
            if not nombre.strip():
                return
            try:
                lugares = buscar_lugares(nombre)
            except ValueError as error:
                print(error)
                continue
            if lugares:
                break
            print("No se encontraron lugares. Revisa el nombre e inténtalo nuevamente.")

        for numero, lugar in enumerate(lugares, start=1):
            print(numero, "-", lugar["nombre"], ",", lugar["region"], ",", lugar["pais"])

        while True:
            try:
                seleccion = int(input("Selecciona un lugar (0 para salir): "))
            except ValueError:
                print("Ingresa el número de una opción.")
                continue
            if 0 <= seleccion <= len(lugares):
                break
            print("Selecciona una opción de la lista.")

        if seleccion == 0:
            return

        lugar = lugares[seleccion - 1]
        latitud = lugar["latitud"]
        longitud = lugar["longitud"]
        datos = consultar_clima(latitud, longitud)
        deserializador = DeserializadorClima()
        clima = deserializador.deserializar(datos)

        print("Clima de:", lugar["nombre"], ",", lugar["region"], ",", lugar["pais"])
        print("Las horas se muestran en la zona America/Santiago.")
        print("Temperatura:", clima.get_temperatura(), "°C")
        print("Humedad:", clima.get_humedad(), "%")
        print("Estado del tiempo:", clima.get_descripcion())
        print("Fecha del clima:", clima.get_fecha())
    except ErrorAPI as error:
        print("No se pudo consultar el clima:", error)
    except ValueError as error:
        print("Datos de consulta o de clima no válidos:", error)


if __name__ == "__main__": #Se ejecuta si este archivo es el que iniciamos directamente
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
