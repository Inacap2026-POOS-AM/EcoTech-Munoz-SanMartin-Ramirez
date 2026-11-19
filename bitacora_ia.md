# Bitácora de uso de IA — E3

Herramienta: ChatGPT / Codex. Trabajé en mi rama `e3/munoz` entre el 13 y el 18 de noviembre de 2026, sobre la base de EcoTech de E2. Usé la IA para generar y revisar código, y pedí explicaciones por partes antes de continuar.

## Consultas y decisiones

| Trabajo solicitado | Decisión | Justificación |
|---|---|---|
| Revisar el proyecto y preparar la consulta de clima | Acepto con cambios | Se aprovecharon las clases existentes. La primera consulta se amplió con timeout, errores HTTP diferenciados, tres intentos y logs. |
| Consultar el clima por coordenadas | Modifico | Pedí buscar por nombre. Ahora se muestran coincidencias con región y país para elegir el lugar. |
| Procesar el diccionario de la API | Modifico | Se agregaron deserializadores y objetos propios para validar los datos antes de guardarlos. |
| Mantener Supabase durante un corte de Ethernet | Modifico | Se agregó SQLite como respaldo. La copia se guarda primero y conserva su fecha original de obtención. |
| Dejar un script independiente para consultar clima | Descarto para la entrega | Su flujo se integró al menú para exigir login antes de consultar la API o el respaldo. |
| Conservar Werkzeug y compatibilidad con PBKDF2 | Descarto | Se reiniciaron los datos de prueba por decisión mía y se dejó solo Argon2id, con sal aleatoria. |
| Agregar dólar y conversión de pagos | Acepto | Se comprueban unidad, valor y fecha de mindicador.cl. El cálculo usa Decimal y no modifica salarios ni transfiere dinero. |

Entre las solicitudes del chat estuvieron: «explicame todo el codigo porque debo entenderlo» y «no hay alguna manera de que sea por el nombre del lugar?». Se revisaron los bloques y se acordaron los mensajes de commit antes de subir los avances.

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

Se necesita internet para iniciar sesión. El respaldo permite continuar si la conexión se pierde después de entrar; no cambia su `obtenido_en` al leerse. Sin datos previos muestra un aviso. El indicador del dólar puede ser de un día anterior y por eso siempre se muestra su fecha.
