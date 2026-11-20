# Informe técnico ES3
## Servicios externos, persistencia y seguridad en EcoTech

Autor: Benjamin Ramirez. Nombre completo: Benjamín Francisco Andrés Ramírez Angulo.
Asignatura: Programación Orientada a Objeto Seguro, TI3021. INACAP San Pedro de la Paz.
Docente: Nilson Arturo Guerra Cabeza.
Fecha: 20 de noviembre de 2026. Entrega individual.

# 1. Alcance de mi extensión

Mi versión incorpora clima para proyectos existentes y tipos de cambio para estimar pagos internacionales. Continúa la base EcoTech con su dominio, repositorios y SQLite. El importe calculado es una referencia: no ejecuta una transferencia. El desarrollo y la revisión cuentan con apoyo de ChatGPT/Codex, declarado en la bitácora.

La revisión sigue el checklist de preparación E3 facilitado en esta conversación. Se corrigieron dos diferencias centrales respecto de la preparación anterior: la ausencia de logs por intento y la conversión a diccionarios en lugar de objetos propios tipados.

# 2. Gestión segura de credenciales y secretos

.env está excluido en .gitignore. .env.example contiene ECOTECH_DB, ECOTECH_KEY, ECOTECH_WEATHER_PROVIDER y WEATHERAPI_KEY sin valores privados. La orden configurar genera una clave aleatoria una sola vez, con permisos privados en POSIX. No se incluye .env, una clave o una base personal en el paquete.

La configuración consulta solo nombres pertinentes mediante os.getenv, que tiene prioridad sobre el archivo. Si falta ECOTECH_KEY, o no tiene formato Fernet válido, se muestra un mensaje claro. Si se selecciona WeatherAPI y falta WEATHERAPI_KEY, se rechaza la consulta antes de llamar al proveedor. La ruta pública Open-Meteo no requiere clave externa.

Las contraseñas se guardan como hashes Argon2id con una sal aleatoria por cuenta. Dos cuentas con la misma contraseña producen hashes distintos. No se guardan contraseñas en texto plano, ni se sustituyen sus hashes por Base64 o cifrado reversible. Fernet se reserva para campos que sí requieren recuperación autorizada: dirección, teléfono, sueldo y RUT opcional.

Los archivos están preparados para versionar en una copia individual. No se ha publicado ni modificado un repositorio; ese paso no se presenta como realizado.

# 3. Consumo resiliente y registro de errores

El cliente usa urllib de la biblioteca estándar. Su única llamada de transporte indica timeout=5, equivalente al requisito de timeout explícito para cada petición. Ese valor limita operaciones de socket y no representa el tiempo total de todos los reintentos.

| Situación | Tratamiento implementado |
| --- | --- |
| HTTP 401, 403 o 404 | Un intento y mensaje seguro. No hay token renovable en los proveedores seleccionados. |
| HTTP 429 | Retry-After admite segundos o fecha HTTP. Se respeta el plazo antes de repetir. |
| Espera larga por 429 | Se recupera respaldo y se bloquean nuevas consultas al mismo proveedor durante esa sesión. |
| HTTP 5xx y fallo de red | Hasta tres intentos con espera exponencial; la secuencia se registra. |
| Certificado TLS inválido | Se rechaza sin desactivar verificación ni repetir la conexión. |
| JSON roto, lista inesperada o más de 128 KiB | Se rechaza el contenido sin sobrescribir el respaldo válido. |

Cada intento queda en logs/servicios.log con número, timeout, resultado y espera. No se registran contraseñas, cabeceras, cuerpos externos ni URL con la clave. Un identificador aleatorio permite relacionar los intentos de una misma solicitud.

Para una espera de hasta ocho segundos, el proceso espera antes del reintento. Si el servidor exige más, la consulta se aplaza y usa datos locales; el ClienteAPI conservado por el menú impide otra petición al proveedor antes del plazo. Este bloqueo reside en memoria y no sobrevive a reinicios. La caché sí permanece en SQLite.

No se implementa una renovación ficticia de token: los proveedores públicos no la requieren y WeatherAPI utiliza una clave estática. Un 401 de esa alternativa se informa con un solo intento.

# 4. Deserialización y objetos de dominio

| Clase propia | Tipos y reglas principales |
| --- | --- |
| CondicionClimatica | datetime con zona horaria; temperatura y humedad float finitos y acotados; estado textual no vacío. |
| CotizacionMonetaria | datetime con zona horaria; monedas admitidas; tasa Decimal positiva y finita. |
| PagoEstimado | Cotización validada e importes Decimal; representa el cálculo, no un pago realizado. |

Deserializador selecciona campos del proveedor y construye estas clases antes de persistir. a_dict convierte los objetos solo al mostrarlos o almacenarlos. La recuperación de caché vuelve a deserializar y validar; un JSON local incompleto o corrupto no se acepta sin control.

