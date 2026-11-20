# Bitácora de auditoría de inteligencia artificial

## 1. Información general

- Proyecto: EcoTech
- Evaluación: E3
- Rama de trabajo: e3/sanmartin
- Fecha de elaboración: 19 de noviembre de 2026
- Responsable: San Martín

## 2. Objetivo

Registrar el uso de herramientas de inteligencia artificial durante el desarrollo de la evaluación E3, documentando las consultas realizadas, las recomendaciones revisadas y las decisiones técnicas adoptadas.

La IA se utilizó como herramienta de apoyo. Las sugerencias fueron revisadas y contrastadas con el código y las pruebas del proyecto antes de incorporarse.

## 3. Registro de asistencia de IA

Los siguientes ejemplos representan las consultas técnicas realizadas durante el desarrollo:

| Consulta o tema | Recomendación evaluada | Decisión |
|---|---|---|
| Integración de API de calidad del aire | Implementar un cliente HTTP con timeout y manejo de errores. | Aceptada y adaptada al proyecto. |
| Reintentos ante fallos de conexión | Aplicar reintentos limitados y espera exponencial. | Aceptada, con máximo de cuatro intentos. |
| Respuesta HTTP 429 | Interpretar la cabecera Retry-After. | Aceptada. |
| Persistencia de mediciones | Utilizar consultas SQL parametrizadas. | Aceptada. |
| Recuperación ante caída de API | Consultar la última medición almacenada en PostgreSQL. | Aceptada. |
| Seguridad de credenciales | Mantener secretos en variables de entorno y excluir .env de Git. | Aceptada. |
| Auditoría de código | Buscar patrones inseguros y revisar las dependencias. | Aceptada y ejecutada. |

## 4. Auditoría de cinco señales de alerta

### 4.1. SQL dinámico mediante f-strings

Se ejecutó una búsqueda automatizada de llamadas execute o executemany construidas mediante f-strings.

Resultado: no se encontraron coincidencias con el patrón auditado.

Decisión: se mantiene el uso de consultas parametrizadas para evitar inyección SQL.

Nota: la búsqueda automatizada es una comprobación inicial y no reemplaza una revisión completa del código.

### 4.2. Desactivación de la verificación SSL

Se buscó el uso de verify=False en el proyecto.

Resultado: no se encontraron coincidencias.

Decisión: no se desactiva la verificación de certificados SSL.

### 4.3. Excepciones silenciadas

Se revisaron los bloques de manejo de excepciones.

Se identificó un except ValueError: pass en el método que interpreta Retry-After del cliente de calidad del aire.

Análisis: esta excepción es específica e intencional. Si el valor no puede convertirse a segundos, el programa intenta interpretarlo como una fecha HTTP.

Decisión: se mantiene porque forma parte de un mecanismo de conversión alternativo y no oculta indiscriminadamente errores generales.

### 4.4. Solicitudes HTTP sin timeout

Se revisaron las solicitudes HTTP del proyecto.

Resultado: el cliente de calidad del aire utiliza requests.get con timeout configurado mediante self.TIMEOUT.

Valor configurado: 10 segundos.

Decisión: se mantiene el límite para evitar esperas indefinidas ante problemas de conexión.

### 4.5. Dependencias inexistentes

Se revisaron las dependencias declaradas en requirements.txt:

- Werkzeug
- psycopg
- python-dotenv
- reportlab
- openpyxl
- requests

Resultado: los seis paquetes fueron contrastados con sus respectivos nombres de distribución en PyPI.

Decisión: se mantienen las dependencias declaradas.

## 5. Seguridad de contraseñas y configuración

- Las credenciales de conexión se cargan desde variables de entorno.
- El archivo .env está excluido del control de versiones.
- Se mantiene .env.example como plantilla sin secretos reales.
- Las contraseñas se almacenan mediante Werkzeug, utilizando PBKDF2 con SHA-256 y 600.000 iteraciones.
- La generación del hash incorpora una sal aleatoria.
- La verificación se realiza mediante check_password_hash.

## 6. Pruebas realizadas

Se realizaron las siguientes comprobaciones:

- Deserialización de una respuesta JSON a un objeto MedicionCalidadAire.
- Manejo de timeout seguido de una respuesta exitosa.
- Tratamiento de HTTP 400 sin reintentos.
- Tratamiento de HTTP 429 respetando Retry-After.
- Tratamiento de HTTP 503 mediante reintentos y espera exponencial.
- Persistencia de mediciones en PostgreSQL.
- Recuperación de una medición almacenada mediante una simulación de fallo de la API.
- Integración de la opción de calidad del aire en el menú de la aplicación.
- Ejecución de la suite automatizada: 9 pruebas aprobadas.

Nota: la recuperación ante fallos se comprobó mediante una simulación de error del cliente de API. No se registra como una prueba realizada con desconexión física de Internet.

## 7. Decisiones y responsabilidad

Las recomendaciones de IA no se incorporaron de forma automática. Se revisaron considerando la arquitectura existente, los requisitos de la evaluación y el funcionamiento esperado del sistema.

La implementación final, las pruebas y las decisiones técnicas son responsabilidad del desarrollador.

## 8. Conclusión

La asistencia de inteligencia artificial permitió apoyar la implementación y revisión de la integración de calidad del aire, la persistencia de datos, el manejo de errores y la seguridad.

Las recomendaciones fueron evaluadas y contrastadas con el código y las pruebas disponibles antes de considerarse parte del proyecto.
