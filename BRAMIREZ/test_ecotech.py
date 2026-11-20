import sqlite3
import unittest
from importlib.util import find_spec
from contextlib import redirect_stdout
from io import StringIO
from datetime import date
from demo import ejecutar
from dominio.registro import RegistroTiempo
from dominio.excepciones import ErrorNegocio
from seguridad import crear_usuario, autenticar


class PruebasEcoTech(unittest.TestCase):
    def test_crud_mapeo_bajas_rollback(self):
        with redirect_stdout(StringIO()) as evidencia:
            ejecutar(exportar=False)
        self.assertIn("Personas huérfanas tras el fallo: 0", evidencia.getvalue())

    @unittest.skipUnless(find_spec("reportlab") and find_spec("openpyxl"),
                         "Instale requirements.txt para verificar PDF y Excel.")
    def test_exportaciones(self):
        with redirect_stdout(StringIO()) as evidencia:
            ejecutar()
        self.assertIn("Exportación polimórfica: horas.pdf, horas.xlsx", evidencia.getvalue())

    def test_invariantes_tiempo(self):
        for minutos in (0,-1,1441,True,1.5):
            with self.assertRaises(ErrorNegocio):
                RegistroTiempo("e","p",date.today(),minutos,"Medición")

    def test_rechazo_de_claves_vacias(self):
        con = sqlite3.connect(":memory:")
        self.addCleanup(con.close)
        con.execute("CREATE TABLE usuarios (nombre,hash,rol,empleado)")
        for clave in (None, "", " " * 12, "x" * 129):
            with self.assertRaises(ErrorNegocio):
                crear_usuario(con, "lectora", clave, "consulta")
        self.assertEqual(con.execute("SELECT count(*) FROM usuarios").fetchone()[0], 0)

    def test_clave_y_permisos(self):
        con = sqlite3.connect(":memory:")
        self.addCleanup(con.close)
        con.row_factory = sqlite3.Row
        con.execute("CREATE TABLE usuarios (nombre,hash,rol,empleado)")
        import secrets
        clave = secrets.token_urlsafe()
        crear_usuario(con,"lectora",clave,"consulta")
        self.assertTrue(con.execute("SELECT hash FROM usuarios").fetchone()[0].startswith("$argon2id$"))
        lector = autenticar(con,"lectora",clave)
        lector.exigir("consultar_servicios")
        with self.assertRaises(ErrorNegocio):
            lector.exigir("administrar")
        with self.assertRaises(ErrorNegocio):
            autenticar(con,"lectora","incorrecta")

    def test_cuenta_empleado_y_registro_propio(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from cryptography.fernet import Fernet
        from dominio.empleado import Empleado
        from dominio.proyecto import Proyecto
        from dominio.asignacion import AsignacionProyecto
        from infraestructura.conexion import iniciar, conectar
        from repositorio.empleado import EmpleadoRepositorio
        from repositorio.operaciones import guardar_proyecto, asignar
        from seguridad import revisar_sesion
        from main import registrar_propio
        import secrets

        with TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "personal.db"
            iniciar(ruta)
            llave = Fernet(Fernet.generate_key())
            hoy = date.today()
            with conectar(ruta) as con:
                repo = EmpleadoRepositorio(con, llave)
                repo.guardar(Empleado("e", "Ana", "ana@example.org", "Uno 12", "1234567", hoy, 1000))
                guardar_proyecto(con, Proyecto("p", "Solar", "Estudio", hoy))
                asignar(con, AsignacionProyecto("e", "p", "Analista", hoy))
                clave = secrets.token_urlsafe()
                crear_usuario(con, "ana", clave, "consulta", "e")
                usuario = autenticar(con, "ana", clave)
                with patch("builtins.input", side_effect=["p", hoy.isoformat(), "45", "Medición"]):
                    with redirect_stdout(StringIO()):
                        registrar_propio(con, usuario)
                self.assertEqual(con.execute("SELECT minutos FROM registro").fetchone()[0], 45)
                repo.eliminar("e")
                with self.assertRaises(ErrorNegocio):
                    revisar_sesion(con, usuario)
