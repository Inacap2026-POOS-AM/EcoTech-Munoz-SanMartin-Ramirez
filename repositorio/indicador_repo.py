from contextlib import closing
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
import sqlite3
import psycopg

from dominio.excepciones import ErrorPersistencia
from dominio.indicador_dolar import IndicadorDolar


def validar_guardado(indicador, obtenido_en):
    if not isinstance(indicador, IndicadorDolar):
        raise ValueError("Se requiere un indicador validado")
    if not isinstance(obtenido_en, datetime) or obtenido_en.utcoffset() is None:
        raise ValueError("La fecha de obtención debe incluir zona horaria")


class IndicadorRepositorio:
    def __init__(self, conexion):
        self.__conexion = conexion

    def inicializar(self):
        ruta = Path(__file__).resolve().parent.parent / "datos" / "indicadores.sql"
        try:
            with self.__conexion.cursor() as cursor:
                self._limitar_espera(cursor)
                cursor.execute(ruta.read_text(encoding="utf-8"))
        except psycopg.Error as error:
            raise ErrorPersistencia("No se pudo preparar la tabla de indicadores") from error

    def guardar(self, indicador, obtenido_en):
        validar_guardado(indicador, obtenido_en)
        try:
            with self.__conexion.cursor() as cursor:
                self._limitar_espera(cursor)
                cursor.execute(
                    """
                    INSERT INTO ecotech.indicador_dolar (fecha, valor, obtenido_en)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (fecha) DO UPDATE SET
                        valor = EXCLUDED.valor, obtenido_en = EXCLUDED.obtenido_en
                    WHERE EXCLUDED.obtenido_en >= ecotech.indicador_dolar.obtenido_en
                    """,
                    (indicador.get_fecha(), indicador.get_valor(), obtenido_en),
                )
        except psycopg.errors.UndefinedTable as error:
            raise ErrorPersistencia("Prepara la tabla con python main.py --inicializar-indicadores como administrador") from error
        except psycopg.Error as error:
            raise ErrorPersistencia("No se pudo guardar el indicador en Supabase") from error

    def _limitar_espera(self, cursor):
        cursor.execute("SELECT set_config('statement_timeout', %s, true)", ("10000",))
        cursor.execute("SELECT set_config('lock_timeout', %s, true)", ("5000",))


class IndicadorLocalRepositorio:
    def __init__(self, ruta=None):
        self.__ruta = Path(ruta) if ruta is not None else Path(__file__).resolve().parent.parent / "datos" / "indicadores_local.sqlite3"
        self._ejecutar("""
            CREATE TABLE IF NOT EXISTS indicador_dolar (
                fecha TEXT PRIMARY KEY,
                valor TEXT NOT NULL,
                obtenido_en TEXT NOT NULL
            )
        """)

    def _ejecutar(self, sql, parametros=()):
        try:
            with closing(sqlite3.connect(self.__ruta, timeout=3)) as conexion:
                with conexion:
                    return conexion.execute(sql, parametros).fetchall()
        except sqlite3.Error as error:
            raise ErrorPersistencia("No se pudo acceder al respaldo local del dólar") from error

    def guardar(self, indicador, obtenido_en):
        validar_guardado(indicador, obtenido_en)
        self._ejecutar(
            """
            INSERT INTO indicador_dolar (fecha, valor, obtenido_en) VALUES (?, ?, ?)
            ON CONFLICT (fecha) DO UPDATE SET
                valor = excluded.valor, obtenido_en = excluded.obtenido_en
            WHERE excluded.obtenido_en >= indicador_dolar.obtenido_en
            """,
            (indicador.get_fecha().isoformat(), str(indicador.get_valor()),
             obtenido_en.astimezone(timezone.utc).isoformat(timespec="microseconds")),
        )

    def obtener_ultimo(self):
        filas = self._ejecutar("SELECT fecha, valor, obtenido_en FROM indicador_dolar ORDER BY fecha DESC LIMIT 1")
        if not filas:
            return None
        try:
            fecha, valor, obtenido = filas[0]
            indicador = IndicadorDolar(Decimal(valor), date.fromisoformat(fecha))
            obtenido_en = datetime.fromisoformat(obtenido)
            validar_guardado(indicador, obtenido_en)
            return indicador, obtenido_en
        except (ValueError, ArithmeticError, TypeError) as error:
            raise ErrorPersistencia("El respaldo del dólar contiene datos inválidos") from error
