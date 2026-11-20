"""Auditoría estática acotada a las cinco señales exigidas; no reemplaza las pruebas."""
import ast
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import re


def auditar(raiz=None):
    raiz = Path(raiz) if raiz else Path(__file__).resolve().parent
    hallazgos = []
    llamadas_http = 0
    for archivo in sorted(raiz.rglob('*.py')):
        if any(p in {'.venv', '__pycache__'} for p in archivo.parts):
            continue
        if archivo.name.startswith('test_'):
            continue
        arbol = ast.parse(archivo.read_text(encoding='utf-8'))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Call):
                nombre = nodo.func.attr if isinstance(nodo.func, ast.Attribute) else getattr(nodo.func, 'id', '')
                if nombre in {'execute', 'executemany', 'executescript'} and nodo.args:
                    sql = nodo.args[0]
                    if isinstance(sql, (ast.JoinedStr, ast.BinOp)) or (
                        isinstance(sql, ast.Call) and isinstance(sql.func, ast.Attribute) and sql.func.attr == 'format'
                    ):
                        hallazgos.append((str(archivo.relative_to(raiz)), nodo.lineno, 'SQL construido dinámicamente'))
                if any(k.arg == 'verify' and isinstance(k.value, ast.Constant) and k.value.value is False for k in nodo.keywords):
                    hallazgos.append((str(archivo.relative_to(raiz)), nodo.lineno, 'TLS desactivado'))
                if nombre in {'abrir', 'urlopen'}:
                    llamadas_http += 1
                    if not any(k.arg == 'timeout' for k in nodo.keywords):
                        hallazgos.append((str(archivo.relative_to(raiz)), nodo.lineno, 'Petición sin timeout'))
            if isinstance(nodo, ast.ExceptHandler) and all(isinstance(b, ast.Pass) for b in nodo.body):
                hallazgos.append((str(archivo.relative_to(raiz)), nodo.lineno, 'Excepción silenciada'))
    paquetes = {}
    for linea in (raiz / 'requirements.txt').read_text().splitlines():
        nombre = re.split(r'[<>=!~\s]', linea.strip(), 1)[0]
        if not nombre or nombre.startswith('#'):
            continue
        try:
            paquetes[nombre] = version(nombre)
        except PackageNotFoundError:
            paquetes[nombre] = 'NO INSTALADO'
    return {'alcance': 'Patrones AST y versiones instaladas; referencias PyPI en DEPENDENCIAS_VERIFICADAS.md',
            'llamadas_http_con_timeout': llamadas_http, 'hallazgos': hallazgos,
            'paquetes_instalados': paquetes}


if __name__ == '__main__':
    resultado = auditar()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    raise SystemExit(bool(resultado['hallazgos']) or 'NO INSTALADO' in resultado['paquetes_instalados'].values())
