"""Regresiones sobre requisitos de seguridad, conversión y persistencia de E3."""
from contextlib import redirect_stdout
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO, StringIO
import json
import logging
import os
from pathlib import Path
import sqlite3
import ssl
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from api_cliente import ClienteAPI, ServicioExternoError, espera_servidor
from datos_demo import CAMBIO, CLIMA
from deserializador import Deserializador
from dominio.clima import CondicionClimatica
from dominio.cotizacion import CotizacionMonetaria
from dominio.empleado import Empleado
from dominio.excepciones import ErrorNegocio
from dominio.informe import Informe
from dominio.validaciones import validar_rut
from infraestructura import conexion
from infraestructura.log_api import configurar_log
from informes import ExportadorExcel, ExportadorPDF
from repositorio.empleado import EmpleadoRepositorio
from seguridad import Rol, Usuario
from servicios import ServiciosEcoTech
from cryptography.fernet import Fernet


def respuesta(datos):
    return BytesIO(json.dumps(datos).encode())


class TransporteSeguro(unittest.TestCase):
    def test_log_de_cada_intento_backoff_y_timeout_sin_secretos(self):
        abrir = Mock(side_effect=[URLError("no imprimir clave-secreta"),
                                  HTTPError("https://example.org?key=clave-secreta", 503,
                                            "clave-secreta", {}, None), respuesta(CAMBIO)])
        esperar = Mock()
        with self.assertLogs("ecotech.api", level="INFO") as registro:
            dato = ClienteAPI(abrir, esperar).obtener("https://example.org?key=clave-secreta")
        self.assertEqual(dato, CAMBIO)
        self.assertEqual([c.kwargs["timeout"] for c in abrir.call_args_list], [5, 5, 5])
        self.assertEqual([c.args[0] for c in esperar.call_args_list], [1, 2])
        self.assertEqual(sum(" intento=" in x for x in registro.output), 3)
        self.assertNotIn("clave-secreta", "\n".join(registro.output))
        self.assertNotIn("example.org", "\n".join(registro.output))

    def test_retry_after_fecha_http_y_valor_invalido(self):
        ahora = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)
        self.assertEqual(espera_servidor("Fri, 20 Nov 2026 12:00:07 GMT", 1, ahora), 7)
        self.assertEqual(espera_servidor("no-es-fecha", 2, ahora), 2)
        self.assertEqual(espera_servidor("-3", 2, ahora), 2)

    def test_429_largo_bloquea_nuevas_consultas_al_mismo_proveedor(self):
        tiempo = [1000.0]
        abrir = Mock(side_effect=HTTPError("https://example.org", 429, "", {"Retry-After": "120"}, None))
        esperar = Mock()
        cliente = ClienteAPI(abrir, esperar, lambda: tiempo[0])
        with self.assertLogs("ecotech.api", level="INFO"):
            with self.assertRaises(ServicioExternoError):
                cliente.obtener("https://example.org/ruta1")
            with self.assertRaisesRegex(ServicioExternoError, "todavía vigente"):
                cliente.obtener("https://example.org/ruta2")
        self.assertEqual(abrir.call_count, 1)
        esperar.assert_not_called()
        tiempo[0] = 1120
        abrir.side_effect = None
        abrir.return_value = respuesta(CAMBIO)
        self.assertEqual(cliente.obtener("https://example.org/ruta2"), CAMBIO)
        self.assertEqual(abrir.call_count, 2)

    def test_tls_invalido_no_se_reintenta_ni_expone_detalle(self):
        abrir = Mock(side_effect=URLError(ssl.SSLCertVerificationError("clave-secreta")))
        with self.assertLogs("ecotech.api", level="INFO") as log:
            with self.assertRaisesRegex(ServicioExternoError, "TLS"):
                ClienteAPI(abrir, Mock()).obtener("https://example.org")
        self.assertEqual(abrir.call_count, 1)
        self.assertNotIn("clave-secreta", "\n".join(log.output))

    def test_entrada_no_https_y_redireccion_no_se_aceptan(self):
        abrir = Mock()
        for url in ("http://example.org", "https:///sin-host", "https://u:p@example.org"):
            with self.subTest(url=url), self.assertRaises(ServicioExternoError):
                ClienteAPI(abrir).obtener(url)
        abrir.assert_not_called()
        abrir.side_effect = HTTPError("https://example.org", 302, "", {}, None)
        with self.assertLogs("ecotech.api", level="INFO"):
            with self.assertRaisesRegex(ServicioExternoError, "302"):
                ClienteAPI(abrir).obtener("https://example.org")
        self.assertEqual(abrir.call_count, 1)

    def test_respuesta_malformada_sobredimensionada_o_no_objeto(self):
        for contenido in (b'{', b'[]', b'x' * 131073):
            abrir = Mock(return_value=BytesIO(contenido))
            with self.subTest(tamano=len(contenido)):
                with self.assertLogs("ecotech.api", level="INFO"):
                    with self.assertRaises(ServicioExternoError):
                        ClienteAPI(abrir).obtener("https://example.org")
                self.assertEqual(abrir.call_count, 1)


