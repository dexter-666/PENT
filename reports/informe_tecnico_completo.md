# INFORME TÉCNICO DE PENETRATION TESTING
## Auditoría de Seguridad Web — Universidad Nacional del Santa (UNS)
### 2026 — CONFIDENCIAL — Uso Técnico Restringido

---

> **Clasificación**: CONFIDENCIAL — Uso exclusivo del equipo técnico de TI y autoridades universitarias
> **Preparado por**: [Nombre del Tesista] | Escuela de [Ingeniería de Sistemas / Computación]
> **Metodología**: OWASP WSTG v4.2 + PTES
> **Herramientas Propias**: recon_subdomains.py · security_headers_audit.py · sensitive_files_scanner.py
> **Periodo de evaluación**: Septiembre 2026
> **Versión**: 1.0

---

## 1. Introducción

### 1.1 Objetivo
El presente informe documenta los resultados de la auditoría de seguridad web realizada sobre la infraestructura digital de la Universidad Nacional del Santa (UNS), con foco en el sistema **SIIGAA** (`registro.uns.edu.pe`) y el ecosistema completo de subdominios universitarios.

### 1.2 Alcance — Subdominios Auditados

**Origen de descubrimiento**: OSINT pasivo vía hackertarget.com (Certificate Transparency + DNS)

| # | Subdominio | IP | HTTP | HTTPS | Servidor |
|---|-----------|-----|------|-------|---------|
| 1 | `biblioteca.uns.edu.pe` | 190.119.171.165 | 200 | 200 | OpenResty |
| 2 | `campus.uns.edu.pe` | 190.119.171.165 | 200 | 200 | OpenResty |
| 3 | `cecomp.uns.edu.pe` | 190.119.171.165 | 200 | 200 | OpenResty |
| 4 | `cepuns.uns.edu.pe` | 190.119.171.165 | 200 | 200 | OpenResty |
| 5 | `cspf.uns.edu.pe` | 190.119.171.165 | 502 | 502 | OpenResty |
| 6 | `hpda.uns.edu.pe` | 190.119.171.165 | 200 | 200 | OpenResty |
| 7 | `incuba.uns.edu.pe` | 190.119.171.165 | 200 | 200 | OpenResty |
| 8 | `marcaciones.uns.edu.pe` | 190.119.171.165 | 200 | 200 | OpenResty |
| 9 | `noradx.uns.edu.pe` | 190.119.171.165 | 502 | --- | OpenResty |
| 10 | `onvsw.uns.edu.pe` | 190.119.171.165 | 200 | 200 | OpenResty |
| 11 | `orcl.uns.edu.pe` | 190.119.171.165 | 200 | 200 | OpenResty |
| 12 | `posgrado.uns.edu.pe` | 190.119.171.165 | 200 | 200 | OpenResty |
| 13 | `pruebas.uns.edu.pe` | 190.119.171.170 | --- | --- | Sin resp. |
| 14 | `pure.uns.edu.pe` | 104.18.39.240 | 200 | 200 | Cloudflare |
| 15 | `registro.uns.edu.pe` | 190.119.171.166 | --- | 200 | (oculto) |
| 16 | `repositorio.uns.edu.pe` | 190.119.171.167 | --- | --- | Sin resp. |
| 17 | `revistas.uns.edu.pe` | 190.119.171.165 | 200 | --- | OpenResty |
| 18 | `sgpi.uns.edu.pe` | 190.119.171.165 | 502 | --- | OpenResty |
| 19 | `sigea.uns.edu.pe` | 190.119.171.165 | 200 | 200 | OpenResty |
| 20 | `sistemas.uns.edu.pe` | 190.119.171.165 | 404 | 404 | (oculto) |
| 21 | `wmdb.uns.edu.pe` | 190.119.171.165 | 502 | 502 | OpenResty |
| 22 | `www.uns.edu.pe` | 190.119.171.172 | 200 | 200 | Apache |

**Observación de infraestructura**: La mayoría de subdominios comparten la IP `190.119.171.165` detrás de un **OpenResty** (Nginx + Lua) que actúa como reverse proxy centralizado. Esto es relevante porque una sola vulnerabilidad en el proxy puede afectar múltiples sistemas.

