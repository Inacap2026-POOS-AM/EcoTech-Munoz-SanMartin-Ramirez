# EcoTech — Evaluación 3

Extensión individual del sistema de empleados y proyectos de la E2. En esta entrega agregué consultas de clima, dólar observado, conversión de CLP a USD y respaldos locales para continuar si se pierde la conexión.

Mi rama es `e3/munoz`. La rama `main` se mantiene como respaldo de la E2.

## Instalación

Necesito Python 3.11 o posterior, Git y una base PostgreSQL en Supabase. Las pruebas se realizaron con Python 3.14.

Desde la carpeta EcoTech:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Si `.venv` o `.env` ya existen, no los reemplazo. En `.env` completo los datos de conexión PostgreSQL de mi proyecto Supabase:

```dotenv
DB_HOST=
DB_PORT=5432
DB_NAME=postgres
DB_USER=
DB_PASSWORD=
DB_SSLMODE=require
```

Uso los datos del método de conexión que muestra Supabase, incluido el puerto correspondiente. `DB_PASSWORD` es la contraseña de PostgreSQL, no una API key. El programa avisa si falta una variable. `.env`, las bases SQLite y los reportes están fuera de Git; solo se entrega `.env.example` sin credenciales.

## Preparar la base

Solo para una base nueva, creo las tablas de empleados, cuentas y proyectos:

```powershell
python main.py --inicializar
```

Si ya tengo la E2 funcionando, no necesito repetirlo. Inicio el programa y, si no existe un administrador, completo su registro inicial:

```powershell
python main.py
```

Después preparo las tablas de la E3 iniciando sesión como administrador en cada comando:

```powershell
python main.py --inicializar-clima
python main.py --inicializar-indicadores
```

Estos comandos no borran datos. Los SQL están en `datos/schema.sql`, `datos/clima.sql` y `datos/indicadores.sql`. Las tablas tienen RLS activo. La consola usa la conexión PostgreSQL propietaria; los roles de la aplicación se comprueban en Python y no son políticas RLS para un cliente público.

## Uso

```powershell
python main.py
```

Ingreso el usuario de la cuenta y su contraseña, no el nombre del empleado. Las contraseñas se guardan con Argon2id y sal aleatoria. La versión actual no admite los hashes PBKDF2 de E2.

| Opción | Función |
|---|---|
| 1 y 2 | Departamentos y empleados, solo administrador |
| 3 | Proyectos; el empleado consulta los que tiene asignados |
| 4 | Horas; el empleado administra solo sus registros |
| 5 | Informes PDF y Excel, solo administrador |
| 6 | Cambiar la contraseña de la cuenta actual |
| 7 | Buscar un lugar y consultar su clima |
| 8 | Consultar el dólar y convertir un importe de CLP a USD |
| 0 | Salir y cerrar la sesión |

### Clima

Escribo el nombre del lugar y selecciono una coincidencia con ciudad, región y país. El programa obtiene sus coordenadas y muestra temperatura, humedad, estado del tiempo y fecha meteorológica. Las horas se expresan siempre en `America/Santiago`, aunque consulte otro país.

