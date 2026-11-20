# Bitácora de revisión con IA · 18 de noviembre de 2026

Herramienta: ChatGPT con Codex. Esta revisión y sus cambios fueron realizados por el asistente. La comprensión y la defensa presencial corresponden al estudiante. No se atribuyen reuniones, commits, programación manual o revisiones personales que no constan.

## Interacciones comprobables de esta continuación

- Instrucción literal: «recuerda que no hagas cambio en el repo es personal y ese repo es de mas de una persona».
- Respuesta de trabajo: «Revisaré el contexto y los archivos disponibles para retomar la tarea, manteniendo cualquier trabajo fuera del repositorio compartido».
- Contexto consultado: HANDOFF_TI3021_PROGRAMACION.md, guías auténticas y código local de preparación. El enunciado de trabajo conservado en Pasted text.txt solicita completar las tareas sin enviarlas.

## Auditoría de fragmentos reales

| Fragmento revisado | Decisión | Fundamento y evidencia |
| --- | --- | --- |
| crear_usuario: longitud de contraseña | Modificar por seguridad | Una cadena de doce espacios pasaba la longitud mínima. Se rechaza texto vacío o compuesto solo por espacios, sin recortar contraseñas válidas. test_rechazo_de_claves_vacias verifica que no se cree ninguna cuenta. |
| EmpleadoRepositorio.guardar y _mapear | Aceptar tras inspección y prueba | SQL fijo con parámetros; direcciones, teléfonos y salarios se cifran con Fernet y se reconstruyen al leer. La demo comprueba lectura y actualización. |
| conectar y alta persona/empleado | Aceptar | El bloque transaccional revierte ambas tablas ante un departamento inexistente. La demo comprueba cero personas huérfanas. |
| ExportadorPDF y ExportadorExcel: importaciones | Modificar | Se cargan dentro de cada exportador para poder usar el dominio y el CRUD sin las librerías de salida. La prueba de exportación se identifica como omitida si no están instaladas; nunca se registra como aprobada. |
| Dataclass frozen y super().__post_init__ | Aceptar con alcance explícito | Evitan cambios accidentales y reutilizan validaciones; no son una barrera de seguridad contra quien ejecuta código Python dentro del mismo proceso. |
| ExportadorExcel: celda.data_type = s | Conservar tras inspección | Las cadenas se guardan como texto para evitar interpretación accidental de fórmulas. La ejecución de la exportación está pendiente en este entorno. |

## Límites de la evidencia

La prueba automática actual y sus omisiones están en evidencia_pruebas.txt. Las imágenes nuevas de consola son transcripciones visuales generadas a partir de una ejecución real; no se presentan como capturas de un terminal gráfico. Las antiguas imágenes de preparación no se incluyen como evidencia actual. Esta bitácora no inventa respuestas históricas de IA ni atribuye al estudiante la revisión realizada por Codex.

## Auditoría específica de ES3

| Riesgo solicitado | Decisión aplicada | Evidencia |
| --- | --- | --- |
| SQL interpolado | Conservar sentencias fijas con parámetros y UPSERT por clave de consulta. | Dos vueltas mantienen dos filas de caché. |
| verify=False | Descartar ese patrón de implementación; no estaba presente en esta versión. | El cliente usa el contexto TLS predeterminado de urllib. |
| except: pass | Descartar ese patrón; se distinguen HTTP, red y JSON. | Errores provocados y respaldo identificado. |
| Ausencia de timeout | Conservar cinco segundos por operación de socket y tres intentos máximos. | El transporte simulado recibe timeout=5. No es un plazo total de cinco segundos para toda la consulta. |
| Librerías inexistentes | Conservar urllib, json y sqlite3 de Python; Argon2id de cryptography. | Importación y pruebas reales de autenticación. |
| Espera tras 429 | Modificar: la secuencia anterior podía pasar de 3 a 2 segundos. | Ahora espera 3 y 6 segundos ante 429 seguido de 503; los tests simulan la espera. |

WeatherAPI con clave se comprobó mediante transporte simulado. No se dispone de una clave real y no se afirma haber probado esa autenticación contra el proveedor. Open-Meteo y ExchangeRate-API se contrastaron con su documentación; no hubo consulta real de datos desde este entorno restringido. El plazo Retry-After se respeta dentro de cada operación; no se implementa un limitador persistente entre reinicios o nuevas operaciones.
