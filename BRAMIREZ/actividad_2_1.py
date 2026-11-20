"""C05. Un objeto por clase concreta y sus relaciones de EcoTech."""
from datetime import date

from dominio.asignacion import AsignacionProyecto
from dominio.departamento import Departamento
from dominio.empleado import Empleado
from dominio.proyecto import Proyecto
from dominio.registro import RegistroTiempo


def main():
    inicio = date(2026, 9, 1)
    departamento = Departamento("D01", "Operaciones")
    empleada = Empleado(
        "E01", "Ana Soto", "ana@example.org", "Calle Uno 12",
        "+56912345678", inicio, 850000, departamento.id
    )
    proyecto = Proyecto("P01", "Sensores del Biobío", "Calidad del aire", inicio)
    asignacion = AsignacionProyecto(empleada.id, proyecto.id, "Analista", inicio)
    registro = RegistroTiempo(empleada.id, proyecto.id, inicio, 90, "Inspección de estación")
    for objeto in (departamento, empleada, proyecto, asignacion, registro):
        print(f"{type(objeto).__name__}: {objeto}")
    print(f"Departamento de {empleada.nombre}: {empleada.departamento}")


if __name__ == "__main__":
    main()
