# VULN-002 — Divulgación de Componente EOL (PHP 7.1.33) en Header HTTP
## `sigea.uns.edu.pe` — Universidad Nacional del Santa

---

| Campo | Detalle |
|-------|---------|
| **ID** | VULN-002 |
| **Severidad Confirmada** | 🟡 **Media** |
| **CVSS v3.1 Base** | **5.3** (Estrictamente justificado sobre evidencia empírica) |
| **Vector CVSS** | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` |
| **OWASP Top 10 - 2021** | A06 – Vulnerable and Outdated Components |
| **WSTG ID** | WSTG-INFO-02 (Fingerprinting), WSTG-CONF-05 (Infrastructure Enumerate) |
| **CWE** | CWE-200 (Exposure of Sensitive Information), CWE-1104 (Use of Unmaintained Third Party Components) |
| **URL Afectada** | `https://sigea.uns.edu.pe` |
| **Fecha de Validación** | 2026-10-25 |
| **Hipótesis RCE Asociada** | CVE-2019-11043 (CVSS 9.8 de referencia, **No Confirmada — Limitación Caja Negra**) |

> [!IMPORTANT]
> **Criterio Metodológico de Puntuación CVSS:**
> La severidad base de este hallazgo se evalúa en **5.3 (Media)** correspondiente a la evidencia demostrada: *divulgación no autenticada de versión exacta de un componente sin soporte oficial*. No se asigna una severidad crítica (9.8 ni 7.5) únicamente por la antigüedad de PHP, ya que la explotabilidad de fallos de ejecución remota de código (RCE) requiere condiciones específicas de configuración que no han sido comprobadas en auditoría pasiva/caja negra.

---

## 1. Desglose Estructurado del Hallazgo

### A. Versión Obsoleta (Vulnerabilidad Confirmada)
El servidor expone en cada respuesta HTTP la cabecera:
```http
X-Powered-By: PHP/7.1.33
Server: openresty
```
PHP 7.1 alcanzó su fin de ciclo de vida (**End of Life - EOL**) el **1 de diciembre de 2019** (+6 años sin mantenimiento). Esto representa una deficiencia de gestión de parches (CWE-1104) y una señal de exposición clara para atacantes.

### B. Configuración del Entorno (Arquitectura Observada)
* **Reverse Proxy / Web Server:** OpenResty (Nginx + Lua).
* **Manejador de Backend:** PHP-FPM / FastCGI.
* **Framework:** **CodeIgniter** (confirmado al devolver la plantilla nativa de error en `/index.php/test_path_info_probe`).

### C. Evaluación de la Hipótesis de RCE y Limitación Metodológica
Para que vulnerabilidades críticas como **CVE-2019-11043** o desbordamientos de memoria en FastCGI sean explotables, se requieren configuraciones internas muy precisas en el bloque `location ~ \.php` de Nginx:
1. Directiva `fastcgi_split_path_info` con expresión regular permisiva.
2. Transferencia ciega de `PATH_INFO` sin directiva `try_files $fastcgi_script_name =404;`.
3. Ausencia de sanitización previa en el proxy OpenResty.

> [!WARNING]
> **Limitación de Alcance (Auditoría Caja Negra):**
> Al no disponer de acceso administrativo (SSH / lectura de `nginx.conf` y `php-fpm.conf`) ni de autorización para ejecutar un exploit que desestabilice la memoria de los procesos worker en producción, **la hipótesis de RCE se clasifica como NO CONFIRMADA**. Se documenta como riesgo potencial a investigar en una fase de caja blanca o de hardening defensivo.

---

## 2. Matriz de Validación de Requisitos Técnicos para CVE-2019-11043

| Requisito Técnico del CVE | ¿Observado en SIGEA? | Tipo de Evidencia | Estado |
| :--- | :---: | :--- | :---: |
| **1. Servidor Nginx / OpenResty** | ✅ Sí | Cabecera HTTP `Server: openresty` | **Confirmado** |
| **2. Intérprete PHP vulnerable (7.1.x)** | ✅ Sí | Cabecera HTTP `X-Powered-By: PHP/7.1.33` | **Confirmado** |
| **3. Procesamiento FastCGI a index.php** | ✅ Sí | Subruta procesada por CodeIgniter (HTTP 404 de aplicación) | **Confirmado** |
| **4. Directiva `fastcgi_split_path_info` vulnerable** | ❓ Desconocido | Requiere lectura interna de archivo `nginx.conf` | ⚠️ **No Verificable (Caja Negra)** |
| **5. Omisión de `try_files` en Nginx** | ❓ Desconocido | Requiere lectura interna de archivo `nginx.conf` | ⚠️ **No Verificable (Caja Negra)** |
| **6. Explotabilidad RCE en caliente** | ❌ No ejecutada | No autorizada para prevenir caída de servicio | ⚪ **Hipótesis No Confirmada** |

---

## 3. Evidencia Empírica Reproducible (Telemetría de Red)