El clima se asocia a un proyecto y coordenadas válidas. Se verifican unidades Celsius y porcentaje, códigos meteorológicos, números finitos, monedas y montos. Persona valida correo y teléfono. El RUT opcional valida formato y dígito verificador por módulo 11, se normaliza y se cifra al guardar. No reemplaza el identificador interno ni prueba la existencia real de una persona.

# 5. Persistencia y degradación controlada

La caché usa una clave primaria por consulta, obtenido_en y los campos seleccionados. El clima distingue proyecto, coordenadas y proveedor; la conversión distingue par de monedas. Un UPSERT parametrizado actualiza la misma consulta en lugar de acumular duplicados.

```sql
INSERT INTO cache_api(clave,obtenido_en,datos) VALUES (?,?,?)
ON CONFLICT(clave) DO UPDATE SET
obtenido_en=excluded.obtenido_en,datos=excluded.datos
```

Si la red falla, se consulta solo el respaldo correspondiente. La consola informa que es local, la causa, obtenido_en y su antigüedad. La fecha de la fuente se conserva por separado. Si no hay respaldo, o está inválido, el error de negocio devuelve el control al menú sin inventar un resultado.

Los repositorios mantienen consultas fijas con parámetros. La migración agrega la columna cifrada de RUT solo si falta y puede ejecutarse dos veces. Las claves foráneas y las transacciones conservan las relaciones; el fallo de la segunda escritura de un empleado revierte la primera.

# 6. Verificación de la versión final

La suite final pasó 28 pruebas con cero fallos, cero errores y cero omisiones en Python 3.12.14. Incluye las exportaciones reales PDF y Excel, que en la preparación anterior estaban pendientes.

| Comprobación | Evidencia obtenida |
| --- | --- |
| Log, timeout y reintentos | Tres intentos registrados con timeout=5; esperas de 1 y 2 segundos. |
| Combinación de 429 y 503 | Se verifican esperas de 3 y 6 segundos. |
| Retry-After largo | Una sola petición nueva; la siguiente consulta del mismo proveedor queda bloqueada. |
| Tipos y persistencia | Se construyen clases propias y se recupera el mismo tipo desde caché. Datos inválidos no se guardan. |
| Contraseñas y entradas | Hashes Argon2id distintos, rechazo de claves vacías, RUT y correo inválidos. |
| Exportación | PDF leído y Excel comprobado; una cadena de fórmula conserva tipo texto. |

También se hicieron llamadas reales a Open-Meteo y ExchangeRate-API y se validaron sus respuestas. Los datos seleccionados están en evidencias/api_real.json. La demostración sin red utiliza respuestas sintéticas identificadas; no se confunden con mediciones ni tasas reales. WeatherAPI con clave es una alternativa opcional y solo se comprobó mediante simulación.

Los archivos evidencia_pruebas.txt, evidencias/demo_http.log y evidencias/auditoria_estatica.json permiten repetir la revisión. La captura de terminal documenta la ejecución de la demostración.

# 7. Auditoría crítica de IA

La bitácora conserva instrucciones y diagnóstico reales de esta continuación. El asistente propuso y aplicó objetos tipados, logs por intento, conservación del plazo de 429 y validación de RUT opcional. Se documenta qué se aceptó, modificó o descartó, sin atribuir una revisión personal que no consta.

| Señal crítica | Decisión y comprobación |
| --- | --- |
| SQL dinámico con datos interpolados | Descartado como patrón; se mantienen parámetros y se inspeccionan llamadas con AST. |
| verify=False | Descartado; TLS conserva la validación predeterminada. |
| except Exception: pass | Descartado; los errores se clasifican, se registran y se comunican de forma controlada. |
| Petición sin timeout | Aceptado tras verificación: la única llamada de transporte declara cinco segundos. |
| Librerías inexistentes | Se contrastaron cryptography, reportlab, openpyxl y pypdf con sus registros oficiales de PyPI. |

La auditoría automatizada no encontró esos patrones en el código auditado. Su alcance es limitado y no acredita seguridad universal. La defensa debe demostrar comprensión del código, sus pruebas y sus límites.

# 8. Ejecución y entrega

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v
python auditar_seguridad.py
python demostracion_es3.py
```

Para usar una base personal, continúo con configurar, alta-admin y el menú de main.py. El ZIP contiene una carpeta BRAMIREZ independiente del repositorio compartido. La publicación de un enlace individual y la entrega en AAI siguen pendientes; el paquete no sustituye el enlace exigido por el aviso específico de la actividad.

# Referencias

INACAP. (2026). Unidad 3: Servicios Externos y Seguridad en Python - Preparación E3 [Checklist de asignatura facilitado por el estudiante].
Open-Meteo. (s. f.). Weather Forecast API. https://open-meteo.com/en/docs
ExchangeRate-API. (s. f.). Open Access Endpoint. https://www.exchangerate-api.com/docs/free
Python Software Foundation. (s. f.). urllib.request. https://docs.python.org/3/library/urllib.request.html
Python Package Index. (s. f.). cryptography; reportlab; openpyxl; pypdf. Registros oficiales enlazados en DEPENDENCIAS_VERIFICADAS.md.
