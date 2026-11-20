"""EcoTech. Ejecute python main.py --help."""
import argparse
from datetime import date
from getpass import getpass
import sqlite3
from uuid import uuid4
from cryptography.fernet import InvalidToken
from infraestructura.conexion import ajustes, configurar, conectar, iniciar, clave_clima
from infraestructura.log_api import configurar_log
from api_cliente import ClienteAPI
from dominio.empleado import Empleado
from dominio.departamento import Departamento
from dominio.proyecto import Proyecto
from dominio.asignacion import AsignacionProyecto
from dominio.registro import RegistroTiempo
from dominio.excepciones import ErrorNegocio
from repositorio.empleado import EmpleadoRepositorio
from repositorio.departamento import DepartamentoRepositorio
from repositorio.operaciones import asignar, finalizar, registrar, guardar_proyecto
from seguridad import autenticar, crear_usuario, revisar_sesion
from informes import ServicioInformes, ExportadorPDF, ExportadorExcel, CONSULTAS


def capturar_empleado(id):
    return Empleado(id, input("Nombre: "),input("Correo: "),input("Dirección: "),input("Teléfono: "),
                    date.fromisoformat(input("Inicio AAAA-MM-DD: ")),int(input("Sueldo CLP: ")),
                    input("ID departamento (Enter si vacante): ").strip() or None,
                    rut=input("RUT opcional (Enter para omitir): ").strip() or None)


def operar(op, con, llave):
    emp, dept = EmpleadoRepositorio(con,llave), DepartamentoRepositorio(con)
    if op in ("e+","e~"):
        id = str(uuid4()) if op=="e+" else input("ID del empleado: ")
        obj = capturar_empleado(id)
        (emp.guardar if op=="e+" else emp.actualizar)(obj)
        print(obj)
    elif op in ("d+","d~"):
        id = str(uuid4()) if op=="d+" else input("ID del departamento: ")
        obj = Departamento(id,input("Nombre: "),input("ID gerente (opcional): ").strip() or None)
        (dept.guardar if op=="d+" else dept.actualizar)(obj)
        print(obj)
    elif op in ("e?","d?"):
        repo = emp if op=="e?" else dept
        for item in repo.listar(input("Buscar nombre (Enter para todos): ")):
            print(item)
    elif op in ("e-","d-"):
        (emp if op=="e-" else dept).eliminar(input("ID para retirar: "))
    elif op in ("p+","p~"):
        id = str(uuid4()) if op=="p+" else input("ID del proyecto: ")
        p = Proyecto(id,input("Nombre: "),input("Descripción: "),date.fromisoformat(input("Inicio AAAA-MM-DD: ")),
                     input("Estado PLANIFICADO/ACTIVO/PAUSADO/FINALIZADO: ").upper())
        guardar_proyecto(con,p,editar=op=="p~")
        print("ID:",p.id)
    elif op=="p?":
        for f in con.execute("SELECT id,nombre,estado FROM proyecto ORDER BY nombre"):
            print(*f,sep=" · ")
    elif op=="p-":
        if not con.execute("DELETE FROM proyecto WHERE id=?", (input("ID proyecto: "),)).rowcount:
            raise ErrorNegocio("Proyecto inexistente.")
    elif op=="asignar":
        asignar(con,AsignacionProyecto(input("ID empleado: "),input("ID proyecto: "),input("Función: "),date.today()))
    elif op=="finalizar":
        finalizar(con,input("ID empleado: "),input("ID proyecto: "))
    elif op=="tiempo":
        registrar(con,RegistroTiempo(input("ID empleado: "),input("ID proyecto: "),date.fromisoformat(input("Fecha: ")),
                                      int(input("Minutos: ")),input("Descripción: ")))
    elif op=="informe":
        tipo = input("empleados / departamentos / proyectos / horas: ")
        if tipo not in CONSULTAS:
            raise ErrorNegocio("Tipo de informe inválido.")
        for f in ServicioInformes().generar(con,tipo,[ExportadorPDF(),ExportadorExcel()],"exportaciones"):
            print(f)
    elif op=="usuario":
        crear_usuario(
            con, input("Nuevo usuario de consulta: "), getpass("Nueva contraseña: "),
            "consulta", input("ID empleado (opcional): ").strip() or None,
        )
    else:
        raise ErrorNegocio("Opción desconocida.")


