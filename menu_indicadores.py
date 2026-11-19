from datetime import datetime, timezone
import psycopg

from api_cliente import ErrorAPI
from deserializador_dolar import DeserializadorDolar
from dominio.excepciones import AutorizacionError, ConexionBaseDatosError, ErrorPersistencia
from repositorio.conexion import obtener_conexion
from repositorio.indicador_repo import IndicadorRepositorio, IndicadorLocalRepositorio
from servicios import GestionEcoTech


def consultar_indicadores_menu(gestion):
    if not isinstance(gestion, GestionEcoTech):
        raise AutorizacionError("Debes iniciar sesión antes de consultar indicadores")
    gestion.exigir_sesion()
    try:
        respaldo = IndicadorLocalRepositorio()
    except ErrorPersistencia as error:
        print(error)
        respaldo = None

    try:
        desde_respaldo = False
        try:
            datos = gestion.consultar_dolar()
            obtenido_en = datetime.now(timezone.utc)
            indicador = DeserializadorDolar().deserializar(datos)
        except (ErrorAPI, ValueError) as error:
            print("No se obtuvo un indicador válido:", error)
            guardado = respaldo.obtener_ultimo() if respaldo is not None else None
            if guardado is None:
                print("No hay un indicador local. Se necesita una consulta exitosa previa.")
                return
            indicador, obtenido_en = guardado
            desde_respaldo = True

        if not desde_respaldo:
            if respaldo is not None:
                try:
                    respaldo.guardar(indicador, obtenido_en)
                    print("Copia local del dólar guardada.")
                except (ErrorPersistencia, ValueError) as error:
                    print("No se confirmó el respaldo:", error)
            try:
                with obtener_conexion() as conexion:
                    IndicadorRepositorio(conexion).guardar(indicador, obtenido_en)
                print("Indicador guardado en Supabase sin duplicar su fecha.")
            except (ConexionBaseDatosError, ErrorPersistencia, psycopg.Error, ValueError) as error:
                print("No se confirmó el guardado en Supabase.")
                if isinstance(error, ErrorPersistencia):
                    print(error)

        print("Fuente: mindicador.cl — dólar observado")
        print("Tipo de cambio:", indicador.get_valor(), "CLP por 1 USD")
        print("Fecha del indicador:", indicador.get_fecha())
        print("Obtenido en (UTC):", obtenido_en.isoformat())
        print("Es el último indicador recibido; su fecha puede ser anterior a hoy.")
        if desde_respaldo:
            segundos = max(0, int((datetime.now(timezone.utc) - obtenido_en).total_seconds()))
            print("PLAN B: indicador local obtenido hace", segundos // 60, "minutos y", segundos % 60, "segundos.")
        while True:
            importe = input("Importe del pago en CLP, sin separadores de miles (Enter para volver): ").strip()
            if not importe:
                return
            try:
                resultado = indicador.convertir_a_usd(importe)
            except ValueError as error:
                print(error)
                continue
            print("Equivalente:", resultado, "USD, redondeado a dos decimales.")
            print("Conversión referencial: no incluye comisiones ni modifica salarios o realiza transferencias.")
            return
    except ErrorPersistencia as error:
        print(error)
