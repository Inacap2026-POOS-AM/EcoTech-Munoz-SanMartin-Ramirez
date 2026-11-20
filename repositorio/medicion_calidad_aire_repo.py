from dominio.medicion_calidad_aire import MedicionCalidadAire


class MedicionCalidadAireRepositorio:
    """Almacena y recupera mediciones ambientales en PostgreSQL."""

    def __init__(self, conexion):
        self.__conexion = conexion

    def crear(self, medicion):
        if not isinstance(medicion, MedicionCalidadAire):
            raise ValueError("Se requiere una medici?n v?lida")

        consulta = """
            INSERT INTO ecotech.medicion_calidad_aire (
                pm2_5, pm10, us_aqi, fecha_hora, latitud, longitud
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING pm2_5, pm10, us_aqi, fecha_hora,
                      latitud, longitud, obtenido_en
        """

        parametros = (
            medicion.pm2_5,
            medicion.pm10,
            medicion.us_aqi,
            medicion.fecha_hora,
            medicion.latitud,
            medicion.longitud,
        )

        with self.__conexion.cursor() as cursor:
            cursor.execute(consulta, parametros)
            fila = cursor.fetchone()

        return self._convertir_fila(fila)

    def obtener_ultima(self):
        consulta = """
            SELECT pm2_5, pm10, us_aqi, fecha_hora,
                   latitud, longitud, obtenido_en
            FROM ecotech.medicion_calidad_aire
            ORDER BY obtenido_en DESC, id DESC
            LIMIT 1
        """

        with self.__conexion.cursor() as cursor:
            cursor.execute(consulta)
            fila = cursor.fetchone()

        if fila is None:
            return None

        return self._convertir_fila(fila)

    @staticmethod
    def _convertir_fila(fila):
        medicion = MedicionCalidadAire(
            pm2_5=fila[0],
            pm10=fila[1],
            us_aqi=fila[2],
            fecha_hora=fila[3],
            latitud=fila[4],
            longitud=fila[5],
        )

        return medicion, fila[6]
