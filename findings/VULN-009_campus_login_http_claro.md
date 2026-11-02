# VULN-009 — Login del Campus Virtual servido por HTTP en claro (sin forzado de HTTPS)
## `campus.uns.edu.pe` — Universidad Nacional del Santa

---

| Campo | Detalle |
|-------|---------|
| **ID** | VULN-009 |
| **Severidad** | 🟠 Alta |
| **CVSS v3.1 Score** | **7.4** |
| **Vector CVSS** | `CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:N` |
| **OWASP Top 10 - 2021** | A02 – Cryptographic Failures |
| **WSTG ID** | WSTG-CONF-06, WSTG-CRYP-03 |
| **CWE** | CWE-319 (Cleartext Transmission of Sensitive Information) |
| **Sistema Afectado** | `campus.uns.edu.pe` — Campus Virtual (Moodle LMS) |
| **URL Afectada** | `http://campus.uns.edu.pe/login/index.php` |
| **Fecha de descubrimiento** | 2026-10-11 |

---

## 1. Descripción

El **Campus Virtual de la UNS** (`campus.uns.edu.pe`, plataforma **Moodle** — título de página: *"Entrar al sitio | CV-UNS"*) **no redirige las peticiones HTTP hacia HTTPS**. Al acceder por `http://campus.uns.edu.pe/login/index.php`, el servidor responde con **HTTP 200 en texto claro**, entregando la página completa de login sin cifrar.

Aunque el `<form action>` del login apunta a `https://campus.uns.edu.pe/login/index.php` (las credenciales se POSTean por HTTPS), la **integridad de la página no está protegida**: un atacante en posición MitM puede reescribir la página servida por HTTP y cambiar el `action` del formulario a un servidor controlado por él (ataque de **SSL Stripping**).

Agravante: el sistema **no implementa HSTS** (ver VULN-010), por lo que el navegador nunca "recordará" que debe usar HTTPS y el usuario que escriba `campus.uns.edu.pe` (sin protocolo) puede ser servido en claro.

## 2. Evidencia Real

```
[Herramienta: verify_soft404.py / security_headers_audit.py — 2026-10-11]

GET http://campus.uns.edu.pe/login/index.php HTTP/1.1
Host: campus.uns.edu.pe

HTTP/1.1 200 OK              ← PÁGINA DE LOGIN POR HTTP EN CLARO (sin 301/302)
Content-Type: text/html; charset=utf-8
[Sin Strict-Transport-Security]

<form ... action="https://campus.uns.edu.pe/login/index.php" ...>
```

| Verificación | Resultado |
|--------------|-----------|
| `http://campus.uns.edu.pe/login/index.php` | **200 OK en claro** — sin redirección |
| `https://campus.uns.edu.pe/login/index.php` | 200 OK (Moodle "Entrar al sitio | CV-UNS") |
| Redirección HTTP → HTTPS | ❌ **NO** |
| Header HSTS | ❌ Ausente |

## 3. Escenarios de Ataque

**Escenario A — SSL Stripping en Wi-Fi universitaria:**
1. Estudiante en la red Wi-Fi de la UNS (cafetería, biblioteca, aula) escribe `campus.uns.edu.pe`.
2. El atacante en la misma red responde la petición HTTP en claro con una copia del login cuyo `<form action>` apunta a `http://atacante.com/robar`.
3. El estudiante ingresa sus credenciales institucionales → el atacante las recibe en claro y las reenvía al Moodle real (ataque transparente).

**Escenario B — Inyección de contenido:** el atacante modifica la página servida por HTTP para inyectar JavaScript que capture el `keypress` de usuario/contraseña antes del POST.

## 4. Impacto

- **Confidencialidad**: Alto — credenciales institucionales de estudiantes y docentes transitable/interceptable.
- **Integridad**: Alto — la página de login puede ser modificada en tránsito (phishing transparente).
- **Datos en riesgo**: credenciales de acceso al Campus Virtual (Ley 29733 — datos personales).

## 5. Remediación

### Corrección inmediata (Quick Fix)
Redirigir todo el tráfico HTTP a HTTPS en el reverse proxy OpenResty central (IP 190.119.171.165):

```nginx
server {
    listen 80;
    server_name campus.uns.edu.pe;
    return 301 https://$host$request_uri;
}
```

### Corrección definitiva
1. Forzar HTTPS a nivel de aplicación (`$CFG->sslproxy` / `wwwroot` con `https://` en `config.php` de Moodle).
2. Activar HSTS (ver VULN-010): `add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;`
3. Considerar precarga HSTS (hstspreload.org) para el dominio `uns.edu.pe`.

### Verificación post-parche
```bash
curl -I http://campus.uns.edu.pe/login/index.php
→ HTTP/1.1 301 Moved Permanently
→ Location: https://campus.uns.edu.pe/login/index.php   ✅
```

## 6. Referencias

- [OWASP WSTG-CONF-06: Test HTTP Strict Transport Security](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/07-Test_HTTP_Strict_Transport_Security)
- [CWE-319: Cleartext Transmission of Sensitive Information](https://cwe.mitre.org/data/definitions/319.html)
- [Mozilla — HSTS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security)
