# Bitácora de uso de IA — E3

Herramienta: ChatGPT / Codex. Trabajé en mi rama `e3/munoz` entre el 13 y el 18 de noviembre de 2026, sobre la base de EcoTech de E2. Usé la IA para generar y revisar código, y pedí explicaciones por partes antes de continuar.

## Prompts, respuestas y cambios en el código

Las citas son extractos de mis mensajes del chat. Las respuestas de Codex están resumidas. Los archivos y commits permiten ubicar cada cambio en mi rama.

| Prompt real | Respuesta de Codex y decisión | Componente generado y comprobación |
|---|---|---|
| «no hay alguna manera de que sea por el nombre del lugar?» | **Modifico.** Pedí que el usuario escribiera una ciudad. Codex propuso buscar coincidencias con Open-Meteo, mostrar región y país y pasar las coordenadas elegidas al cliente de clima. | `buscar_lugares()` en `api_cliente.py`, commit `d2ca497`. Busqué `concepcion`, elegí la opción del Biobío y vi en el log las peticiones de búsqueda y clima. |

## Decisión — Respaldo con SQLite

**Consulta que hice.** «la base de datos que tengo no se podria usar en la prueba sin conexion?» Luego aclaré que el profesor me había dicho que podía usar Supabase y que cortaría Ethernet durante la ejecución.

**Propuesta y decisión.** Codex propuso mantener Supabase como base principal y agregar SQLite como respaldo. Acepté la propuesta porque tanto la API como Supabase requieren conexión. El programa guarda primero una copia local de los datos válidos y después intenta guardarlos en Supabase. Si falla la consulta, puede mostrar el último dato guardado y conservar su fecha de obtención.

**Dónde quedó el cambio.** `repositorio/clima_local_repo.py` guarda y recupera el último clima por coordenadas. `menu_clima.py` usa ese respaldo si falla la consulta y calcula su antigüedad con `obtenido_en`. El respaldo de clima y su integración al menú quedaron en el commit `9ce1ec7`.

**Cómo lo probé.** Guardé el clima de un lugar con internet y desconecté Ethernet con la sesión abierta. Al consultar el mismo lugar, EcoTech mostró el dato guardado y el aviso del Plan B con su antigüedad. El menú quedó limitado a clima y salida. Al reconectar, volvieron las opciones normales.

## Auditoría de las cinco señales de riesgo

Revisión del 18 de noviembre sobre los archivos Python versionados:

| Señal | Resultado y decisión |
|---|---|
| SQL con f-strings o concatenación | No se encontraron. Se mantienen parámetros separados: `%s` en PostgreSQL y `?` en SQLite. Los SQL de inicialización son archivos estáticos. |
| `verify=False` | No se encontró. Requests conserva la validación TLS. |
| `except: pass` | No se encontraron capturas que solo hagan `pass`. Los errores se comunican, se registran o se relanzan. Los `pass` de las clases de excepciones no ocultan fallos. |
| Peticiones sin timeout | La llamada HTTP compartida usa `timeout=(3, 10)`. Los reintentos tienen un máximo de tres intentos en total. |
| Librerías inexistentes | Se verificaron en PyPI argon2-cffi, psycopg, python-dotenv, requests, reportlab y openpyxl. `pip check` no informó dependencias rotas. SQLite viene con Python. |

## Pruebas y límites

En mi equipo probé clima, consultas repetidas, cambio de contraseña y conversión de CLP a USD. Al desconectar Ethernet durante una sesión, funcionó el Plan B y se limitó el menú; al reconectar se recuperaron las opciones. La tabla de clima conservó una fila para las mismas coordenadas y fecha.

En la revisión final pasaron 15 pruebas locales y 17 incluyendo Supabase. Se comprobaron guardados repetidos de ambos servicios con datos temporales que se revirtieron. Un endpoint real inexistente devolvió 404 sin reintentos. También se verificó Argon2id en la base sin mostrar hashes, y que `.env` y los respaldos no estén versionados.

Se necesita internet para iniciar sesión. El respaldo permite continuar si la conexión se pierde después de entrar y conserva su `obtenido_en` original. Sin datos previos muestra un aviso. El indicador del dólar puede ser de un día anterior y por eso siempre se muestra su fecha.
