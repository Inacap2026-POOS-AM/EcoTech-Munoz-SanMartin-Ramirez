import io
from decimal import Decimal
import json
import sqlite3
import unittest
from urllib.error import HTTPError, URLError
from unittest.mock import Mock
from api_cliente import ClienteAPI, ServicioExternoError
from servicios import ServiciosEcoTech
from dominio.excepciones import ErrorNegocio
from seguridad import Rol, Usuario

CLIMA = {"current":{"time":"2026-11-15T17:00","temperature_2m":19,"relative_humidity_2m":65,"weather_code":2},
         "current_units":{"temperature_2m":"°C","relative_humidity_2m":"%"}}
CAMBIO = {"result":"success","base_code":"USD","time_last_update_unix":1794787351,"rates":{"CLP":950}}


class PruebasAPI(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.addCleanup(self.con.close)
        self.con.executescript("CREATE TABLE proyecto(id); INSERT INTO proyecto VALUES ('p'); CREATE TABLE cache_api(clave PRIMARY KEY,obtenido_en,datos);")
        self.cliente = Mock()
        self.s = ServiciosEcoTech(self.con,Usuario("ana",Rol("consulta")),self.cliente)

    def test_sesion(self):
        with self.assertRaises(ErrorNegocio):
            ServiciosEcoTech(self.con,None)

    def test_clima_repetido_y_corte(self):
        self.cliente.obtener.return_value = CLIMA
        for _ in range(2):
            self.s.clima("p",-36.84,-73.1)
        self.assertEqual(self.con.execute("SELECT count(*) FROM cache_api").fetchone()[0],1)
        self.cliente.obtener.side_effect = ServicioExternoError("Sin red")
        aviso,dato = self.s.clima("p",-36.84,-73.1)
        self.assertIn("antigüedad",aviso)
        self.assertEqual(dato.estado,"Parcialmente nublado")
        with self.assertRaisesRegex(ErrorNegocio,"Sin datos locales"):
            self.s.clima("p",0,0)

    def test_conversion_y_datos_invalidos(self):
        self.cliente.obtener.return_value = CAMBIO
        self.assertEqual(self.s.pago("USD","CLP","2.50")[1].pago_estimado,Decimal("2375"))
        self.cliente.obtener.return_value = {"result":"success"}
        self.assertIn("Respuesta inválida",self.s.pago("USD","CLP","10")[0])
        with self.assertRaises(ErrorNegocio):
            self.s.pago("USD","CLP","NaN")

    def test_http_y_reintentos(self):
        def error(codigo,espera="0"):
            return HTTPError("https://example.org",codigo,"",{"Retry-After":espera},None)
        for codigo in (400,401,403,404):
            abrir = Mock(side_effect=error(codigo))
            with self.assertRaisesRegex(ServicioExternoError,str(codigo)):
                ClienteAPI(abrir,Mock()).obtener("https://example.org/invalido")
            self.assertEqual(abrir.call_count,1)
        esperar = Mock()
        abrir = Mock(side_effect=[error(429,"3"),error(503),io.BytesIO(json.dumps(CAMBIO).encode())])
        self.assertEqual(ClienteAPI(abrir,esperar).obtener("https://example.org"),CAMBIO)
        self.assertEqual([c.args[0] for c in esperar.call_args_list],[3,6])
        abrir = Mock(side_effect=URLError("desconectado"))
        with self.assertRaises(ServicioExternoError):
            ClienteAPI(abrir,Mock()).obtener("https://example.org")
        self.assertEqual(abrir.call_count,3)
        abrir = Mock(side_effect=error(429,"120"))
        with self.assertRaises(ServicioExternoError):
            ClienteAPI(abrir,Mock()).obtener("https://example.org")
        self.assertEqual(abrir.call_count,1)

    def test_proveedor_autenticado_simulado(self):
        self.cliente.obtener.return_value={"current":{"last_updated_epoch":1794700000,"temp_c":12,
                                          "humidity":82,"condition":{"text":"Nublado"}}}
        self.assertEqual(self.s.clima("p",-36.84,-73.1,"valor-de-prueba")[1].humedad_pct,82)
