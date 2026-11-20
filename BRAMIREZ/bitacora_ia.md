# Bitácora de IA · revisión E3 del 20 de noviembre de 2026

Herramienta: ChatGPT con Codex. El asistente realizó los cambios, la documentación y las verificaciones de esta copia. La comprensión y defensa presencial corresponden al estudiante. No se atribuyen programación manual, reuniones ni contribuciones ajenas.

## Instrucciones e interacción comprobables

En esta conversación el estudiante indicó: «recuerda que no hagas cambio en el repo es personal y ese repo es de mas de una persona» y luego «sigue trabajando». Posteriormente facilitó el aviso titulado «Unidad 3: Servicios Externos y Seguridad en Python — Preparación E3», con los apartados de secretos, APIs resilientes, deserialización, persistencia y auditoría. La tabla CHECKLIST_E3.md conserva sus requisitos operativos y su correspondencia con la entrega.

Respuesta real del asistente al recibirlo: «Voy a contrastar este checklist con la versión de ES3 que preparé y corregir lo que falte en la copia personal, fuera del repositorio compartido».

Diagnóstico real comunicado: «Detecté dos faltantes claros en la versión anterior: no registraba cada intento HTTP y la deserializadora devolvía diccionarios, no objetos de dominio tipados».

## Sugerencias generadas y decisiones aplicadas

| Fragmento revisado o sugerencia aplicada | Decisión | Justificación y comprobación |
| --- | --- | --- |
| Deserializador que devolvía dict | Modifico | Ahora construye dataclass validadas con datetime y Decimal. La caché vuelve a construir el mismo tipo, no entrega JSON sin validar. |
| Cliente sin registro de intentos | Modifico | Se usa logging INFO por intento, espera y resultado. La prueba cuenta tres entradas y verifica que no aparezca una clave sintética. |
| Aplazar un 429 largo sin conservar el plazo entre consultas | Modifico por resiliencia | Se conserva el bloqueo del origen en el ClienteAPI que reutiliza el menú. No hay nueva petición hasta que venza; el estado no sobrevive a un reinicio. |
| Configuración que mezclaba todo os.environ | Modifico | Lee solo nombres pertinentes mediante os.getenv y muestra qué secreto requerido falta. La clave opcional se exige solo si se selecciona su proveedor. |
| Validación de correo y tipos sin RUT de contacto | Modifico | Se agrega un RUT opcional independiente del ID; valida formato y módulo 11, y se cifra al persistir. Migración repetible para bases anteriores. |
| SQL con parámetros y UPSERT | Acepto tras inspección y prueba | Los datos externos y las entradas no se incorporan a la instrucción SQL. La búsqueda con el payload de la pauta no retorna todas las filas. |
| Mantener TLS y rechazar redirecciones | Acepto | No se permite HTTP ni verificación desactivada; un fallo de certificado no se reintenta y no filtra su detalle. |
| Inventar una renovación de token para 401 | Descarto como diseño | Los proveedores públicos no usan token de acceso renovable; WeatherAPI usa una clave estática. Un 401 se informa con un intento. |

## Cinco señales críticas

1. SQL interpolado: ninguna construcción con f-string, concatenación o format en las llamadas SQL auditadas.
2. TLS desactivado: no se utiliza verify=False; urllib mantiene el contexto de certificados predeterminado.
3. Errores ocultos: no hay bloques except que solo ejecuten pass. Los fallos se clasifican y se registran sin cuerpo remoto ni secretos.
4. Timeout ausente: la única llamada de transporte tiene timeout=5; las pruebas inspeccionan cada invocación.
5. Paquetes inventados: cryptography, reportlab, openpyxl y pypdf se contrastaron con sus páginas oficiales de PyPI y se ejecutaron en las versiones documentadas.

La inspección se automatiza parcialmente con auditar_seguridad.py. No se afirma que esos patrones prohibidos hubieran sido sugeridos en una interacción histórica que no consta; se distingue el patrón descartado del código que realmente se corrigió.

## Resultado real

La suite final pasó 28 pruebas, sin omisiones. Se probaron PDF y Excel, incluidas lectura y protección de texto frente a interpretación de fórmulas. Las llamadas reales de los dos proveedores públicos pasaron la deserialización; los fallos deliberados y la variante WeatherAPI se comprobaron con transporte simulado. Los archivos de evidencia identifican su origen. La bitácora del 18 de noviembre queda archivada como registro histórico de aquella preparación.
