"""Respaldo del último clima válido por lugar, sin conexión a internet."""

import sqlite3
import unicodedata
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from dominio.clima import Clima
from dominio.excepciones import ErrorPersistencia


class ClimaLocalRepositorio:
    def __init__(self, ruta=None):
        self.__ruta = Path(ruta) if ruta is not None else (
            Path(__file__).resolve().parent.parent / "datos" / "clima_local.sqlite3"
        )
        self._ejecutar("""
            CREATE TABLE IF NOT EXISTS clima_local (
                nombre TEXT NOT NULL CHECK (length(trim(nombre)) BETWEEN 1 AND 200),
                region TEXT NOT NULL CHECK (length(trim(region)) BETWEEN 1 AND 200),
                pais TEXT NOT NULL CHECK (length(trim(pais)) BETWEEN 1 AND 200),
                latitud REAL NOT NULL CHECK (latitud BETWEEN -90 AND 90),
                longitud REAL NOT NULL CHECK (longitud BETWEEN -180 AND 180),
                temperatura REAL NOT NULL,
                humedad REAL NOT NULL CHECK (humedad BETWEEN 0 AND 100),
                codigo INTEGER NOT NULL,
                fecha_clima TEXT NOT NULL,
                obtenido_en TEXT NOT NULL,
                PRIMARY KEY (latitud, longitud)
            )
        """)

    def _ejecutar(self, consulta, parametros=()):
        try:
            # El with de sqlite3 confirma o revierte; closing también cierra la conexión.
            with closing(sqlite3.connect(self.__ruta, timeout=3)) as conexion:
                conexion.row_factory = sqlite3.Row
                with conexion:
                    return conexion.execute(consulta, parametros).fetchall()
        except sqlite3.Error as error:
            raise ErrorPersistencia("No se pudo acceder al respaldo local del clima") from error

    def guardar(self, lugar: dict, clima: Clima, obtenido_en: datetime):
        if not isinstance(lugar, dict) or not isinstance(clima, Clima):
            raise ValueError("Se requiere un lugar y un objeto Clima válidos")
        for campo in ("nombre", "region", "pais"):
            texto = lugar.get(campo)
            if not isinstance(texto, str) or not texto.strip() or not texto.isprintable() or len(texto) > 200:
                raise ValueError("El lugar del respaldo contiene textos inválidos")
        for campo, limite in (("latitud", 90), ("longitud", 180)):
            valor = lugar.get(campo)
            if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not -limite <= valor <= limite:
                raise ValueError("Las coordenadas del respaldo no son válidas")
        if not isinstance(obtenido_en, datetime) or obtenido_en.utcoffset() is None:
            raise ValueError("obtenido_en debe incluir zona horaria")
        if clima.get_fecha().tzinfo is not None:
            raise ValueError("La fecha meteorológica debe estar en hora local de Santiago sin offset")

        self._ejecutar(
            """
            INSERT INTO clima_local (
                nombre, region, pais, latitud, longitud,
                temperatura, humedad, codigo, fecha_clima, obtenido_en
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (latitud, longitud) DO UPDATE SET
                nombre = excluded.nombre,
                region = excluded.region,
                pais = excluded.pais,
                temperatura = excluded.temperatura,
                humedad = excluded.humedad,
                codigo = excluded.codigo,
                fecha_clima = excluded.fecha_clima,
                obtenido_en = excluded.obtenido_en
            WHERE excluded.fecha_clima > clima_local.fecha_clima
               OR (excluded.fecha_clima = clima_local.fecha_clima
                   AND excluded.obtenido_en >= clima_local.obtenido_en)
            """,
            (
                lugar["nombre"].strip(), lugar["region"].strip(), lugar["pais"].strip(),
                round(lugar["latitud"], 6), round(lugar["longitud"], 6),
                clima.get_temperatura(), clima.get_humedad(), clima.get_codigo(),
                clima.get_fecha().isoformat(timespec="microseconds"),
                obtenido_en.astimezone(timezone.utc).isoformat(timespec="microseconds"),
            ),
        )

    def buscar_lugares(self, nombre: str):
        if not isinstance(nombre, str) or not 2 <= len(nombre.strip()) <= 100 or not nombre.isprintable():
            raise ValueError("Ingresa un nombre de lugar válido de 2 a 100 caracteres")
        buscado = self._normalizar(nombre)
        filas = self._ejecutar("SELECT nombre, region, pais, latitud, longitud FROM clima_local ORDER BY nombre")
        return [dict(fila) for fila in filas if self._normalizar(fila["nombre"]).startswith(buscado)][:5]

    def obtener_ultimo(self, latitud, longitud):
        filas = self._ejecutar(
            "SELECT temperatura, humedad, codigo, fecha_clima, obtenido_en FROM clima_local WHERE latitud = ? AND longitud = ?",
            (round(latitud, 6), round(longitud, 6)),
        )
        if not filas:
            return None
        fila = filas[0]
        try:
            clima = Clima(fila["temperatura"], fila["humedad"], fila["codigo"], datetime.fromisoformat(fila["fecha_clima"]))
            obtenido_en = datetime.fromisoformat(fila["obtenido_en"])
            if obtenido_en.utcoffset() is None:
                raise ValueError("El respaldo no tiene zona horaria")
            return clima, obtenido_en
        except (ValueError, TypeError) as error:
            raise ErrorPersistencia("El respaldo local contiene datos inválidos") from error

    @staticmethod
    def _normalizar(texto):
        return "".join(
            letra for letra in unicodedata.normalize("NFD", texto.strip().casefold())
            if unicodedata.category(letra) != "Mn"
        )
