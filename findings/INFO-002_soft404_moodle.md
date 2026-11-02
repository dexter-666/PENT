# INFO-002 — Comportamiento Soft-404 en campus.uns.edu.pe (Moodle) y Lección Metodológica
## Universidad Nacional del Santa

---

| Campo | Detalle |
|-------|---------|
| **ID** | INFO-002 |
| **Severidad** | ⚪ Informativa |
| **WSTG ID** | WSTG-CONF-04, WSTG-INFO-04 |
| **Sistema** | `campus.uns.edu.pe` — Campus Virtual (Moodle LMS) |
| **Fecha** | 2026-10-11 |

---

## 1. Hallazgo: Soft-404 generalizado

Moodle, detrás del reverse proxy OpenResty, **responde HTTP 200 con la página principal** ("Página Principal | CV-UNS", 36,664 bytes) para **cualquier ruta inexistente**, en lugar de un `404 Not Found`:

```
GET /.git/config      → 200 OK  (36,664 B) "Página Principal | CV-UNS"
GET /backup.sql       → 200 OK  (36,664 B) "Página Principal | CV-UNS"
GET /phpmyadmin/      → 200 OK  (36,664 B) "Página Principal | CV-UNS"
GET /actuator         → 200 OK  (36,664 B) "Página Principal | CV-UNS"
GET /swagger-ui/      → 200 OK  (36,664 B) "Página Principal | CV-UNS"
GET /robots.txt       → 200 OK  (36,664 B) "Página Principal | CV-UNS"  ← ¡robots.txt no existe realmente!
GET /sitemap.xml      → 200 OK  (36,664 B) "Página Principal | CV-UNS"
```

**Validación realizada** (`tools/verify_soft404.py`): se comparó el hash MD5 y la longitud del contenido de 49 rutas marcadas como "HIGH" por el scanner. **Todas** devolvieron la misma página principal → **48 de 49 hallazgos del scanner fueron FALSOS POSITIVOS**.

### Hallazgos válidos tras la validación

| Ruta | Status | Conclusión |
|------|--------|------------|
| `/backup/` | 403 | Existe pero protegido (requiere autenticación) — no explotable |
| `/.htaccess` | 403 | Protegido por el proxy |
| `/security.txt` | 200 (670 B) | ⚠️ Es el `security.txt` **genérico de Moodle HQ** (apunta a `moodle.org/security/report`), **NO** tiene el contacto de seguridad institucional de la UNS |
| `/robots.txt` | 200 (soft-404) | No existe un robots.txt real — no revela rutas, pero tampoco restringe crawlers |
| Resto (45 rutas) | 200 (soft-404) | **Falsos positivos** — no expuestos |

### Impacto del soft-404
- **Para atacantes**: dificulta el mapeo de contenido (no distingue 200 real de 200 genérico) — efecto mixto.
- **Para la UNS**: contamina logs/analytics y puede enmascarar errores reales de configuración.
- **Para el equipo de auditoría**: cualquier scanner debe validar por **contenido** (hash/título), no solo por código de estado.

## 2. Lección metodológica (incluir en tesis)

> **Regla**: un HTTP 200 **no** implica exposición. En aplicaciones con soft-404 (Moodle, WordPress con ciertos themes, SPA), el scanner debe:
> 1. Descargar una página de referencia (login/home).
> 2. Comparar hash MD5 + longitud + `<title>` de cada respuesta 200.
> 3. Confirmar contenido específico (patrones como `ref: refs/` para `.git/HEAD`, `phpinfo()` para phpinfo).
>
> Sin esta validación, el reporte de la tesis habría incluido **48 hallazgos "críticos" inexistentes** (`.git`, `.env`, backups, phpmyadmin, swagger, actuator...), lo que habría invalidado la credibilidad del informe.

Herramienta desarrollada para la tesis: `tools/verify_soft404.py` (anti-falsos positivos).

## 3. Recomendaciones

1. **Institucionalizar `security.txt`** con contacto real de seguridad de la UNS (equipo de TI / CERT interno) en `https://campus.uns.edu.pe/.well-known/security.txt`.
2. Crear un `robots.txt` real que restrinja rutas administrativas de Moodle (`/admin/`, `/login/`, etc.).
3. (Opcional) Configurar OpenResty para devolver `404` real en rutas inexistentes, mejorando telemetría y escaneos futuros.

## 4. Referencias

- [RFC 9116 — security.txt](https://www.rfc-editor.org/rfc/rfc9116)
- [OWASP WSTG-INFO-04: Review Old Backup and Unreferenced Files](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/04-Review_Old_Backup_and_Unreferenced_Files_for_Sensitive_Information)
- [Moodle security.txt por defecto](https://moodle.org/security/report/)
