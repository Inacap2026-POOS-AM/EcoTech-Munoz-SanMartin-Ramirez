# Recorrido para defender ES3

## Demostración reproducible sin Internet

Desde BRAMIREZ con el entorno activado:

```sh
python -m unittest -v
python auditar_seguridad.py
python demostracion_es3.py
```

La demostración usa una base temporal y respuestas sintéticas. Dos vueltas conservan dos filas. Después fuerza caída de red, 404, 429 y 503; muestra el respaldo y su antigüedad. El 429 largo permite una sola petición nueva y bloquea la siguiente durante la misma sesión. El log conserva los intentos y las esperas. No se presenta 950 como una cotización real.

## Demostración con servicios reales

```sh
python verificar_api_real.py
```

evidencias/api_real.json conserva las respuestas seleccionadas de la verificación del 20 de noviembre. Este script se puede repetir cuando haya red, sujeto a la disponibilidad y límites del proveedor. No hace falta una clave externa para la ruta pública. La opción WeatherAPI requiere una clave privada y no se afirma una verificación real de esa alternativa.

## Preguntas que debo responder con el código abierto

- ¿Dónde se separa JSON del dominio? Deserializador.clima y cambio construyen objetos propios; a_dict se usa solo para salida o persistencia.
- ¿Qué hace el timeout? Limita operaciones de socket; no incluye todo el tiempo acumulado de reintentos.
- ¿Por qué no se reintenta un 404? Es un rechazo definitivo. Los fallos de red y 5xx sí pueden ser transitorios.
- ¿Qué pasa con 429? Se respeta Retry-After. Una espera larga utiliza el respaldo y conserva el bloqueo del proveedor mientras sigue la misma sesión.
- ¿Qué ocurre al reiniciar? La caché SQLite permanece; el bloqueo de rate limit en memoria no se conserva. Es una limitación declarada.
- ¿Qué pasa si no existe respaldo? Se muestra un error de negocio y el menú conserva el control; no se inventan datos.
- ¿Cómo evito duplicados? UPSERT con clave primaria por consulta.
- ¿Qué diferencia hash y cifrado? Argon2id verifica la contraseña sin recuperarla; Fernet recupera campos autorizados como el RUT opcional.
- ¿Cómo valido el RUT? Formato y módulo 11; no se acredita identidad ni existencia real.
- ¿Cómo sé que el log no filtra una clave? La prueba usa una clave sintética en URL y excepciones y comprueba que no quede en el registro.

La captura de consola y los registros muestran ejecuciones reales. Comprender y exponer esta solución sigue siendo una actividad individual, no una defensa ya realizada. El enlace GitHub individual está pendiente de publicación autorizada; el repositorio compartido no se modifica.
