# VULN-010 — Cabeceras de Seguridad HTTP Parciales en Campus Virtual (Score 44/100, Grado D)
## `campus.uns.edu.pe` — Universidad Nacional del Santa

---

| Campo | Detalle |
|-------|---------|
| **ID** | VULN-010 |
| **Severidad** | 🟡 Media |
| **CVSS v3.1 Score** | **6.1** |
| **Vector CVSS** | `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N` |
| **OWASP Top 10 - 2021** | A05 – Security Misconfiguration |
| **WSTG ID** | WSTG-CONF-06, WSTG-CONF-07, WSTG-SESS-02 |
| **CWE** | CWE-693 (Protection Mechanism Failure), CWE-1021 |
| **Sistema Afectado** | `campus.uns.edu.pe` — Campus Virtual (Moodle LMS) |
| **Fecha de descubrimiento** | 2026-10-11 |

---

## 1. Descripción

El Campus Virtual obtuvo **44/100 (Grado D)** en la auditoría de cabeceras de seguridad. Implementa `X-Frame-Options: sameorigin` (protección básica anti-clickjacking de Moodle) y no expone `X-Powered-By` ni versión en el header `Server` (`openresty` sin versión — buena práctica), pero **carece de 5 de las 6 cabeceras de protección estándar**:

| Cabecera | Estado | Ataque que previene |
|----------|--------|---------------------|
| `Strict-Transport-Security` | ❌ AUSENTE | SSL Stripping, MitM (agrava VULN-009) |
| `Content-Security-Policy` | ❌ AUSENTE | XSS, inyección de contenido |
| `X-Frame-Options` | ✅ `sameorigin` | Clickjacking (parcial — `DENY` sería más restrictivo) |
| `X-Content-Type-Options` | ❌ AUSENTE | MIME sniffing |
| `Referrer-Policy` | ❌ AUSENTE | Filtración de URLs/tokens vía Referer |
| `Permissions-Policy` | ❌ AUSENTE | Abuso de APIs del navegador |

**Cookie de sesión** (`MoodleSession`): incluye `Secure` y `HttpOnly` ✅, pero **no lleva atributo `SameSite`** (Moodle < 4.x), lo que reduce la protección contra CSRF en navegadores modernos.

## 2. Evidencia Real

```
[Herramienta: security_headers_audit.py — 2026-10-11 01:03]

--- https://campus.uns.edu.pe ---
  ❌ FALTANTE   Strict-Transport-Security
  ❌ FALTANTE   Content-Security-Policy
  ✅ OK         X-Frame-Options: sameorigin
  ❌ FALTANTE   X-Content-Type-Options
  ❌ FALTANTE   Referrer-Policy
  ❌ FALTANTE   Permissions-Policy
  ✅ AUSENTE (correcto)  X-Powered-By
  ✅ AUSENTE (correcto)  Server: openresty (sin versión)
  ✅ No se detectaron métodos HTTP peligrosos (PUT/DELETE/TRACE → 405)

  📊 Puntuación: 44/100 | Grado: D

Set-Cookie: MoodleSession=7nqo9hcv013pt8t0m5hteq86cb; path=/; secure; HttpOnly
            [Sin SameSite]
```

## 3. Escenarios de Ataque

- **XSS sin CSP**: si algún plugin de Moodle (tema `academi`, actividades, filtros) presenta un XSS almacenado/reflejado, no existe CSP que bloquee la ejecución del script en el navegador de miles de estudiantes.
- **Clickjacking parcial**: `sameorigin` permite embeber el campus virtual desde páginas del mismo dominio; `DENY` sería más seguro para una pantalla de login.
- **MIME sniffing**: sin `nosniff`, recursos subidos por usuarios (archivos de curso) pueden ser interpretados como HTML/JS.
- **Filtración por Referer**: navegación desde el campus hacia enlaces externos puede filtrar URLs con tokens (`sesskey`, `id`).

## 4. Remediación

Agregar en el bloque del servidor (OpenResty/Nginx) del campus virtual:

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; frame-src 'self'" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;
```

En Moodle (`config.php`), habilitar SameSite en cookies:
```php
$CFG->cookiesamesite = "Strict";   // Moodle 3.11+ / 4.x
```

**Validación**: https://securityheaders.com/?q=campus.uns.edu.pe → objetivo grado **A/A+**.

## 5. Referencias

- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [OWASP WSTG-CONF-07](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/07-Test_HTTP_Strict_Transport_Security)
- [Moodle docs: cookiesamesite](https://docs.moodle.org/en/config.php)
