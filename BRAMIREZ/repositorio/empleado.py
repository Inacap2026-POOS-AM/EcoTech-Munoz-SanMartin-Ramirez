from datetime import date
from dominio.empleado import Empleado
from dominio.excepciones import NoEncontrado

class EmpleadoRepositorio:
    def __init__(self, con, cifrado):
        self.con = con
        self.cifrado = cifrado

    def _cifrar(self, valor):
        return self.cifrado.encrypt(str(valor).encode())

    def _leer(self, valor):
        return self.cifrado.decrypt(valor).decode()

    def _mapear(self, f):
        return Empleado(f["id"], f["nombre"], f["correo"], self._leer(f["direccion"]),
                        self._leer(f["telefono"]), date.fromisoformat(f["inicio"]),
                        int(self._leer(f["sueldo"])), f["departamento"],
                        rut=self._leer(f["rut"]) if f["rut"] is not None else None)

    def guardar(self, e):
        self.con.execute("INSERT INTO persona(id,nombre,correo,direccion,telefono,rut) VALUES (?,?,?,?,?,?)",
                         (e.id, e.nombre, e.correo, self._cifrar(e.direccion), self._cifrar(e.telefono),
                          self._cifrar(e.rut) if e.rut is not None else None))
        self.con.execute("INSERT INTO empleado(id,inicio,sueldo,departamento) VALUES (?,?,?,?)",
                         (e.id, e.inicio.isoformat(), self._cifrar(e.sueldo), e.departamento))

    def obtener(self, id):
        fila = self.con.execute("""SELECT p.id,p.nombre,p.correo,p.direccion,p.telefono,p.rut,e.inicio,e.sueldo,e.departamento
               FROM persona p JOIN empleado e ON p.id=e.id WHERE e.activo=1 AND e.id=?""", (id,)).fetchone()
        return self._mapear(fila) if fila else None

    def listar(self, filtro=""):
        filas = self.con.execute("""SELECT p.id,p.nombre,p.correo,p.direccion,p.telefono,p.rut,e.inicio,e.sueldo,e.departamento
               FROM persona p JOIN empleado e ON p.id=e.id WHERE e.activo=1
               AND instr(lower(p.nombre),lower(?))>0 ORDER BY p.nombre""", (filtro,))
        return [self._mapear(f) for f in filas]

    def actualizar(self, e):
        if not self.con.execute("UPDATE empleado SET inicio=?,sueldo=?,departamento=? WHERE id=? AND activo=1",
                                (e.inicio.isoformat(), self._cifrar(e.sueldo), e.departamento, e.id)).rowcount:
            raise NoEncontrado("Empleado inexistente.")
        self.con.execute("UPDATE persona SET nombre=?,correo=?,direccion=?,telefono=?,rut=? WHERE id=?",
                         (e.nombre,e.correo,self._cifrar(e.direccion),self._cifrar(e.telefono),
                          self._cifrar(e.rut) if e.rut is not None else None,e.id))
        self.con.execute("UPDATE departamento SET gerente=NULL WHERE gerente=? AND id IS NOT ?", (e.id,e.departamento))

    def eliminar(self, id):
        if not self.con.execute("UPDATE empleado SET activo=0 WHERE id=? AND activo=1", (id,)).rowcount:
            raise NoEncontrado("Empleado inexistente.")
        self.con.execute("UPDATE departamento SET gerente=NULL WHERE gerente=?", (id,))
        self.con.execute("UPDATE asignacion SET fin=? WHERE empleado=? AND fin IS NULL", (date.today().isoformat(),id))