---

## 2. Resumen de Hallazgos

| ID | Vulnerabilidad | Sistema Afectado | Severidad | CVSS |
|----|---------------|-----------------|-----------|------|
| VULN-001 | Divulgación de PHP 7.1.33 EOL en Header (Hipótesis RCE No Confirmada) | `sigea.uns.edu.pe` | 🟡 Media | 5.3 |
| VULN-002 | Sin HTTPS forzado — HTTP no redirige a HTTPS | `registro.uns.edu.pe` | 🔴 Alta | 7.4 |
| VULN-003 | Consola de servidor `/console` accesible (302 → noredirect.html) | `registro.uns.edu.pe` | 🟠 Media-Alta | 6.5 |
| VULN-004 | Ausencia total de cabeceras de seguridad HTTP (0/100) | `revistas.uns.edu.pe`, `sgpi.uns.edu.pe` | 🟠 Alta | 7.2 |
| VULN-005 | Sin cabeceras de seguridad en SIIGAA — vulnerable a Clickjacking | `registro.uns.edu.pe` | 🟠 Media | 6.1 |
| VULN-006 | [Falso Positivo Descartado] Métodos HTTP PUT/DELETE bloqueados (405) | `sigea.uns.edu.pe`, `pure.uns.edu.pe` | ⚪ Descartado | — |
| VULN-007 | Sin HTTP Strict-Transport-Security (HSTS) en 16/20 sistemas | Múltiples | 🟡 Media | 5.9 |
| VULN-008 | Sin Content-Security-Policy en 18/20 sistemas | Múltiples | 🟡 Media | 5.4 |
| VULN-009 | Login del Campus Virtual (Moodle) servido por HTTP en claro, sin redirección a HTTPS | `campus.uns.edu.pe` | 🟠 Alta | 7.4 |
| VULN-010 | Cabeceras de seguridad parciales (44/100, Grado D) — sin HSTS, CSP, X-Content-Type-Options, Referrer-Policy, Permissions-Policy; cookie sin SameSite | `campus.uns.edu.pe` | 🟡 Media | 6.1 |
| INFO-001 | Infraestructura en servidor único (SPOF) — OpenResty 190.119.171.165 | Infraestructura | ⚪ Info | — |
| INFO-002 | Soft-404 generalizado en Moodle (200 para rutas inexistentes) — 48 falsos positivos del scanner descartados por validación de contenido | `campus.uns.edu.pe` | ⚪ Info | — |

---

## 3. Hallazgos Detallados

---

### VULN-001 — Divulgación de Componente EOL (PHP 7.1.33) en Header HTTP

| Campo | Detalle |
|-------|---------|
| **Severidad** | 🟡 Media |
| **CVSS v3.1** | **5.3** (Justificado sobre evidencia confirmada) |
| **Vector CVSS** | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` |
| **OWASP Top 10** | A06 – Vulnerable and Outdated Components |
| **WSTG ID** | WSTG-INFO-02, WSTG-CONF-05 |
| **CWE** | CWE-200, CWE-1104 |
| **URL Afectada** | `https://sigea.uns.edu.pe` |

#### Descripción Técnica
El sistema **SIGEA** expone en el header HTTP de respuesta la versión exacta de PHP utilizada: `X-Powered-By: PHP/7.1.33`. PHP 7.1 alcanzó su **End of Life (EOL) en Diciembre 2019**, lo que significa que lleva más de **6 años sin recibir parches de seguridad**.

> [!IMPORTANT]
> **Criterio de Evaluación y Separación de Hipótesis:**
> La severidad base de este hallazgo se evalúa estrictamente en **5.3 (Media)** por la divulgación de información tecnológica sin soporte. No se le asigna severidad crítica (9.8 ni 7.5) únicamente por la antigüedad de PHP. La posibilidad de Ejecución Remota de Código (RCE vía CVE-2019-11043) se cataloga como **Hipótesis No Confirmada**, debido a la limitación metodológica de auditoría de caja negra (la comprobación de la regex de `fastcgi_split_path_info` requiere inspección interna de `nginx.conf` o exploits intrusivos no autorizados).

