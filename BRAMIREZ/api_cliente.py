"""HTTPS con TLS, timeout, reintentos acotados y logs sin URL ni secretos."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from http.client import HTTPException
import json
import logging
import math
import ssl
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

LOG = logging.getLogger("ecotech.api")
MAX_INTENTOS, TIMEOUT, MAX_BYTES = 3, 5, 131072


class ServicioExternoError(ValueError):
    """Mensaje seguro: no contiene URL, token ni respuesta remota."""


class SinRedireccion(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def espera_servidor(valor, defecto, ahora=None):
    """Retry-After admite segundos enteros o fecha HTTP."""
    if not valor:
        return defecto
    try:
        segundos = float(int(valor))
    except (ValueError, TypeError, OverflowError):
        try:
            fecha = parsedate_to_datetime(valor)
            if fecha.tzinfo is None:
                return defecto
            segundos = (fecha - (ahora or datetime.now(timezone.utc))).total_seconds()
        except (TypeError, ValueError, OverflowError):
            return defecto
    return max(defecto, segundos) if math.isfinite(segundos) else defecto


class ClienteAPI:
    def __init__(self, abrir=None, esperar=sleep, reloj=monotonic):
        self.abrir = abrir or build_opener(SinRedireccion()).open
        self.esperar = esperar
        self.reloj = reloj
        self._bloqueado_hasta = {}

    def obtener(self, url):
        try:
            partes = urlsplit(url)
            if (partes.scheme != "https" or not partes.hostname
                    or partes.username or partes.password or partes.fragment):
                raise ValueError
            origen = (partes.hostname, partes.port or 443)
        except (ValueError, TypeError):
            raise ServicioExternoError("Se requiere una URL HTTPS válida.") from None
        if self._bloqueado_hasta.get(origen, 0) > self.reloj():
            LOG.warning("consulta aplazada: Retry-After todavía vigente")
            raise ServicioExternoError("HTTP 429. Retry-After todavía vigente.")
        solicitud = uuid4().hex[:8]
        req = Request(url, headers={"Accept": "application/json",
                                   "User-Agent": "EcoTech-TI3021/1.1"})
        ultima_pausa = 0
        for intento in range(1, MAX_INTENTOS + 1):
            pausa = max(2 ** (intento - 1), ultima_pausa * 2)
            LOG.info("solicitud=%s intento=%d/%d timeout=%ds",
                     solicitud, intento, MAX_INTENTOS, TIMEOUT)
            try:
                with self.abrir(req, timeout=TIMEOUT) as respuesta:
                    contenido = respuesta.read(MAX_BYTES + 1)
                if len(contenido) > MAX_BYTES:
                    raise ServicioExternoError("Respuesta demasiado grande.")
                valor = json.loads(contenido)
                if not isinstance(valor, dict):
                    raise ServicioExternoError("Se esperaba un objeto JSON.")
                self._bloqueado_hasta.pop(origen, None)
                LOG.info("solicitud=%s resultado=correcto", solicitud)
                return valor
            except HTTPError as error:
                codigo = error.code
                cabecera = error.headers.get("Retry-After") if error.headers else None
                error.close()
                mensaje = f"HTTP {codigo}"
                LOG.warning("solicitud=%s resultado=HTTP_%d", solicitud, codigo)
                if codigo == 429:
                    pausa = espera_servidor(cabecera, pausa)
                    self._bloqueado_hasta[origen] = self.reloj() + pausa
                elif not 500 <= codigo < 600:
                    raise ServicioExternoError(mensaje) from None
            except (ssl.SSLError, URLError, OSError, HTTPException) as error:
                if isinstance(getattr(error, "reason", error), ssl.SSLError):
                    LOG.warning("solicitud=%s resultado=TLS_rechazado", solicitud)
                    raise ServicioExternoError("Error de verificación TLS.") from None
                mensaje = "Conexión no disponible"
                LOG.warning("solicitud=%s resultado=fallo_red", solicitud)
            except (json.JSONDecodeError, UnicodeError, RecursionError):
                LOG.warning("solicitud=%s resultado=JSON_invalido", solicitud)
                raise ServicioExternoError("Respuesta JSON ilegible.") from None
            except ServicioExternoError:
                LOG.warning("solicitud=%s resultado=contenido_rechazado", solicitud)
                raise
            if intento == MAX_INTENTOS or pausa > 8:
                LOG.warning("solicitud=%s resultado=aplazado espera_s=%g", solicitud, pausa)
                raise ServicioExternoError(mensaje + ". Consulta aplazada.")
            LOG.info("solicitud=%s reintento_en_s=%g", solicitud, pausa)
            self.esperar(pausa)
            ultima_pausa = pausa
