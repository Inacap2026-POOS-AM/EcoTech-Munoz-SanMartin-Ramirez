"""Recorrido reproducible de C14 con transporte simulado y base temporal."""
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock
from urllib.error import HTTPError, URLError
import io
import json
import secrets

from api_cliente import ClienteAPI
from infraestructura.conexion import iniciar, conectar
from dominio.proyecto import Proyecto
from repositorio.operaciones import guardar_proyecto
from seguridad import crear_usuario, autenticar
from servicios import ServiciosEcoTech
from infraestructura.log_api import configurar_log
from datos_demo import CAMBIO, CLIMA


def main():
    configurar_log()
    print("Datos sintéticos de demostración; servicios HTTP simulados.")
    with TemporaryDirectory() as tmp:
        ruta = Path(tmp)/"c14.db"
        iniciar(ruta)
        with conectar(ruta) as con:
            clave = secrets.token_urlsafe()
            crear_usuario(con,"analista",clave,"consulta")
            sesion = autenticar(con,"analista",clave)
            guardar_proyecto(con,Proyecto("P01","Terreno","Medición",date.today()))
            abrir = Mock()
            api = ServiciosEcoTech(con,sesion,ClienteAPI(abrir,lambda segundos: None))
            for i in (1,2):
                abrir.side_effect = [io.BytesIO(json.dumps(CLIMA).encode()),io.BytesIO(json.dumps(CAMBIO).encode())]
                print("Vuelta",i,api.clima("P01",-36.84,-73.1)[1].estado,
                      "· pago CLP",api.pago("USD","CLP","2.50")[1].pago_estimado,
                      "· filas",con.execute("SELECT count(*) FROM cache_api").fetchone()[0])
            abrir.side_effect = URLError("sin red")
            print(api.clima("P01",-36.84,-73.1)[0])
            abrir.side_effect = HTTPError("https://example.org/invalido",404,"",{},None)
            print(api.pago("USD","CLP","2.50")[0])
            abrir.side_effect = [
                HTTPError("https://example.org",429,"",{"Retry-After":"3"},None),
                HTTPError("https://example.org",503,"",{},None),
                io.BytesIO(json.dumps(CAMBIO).encode())]
            print("429 y 503 recuperados:",api.pago("USD","CLP","2.50")[1].pago_estimado)
            antes = abrir.call_count
            abrir.side_effect = HTTPError("https://example.org",429,"",{"Retry-After":"120"},None)
            print("429 largo:",api.pago("USD","CLP","2.50")[0])
            print("Nueva consulta durante Retry-After:",api.pago("USD","CLP","2.50")[0])
            print("Llamadas nuevas al proveedor durante el 429 largo:",abrir.call_count-antes)
            print("Formato del hash:",con.execute("SELECT hash FROM usuarios").fetchone()[0].split("$")[1])


if __name__=="__main__":
    main()
