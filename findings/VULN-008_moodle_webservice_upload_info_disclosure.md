# VULN-008 — Moodle: API de Upload Responde HTTP 200 sin Autenticación (Divulgación de Información)

| Campo              | Valor                                                                                      |
|--------------------|--------------------------------------------------------------------------------------------|
| **ID**             | VULN-008                                                                                   |
| **Objetivo**       | `campus.uns.edu.pe`                                                                        |
| **Componente**     | Moodle LMS — endpoint `/webservice/upload.php`                                             |
| **Clasificación**  | `EXPOSICION_INFO` / `CONFIGURACION_DEBIL`                                                  |
| **CVSS 3.1**       | 5.3 (Media) — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N`                             |
| **Fecha detectado**| 2026-10-25                                                                                 |
| **Método**         | Prueba manual no destructiva — caja negra                                                  |
| **Estado**         | `CONFIRMADO` (evidencia reproducible)                                                      |

---

## Descripción

El endpoint `/webservice/upload.php` del LMS Moodle devuelve **HTTP 200** ante una
solicitud `POST` no autenticada, junto con un cuerpo JSON que revela información
interna del servidor:

- El nombre exacto del parámetro esperado (`token`).
- El código de error interno de Moodle (`missingparam`).
- Los campos de la respuesta de error (`stacktrace`, `debuginfo`, `reproductionlink`).

Este comportamiento difiere de un error `401 Unauthorized` o `403 Forbidden`, lo que
facilita la enumeración de la API y proporciona una "huella" de la versión y
configuración del servicio web a un atacante no autenticado.

---

## Solicitud y Respuesta (Evidencia Reproducible)

**Solicitud:**
```http
POST /webservice/upload.php HTTP/1.1
Host: campus.uns.edu.pe
Content-Type: multipart/form-data

[archivo: audit_probe.txt — contenido: "AUDIT-PROBE-SAFE"]
```

**Respuesta:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "error": "Un parámetro necesario (token) faltaba",
  "errorcode": "missingparam",
  "stacktrace": null,
  "debuginfo": null,
  "reproductionlink": null
}
```

**Estado de restauración:** No se creó ningún recurso. El servidor rechazó la
operación a nivel de lógica de negocio (token faltante), confirmando que el
endpoint **no permite escritura sin autenticación**. Sin embargo, revela información de la API.

---

## Función de Escritura Identificada y Permisos

| Función                  | URL                             | Permisos requeridos              | Operación                            |
|--------------------------|---------------------------------|----------------------------------|--------------------------------------|
| Upload API REST          | `/webservice/upload.php` (POST) | `wstoken` válido (API token)     | Subida de archivos al repositorio    |
| Repositorio de usuario   | `/user/files.php` (GET)         | Sesión autenticada               | Gestión de archivos personales       |
| Archivos en borrador     | `/draftfile.php` (GET)          | Sesión autenticada               | Acceso a archivos temporales         |
| Upload cursos (admin)    | `/admin/tool/uploadcourse/`     | Sesión de administrador          | Importación masiva de cursos         |
| Upload usuarios (admin)  | `/admin/tool/uploaduser/`       | Sesión de administrador          | Importación masiva de usuarios       |

---

## Alcance de Permisos Verificados (Sin Autenticación)

| Operación                              | Resultado sin autenticación    | Estado     |
|----------------------------------------|--------------------------------|------------|
| GET `/user/files.php`                  | HTTP 303 → login               | ✅ Correcto |
| GET `/draftfile.php`                   | HTTP 303 → login               | ✅ Correcto |
| POST `/webservice/upload.php`          | HTTP 200 + JSON de error       | ⚠️ Débil   |
| GET `/admin/tool/uploadcourse/`        | HTTP 303 → login               | ✅ Correcto |
| PUT `sigea.uns.edu.pe/*` (arbitrario)  | Error de conexión              | ✅ Sin escritura |

---

## Riesgo

El endpoint devuelve HTTP 200 en lugar de 401/403, lo que:
1. Confirma que el servicio web de Moodle está **habilitado y activo**.
2. Expone el nombre del parámetro de autenticación (`token`), facilitando enumeración de tokens.
3. En versiones antiguas, `debuginfo` puede incluir rutas del sistema de archivos del servidor.

---

## Recomendación

1. Configurar Moodle para responder con **HTTP 401** cuando falte el token en la API REST.
2. Desactivar el servicio web REST si no está en uso: *Admin → Complementos → Servicios Web → Gestionar protocolos*.
3. Verificar que `$CFG->enablewebservices` esté en `false` si no se usa la API externamente.
4. Revisar si `debuginfo` o `stacktrace` revelan rutas de sistema en producción.

---

## Referencias

- [Moodle Security — Web Services](https://docs.moodle.org/en/Web_services_security)
- [WSTG-CONF-05: Enumerate Infrastructure and Application Admin Interfaces](https://owasp.org/www-project-web-security-testing-guide/)