> [!NOTE]
> **Ajuste metodológico tras verificación manual:** El scanner automatizado inicial reportó métodos `PUT` y `DELETE` respondiendo `200 OK`. Las pruebas empíricas no destructivas confirmaron que el servidor responde con **`HTTP 405 Method Not Allowed`**, descartando la posibilidad de manipulación o borrado de archivos por métodos HTTP no autorizados.

#### Evidencia — Respuesta HTTP y Ruteo FastCGI Observado
```http
GET / HTTP/1.1
Host: sigea.uns.edu.pe

HTTP/1.1 200 OK
X-Powered-By: PHP/7.1.33      ← VERSIÓN EOL EXPUESTA (+6 años sin parches)
Server: openresty             ← Reverse proxy / Web server Nginx+Lua
Strict-Transport-Security: max-age=63072000; preload
[Sin X-Frame-Options, Sin CSP, Sin X-Content-Type-Options]
```

```http
# Comprobación de ruteo FastCGI hacia el framework PHP:
GET /index.php/test_path_info HTTP/1.1
Host: sigea.uns.edu.pe

HTTP/1.1 404 Page Not Found   (CodeIgniter Framework error page)
→ Confirma que OpenResty transfiere rutas a index.php en el backend.
```

```http
# Comprobación de Métodos HTTP:
PUT /test_probe_audit.txt HTTP/1.1
Host: sigea.uns.edu.pe

HTTP/1.1 405 Method Not Allowed   ← MÉTODO RECHAZADO CORRECTAMENTE (No explotable)
```

#### Impacto
- El fingerprinting público (`PHP/7.1.33`) permite a atacantes automatizados dirigir exploits diseñados específicamente para ramas sin parches.
- Al operar detrás de OpenResty (Nginx) con FastCGI, configuraciones sin validación de `fastcgi_split_path_info` exponen al proceso worker a sobreescritura de memoria y ejecución remota de código (CVE-2019-11043).

#### Remediación
1. **Inmediata**: Deshabilitar el header `X-Powered-By` en `php.ini`: `expose_php = Off` o en OpenResty: `more_clear_headers 'X-Powered-By';`.
2. **Urgente**: Actualizar el intérprete PHP a una versión con soporte de seguridad vigente (**PHP 8.2+ o superior**).
3. **Hardening en OpenResty/Nginx**: Añadir validación estricta antes de transferir peticiones al socket FastCGI:
```nginx
location ~ [^/]\.php(/|$) {
    fastcgi_split_path_info ^(.+?\.php)(/.*)$;
    try_files $fastcgi_script_name =404;   # Bloquea ataques tipo CVE-2019-11043
    fastcgi_pass unix:/var/run/php/php-fpm.sock;
    include fastcgi_params;
}
```

---

### VULN-002 — SIIGAA sin Forzado de HTTPS (HTTP en Claro)

| Campo | Detalle |
|-------|---------|
| **Severidad** | 🔴 Alta |
| **CVSS v3.1** | 7.4 |
| **Vector CVSS** | `CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:N` |
| **OWASP Top 10** | A02 – Cryptographic Failures |
| **WSTG ID** | WSTG-CRYP-03, WSTG-CONF-06 |
| **CWE** | CWE-319 |
| **URL Afectada** | `http://registro.uns.edu.pe` |

#### Descripción Técnica
El sistema **SIIGAA** (`registro.uns.edu.pe`) no redirige automáticamente las peticiones HTTP al protocolo seguro HTTPS. Si un estudiante accede vía `http://registro.uns.edu.pe`, sus credenciales de acceso (usuario y contraseña) son transmitidas en texto plano por la red.

Esto es especialmente crítico en entornos universitarios donde muchos usuarios se conectan desde redes Wi-Fi públicas o compartidas (cafetería, biblioteca, laboratorios) donde un atacante puede realizar un ataque **Man-in-the-Middle (MitM)** para interceptar las credenciales.

Adicionalmente, el sistema carece del header **HTTP Strict-Transport-Security (HSTS)**, lo que impide que el navegador recuerde que debe usar HTTPS y expone a los usuarios a ataques de **SSL Stripping**.

