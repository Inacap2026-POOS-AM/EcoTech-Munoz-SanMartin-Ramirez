# Correspondencia con el checklist E3

Actualización: 20 de noviembre de 2026. Resultado de ejecución: 28 pruebas aprobadas, cero fallos y cero omisiones.

| Requisito recibido | Implementación y evidencia | Estado |
| --- | --- | --- |
| .env fuera de Git y ejemplo sin secretos | .gitignore, .env.example y configurar, que genera una clave privada una sola vez. | Archivos preparados; publicación individual pendiente. |
| os.getenv o dotenv y error por secreto faltante | infraestructura/conexion.py: entorno, ajustes y clave_clima; prueba de configuración ausente. | Probado. |
| Hash de contraseñas con salt | seguridad.py: Argon2id con sal aleatoria de 16 bytes; dos cuentas con la misma clave generan hashes distintos. | Probado. |
| Timeout explícito en cada petición | api_cliente.py: self.abrir(req, timeout=5). urllib es la biblioteca HTTP utilizada. | Probado; una única llamada de transporte. |
| 401, 403 y 404 sin reintentos | Un intento; mensajes sin detalles privados. No hay token renovable en los proveedores seleccionados. | Probado. |
| 429 y Retry-After | Segundos o fecha HTTP; espera corta real o aplazamiento con bloqueo del proveedor durante la sesión. | Probado. |
| 5xx y fallos de red reintentables | Hasta tres intentos; esperas exponenciales; prueba 429 seguido de 503 con pausas de 3 y 6 segundos. | Probado. |
| Registro de cada intento | Logs INFO con número de intento, timeout, espera y resultado; sin clave ni URL de consulta. | Probado. |
| Plan B con antigüedad | Cache SQLite parametrizada, obtenido_en, antigüedad, validación al recuperar y aviso si no existe. | Probado. |
| Deserializadora a objetos propios | deserializador.py y clases CondicionClimatica y CotizacionMonetaria; PagoEstimado combina cálculo y cotización. | Probado. |
| Insert y update parametrizados | UPSERT por clave de caché y repositorios sin SQL con datos concatenados. | Inspección AST y pruebas. |
| Validación de correo, RUT y tipos | Persona, validar_rut y dominio externo; RUT opcional con dígito verificador y almacenamiento cifrado. | Probado. |
| Cinco señales críticas de IA | auditar_seguridad.py y evidencias/auditoria_estatica.json; comprobación de paquetes en PyPI. | Sin hallazgos en los patrones auditados. |
| Prompts, sugerencias y decisiones | bitacora_ia.md, registro del checklist recibido y revisión de fragmentos concretos. | Documentado. |

Las llamadas reales a Open-Meteo y ExchangeRate-API se ejecutaron y validaron el 20 de noviembre. WeatherAPI con clave es una alternativa opcional probada mediante simulación, sin clave real. El timeout de cinco segundos es por operación de socket; no es un límite total de duración de la consulta. La auditoría estática detecta patrones definidos, no demuestra ausencia universal de vulnerabilidades.
