"""Consulta de clima disponible desde una sesión autenticada de EcoTech."""

from datetime import datetime, timezone

import psycopg

from api_cliente import ErrorAPI
from deserializador_clima import DeserializadorClima
from dominio.excepciones import AutorizacionError, ConexionBaseDatosError, ErrorPersistencia
from repositorio.clima_repo import ClimaRepositorio
from repositorio.clima_local_repo import ClimaLocalRepositorio
from repositorio.conexion import obtener_conexion
from servicios import GestionEcoTech


def consultar_clima_menu(gestion):
    if not isinstance(gestion, GestionEcoTech):
        raise AutorizacionError("Debes iniciar sesión antes de consultar el clima")
    gestion.exigir_sesion()
    try:
        respaldo = ClimaLocalRepositorio()
    except ErrorPersistencia as error:
        print(error)
        print("La consulta en línea continuará, pero el respaldo local no está disponible.")
        respaldo = None

    try:
        while True:
            nombre = input("Nombre del lugar (Enter para salir): ")
            if not nombre.strip():
                return
            try:
                lugares = gestion.buscar_lugares_clima(nombre)
            except ErrorAPI as error:
                print(error)
                if respaldo is None:
                    print("No hay un respaldo local disponible para buscar lugares.")
                    return
                lugares = respaldo.buscar_lugares(nombre)
                if lugares:
                    print("Servicio de búsqueda no disponible. Mostrando lugares con clima guardado localmente.")
                else:
                    print("No hay lugares guardados con ese nombre. Puedes probar otro o salir con Enter.")
                    continue
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
        desde_respaldo = False
        try:
            datos = gestion.consultar_clima(latitud, longitud)
            obtenido_en = datetime.now(timezone.utc)
            deserializador = DeserializadorClima()
            clima = deserializador.deserializar(datos)
        except (ErrorAPI, ValueError) as error:
            print("No se obtuvo clima válido del servicio:", error)
            guardado = respaldo.obtener_ultimo(latitud, longitud) if respaldo is not None else None
            if guardado is None:
                print("No hay datos locales para este lugar. Se necesita una consulta exitosa previa.")
                return
            clima, obtenido_en = guardado
            desde_respaldo = True

        # Guardar primero en el equipo: no depende de que Supabase esté disponible.
        if not desde_respaldo and respaldo is not None:
            try:
                respaldo.guardar(lugar, clima, obtenido_en)
                print("Copia local guardada.")
            except (ErrorPersistencia, ValueError) as error:
                print("No se confirmó la copia local:", error)

        print("Clima de:", lugar["nombre"], ",", lugar["region"], ",", lugar["pais"])
        print("Las horas se muestran en la zona America/Santiago.")
        print("Temperatura:", clima.get_temperatura(), "°C")
        print("Humedad:", clima.get_humedad(), "%")
        print("Estado del tiempo:", clima.get_descripcion())
        print("Fecha del clima:", clima.get_fecha())
        print("Obtenido en:", obtenido_en.isoformat())

        if desde_respaldo:
            antiguedad = max(0, int((datetime.now(timezone.utc) - obtenido_en).total_seconds()))
            print("PLAN B: datos del respaldo local, obtenidos hace", antiguedad // 60, "minutos y", antiguedad % 60, "segundos.")
            print("No representan necesariamente el clima actual. No se enviarán de nuevo a Supabase.")
            return

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
    except ErrorPersistencia as error:
        print(error)
        print("No se pudieron recuperar datos del respaldo local.")

