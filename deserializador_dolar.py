from datetime import datetime
from decimal import Decimal

from dominio.indicador_dolar import IndicadorDolar


class DeserializadorDolar:
    def deserializar(self, datos):
        if not isinstance(datos, dict) or datos.get("codigo") != "dolar" or datos.get("unidad_medida") != "Pesos":
            raise ValueError("La respuesta debe corresponder al dólar observado expresado en pesos")
        serie = datos.get("serie")
        if not isinstance(serie, list) or not serie:
            raise ValueError("El servicio no entregó una serie de valores del dólar")
        indicadores = []
        for fila in serie:
            if not isinstance(fila, dict):
                raise ValueError("La serie del dólar tiene una estructura inválida")
            valor, fecha_texto = fila.get("valor"), fila.get("fecha")
            if isinstance(valor, bool) or not isinstance(valor, (int, float, Decimal)) or not isinstance(fecha_texto, str):
                raise ValueError("Faltan un valor numérico o una fecha del dólar")
            try:
                fecha = datetime.fromisoformat(fecha_texto)
            except ValueError as error:
                raise ValueError("La fecha del indicador tiene un formato inválido") from error
            if fecha.utcoffset() is None:
                raise ValueError("La fecha del indicador debe incluir zona horaria")
            indicadores.append(IndicadorDolar(Decimal(str(valor)), fecha.date()))
        return max(indicadores, key=lambda indicador: indicador.get_fecha())