#### Evidencia
```http
# Petición HTTP sin cifrar:
GET /udemsi/faces/modulos.xhtml HTTP/1.1
Host: registro.uns.edu.pe
→ No hay redirección 301/302 a HTTPS

# Cabeceras de respuesta HTTPS — sin HSTS:
HTTP/1.1 200 OK
[Sin Strict-Transport-Security]
[Sin Content-Security-Policy]
[Sin X-Frame-Options]
[Sin X-Content-Type-Options]
```

#### Impacto
- Interceptación de credenciales académicas (usuario/contraseña) de estudiantes y docentes.
- Ataque de Clickjacking: la página puede ser embebida en un iframe malicioso para robar clics.
- Exposición de tokens de sesión.

#### Remediación
```nginx
# 1. Redireccionamiento HTTP → HTTPS permanente en Nginx/OpenResty:
server {
    listen 80;
    server_name registro.uns.edu.pe;
    return 301 https://$host$request_uri;
}

# 2. Agregar HSTS en el bloque HTTPS:
server {
    listen 443 ssl;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

---

### VULN-003 — Consola de Servidor de Aplicaciones Accesible

| Campo | Detalle |
|-------|---------|
| **Severidad** | 🟠 Media-Alta |
| **CVSS v3.1** | 6.5 |
| **OWASP Top 10** | A05 – Security Misconfiguration |
| **WSTG ID** | WSTG-CONF-02 |
| **CWE** | CWE-912 |
| **URL Afectada** | `https://registro.uns.edu.pe/console` |

#### Descripción Técnica
La ruta `/console` en el SIIGAA responde con un **HTTP 302** redireccionando a `/noredirect.html`, en lugar de un **404 Not Found**. Esto confirma que la ruta `/console` existe en el servidor de aplicaciones subyacente (consistente con Oracle WebLogic, Oracle GlassFish, o Oracle ADF — sistemas comúnmente usados con Java Faces como el SIIGAA que usa `faces/modulos.xhtml`).

La existencia de esta ruta, aunque actualmente protegida con una redirección, representa un riesgo porque:
1. Confirma el tipo de servidor de aplicaciones (facilita ataques dirigidos).
2. La protección por redirección puede eludirse con técnicas de path traversal o cambios de método HTTP.
3. Versiones antiguas de Oracle WebLogic tienen vulnerabilidades RCE críticas conocidas (CVE-2020-14882, CVE-2021-2109).

#### Evidencia
```http
GET /console HTTP/1.1
Host: registro.uns.edu.pe

HTTP/1.1 302 Found
Location: /noredirect.html    ← Confirma existencia de la ruta
```

#### Remediación
1. Si no se usa: Deshabilitar completamente el Admin Console en la configuración del servidor de aplicaciones.
2. Si se usa: Restringir acceso exclusivamente a IPs de red interna mediante regla de firewall.
3. Actualizar el servidor de aplicaciones a la versión más reciente con todos los parches de seguridad.

---

### VULN-004 — Ausencia Total de Cabeceras de Seguridad HTTP

| Campo | Detalle |
|-------|---------|
| **Severidad** | 🟠 Alta |
| **CVSS v3.1** | 7.2 |
| **OWASP Top 10** | A05 – Security Misconfiguration |
| **WSTG ID** | WSTG-CONF-07 |
| **Sistemas** | `revistas.uns.edu.pe` (0%), `sgpi.uns.edu.pe` (0%) |

#### Descripción Técnica
Los sistemas `revistas.uns.edu.pe` y `sgpi.uns.edu.pe` obtuvieron una puntuación de **0/100** en la auditoría de cabeceras de seguridad. No implementan ninguna de las siguientes protecciones básicas:

| Cabecera Faltante | Ataque que previene |
|------------------|---------------------|
| `Content-Security-Policy` | Cross-Site Scripting (XSS), inyección de contenido |
| `Strict-Transport-Security` | SSL Stripping, MitM |
| `X-Frame-Options` | Clickjacking |
| `X-Content-Type-Options` | MIME sniffing attacks |
| `Referrer-Policy` | Filtración de información sensible en URLs |

Adicionalmente, `revistas.uns.edu.pe` y `sgpi.uns.edu.pe` tampoco redirigen HTTP → HTTPS.

#### Remediación
Agregar al bloque de configuración del servidor (Nginx/OpenResty):
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

