"""Log local sin URL, cabeceras ni datos personales."""
import logging
import os
from pathlib import Path


def configurar_log(ruta=None):
    ruta = Path(ruta) if ruta else Path(__file__).resolve().parents[1] / "logs/servicios.log"
    ruta.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(ruta, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    os.close(descriptor)
    logger = logging.getLogger("ecotech")
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    formato = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    for handler in [logging.FileHandler(ruta, encoding="utf-8"), logging.StreamHandler()]:
        handler.setFormatter(formato)
        logger.addHandler(handler)
    logger.propagate = False
    return ruta
