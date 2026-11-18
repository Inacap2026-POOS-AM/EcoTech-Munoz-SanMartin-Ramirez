from datetime import datetime # Para comprobar que obtenido_en sea una fecha y hora
from pathlib import Path # Permite localizar y leer el archivo datos/clima.sql

import psycopg # Para trabajar con postgres y manejar sus errores

from dominio.clima import Clima
from dominio.excepciones import ErrorPersistencia


class ClimaRepositorio:
    """Guarda clima; la conexión externa controla commit y rollback."""

    def __init__(self, conexion):
        self.__conexion = conexion

    def inicializar(self):
        ruta = Path(__file__).resolve().parent.parent / "datos" / "clima.sql" # Para localizar el archivo clima.sql y leerlo
        try:
            with self.__conexion.cursor() as cursor: # Para ejecutar instrucciones SQL
                self._limitar_espera(cursor)
                cursor.execute(ruta.read_text(encoding="utf-8")) # Para crear la tabla si no existe
        except psycopg.Error as error:
            raise ErrorPersistencia("No se pudo preparar la tabla de clima") from error

    def guardar(self, lugar: dict, clima: Clima, obtenido_en: datetime):
        if not isinstance(lugar, dict) or not isinstance(clima, Clima):
            raise ValueError("Se requiere un lugar y un objeto Clima válidos")
        for campo in ("nombre", "region", "pais"):
            texto = lugar.get(campo)
            if not isinstance(texto, str) or not texto.strip() or not texto.isprintable() or len(texto) > 200:
                raise ValueError("El nombre, región y país deben ser textos válidos")
        for campo, limite in (("latitud", 90), ("longitud", 180)):
            valor = lugar.get(campo)
            if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not -limite <= valor <= limite:
                raise ValueError("Las coordenadas del lugar no son válidas")
        if not isinstance(obtenido_en, datetime) or obtenido_en.utcoffset() is None:
            raise ValueError("obtenido_en debe ser una fecha con zona horaria")
        if clima.get_fecha().tzinfo is not None:
            raise ValueError("La fecha del clima debe ser la hora local sin offset de America/Santiago")

        try:
            with self.__conexion.cursor() as cursor:
                self._limitar_espera(cursor)
                cursor.execute(
                    """
                    INSERT INTO ecotech.clima (
                        nombre, region, pais, latitud, longitud,
                        temperatura, humedad, codigo, fecha_clima, obtenido_en
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (latitud, longitud, fecha_clima)
                    DO UPDATE SET
                        nombre = EXCLUDED.nombre,
                        region = EXCLUDED.region,
                        pais = EXCLUDED.pais,
                        temperatura = EXCLUDED.temperatura,
                        humedad = EXCLUDED.humedad,
                        codigo = EXCLUDED.codigo,
                        obtenido_en = EXCLUDED.obtenido_en
                    WHERE EXCLUDED.obtenido_en >= ecotech.clima.obtenido_en
                    """,
                    (
                        lugar["nombre"].strip(), lugar["region"].strip(), lugar["pais"].strip(),
                        lugar["latitud"], lugar["longitud"],
                        clima.get_temperatura(), clima.get_humedad(), clima.get_codigo(),
                        clima.get_fecha(), obtenido_en,
                    ),
                )
        except psycopg.errors.UndefinedTable as error:
            raise ErrorPersistencia(
                "Falta la tabla de clima. Ejecuta python main.py --inicializar-clima como administrador"
            ) from error
        except psycopg.Error as error:
            raise ErrorPersistencia("No se pudo guardar el clima en la base de datos") from error

    def _limitar_espera(self, cursor):
        # Configuración local a la transacción: evita quedar esperando indefinidamente.
        cursor.execute("SELECT set_config('statement_timeout', %s, true)", ("10000",))
        cursor.execute("SELECT set_config('lock_timeout', %s, true)", ("5000",))