---

### VULN-009 — Login del Campus Virtual servido por HTTP en claro

| Campo | Detalle |
|-------|---------|
| **Severidad** | 🟠 Alta |
| **CVSS v3.1** | 7.4 |
| **Vector CVSS** | `CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:N` |
| **OWASP Top 10** | A02 – Cryptographic Failures |
| **WSTG ID** | WSTG-CONF-06, WSTG-CRYP-03 |
| **CWE** | CWE-319 |
| **URL Afectada** | `http://campus.uns.edu.pe/login/index.php` |

#### Descripción Técnica
El **Campus Virtual** (`campus.uns.edu.pe`, plataforma **Moodle LMS** — página "Entrar al sitio | CV-UNS") **no redirige HTTP a HTTPS**: `http://campus.uns.edu.pe/login/index.php` responde **200 OK en texto claro** entregando la página completa de login.

Aunque el `<form action>` del login apunta a `https://campus.uns.edu.pe/login/index.php`, la integridad de la página no está protegida: un atacante en posición MitM (ej. Wi-Fi universitaria) puede reescribir la página y cambiar el `action` del formulario a un servidor controlado (**SSL Stripping**). Agravante: no hay HSTS (VULN-010), por lo que el navegador no fuerza HTTPS.

#### Evidencia
```http
GET http://campus.uns.edu.pe/login/index.php HTTP/1.1
Host: campus.uns.edu.pe

HTTP/1.1 200 OK              ← LOGIN POR HTTP EN CLARO (sin 301/302)
Content-Type: text/html; charset=utf-8

<form ... action="https://campus.uns.edu.pe/login/index.php" ...>
```

#### Impacto
- Interceptación de credenciales institucionales (estudiantes/docentes) vía SSL stripping.
- Modificación de la página de login en tránsito (phishing transparente).
- Datos en riesgo: credenciales (Ley 29733).

#### Remediación
```nginx
server {
    listen 80;
    server_name campus.uns.edu.pe;
    return 301 https://$host$request_uri;
}
# Más HSTS en el bloque HTTPS (ver VULN-010) y $CFG->wwwroot con https:// en config.php de Moodle
```

---

### VULN-010 — Cabeceras de Seguridad Parciales en Campus Virtual (44/100, Grado D)

| Campo | Detalle |
|-------|---------|
| **Severidad** | 🟡 Media |
| **CVSS v3.1** | 6.1 |
| **Vector CVSS** | `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N` |
| **OWASP Top 10** | A05 – Security Misconfiguration |
| **WSTG ID** | WSTG-CONF-06, WSTG-CONF-07, WSTG-SESS-02 |
| **CWE** | CWE-693, CWE-1021 |
| **Sistema** | `campus.uns.edu.pe` |

#### Descripción Técnica
El Campus Virtual implementa `X-Frame-Options: sameorigin` y oculta `X-Powered-By`/versión de `Server` (`openresty` sin versión — buena práctica), pero **carece de 5 de 6 cabeceras de protección**: HSTS, CSP, X-Content-Type-Options, Referrer-Policy y Permissions-Policy. La cookie de sesión `MoodleSession` incluye `Secure` y `HttpOnly` pero **no `SameSite`** (protección CSRF reducida).

#### Evidencia
```http
HTTP/1.1 200 OK
X-Frame-Options: sameorigin
[Sin Strict-Transport-Security]
[Sin Content-Security-Policy]
[Sin X-Content-Type-Options]
[Sin Referrer-Policy]
[Sin Permissions-Policy]
Set-Cookie: MoodleSession=...; path=/; secure; HttpOnly   ← sin SameSite
📊 Puntuación: 44/100 | Grado: D
```

