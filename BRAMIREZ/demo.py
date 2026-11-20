from dataclasses import replace
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from cryptography.fernet import Fernet
from dominio.empleado import Empleado
from dominio.departamento import Departamento
from dominio.proyecto import Proyecto
from dominio.asignacion import AsignacionProyecto
from dominio.registro import RegistroTiempo
from dominio.excepciones import Conflicto
from infraestructura.conexion import conectar, iniciar
from repositorio.departamento import DepartamentoRepositorio
from repositorio.empleado import EmpleadoRepositorio
from repositorio.operaciones import guardar_proyecto, asignar, registrar
from informes import ServicioInformes, ExportadorPDF, ExportadorExcel


def ejecutar(*, exportar=True):
    with TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "prueba.db"
        llave = Fernet(Fernet.generate_key())
        iniciar(ruta)
        iniciar(ruta)
        hoy = date.today()
        d = Departamento("D01","Terreno")
        e = Empleado("E01","Ana Soto","ana@example.org","Calle Uno 12","+56912345678",hoy,850000,d.id)
        p = Proyecto("P01","Sensores del Biobío","Medición de calidad del aire",hoy)
        a = AsignacionProyecto(e.id,p.id,"Analista",hoy)
        r = RegistroTiempo(e.id,p.id,hoy,90,"Inspección de estación")
        with conectar(ruta) as con:
            deps, emp = DepartamentoRepositorio(con), EmpleadoRepositorio(con,llave)
            deps.guardar(d)
            emp.guardar(e)
            guardar_proyecto(con,p)
            asignar(con,a)
            registrar(con,r)
            for objeto in [d,e,p,a,r]:
                print(objeto)
            deps.actualizar(replace(d,nombre="Operaciones",gerente=e.id))
            emp.actualizar(replace(e,sueldo=900000))
            print("Lectura posterior:", deps.obtener(d.id).nombre, "· sueldo",emp.obtener(e.id).sueldo)
            entrada = "' OR '1'='1"
            assert emp.obtener(entrada) is None and not emp.listar(entrada)
            assert deps.obtener(entrada) is None and not deps.listar(entrada)
            print(f"Filtro literal {entrada!r} → 0 coincidencias; empleados activos:",len(emp.listar()))
            if exportar:
                archivos = ServicioInformes().generar(con,"horas",[ExportadorPDF(),ExportadorExcel()],tmp)
                print("Exportación polimórfica:",", ".join(f.name for f in archivos))
        try:
            with conectar(ruta) as con:
                EmpleadoRepositorio(con,llave).guardar(replace(e,id="E02",correo="otra@example.org",departamento="ausente"))
        except Conflicto:
            print("Rollback por departamento inexistente.")
        with conectar(ruta) as con:
            assert not con.execute("SELECT 1 FROM persona WHERE id='E02'").fetchone()
            print("Personas huérfanas tras el fallo: 0")
            EmpleadoRepositorio(con,llave).eliminar(e.id)
            DepartamentoRepositorio(con).eliminar(d.id)
            assert not EmpleadoRepositorio(con,llave).listar() and not DepartamentoRepositorio(con).listar()
            print("Bajas verificadas. Registros históricos:",con.execute("SELECT count(*) FROM registro").fetchone()[0])