Fuentes: [búsqueda de lugares](https://open-meteo.com/en/docs/geocoding-api) y [clima de Open-Meteo](https://open-meteo.com/en/docs).

### Dólar

La opción 8 obtiene el dólar observado desde [mindicador.cl](https://mindicador.cl/api/dolar). Muestra el valor en CLP por USD y la fecha más reciente de la serie. Esa fecha puede ser anterior a hoy.

Ingreso un importe como `900000`, sin símbolos ni separadores de miles. Se permiten hasta dos decimales, con punto. El cálculo es `importe CLP / valor del dólar`; usa `Decimal` y redondea a dos decimales con `ROUND_HALF_UP`.

Es una conversión referencial: no incluye comisiones, no modifica salarios ni realiza transferencias. Ambos roles pueden ingresar un importe; esta opción no muestra sueldos de otros empleados.

## Errores y respaldo local

Todas las peticiones pasan por `api_cliente.py`, con timeout de conexión de 3 segundos y de lectura de 10 segundos. Hay como máximo tres intentos en total:

- Los errores 4xx no se reintentan, salvo 429. Estas APIs no usan tokens que deban renovarse ante un 401.
- En 429 se respeta `Retry-After`, en segundos o fecha HTTP. Si falta o es inválido, se usa la espera base.
- Los errores 5xx, timeout y conexión se reintentan con esperas base de 1 y 2 segundos. Si un 5xx indica un `Retry-After` válido, también se respeta.
- No se desactiva la verificación TLS. Los errores SSL y el JSON inválido se comunican sin reintentos automáticos.

Los intentos y esperas aparecen en la terminal. Los deserializadores validan la estructura y crean objetos `Clima` o `IndicadorDolar` antes de guardar.

Primero se guarda una copia en SQLite y después se intenta Supabase. El respaldo se crea automáticamente en `datos/clima_local.sqlite3` y `datos/indicadores_local.sqlite3`; no requiere instalar un servidor. Guarda el último clima por coordenadas y los indicadores por fecha.

Si falla internet, se buscan lugares previamente guardados y se recupera el dato local. El aviso `PLAN B` muestra la antigüedad de `obtenido_en`. Esa fecha no cambia al leer el respaldo. Si nunca hubo una consulta exitosa, se informa que no hay datos locales. Los datos recuperados no se vuelven a enviar como nuevos a Supabase.

Necesito internet para iniciar sesión. Si la conexión se corta después, la sesión permanece en memoria y el menú ofrece 7, 8 y 0. Al recuperar Supabase se comprueba otra vez la cuenta. Una revocación remota no puede detectarse mientras está desconectado. No hay login sin conexión ni sincronización automática de escrituras remotas pendientes.

## Persistencia y seguridad

Las consultas usan parámetros separados del SQL: `%s` con Psycopg y `?` con SQLite. Supabase conserva una fila por coordenadas y fecha meteorológica para clima, y una por fecha para dólar. Una consulta repetida actualiza la fila; una observación con otra fecha es un registro distinto.

`fecha_clima` y la fecha del dólar describen el dato externo. `obtenido_en` registra cuándo lo recibió el programa, en UTC. Si falla la confirmación remota, se informa que el guardado no se confirmó; no se asegura que haya fallado antes de llegar al servidor.

Los repositorios remotos dejan el commit o rollback al bloque que abrió la conexión. Las operaciones E3 tienen límites de ejecución y bloqueo en PostgreSQL. Esos límites no garantizan una detección inmediata de todo corte de red. `sslmode=require` cifra la conexión PostgreSQL; no equivale a verificar completamente el certificado con `verify-full`.

## Pruebas

Sin Supabase:

```powershell
python main.py --verificar-local
```

Con Supabase:

```powershell
python main.py --verificar
```

El 18 de noviembre pasaron 15 pruebas locales y 17 al incluir integración. Cubren dominio, Argon2, permisos, informes, conversión, validación, reintentos, respaldo del dólar y rollback. La integración utiliza datos temporales y los revierte o limpia; los números de secuencia pueden avanzar aunque una transacción se revierta.

También se verificaron ambos guardados E3 sin duplicados, el formato Argon2id en la base y un endpoint real inexistente de Open-Meteo: respondió 404 y no se reintentó. En mi equipo comprobé las opciones 7 y 8, el corte de Ethernet durante la sesión, el Plan B y la recuperación del menú al reconectar.

Para repetir la prueba manual, consulto y guardo primero con internet, dejo la sesión abierta, desconecto la red y vuelvo a elegir 7 u 8. Debe mostrar datos anteriores y su antigüedad. Reconecto al terminar.

Para revisar duplicados en el SQL Editor de Supabase:

```sql
SELECT latitud, longitud, fecha_clima, COUNT(*)
FROM ecotech.clima
GROUP BY latitud, longitud, fecha_clima
HAVING COUNT(*) > 1;

SELECT fecha, COUNT(*)
FROM ecotech.indicador_dolar
GROUP BY fecha
HAVING COUNT(*) > 1;
```

Ninguna consulta debe devolver filas. Para revisar usuarios, basta comprobar en Supabase que `contrasena_hash` empiece por `$argon2id$`; no comparto la contraseña ni el hash completo.

## Archivos principales

- `main.py`: login, menú y comandos de inicialización y pruebas.
- `servicios.py`: sesiones, roles y acceso a servicios externos.
- `api_cliente.py`: peticiones HTTP, errores y reintentos compartidos.
- `deserializador_clima.py` y `deserializador_dolar.py`: validación de respuestas.
- `dominio/`: objetos y reglas del sistema, incluidos clima, dólar y cuentas.
- `repositorio/`: acceso a PostgreSQL y respaldos SQLite.
- `menu_clima.py` y `menu_indicadores.py`: presentación de las consultas.
- `verificaciones.py` y `verificaciones_indicadores.py`: pruebas automáticas.
- `bitacora_ia.md`: registro de apoyo de IA y decisiones técnicas.

## Entrega

Entrego el enlace a [mi rama e3/munoz](https://github.com/Inacap2026-POOS-AM/EcoTech-Munoz-SanMartin-Ramirez/tree/e3/munoz). No fusiono a `main` mientras se realizan las evaluaciones individuales.
