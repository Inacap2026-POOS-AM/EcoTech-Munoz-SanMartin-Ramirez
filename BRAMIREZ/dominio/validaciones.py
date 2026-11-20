"""Formato y dígito verificador; no acredita existencia ni identidad."""
import re
from .excepciones import ErrorNegocio


def validar_rut(valor):
    if not isinstance(valor, str) or not re.fullmatch(
        r"(?:[0-9]{1,8}|[0-9]{1,2}(?:\.[0-9]{3}){2})-[0-9Kk]", valor.strip()
    ):
        raise ErrorNegocio("RUT inválido: use cuerpo y dígito verificador separados por guion.")
    cuerpo, verificador = valor.strip().replace(".", "").upper().split("-")
    if int(cuerpo) == 0 or (len(cuerpo) > 1 and cuerpo.startswith("0")):
        raise ErrorNegocio("Cuerpo de RUT inválido.")
    suma = sum(int(digito) * (2 + posicion % 6)
               for posicion, digito in enumerate(reversed(cuerpo)))
    calculo = 11 - suma % 11
    esperado = "0" if calculo == 11 else "K" if calculo == 10 else str(calculo)
    if verificador != esperado:
        raise ErrorNegocio("Dígito verificador del RUT inválido.")
    return cuerpo + "-" + verificador
