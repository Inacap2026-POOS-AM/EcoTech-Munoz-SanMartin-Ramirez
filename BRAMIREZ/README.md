# EcoTech ES3 · Entrega individual de Benjamin Ramirez

Versión revisada el 20 de noviembre de 2026 contra el checklist de preparación E3. La carpeta BRAMIREZ contiene mi implementación individual en la rama e3/ramirez del repositorio del equipo. Contiene la base EcoTech y su extensión de clima y tipos de cambio.

## Instalación y ejecución

Python 3.11 o posterior, desde BRAMIREZ. En Linux con Kitty y zsh/bash:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v
python auditar_seguridad.py
python demostracion_es3.py
python main.py configurar
python main.py alta-admin
python main.py
```

En Windows PowerShell active con .\.venv\Scripts\Activate.ps1. requirements.lock.txt fija las cuatro dependencias directas probadas; no es un bloqueo de todas las dependencias transitivas.

La demostración usa datos sintéticos y HTTP simulado, sin tocar la base personal. Ejecutarla dos veces mantiene dos registros por consulta; también demuestra red caída, 404, 503 y 429. La suite actual pasa 28 pruebas sin omisiones, incluidas PDF y Excel. evidencia_pruebas.txt contiene la salida real y evidencias/api_real.json conserva las respuestas seleccionadas de llamadas reales a Open-Meteo y ExchangeRate-API.

## Secretos y configuración

configurar crea .env una sola vez, con una clave Fernet aleatoria y permisos 0600 en POSIX. No copie una clave ficticia: si ECOTECH_KEY falta o es inválida, se informa claramente. os.getenv da prioridad al entorno sobre el archivo. .env.example contiene los cuatro nombres sin valores privados y .gitignore excluye .env, claves, bases, exportaciones y logs de ejecución.

El clima público usa Open-Meteo, sin clave externa. Para elegir WeatherAPI, añada ECOTECH_WEATHER_PROVIDER=weatherapi y WEATHERAPI_KEY solo a su .env; si falta esa clave, la consulta se rechaza antes de llamar al proveedor. Una clave API estática no dispone de renovación de token. Un 401 no se reintenta; no se inventa una función de renovación.

Las contraseñas se verifican con Argon2id y sal individual; nunca se guardan ni se cifran de forma reversible. Dirección, teléfono, sueldo y RUT opcional se cifran con Fernet porque su recuperación sí es necesaria. El RUT se valida con módulo 11, se normaliza y no reemplaza el ID interno. Se valida formato, no la existencia real de una identidad.

## APIs, objetos y continuidad

El cliente usa urllib de Python con timeout=5 explícito, tres intentos máximos y backoff. Los resultados son CondicionClimatica, CotizacionMonetaria y PagoEstimado; solo al mostrar o guardar se usa a_dict. La caché también se deserializa y valida al recuperarla.

Cada intento y resultado queda en logs/servicios.log sin URL de consulta, clave ni cuerpo externo. Los errores 4xx no se reintentan; 5xx y fallos de red sí. Retry-After acepta segundos o fecha HTTP. Si la espera supera ocho segundos, se usa el respaldo y se mantiene un bloqueo del proveedor para nuevas consultas durante la misma sesión, sin enviar otra petición antes del plazo. El bloqueo está en memoria y no se conserva al reiniciar.

La caché identifica proyecto, coordenadas y proveedor, o par de monedas. Usa UPSERT parametrizado e indica obtenido_en y antigüedad. Si no hay respaldo o está corrupto se informa y la consola conserva el control. La tasa es una referencia diaria; pago no transfiere dinero.

## Archivos de evaluación

- CHECKLIST_E3.md: correspondencia con cada requisito del aviso.
- bitacora_ia.md: instrucciones reales, sugerencias y decisiones.
- evidencias/: prueba automatizada, auditoría, API reales y captura auténtica de terminal.
- Ramirez_Benjamin_ES3_TI3021.pdf y .docx: informe actualizado.