#### Remediación
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; frame-src 'self'" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;
```
En `config.php` de Moodle: `$CFG->cookiesamesite = "Strict";`

---

### INFO-002 — Soft-404 en campus.uns.edu.pe (lección metodológica)

Moodle responde **HTTP 200 con la página principal** ("Página Principal | CV-UNS", 36,664 bytes) para **cualquier ruta inexistente**. El scanner marcó 48 rutas como "HIGH" (`/.git/config`, `/backup.sql`, `/phpmyadmin/`, `/actuator`, `/swagger-ui/`, `/console`, `/error.log`, etc.), pero la validación con `tools/verify_soft404.py` (comparación de hash MD5 + longitud + `<title>`) demostró que **todas devuelven la misma página genérica → 48 FALSOS POSITIVOS**.

**Hallazgos válidos tras validación**:
- `/backup/` y `/.htaccess` → 403 (protegidos, no explotables).
- `/security.txt` → existe, pero es el genérico de Moodle HQ (apunta a `moodle.org`), sin contacto institucional de la UNS.
- No existe `robots.txt` real (el soft-404 lo simula).

**Lección para la tesis**: en aplicaciones con soft-404, un HTTP 200 no implica exposición; todo hallazgo debe validarse por **contenido**, no por código de estado. Sin esta validación, el informe habría reportado 48 vulnerabilidades "críticas" inexistentes.

**Recomendaciones**: publicar `/.well-known/security.txt` con contacto de seguridad UNS (RFC 9116); crear `robots.txt` real; (opcional) devolver 404 real en OpenResty.

---

## 4. Matriz de Puntuación de Seguridad — Cabeceras HTTP

| Sistema | Score | Grado | HSTS | CSP | X-Frame | XCT | HTTP→HTTPS |
|---------|-------|-------|------|-----|---------|-----|-----------|
| `pure.uns.edu.pe` | 100% | **A** | ✅ | ✅ | ✅ | ✅ | ✅ |
| `orcl.uns.edu.pe` | 89% | **B** | ✅ | ✅ | ✅ | ✅ | ✅ |
| `onvsw.uns.edu.pe` | 67% | **C** | ✅ | ❌ | ✅ | ✅ | ✅ |
| `sistemas.uns.edu.pe` | 67% | **C** | ❌ | ❌ | ✅ | ✅ | ✅ |
| `campus.uns.edu.pe` | 44% | **D** | ❌ | ❌ | ❌ | ❌ | ✅ |
| `cecomp.uns.edu.pe` | 44% | **D** | ❌ | ❌ | ❌ | ❌ | ✅ |
| `posgrado.uns.edu.pe` | 44% | **D** | ❌ | ❌ | ✅ | ❌ | ✅ |
| `www.uns.edu.pe` | 44% | **D** | ❌ | ❌ | ✅ | ❌ | ✅ |
| `registro.uns.edu.pe` | 33% | 🔴 **F** | ❌ | ❌ | ❌ | ❌ | ❌ |
| `sigea.uns.edu.pe` | 33% | 🔴 **F** | ✅ | ❌ | ❌ | ❌ | ✅ |
| `biblioteca.uns.edu.pe` | 33% | 🔴 **F** | ❌ | ❌ | ❌ | ❌ | ✅ |
| `cepuns.uns.edu.pe` | 33% | 🔴 **F** | ❌ | ❌ | ❌ | ❌ | ✅ |
| `hpda.uns.edu.pe` | 33% | 🔴 **F** | ❌ | ❌ | ❌ | ❌ | ✅ |
| `incuba.uns.edu.pe` | 33% | 🔴 **F** | ❌ | ❌ | ❌ | ❌ | ✅ |
| `marcaciones.uns.edu.pe` | 33% | 🔴 **F** | ❌ | ❌ | ❌ | ❌ | ✅ |
| `wmdb.uns.edu.pe` | 33% | 🔴 **F** | ❌ | ❌ | ❌ | ❌ | ✅ |
| `noradx.uns.edu.pe` | 33% | 🔴 **F** | ❌ | ❌ | ❌ | ❌ | ✅ |
| `revistas.uns.edu.pe` | 0% | 🔴 **F** | ❌ | ❌ | ❌ | ❌ | ❌ |
| `sgpi.uns.edu.pe` | 0% | 🔴 **F** | ❌ | ❌ | ❌ | ❌ | ❌ |

**Resumen**: 13 de 19 sistemas con grado F. Solo 1 sistema (pure.uns.edu.pe, manejado por Cloudflare/Elsevier) obtiene grado A.

---

## 5. Escaneo de Archivos y Rutas Sensibles — SIIGAA

**Target**: `https://registro.uns.edu.pe`
**Rutas verificadas**: 61
**Herramienta**: `sensitive_files_scanner.py` (custom)