Pruebas ejecutadas con la herramienta del proyecto [`tools/audit_validator.py`](file:///c:/Users/Leguion%20T/Desktop/plan%20te%20pent/tools/audit_validator.py):

```http
[Fecha UTC: 2026-10-25T06:43:07Z]
GET https://sigea.uns.edu.pe/ HTTP/1.1
Host: sigea.uns.edu.pe
User-Agent: Thesis-Security-Audit/1.0

HTTP/1.1 200 OK
Server: openresty
X-Powered-By: PHP/7.1.33
Strict-Transport-Security: max-age=63072000; preload
Content-Type: text/html; charset=UTF-8
[Sin Content-Security-Policy]
[Sin X-Frame-Options]
[Sin X-Content-Type-Options]
```

```http
[Comprobación de Métodos HTTP en recurso inexistente]
PUT /test_probe_audit_sigea_uns_edu_pe.txt HTTP/1.1
Host: sigea.uns.edu.pe

HTTP/1.1 405 Method Not Allowed
→ Confirmación: Métodos destructivos están deshabilitados.
```

### Ataque A: Fingerprinting y Selección de Exploit
```bash
# Paso 1: El atacante detecta la versión PHP en el header
curl -I https://sigea.uns.edu.pe/
→ X-Powered-By: PHP/7.1.33

# Paso 2: El atacante busca CVEs específicos para versiones sin soporte (EOL)
searchsploit php 7.1
```

### Ataque B: Explotación de CVE-2019-11043 (PHP-FPM RCE)
Dado que el servidor utiliza OpenResty pasando rutas dinámicas a PHP (`index.php` de CodeIgniter), si la configuración de Nginx carece de `try_files $fastcgi_script_name =404;`, existe riesgo de **ejecución remota de código**:
```bash
# Herramienta de auditoría phuip-fpizdam para CVE-2019-11043
phuip-fpizdam https://sigea.uns.edu.pe/index.php
```

### Vector Descartado: Métodos HTTP PUT / DELETE (Falso Positivo)
Los reportes iniciales sugerían que métodos PUT y DELETE permitían modificar o eliminar recursos (HTTP 200 OK). Las pruebas empíricas no destructivas confirmaron que el servidor responde con **`HTTP 405 Method Not Allowed`**, descartando la posibilidad de subir webshells o borrar archivos por este vector.

---

## 4. Remediación

### Para la Versión PHP EOL

#### Corrección Inmediata — Ocultar la Versión
Editar `/etc/php/7.1/fpm/php.ini` (o la ruta del php.ini activo):
```ini
; Deshabilitar exposición de la versión PHP en headers HTTP
expose_php = Off
```
Reiniciar PHP-FPM:
```bash
sudo systemctl restart php7.1-fpm
# o
sudo service php7.1-fpm restart
```
Verificar:
```bash
curl -I https://sigea.uns.edu.pe/
# El header X-Powered-By ya NO debe aparecer
```

#### Corrección Definitiva — Actualizar PHP
```bash
# Instalar PHP 8.1 (LTS, soportado hasta Nov 2025) o PHP 8.3 (actual)
sudo apt install php8.3 php8.3-fpm php8.3-mysql php8.3-common php8.3-mbstring

# Verificar que la aplicación es compatible con PHP 8.x
# (puede requerir ajustes de código si usa funciones deprecadas)

# Actualizar la configuración de Nginx para usar la nueva versión:
# fastcgi_pass unix:/var/run/php/php8.3-fpm.sock;
```

### Para los Métodos HTTP PUT y DELETE

#### En Nginx / OpenResty:
```nginx
server {
    listen 443 ssl;
    server_name sigea.uns.edu.pe;

    # OPCIÓN 1: Bloquear todos los métodos excepto GET, HEAD, POST
    if ($request_method !~ ^(GET|HEAD|POST)$ ) {
        return 405;
    }

    # OPCIÓN 2: Lista blanca más explícita por location
    location / {
        limit_except GET HEAD POST {
            deny all;
        }
        proxy_pass http://app_backend;
    }
}
```

#### En Apache (si aplica):
```apache
# En .htaccess o httpd.conf:
<LimitExcept GET POST HEAD>
    Order Allow,Deny
    Deny from all
</LimitExcept>
```

#### En PHP (capa de aplicación):
```php
// Al inicio de cada script PHP que recibe requests:
$allowed_methods = ['GET', 'POST', 'HEAD'];
if (!in_array($_SERVER['REQUEST_METHOD'], $allowed_methods)) {
    http_response_code(405);
    header('Allow: GET, POST, HEAD');
    exit('Method Not Allowed');
}
```

### Adicionalmente — Eliminar Header X-Powered-By en Nginx:
```nginx
# Eliminar también el header a nivel de Nginx como capa adicional:
fastcgi_hide_header X-Powered-By;
proxy_hide_header X-Powered-By;
```

---

## 5. Verificación del Parche

```bash
# Verificar que el header ya no aparece:
curl -I https://sigea.uns.edu.pe/
# → Ya NO debe aparecer: X-Powered-By

# Verificar que PUT retorna 405:
curl -X PUT https://sigea.uns.edu.pe/ -I
# → HTTP/1.1 405 Method Not Allowed  ✅

# Verificar que DELETE retorna 405:
curl -X DELETE https://sigea.uns.edu.pe/ -I
# → HTTP/1.1 405 Method Not Allowed  ✅
```

---

## 6. Referencias

- [CVE-2019-11043 — PHP-FPM RCE](https://nvd.nist.gov/vuln/detail/CVE-2019-11043)
- [OWASP — A06:2021 Vulnerable and Outdated Components](https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/)
- [PHP Supported Versions](https://www.php.net/supported-versions.php)
- [WSTG-CONF-05: Enumerate Infrastructure and Application Admin Interfaces](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/05-Enumerate_Infrastructure_and_Application_Admin_Interfaces)
- [CWE-200: Exposure of Sensitive Information](https://cwe.mitre.org/data/definitions/200.html)
