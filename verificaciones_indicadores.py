from contextlib import closing, redirect_stdout
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from io import StringIO
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch, call
import requests

from api_cliente import ErrorAPI, consultar_dolar
from deserializador_dolar import DeserializadorDolar
from dominio.excepciones import AutorizacionError, ConexionBaseDatosError
from dominio.indicador_dolar import IndicadorDolar
from menu_indicadores import consultar_indicadores_menu
from repositorio.indicador_repo import IndicadorLocalRepositorio
from servicios import GestionEcoTech, Sesion


class IndicadoresTest(TestCase):
    def datos(self):
        return {"codigo": "dolar", "unidad_medida": "Pesos", "serie": [
            {"fecha": "2026-11-17T03:00:00.000Z", "valor": Decimal("900")},
            {"fecha": "2026-11-18T03:00:00.000Z", "valor": Decimal("950.50")},
        ]}

    def test_conversion_y_validaciones(self):
        indicador = IndicadorDolar(Decimal("900"), date(2026, 11, 18))
        self.assertEqual(indicador.convertir_a_usd("900000"), Decimal("1000.00"))
        self.assertEqual(indicador.convertir_a_usd("1"), Decimal("0.00"))
        for valor in ("0", "-1", "NaN", "Infinity", "texto", "1.001", True, "10000000000"):
            with self.assertRaises(ValueError):
                indicador.convertir_a_usd(valor)
        for valor in (Decimal("0"), Decimal("NaN"), Decimal("Infinity"), Decimal("-1")):
            with self.assertRaises(ValueError):
                IndicadorDolar(valor, date.today())

    def test_deserializador_selecciona_fecha_mas_reciente(self):
        indicador = DeserializadorDolar().deserializar(self.datos())
        self.assertEqual(indicador.get_valor(), Decimal("950.50"))
        self.assertEqual(indicador.get_fecha(), date(2026, 11, 18))
        for datos in (None, {}, {**self.datos(), "codigo": "euro"}, {**self.datos(), "unidad_medida": "Dolares"}, {**self.datos(), "serie": []}, {**self.datos(), "serie": [{"fecha": "invalida", "valor": 900}]}, {**self.datos(), "serie": [{"fecha": "2026-11-18T00:00", "valor": True}]}):
            with self.assertRaises(ValueError):
                DeserializadorDolar().deserializar(datos)

    def test_sqlite_idempotente_y_persistente(self):
        with TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "indicadores.sqlite3"
            repo = IndicadorLocalRepositorio(ruta)
            self.assertIsNone(repo.obtener_ultimo())
            indicador = IndicadorDolar(Decimal("900.12"), date(2026, 11, 18))
            ahora = datetime.now(timezone.utc)
            repo.guardar(indicador, ahora)
            repo.guardar(indicador, ahora)
            repo.guardar(IndicadorDolar(Decimal("1"), indicador.get_fecha()), ahora - timedelta(days=1))
            with closing(sqlite3.connect(ruta)) as conexion:
                self.assertEqual(conexion.execute("SELECT COUNT(*) FROM indicador_dolar").fetchone()[0], 1)
            recuperado, obtenido = IndicadorLocalRepositorio(ruta).obtener_ultimo()
            self.assertEqual(recuperado.get_valor(), Decimal("900.12"))
            self.assertEqual(obtenido, ahora)

    def test_api_decimal_reintentos_y_errores(self):
        def respuesta(codigo):
            r = requests.Response()
            r.status_code = codigo
            r._content = b'{"valor":950.51}'
            r._content_consumed = True
            r.headers["Retry-After"] = "4"
            return r
        with patch("api_cliente.requests.get", side_effect=[respuesta(429), respuesta(200)]) as get, patch("api_cliente.time.sleep") as dormir:
            self.assertEqual(consultar_dolar()["valor"], Decimal("950.51"))
            dormir.assert_called_once_with(4)
            self.assertEqual(get.call_args.kwargs["timeout"], (3, 10))
        with patch("api_cliente.requests.get", return_value=respuesta(404)) as get, patch("api_cliente.time.sleep") as dormir:
            with self.assertRaises(ErrorAPI):
                consultar_dolar()
            self.assertEqual(get.call_count, 1)
            dormir.assert_not_called()
        with patch("api_cliente.requests.get", side_effect=requests.exceptions.Timeout()) as get, patch("api_cliente.time.sleep") as dormir:
            with self.assertRaises(ErrorAPI):
                consultar_dolar()
            self.assertEqual(get.call_count, 3)
            self.assertEqual(dormir.call_args_list, [call(1), call(2)])

    def test_menu_exige_login(self):
        gestion = GestionEcoTech(Sesion(1, 2))
        with patch("servicios.consultar_dolar") as api, patch("menu_indicadores.IndicadorLocalRepositorio") as local:
            with self.assertRaises(AutorizacionError):
                consultar_indicadores_menu(gestion)
            api.assert_not_called()
            local.assert_not_called()

    def test_menu_con_api_y_fallo_supabase_conserva_respaldo(self):
        with TemporaryDirectory() as carpeta:
            repo = IndicadorLocalRepositorio(Path(carpeta) / "respaldo.sqlite3")
            gestion = GestionEcoTech(Sesion(1, 2))
            salida = StringIO()
            with patch.object(gestion, "exigir_sesion"), patch.object(gestion, "consultar_dolar", return_value=self.datos()), patch("menu_indicadores.IndicadorLocalRepositorio", return_value=repo), patch("menu_indicadores.obtener_conexion", side_effect=ConexionBaseDatosError("Sin conexión")), patch("builtins.input", side_effect=["invalido", "950500"]), redirect_stdout(salida):
                consultar_indicadores_menu(gestion)
            self.assertIn("1000.00 USD", salida.getvalue())
            self.assertIn("No se confirmó", salida.getvalue())
            self.assertEqual(repo.obtener_ultimo()[0].get_valor(), Decimal("950.50"))

    def test_menu_plan_b_y_sin_datos(self):
        with TemporaryDirectory() as carpeta:
            repo = IndicadorLocalRepositorio(Path(carpeta) / "respaldo.sqlite3")
            gestion = GestionEcoTech(Sesion(1, 2))
            for con_datos in (False, True):
                if con_datos:
                    repo.guardar(IndicadorDolar(Decimal("900"), date(2026, 11, 18)), datetime.now(timezone.utc) - timedelta(minutes=20))
                salida = StringIO()
                with patch.object(gestion, "exigir_sesion"), patch.object(gestion, "consultar_dolar", side_effect=ErrorAPI("Sin red")), patch("menu_indicadores.IndicadorLocalRepositorio", return_value=repo), patch("menu_indicadores.obtener_conexion") as remoto, patch("builtins.input", return_value="900000"), redirect_stdout(salida):
                    consultar_indicadores_menu(gestion)
                remoto.assert_not_called()
                if con_datos:
                    self.assertIn("PLAN B", salida.getvalue())
                    self.assertIn("1000.00 USD", salida.getvalue())
                else:
                    self.assertIn("No hay un indicador local", salida.getvalue())
