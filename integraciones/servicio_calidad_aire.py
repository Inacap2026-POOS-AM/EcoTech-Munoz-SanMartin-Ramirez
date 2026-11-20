from dataclasses import dataclass
import logging

import psycopg

from dominio.excepciones import ConexionBaseDatosError
from dominio.medicion_calidad_aire import MedicionCalidadAire
from integraciones.cliente_calidad_aire import (
    ClienteCalidadAire,
    ErrorCalidadAire,
)
from repositorio.conexion import obtener_conexion
from repositorio.medicion_calidad_aire_repo import (
    MedicionCalidadAireRepositorio,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultadoCalidadAire:
    """Resultado de una consulta, con información sobre su procedencia."""

    medicion: MedicionCalidadAire
    obtenido_en: object
    desde_respaldo: bool
    guardada: bool


class ServicioCalidadAire:
    """Coordina la API de calidad del aire y su respaldo en PostgreSQL."""

    def __init__(self, cliente=None, conexion_factory=None):
        self.__cliente = cliente or ClienteCalidadAire()
        self.__conexion_factory = conexion_factory or obtener_conexion

    def obtener_medicion(self):
        try:
            medicion = self.__cliente.obtener_medicion_actual()
        except ErrorCalidadAire as error:
            logger.warning(
                "No se pudo consultar Open-Meteo. Se intentará usar PostgreSQL."
            )
            return self._obtener_respaldo(error)

        try:
            with self.__conexion_factory() as conexion:
                resultado = MedicionCalidadAireRepositorio(
                    conexion
                ).crear(medicion)

            medicion_guardada, obtenido_en = resultado

            return ResultadoCalidadAire(
                medicion=medicion_guardada,
                obtenido_en=obtenido_en,
                desde_respaldo=False,
                guardada=True,
            )

        except (ConexionBaseDatosError, psycopg.Error):
            logger.exception(
                "La API respondió, pero no fue posible guardar la medición."
            )

            return ResultadoCalidadAire(
                medicion=medicion,
                obtenido_en=None,
                desde_respaldo=False,
                guardada=False,
            )

    def _obtener_respaldo(self, error_api):
        try:
            with self.__conexion_factory() as conexion:
                resultado = MedicionCalidadAireRepositorio(
                    conexion
                ).obtener_ultima()

        except (ConexionBaseDatosError, psycopg.Error) as error_db:
            raise ErrorCalidadAire(
                "Fallaron Open-Meteo y la conexión con el respaldo PostgreSQL."
            ) from error_db

        if resultado is None:
            raise ErrorCalidadAire(
                "Open-Meteo no está disponible y no existen mediciones guardadas."
            ) from error_api

        medicion, obtenido_en = resultado

        return ResultadoCalidadAire(
            medicion=medicion,
            obtenido_en=obtenido_en,
            desde_respaldo=True,
            guardada=True,
        )
