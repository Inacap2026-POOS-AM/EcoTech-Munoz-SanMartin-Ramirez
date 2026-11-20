"""Servicios de EcoTech con persistencia parametrizada y respaldo validado."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import logging
from urllib.parse import urlencode
from api_cliente import ClienteAPI, ServicioExternoError
from deserializador import Deserializador, numero
from dominio.clima import CondicionClimatica
from dominio.cotizacion import MONEDAS
from dominio.pago_estimado import PagoEstimado
from dominio.excepciones import ErrorNegocio

LOG = logging.getLogger("ecotech.servicios")


class ServiciosEcoTech:
    def __init__(self, con, usuario, cliente=None):
        if usuario is None:
            raise ErrorNegocio("Inicie sesión.")
        usuario.exigir("consultar_servicios")
        self.con = con
        self.cliente = cliente or ClienteAPI()

    def _leer(self, clave, url, parsear, cargar_cache, fuente):
        ahora = datetime.now(timezone.utc)
        try:
            datos = parsear(self.cliente.obtener(url))
        except (ServicioExternoError, KeyError, TypeError, ValueError,
                OverflowError, InvalidOperation) as exc:
            causa = str(exc) if isinstance(exc, ServicioExternoError) else "Respuesta inválida"
            LOG.warning("fuente=%s resultado=respaldo_solicitado", fuente)
            fila = self.con.execute(
                "SELECT obtenido_en,datos FROM cache_api WHERE clave=?", (clave,)
            ).fetchone()
            if not fila:
                raise ErrorNegocio(causa + ". Sin datos locales para esta consulta.") from None
            try:
                marca = datetime.fromisoformat(fila[0])
                if marca.utcoffset() is None:
                    raise ValueError
                respaldo = cargar_cache(json.loads(fila[1]))
                minutos = max(0, int((ahora - marca).total_seconds() // 60))
            except (KeyError, TypeError, ValueError, OverflowError, InvalidOperation):
                LOG.error("fuente=%s resultado=respaldo_invalido", fuente)
                raise ErrorNegocio(causa + ". Datos locales inválidos; repita la consulta con red.") from None
            LOG.info("fuente=%s resultado=respaldo_local antiguedad_min=%d", fuente, minutos)
            return (f"Respaldo local · {causa} · obtenido_en {marca.isoformat()} · "
                    f"antigüedad {minutos} min · {fuente}"), respaldo
        obtenido = datetime.now(timezone.utc).isoformat()
        self.con.execute(
            """INSERT INTO cache_api(clave,obtenido_en,datos) VALUES (?,?,?)
               ON CONFLICT(clave) DO UPDATE SET
               obtenido_en=excluded.obtenido_en,datos=excluded.datos""",
            (clave, obtenido, json.dumps(datos.a_dict(), allow_nan=False)),
        )
        LOG.info("fuente=%s resultado=datos_validados_y_persistidos", fuente)
        return f"En línea · obtenido_en {obtenido} · {fuente}", datos

    def clima(self, proyecto, lat, lon, clave_api=None) -> tuple[str, CondicionClimatica]:
        if not isinstance(proyecto, str) or not self.con.execute(
            "SELECT 1 FROM proyecto WHERE id=?", (proyecto,)
        ).fetchone():
            raise ErrorNegocio("Proyecto inexistente.")
        lat, lon = numero(lat, -90, 90), numero(lon, -180, 180)
        sitio = f"{lat:.4f},{lon:.4f}"
        if clave_api:
            url = "https://api.weatherapi.com/v1/current.json?" + urlencode(
                {"key": clave_api, "q": sitio, "lang": "es"})
            fuente, parsear = "WeatherAPI.com", Deserializador.clima_con_clave
        else:
            url = "https://api.open-meteo.com/v1/forecast?" + urlencode(
                {"latitude": round(lat, 4), "longitude": round(lon, 4),
                 "current": "temperature_2m,relative_humidity_2m,weather_code", "timezone": "GMT"})
            fuente, parsear = "Open-Meteo · https://open-meteo.com", Deserializador.clima
        return self._leer(json.dumps(["clima", fuente, proyecto, sitio]), url, parsear,
                          Deserializador.clima_guardado, fuente)

    def pago(self, base, destino, importe) -> tuple[str, PagoEstimado]:
        if (not isinstance(base, str) or not isinstance(destino, str)
                or base not in MONEDAS or destino not in MONEDAS):
            raise ErrorNegocio("Moneda no disponible.")
        try:
            monto = Decimal(str(importe))
            if not monto.is_finite() or not 0 < monto <= 10**12:
                raise ValueError
        except (InvalidOperation, ValueError):
            raise ErrorNegocio("Importe inválido.") from None
        aviso, cotizacion = self._leer(
            "cambio:" + base + ":" + destino, "https://open.er-api.com/v6/latest/" + base,
            lambda datos: Deserializador.cambio(datos, base, destino),
            Deserializador.cambio_guardado,
            "Rates By Exchange Rate API · https://www.exchangerate-api.com",
        )
        if cotizacion.base != base or cotizacion.destino != destino:
            raise ErrorNegocio("La cotización local no corresponde a las monedas solicitadas.")
        unidad = Decimal("1") if destino in {"CLP", "JPY"} else Decimal("0.01")
        total = (monto * cotizacion.tasa).quantize(unidad)
        return aviso, PagoEstimado(cotizacion, monto, total)
