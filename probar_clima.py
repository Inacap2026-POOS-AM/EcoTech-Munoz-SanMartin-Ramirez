"""Prueba manual de la consulta y deserialización durante el desarrollo."""

import argparse
import logging
from datetime import datetime, timezone

import psycopg

from api_cliente import ErrorAPI, buscar_lugares, consultar_clima
from deserializador_clima import DeserializadorClima
from dominio.excepciones import ConexionBaseDatosError, ErrorPersistencia
from repositorio.clima_repo import ClimaRepositorio
from repositorio.conexion import obtener_conexion


def main():
    parser = argparse.ArgumentParser(description="Prueba de consulta y guardado del clima") # Para leer las opciones escritar despues del nombre del archivo en la terminal
    parser.add_argument("--inicializar-clima", action="store_true", help="Crear la tabla de clima sin borrar datos")
    argumentos = parser.parse_args()
    if argumentos.inicializar_clima:
        try:
            with obtener_conexion() as conexion:
                ClimaRepositorio(conexion).inicializar()
            print("Tabla de clima preparada. Los datos existentes se conservaron.")
        except (ConexionBaseDatosError, ErrorPersistencia, psycopg.Error, ValueError, OSError):
            print("No se pudo preparar la tabla. Revisa la conexión y la configuración de la base.")
        return

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
        obtenido_en = datetime.now(timezone.utc)
        deserializador = DeserializadorClima()
        clima = deserializador.deserializar(datos)

        print("Clima de:", lugar["nombre"], ",", lugar["region"], ",", lugar["pais"])
        print("Las horas se muestran en la zona America/Santiago.")
        print("Temperatura:", clima.get_temperatura(), "°C")
        print("Humedad:", clima.get_humedad(), "%")
        print("Estado del tiempo:", clima.get_descripcion())
        print("Fecha del clima:", clima.get_fecha())
        print("Obtenido en:", obtenido_en.isoformat())

        try:
            with obtener_conexion() as conexion:
                ClimaRepositorio(conexion).guardar(lugar, clima, obtenido_en)
            print("Consulta guardada en Supabase sin duplicar el mismo lugar y fecha del clima.")
        except ErrorPersistencia as error:
            print(error)
            print("No se confirmó el guardado en Supabase; los datos de la API se muestran arriba.")
        except (ConexionBaseDatosError, psycopg.Error, ValueError):
            print("No se confirmó el guardado en Supabase. Revisa la conexión y la configuración.")
    except ErrorAPI as error:
        print("No se pudo consultar el clima:", error)
    except ValueError as error:
        print("Datos de consulta o de clima no válidos:", error)


if __name__ == "__main__": #Se ejecuta si este archivo es el que iniciamos directamente
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
