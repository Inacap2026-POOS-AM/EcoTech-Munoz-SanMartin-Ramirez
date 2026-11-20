from dominio.departamento import Departamento
from dominio.excepciones import ErrorNegocio, NoEncontrado


class DepartamentoRepositorio:
    def __init__(self, con):
        self.con = con

    @staticmethod
    def _mapear(fila):
        return Departamento(*fila)

    def _validar_gerente(self, d):
        if d.gerente and not self.con.execute(
            "SELECT 1 FROM empleado WHERE id=? AND departamento=? AND activo=1",
            (d.gerente, d.id)).fetchone():
            raise ErrorNegocio("El gerente debe ser empleado activo de esta unidad.")

    def guardar(self, d):
        self._validar_gerente(d)
        self.con.execute("INSERT INTO departamento VALUES (?,?,?)", (d.id, d.nombre, d.gerente))

    def obtener(self, id):
        fila = self.con.execute("SELECT * FROM departamento WHERE id=?", (id,)).fetchone()
        return self._mapear(fila) if fila else None

    def listar(self, filtro=""):
        filas = self.con.execute("SELECT * FROM departamento WHERE instr(lower(nombre),lower(?))>0 ORDER BY nombre", (filtro,))
        return [self._mapear(f) for f in filas]

    def actualizar(self, d):
        self._validar_gerente(d)
        if not self.con.execute("UPDATE departamento SET nombre=?, gerente=? WHERE id=?",
                                (d.nombre, d.gerente, d.id)).rowcount:
            raise NoEncontrado("Departamento inexistente.")

    def eliminar(self, id):
        if not self.con.execute("DELETE FROM departamento WHERE id=?", (id,)).rowcount:
            raise NoEncontrado("Departamento inexistente.")
