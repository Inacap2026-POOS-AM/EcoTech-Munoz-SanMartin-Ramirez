from contextlib import contextmanager, closing
from pathlib import Path
import os
import sqlite3
from cryptography.fernet import Fernet
from dominio.excepciones import Conflicto, ErrorNegocio

BASE = Path(__file__).resolve().parents[1]


def configurar():
    """Crea la configuración privada una sola vez, sin sobrescribir claves."""
    ruta = BASE / ".env"
    ajuste = "ECOTECH_DB=ecotech.db\nECOTECH_KEY=" + Fernet.generate_key().decode() + "\n"
    with os.fdopen(os.open(ruta, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "w") as f:
        f.write(ajuste)


def entorno():
    ruta = BASE / ".env"
    valores = {}
    if ruta.exists():
        for linea in ruta.read_text().splitlines():
            if linea.strip() and not linea.lstrip().startswith("#"):
                clave, sep, valor = linea.partition("=")
                if not sep:
                    raise ErrorNegocio("Línea sin signo igual en .env.")
                valores[clave.strip()] = valor.strip()
    for clave in ("ECOTECH_DB", "ECOTECH_KEY", "ECOTECH_WEATHER_PROVIDER", "WEATHERAPI_KEY"):
        valor = os.getenv(clave)
        if valor is not None:
            valores[clave] = valor
    return valores


def ajustes():
    valores = entorno()
    if not valores.get("ECOTECH_KEY"):
        raise ErrorNegocio("Falta ECOTECH_KEY. Ejecute: python main.py configurar")
    try:
        llave = Fernet(valores["ECOTECH_KEY"])
    except (ValueError, TypeError):
        raise ErrorNegocio("ECOTECH_KEY no es una clave Fernet válida.") from None
    return BASE / (valores.get("ECOTECH_DB") or "ecotech.db"), llave


def clave_clima():
    valores = entorno()
    proveedor = valores.get("ECOTECH_WEATHER_PROVIDER") or (
        "weatherapi" if valores.get("WEATHERAPI_KEY") else "open-meteo")
    if proveedor == "open-meteo":
        return None
    if proveedor != "weatherapi":
        raise ErrorNegocio("Proveedor de clima inválido: use open-meteo o weatherapi.")
    clave = valores.get("WEATHERAPI_KEY", "").strip()
    if not clave:
        raise ErrorNegocio("Falta WEATHERAPI_KEY para el proveedor weatherapi.")
    return clave


@contextmanager
def conectar(ruta):
    with closing(sqlite3.connect(ruta, timeout=5)) as con:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            with con:
                yield con
        except sqlite3.IntegrityError as error:
            raise Conflicto("Clave repetida, relación inválida o historial protegido.") from error


def iniciar(ruta):
    with conectar(ruta) as con:
        con.executescript((BASE / "db/01_esquema.sql").read_text(encoding="utf-8"))

        columnas = {f[1] for f in con.execute("PRAGMA table_info(usuarios)")}
        if "empleado" not in columnas:
            con.execute("ALTER TABLE usuarios ADD COLUMN empleado TEXT REFERENCES empleado(id)")
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS usuario_empleado ON usuarios(empleado)")
        if "rut" not in {f[1] for f in con.execute("PRAGMA table_info(persona)")}:
            con.execute("ALTER TABLE persona ADD COLUMN rut BLOB")