def registrar_propio(con, usuario):
    usuario.exigir("registrar_tiempo")
    if not usuario.empleado:
        raise ErrorNegocio("Su cuenta requiere un empleado asociado.")
    for fila in con.execute(
        "SELECT p.id,p.nombre FROM proyecto p JOIN asignacion a ON a.proyecto=p.id "
        "WHERE a.empleado=? AND a.fin IS NULL", (usuario.empleado,)
    ):
        print(*fila, sep=" · ")
    registro = RegistroTiempo(
        usuario.empleado, input("ID proyecto: "),
        date.fromisoformat(input("Fecha AAAA-MM-DD: ")),
        int(input("Minutos: ")), input("Descripción: "),
    )
    registrar(con, registro)


def menu(ruta, llave):
    with conectar(ruta) as con:
        usuario = autenticar(con,input("Usuario: "),getpass("Contraseña: "))
    cliente_api = ClienteAPI()
    while True:
        print("\ne empleado | d departamento | p proyecto  (+ crear, ? listar, ~ editar, - retirar)")
        print("clima · pago · asignar · finalizar · tiempo · informe · usuario · salir")
        op = input("> ").strip()
        if op=="salir":
            return
        try:
            with conectar(ruta) as con:
                usuario = revisar_sesion(con, usuario)
                if op == "tiempo" and usuario.rol.nombre == "consulta":
                    registrar_propio(con, usuario)
                elif op in ("clima","pago"):
                    from servicios import ServiciosEcoTech
                    api = ServiciosEcoTech(con,usuario,cliente_api)
                    if op=="clima":
                        proyecto = input("ID del proyecto: ")
                        aviso,dato = api.clima(proyecto,float(input("Latitud: ")),float(input("Longitud: ")),clave_clima())
                    else:
                        aviso,dato = api.pago(input("Moneda origen: ").upper(),input("Moneda destino: ").upper(),input("Importe: "))
                    print(aviso)
                    for campo,valor in dato.a_dict().items():
                        print(f"  {campo}: {valor}")
                else:
                    usuario.exigir("administrar")
                    operar(op,con,llave)
            print("Operación completada.")
        except ImportError:
            print("Para exportar PDF o Excel, instale las dependencias de requirements.txt.")
        except (ValueError,sqlite3.Error,InvalidToken,OSError) as exc:
            print("No se pudo completar:", str(exc) if isinstance(exc,ErrorNegocio) else "revise datos, permisos y configuración.")


def main():
    parser = argparse.ArgumentParser(description="Gestión EcoTech")
    parser.add_argument("accion",nargs="?",default="menu",choices=["menu","configurar","alta-admin","demo"])
    accion = parser.parse_args().accion
    if accion=="demo":
        from demo import ejecutar
        from importlib.util import find_spec
        exportar = bool(find_spec("reportlab") and find_spec("openpyxl"))
        if not exportar:
            print("Demo sin exportación: instale requirements.txt para PDF y Excel.")
        return ejecutar(exportar=exportar)
    if accion=="configurar":
        configurar()
        print("Configuración privada creada.")
        return
    ruta,llave = ajustes()
    iniciar(ruta)
    if accion=="alta-admin":
        with conectar(ruta) as con:
            con.execute("BEGIN IMMEDIATE")
            if con.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone():
                raise ErrorNegocio("La instalación ya tiene una cuenta.")
            crear_usuario(con,input("Administrador: "),getpass("Contraseña nueva: "),"admin")
        print("Administrador registrado.")
    else:
        menu(ruta,llave)


if __name__=="__main__":
    try:
        configurar_log()
        main()
    except (ValueError,OSError,sqlite3.Error,EOFError,KeyboardInterrupt) as exc:
        print("Operación detenida:", str(exc) if isinstance(exc,ErrorNegocio) else "revise la configuración o entrada.")
        raise SystemExit(1)
