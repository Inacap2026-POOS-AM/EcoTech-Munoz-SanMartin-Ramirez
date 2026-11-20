# Dependencias comprobadas · 20 de noviembre de 2026

Cada nombre de requirements.txt corresponde a un proyecto existente en PyPI. La existencia se contrastó con las páginas oficiales siguientes; las versiones instaladas y ejecutadas están en requirements.lock.txt y evidencias/auditoria_estatica.json.

| Paquete | Uso | Registro oficial |
| --- | --- | --- |
| cryptography | Argon2id con sal y cifrado Fernet de campos recuperables. | https://pypi.org/project/cryptography/ |
| reportlab | Exportación de informes PDF. | https://pypi.org/project/reportlab/ |
| openpyxl | Exportación y lectura de Excel. | https://pypi.org/project/openpyxl/ |
| pypdf | Lectura del PDF para comprobar su contenido en las pruebas. | https://pypi.org/project/pypdf/ |

urllib, json, logging, sqlite3, dataclasses y unittest pertenecen a la biblioteca estándar y no se agregan como paquetes PyPI. El hash de contraseñas es Argon2id de cryptography; no se sustituye por cifrado reversible. No se necesita requests para el cliente HTTP basado en urllib.
