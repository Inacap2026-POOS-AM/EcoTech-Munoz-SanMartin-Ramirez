from dominio.rol import Rol
from dominio.usuario import Usuario
import os
import re
from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from dominio.excepciones import ErrorNegocio


def crear_usuario(con, nombre, clave, rol, empleado=None):
    if (not isinstance(nombre, str) or not isinstance(clave, str)
            or not re.fullmatch(r"[a-zA-Z0-9_.-]{3,40}", nombre)
            or not 12 <= len(clave) <= 128 or not clave.strip()):
        raise ErrorNegocio("Use un usuario de 3 a 40 caracteres y una clave de 12 a 128.")
    if empleado and not con.execute(
        "SELECT 1 FROM empleado WHERE id=? AND activo=1", (empleado,)
    ).fetchone():
        raise ErrorNegocio("Empleado inexistente o retirado.")
    kdf = Argon2id(salt=os.urandom(16), length=32, iterations=3, lanes=1, memory_cost=65536)
    con.execute(
        "INSERT INTO usuarios(nombre,hash,rol,empleado) VALUES (?,?,?,?)",
        (nombre, kdf.derive_phc_encoded(clave.encode()), rol, empleado),
    )


def autenticar(con, nombre, clave):
    fila = con.execute("SELECT nombre,hash,rol,empleado FROM usuarios WHERE nombre=?", (nombre,)).fetchone()
    if fila and len(clave) <= 128:
        try:
            Argon2id.verify_phc_encoded(clave.encode(),fila["hash"])
            return Usuario(fila["nombre"], Rol(fila["rol"]), fila["empleado"])
        except (InvalidKey, ValueError):
            raise ErrorNegocio("Credenciales incorrectas.") from None
    raise ErrorNegocio("Credenciales incorrectas.")


def revisar_sesion(con, usuario):
    fila = con.execute(
        "SELECT nombre,rol,empleado FROM usuarios WHERE nombre=?", (usuario.nombre,)
    ).fetchone()
    if not fila:
        raise ErrorNegocio("La cuenta ya no está disponible.")
    if fila["empleado"] and not con.execute(
        "SELECT 1 FROM empleado WHERE id=? AND activo=1", (fila["empleado"],)
    ).fetchone():
        raise ErrorNegocio("La cuenta está vinculada a un empleado retirado.")
    return Usuario(fila["nombre"], Rol(fila["rol"]), fila["empleado"])