class DatosYPersistencia(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.addCleanup(self.con.close)
        self.con.executescript("CREATE TABLE proyecto(id); INSERT INTO proyecto VALUES ('p'); "
                               "CREATE TABLE cache_api(clave PRIMARY KEY, obtenido_en, datos);")
        self.cliente = Mock()
        self.s = ServiciosEcoTech(self.con, Usuario("lectora", Rol("consulta")), self.cliente)

    def test_deserializador_entrega_objetos_tipados_y_validados(self):
        clima = Deserializador.clima(CLIMA)
        cambio = Deserializador.cambio(CAMBIO, "USD", "CLP")
        self.assertIsInstance(clima, CondicionClimatica)
        self.assertIsInstance(clima.fecha_fuente, datetime)
        self.assertIsInstance(clima.temperatura_C, float)
        self.assertIsInstance(cambio, CotizacionMonetaria)
        self.assertIsInstance(cambio.tasa, Decimal)
        self.assertIsNotNone(clima.fecha_fuente.utcoffset())
        self.assertEqual(cambio.tasa, Decimal("950"))

    def test_datos_invalidos_no_se_persisten(self):
        for invalido in (None, True, float("nan"), 120):
            datos = json.loads(json.dumps(CLIMA))
            datos["current"]["relative_humidity_2m"] = invalido
            self.cliente.obtener.return_value = datos
            with self.subTest(valor=invalido), self.assertLogs("ecotech.servicios"):
                with self.assertRaises(ErrorNegocio):
                    self.s.clima("p", -36.84, -73.1)
            self.assertEqual(self.con.execute("SELECT count(*) FROM cache_api").fetchone()[0], 0)

    def test_respaldo_reconstruye_el_tipo_y_muestra_antiguedad(self):
        self.cliente.obtener.return_value = CLIMA
        original = self.s.clima("p", -36.84, -73.1)[1]
        hace = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        self.con.execute("UPDATE cache_api SET obtenido_en=?", (hace,))
        self.cliente.obtener.side_effect = ServicioExternoError("Sin red")
        with self.assertLogs("ecotech.servicios", level="INFO"):
            aviso, respaldo = self.s.clima("p", -36.84, -73.1)
        self.assertEqual(original, respaldo)
        self.assertIsInstance(respaldo, CondicionClimatica)
        self.assertIn("antigüedad 120 min", aviso)
        self.assertIn("obtenido_en", aviso)

    def test_cache_corrupta_no_se_usa_a_ciegas(self):
        self.cliente.obtener.return_value = CLIMA
        self.s.clima("p", -36.84, -73.1)
        self.con.execute("UPDATE cache_api SET datos=?", ('{"estado":"incompleto"}',))
        self.cliente.obtener.side_effect = ServicioExternoError("Sin red")
        with self.assertLogs("ecotech.servicios"):
            with self.assertRaisesRegex(ErrorNegocio, "Datos locales inválidos"):
                self.s.clima("p", -36.84, -73.1)

    def test_coordenadas_y_moneda_invalidas_no_llaman_al_proveedor(self):
        for lat, lon in ((True, 0), (91, 0), (0, float("nan")), (0, 181)):
            with self.assertRaises(ValueError):
                self.s.clima("p", lat, lon)
        with self.assertRaises(ErrorNegocio):
            self.s.pago("USD'; DELETE", "CLP", "10")
        self.cliente.obtener.assert_not_called()


class ConfiguracionYPersonas(unittest.TestCase):
    def test_secretos_faltantes_y_prioridad_de_os_getenv(self):
        with TemporaryDirectory() as tmp, patch.object(conexion, "BASE", Path(tmp)), patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ErrorNegocio, "Falta ECOTECH_KEY"):
                conexion.ajustes()
            conexion.configurar()
            archivo = Path(tmp) / ".env"
            anterior = archivo.read_bytes()
            with self.assertRaises(FileExistsError):
                conexion.configurar()
            self.assertEqual(archivo.read_bytes(), anterior)
            if os.name == "posix":
                self.assertEqual(archivo.stat().st_mode & 0o777, 0o600)
            with patch.dict(os.environ, {"ECOTECH_DB": "otra.db"}):
                self.assertEqual(conexion.ajustes()[0], Path(tmp) / "otra.db")
            with patch.dict(os.environ, {"ECOTECH_WEATHER_PROVIDER": "weatherapi"}):
                with self.assertRaisesRegex(ErrorNegocio, "Falta WEATHERAPI_KEY"):
                    conexion.clave_clima()

    def test_argon2_con_sal_distinta_y_sin_clave_en_la_base(self):
        from seguridad import crear_usuario, autenticar
        import secrets
        with sqlite3.connect(":memory:") as con:
            con.row_factory = sqlite3.Row
            con.execute("CREATE TABLE usuarios(nombre,hash,rol,empleado)")
            clave = secrets.token_urlsafe()
            crear_usuario(con, "ana", clave, "consulta")
            crear_usuario(con, "bea", clave, "consulta")
            hashes = [f[0] for f in con.execute("SELECT hash FROM usuarios")]
            self.assertNotEqual(hashes[0], hashes[1])
            self.assertTrue(all(h.startswith("$argon2id$") and clave not in h for h in hashes))
            self.assertEqual(autenticar(con, "ana", clave).nombre, "ana")

    def test_validacion_de_rut_correo_y_tipos(self):
        self.assertEqual(validar_rut("12.345.678-5"), "12345678-5")
        for rut in ("12345678-0", "12345678", "0-0", True, "' OR '1'='1"):
            with self.subTest(rut=rut), self.assertRaises(ErrorNegocio):
                validar_rut(rut)
        for correo in (None, "sin-arroba", "x@x"):
            with self.assertRaises(ErrorNegocio):
                Empleado("e", "Ana", correo, "Dirección", "1234567", date.today(), 100)

    def test_rut_se_valida_se_cifra_y_se_recupera_tras_migracion(self):
        with TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "test.db"
            conexion.iniciar(ruta)
            conexion.iniciar(ruta)
            with conexion.conectar(ruta) as con:
                columnas = [f[1] for f in con.execute("PRAGMA table_info(persona)")]
                self.assertEqual(columnas.count("rut"), 1)
                repo = EmpleadoRepositorio(con, Fernet(Fernet.generate_key()))
                e = Empleado("e", "Ana", "ana@example.org", "Dirección", "1234567", date.today(), 100,
                             rut="12.345.678-5")
                repo.guardar(e)
                raw = con.execute("SELECT rut FROM persona").fetchone()[0]
                self.assertIsInstance(raw, bytes)
                self.assertNotIn(b"12345678", raw)
                self.assertEqual(repo.obtener("e").rut, "12345678-5")
                repo.actualizar(replace(e, rut=None))
                self.assertIsNone(repo.obtener("e").rut)

    def test_log_local_privado_y_configurado(self):
        logger = logging.getLogger("ecotech")
        anteriores, nivel, propaga = logger.handlers[:], logger.level, logger.propagate
        with TemporaryDirectory() as tmp:
            try:
                destino = configurar_log(Path(tmp) / "api.log")
                logging.getLogger("ecotech.api").info("intento=1/3 timeout=5s")
                self.assertIn("intento=1/3", destino.read_text())
                if os.name == "posix":
                    self.assertEqual(destino.stat().st_mode & 0o777, 0o600)
            finally:
                for h in logger.handlers:
                    h.close()
                logger.handlers = anteriores
                logger.setLevel(nivel)
                logger.propagate = propaga

    def test_exportaciones_reales_y_texto_excel_no_formula(self):
        from openpyxl import load_workbook
        from pypdf import PdfReader
        with TemporaryDirectory() as tmp:
            informe = Informe("prueba", ("Nombre", "Minutos"), [("=1+1", 90)])
            excel = ExportadorExcel().exportar(informe, Path(tmp))
            pdf = ExportadorPDF().exportar(informe, Path(tmp))
            libro = load_workbook(excel)
            self.assertEqual(libro.active["A2"].value, "=1+1")
            self.assertEqual(libro.active["A2"].data_type, "s")
            libro.close()
            self.assertIn("90", PdfReader(pdf).pages[0].extract_text())
