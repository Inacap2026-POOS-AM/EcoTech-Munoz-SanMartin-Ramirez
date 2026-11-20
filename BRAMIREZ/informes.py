from abc import ABC, abstractmethod
from dominio.informe import Informe
from pathlib import Path
from xml.sax.saxutils import escape

CONSULTAS = {
    "empleados": "SELECT p.nombre,p.correo,coalesce(d.nombre,'Sin departamento') AS departamento FROM persona p JOIN empleado e ON e.id=p.id LEFT JOIN departamento d ON e.departamento=d.id WHERE e.activo=1 ORDER BY p.nombre",
    "departamentos": "SELECT d.nombre,coalesce(p.nombre,'Vacante') AS gerente FROM departamento d LEFT JOIN persona p ON p.id=d.gerente ORDER BY d.nombre",
    "proyectos": "SELECT nombre,inicio,estado FROM proyecto ORDER BY nombre",
    "horas": "SELECT p.nombre AS empleado, pr.nombre AS proyecto,r.fecha,r.minutos FROM registro r JOIN asignacion a ON r.asignacion=a.id JOIN persona p ON p.id=a.empleado JOIN proyecto pr ON pr.id=a.proyecto ORDER BY r.fecha,p.nombre"
}


class ExportadorInforme(ABC):
    @abstractmethod
    def exportar(self, informe, carpeta):
        """Devuelve la ruta del archivo generado."""


class ExportadorPDF(ExportadorInforme):
    def exportar(self, informe, carpeta):
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, LongTable, Paragraph, TableStyle
        ruta = carpeta / (informe.tipo + ".pdf")
        estilos = getSampleStyleSheet()
        datos = [informe.columnas, *informe.filas]
        tabla = LongTable([[Paragraph(escape(str(v)),estilos["BodyText"]) for v in fila] for fila in datos],
                          colWidths=[450 / len(informe.columnas)] * len(informe.columnas),repeatRows=1)
        tabla.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("VALIGN",(0,0),(-1,-1),"TOP")]))
        SimpleDocTemplate(str(ruta)).build([Paragraph("EcoTech | "+informe.tipo,estilos["Title"]),tabla])
        return ruta


class ExportadorExcel(ExportadorInforme):
    def exportar(self, informe, carpeta):
        from openpyxl import Workbook
        ruta = carpeta / (informe.tipo + ".xlsx")
        libro = Workbook()
        hoja = libro.active
        hoja.title = informe.tipo
        for i,fila in enumerate([informe.columnas,*informe.filas],1):
            for j,valor in enumerate(fila,1):
                celda = hoja.cell(i,j,valor)
                if isinstance(valor,str):
                    celda.data_type = "s"
        hoja.freeze_panes = "A2"
        libro.save(ruta)
        return ruta


class ServicioInformes:
    def generar(self, con, tipo, exportadores, carpeta):
        cursor = con.execute(CONSULTAS[tipo])
        informe = Informe(tipo,tuple(c[0] for c in cursor.description),[tuple(f) for f in cursor])
        ruta = Path(carpeta)
        ruta.mkdir(parents=True,exist_ok=True)
        return [e.exportar(informe,ruta) for e in exportadores]
