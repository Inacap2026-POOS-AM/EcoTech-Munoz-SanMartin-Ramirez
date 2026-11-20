from datetime import date
from dominio.excepciones import ErrorNegocio, NoEncontrado


def guardar_proyecto(con, p, editar=False):
    datos = (p.nombre,p.descripcion,p.inicio.isoformat(),p.estado,p.id)
    if editar:
        if not con.execute("UPDATE proyecto SET nombre=?,descripcion=?,inicio=?,estado=? WHERE id=?", datos).rowcount:
            raise NoEncontrado("Proyecto inexistente.")
    else:
        con.execute("INSERT INTO proyecto(nombre,descripcion,inicio,estado,id) VALUES (?,?,?,?,?)", datos)


def asignar(con, a):
    ok = con.execute("""SELECT 1 FROM empleado e,proyecto p WHERE e.id=? AND e.activo=1 AND p.id=?
                     AND p.estado='ACTIVO' AND p.inicio<=? AND e.inicio<=?""",
                     (a.empleado,a.proyecto,a.inicio.isoformat(),a.inicio.isoformat())).fetchone()
    if not ok or a.inicio > date.today():
        raise ErrorNegocio("Revise el proyecto, el contrato y la fecha de asignación.")
    con.execute("INSERT INTO asignacion(empleado,proyecto,rol,inicio) VALUES (?,?,?,?)",
                (a.empleado,a.proyecto,a.rol,a.inicio.isoformat()))


def finalizar(con, empleado, proyecto):
    if not con.execute("UPDATE asignacion SET fin=? WHERE empleado=? AND proyecto=? AND fin IS NULL",
                       (date.today().isoformat(),empleado,proyecto)).rowcount:
        raise NoEncontrado("No hay asignación abierta.")


def registrar(con, r):
    if not con.in_transaction:
        con.execute("BEGIN IMMEDIATE")
    a = con.execute("""SELECT id FROM asignacion WHERE empleado=? AND proyecto=? AND inicio<=?
                    AND (fin IS NULL OR fin>=?) ORDER BY id DESC LIMIT 1""",
                    (r.empleado,r.proyecto,r.fecha.isoformat(),r.fecha.isoformat())).fetchone()
    if not a:
        raise ErrorNegocio("El empleado no estaba asignado al proyecto en esa fecha.")
    total = con.execute("""SELECT coalesce(sum(r.minutos),0) FROM registro r JOIN asignacion a ON a.id=r.asignacion
                       WHERE a.empleado=? AND r.fecha=?""", (r.empleado,r.fecha.isoformat())).fetchone()[0]
    if total + r.minutos > 1440:
        raise ErrorNegocio("El total diario superaría 24 horas.")
    con.execute("INSERT INTO registro(asignacion,fecha,minutos,descripcion) VALUES (?,?,?,?)",
                (a[0],r.fecha.isoformat(),r.minutos,r.descripcion))