| Ruta | Status | Hallazgo |
|------|--------|---------|
| `/console` | 302 → `/noredirect.html` | ⚪ Consola de app server detectada (ver VULN-003) |
| `/.git/`, `/.env`, `/phpinfo.php`, etc. | 404/No responde | ✅ No expuestos |
| `/backup.*`, `/db.sql`, etc. | 404 | ✅ No expuestos |
| `/swagger-ui.html`, `/api-docs` | 404 | ✅ No expuestos |

**Conclusión**: El SIIGAA no expone archivos de configuración, backups, o repositorios de código en la raíz. El único hallazgo es la presencia de la ruta `/console`.

---

## 5.1 Escaneo de Archivos y Rutas Sensibles — Campus Virtual

**Target**: `https://campus.uns.edu.pe`
**Rutas verificadas**: 61 (scanner) → 49 validadas (`verify_soft404.py`)
**Herramientas**: `sensitive_files_scanner.py` + `verify_soft404.py` (custom)

| Ruta | Status | Hallazgo |
|------|--------|----------|
| `/login/index.php` | 200 | Moodle "Entrar al sitio | CV-UNS" (ver VULN-009, VULN-010) |
| `/security.txt` | 200 (670 B) | ⚪ Genérico de Moodle HQ — sin contacto institucional UNS (ver INFO-002) |
| `/backup/`, `/.htaccess` | 403 | ✅ Protegidos — existen pero requieren autenticación |
| 45 rutas (`.git/`, `.env*`, `backup.*`, `phpmyadmin/`, `actuator`, `swagger`, `console`, `logs`, `robots.txt`, etc.) | 200 (36,664 B) | ⚪ **Soft-404** — todas devuelven la página principal de Moodle → **falsos positivos descartados** |

**Conclusión**: El Campus Virtual **no expone** archivos sensibles reales. El comportamiento soft-404 de Moodle obligó a validar cada hallazgo por contenido (hash + título), descartando 48 falsos positivos (INFO-002). CSV validado: `findings/sensitive_files_campus_validado.csv`.

---

## 6. Metodología y Herramientas

| Herramienta | Tipo | Propósito | WSTG |
|-------------|------|-----------|------|
| `_verify_subdomains.py` (custom) | Pasivo | Verificación HTTP de 22 subdominios | INFO-03 |
| `security_headers_audit.py` (custom) | Activo no intrusivo | Auditoría de 20 subdominios activos | CONF-06/07 |
| `sensitive_files_scanner.py` (custom) | Activo controlado | 61 rutas sensibles en SIIGAA | CONF-03/04 |
| hackertarget.com API | OSINT Pasivo | Descubrimiento de subdominios | INFO-03 |

---

## 7. Conclusiones y Plan de Remediación

### Prioridad 1 — Inmediata (0-15 días)
1. **Actualizar PHP en SIGEA** — PHP 7.1.33 es EOL desde 2019. Actualizar a PHP 8.1+.
2. **Forzar HTTPS en SIIGAA** — Agregar redirect 301 y header HSTS en `registro.uns.edu.pe`.
3. **Deshabilitar métodos PUT/DELETE** en `sigea.uns.edu.pe`.

### Prioridad 2 — Corto Plazo (15-60 días)
4. **Implementar cabeceras de seguridad** en todos los sistemas (plantilla Nginx estándar).
5. **Investigar `/console`** en SIIGAA — deshabilitar o restringir a red interna.
6. **Auditar manualmente** `orcl.uns.edu.pe`, `marcaciones.uns.edu.pe`, `sigea.uns.edu.pe` con Burp Suite.

### Prioridad 3 — Mediano Plazo (60-120 días)
7. **Programa continuo** de auditoría de seguridad semestral.
8. **Capacitación OWASP Top 10** para el equipo de TI.
9. **Política de gestión de vulnerabilidades** institucional formal.

---

*Informe generado como producto de tesis — UNS — Septiembre 2026*
*Herramientas desarrolladas: `recon_subdomains.py`, `security_headers_audit.py`, `sensitive_files_scanner.py`*
