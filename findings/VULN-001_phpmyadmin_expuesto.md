# VULN-001 — phpMyAdmin 5.2.3 Expuesto Públicamente en Internet
## `orcl.uns.edu.pe` — Universidad Nacional del Santa

---

| Campo | Detalle |
|-------|---------|
| **ID** | VULN-001 |
| **Severidad** | 🟠 Alta |
| **CVSS v3.1 Score** | **7.5** |
| **Vector CVSS** | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` |
| **OWASP Top 10 - 2021** | A05 – Security Misconfiguration |
| **WSTG ID** | WSTG-CONF-02, WSTG-CONF-04 |
| **CWE** | CWE-16 (Configuration), CWE-284 (Improper Access Control) |
| **URL Afectada** | `https://orcl.uns.edu.pe/` |
| **Rutas expuestas** | `/README` · `/ChangeLog` (exponen versión exacta) |
| **Rutas inactivas o vacías** | `/setup/` (wizard deshabilitado) · `/config.inc.php` (0 bytes) |
| **Fecha de descubrimiento** | 2026-09-20 |
| **Sistema de BD gestionado** | MySQL / MariaDB (infraestructura UNS) |

> [!NOTE]
> **Severidad ajustada** tras verificación manual. El CVSS original (9.8) asumía `/setup/` explotable y `config.inc.php` legible — ambos vectores resultaron inactivos. La vulnerabilidad real es la **exposición pública del panel de login** con **fingerprinting de versión** y superficie de brute-force.

---

## 1. Descripción de la Vulnerabilidad

**phpMyAdmin** es una herramienta web de administración de bases de datos MySQL/MariaDB. La instancia presente en `orcl.uns.edu.pe` es la versión **5.2.3** y está accesible **públicamente desde cualquier lugar de internet**, sin ningún tipo de restricción de acceso por IP, VPN o autenticación previa a nivel de red.

### Estado verificado de rutas:

| Ruta | Status | Estado real | Riesgo |
|------|--------|-------------|--------|
| `/` (login de phpMyAdmin) | `200 OK` | ✅ Accesible | Panel de login expuesto, brute-force posible |
| `/README` | `200 OK` | ✅ Accesible | Confirma versión exacta: phpMyAdmin 5.2.3 |
| `/ChangeLog` | `200 OK` | ✅ Accesible | Revela historial de versiones |
| `/setup/` | `200 OK` | ❌ **Deshabilitado** | Responde: *"Configuration already exists, setup is disabled!"* — No explotable |
| `/config.inc.php` | `200 OK` | ❌ **0 bytes** | Archivo vacío, no contiene información útil |

> [!IMPORTANT]
> El puerto **MySQL 3306** está filtrado a nivel de red — no fue posible intentar conexión directa a la base de datos.

La vulnerabilidad real consiste en: **(1)** la exposición del panel de login sin restricción de IP permite ataques de fuerza bruta ilimitados, y **(2)** el fingerprinting de versión exacta (5.2.3) permite a un atacante conocer los CVEs específicos que aplican.

---

## 2. Evidencia Real Obtenida

```
[Verificación manual — 2026-09-20]

GET https://orcl.uns.edu.pe/           → 200 OK  ← Login phpMyAdmin EXPUESTO
GET https://orcl.uns.edu.pe/README     → 200 OK  ← Versión 5.2.3 confirmada
GET https://orcl.uns.edu.pe/ChangeLog  → 200 OK  ← Historial de versiones

GET https://orcl.uns.edu.pe/setup/     → 200 OK
  Body: "Configuration already exists, setup is disabled!"
  → Wizard DESHABILITADO — no explotable

GET https://orcl.uns.edu.pe/config.inc.php → 200 OK
  Body: (0 bytes — archivo vacío)
  → Sin información de credenciales ni configuración

nc -zv orcl.uns.edu.pe 3306 → FILTERED (no accesible desde internet)
```

```http
HTTP/1.1 200 OK
Server: openresty
Content-Type: text/html; charset=utf-8
X-Frame-Options: DENY

<!DOCTYPE html>
<html lang="en">
<head>
  <title>phpMyAdmin</title>
  ...versión 5.2.3 confirmada en CSS: href="./themes/pmahomme/jquery/jquery-ui.css?v=5.2.3"
```

---

## 3. Escenario de Ataque — Cómo lo Explotaría un Atacante

> ⚠️ **Este escenario es educativo. No ejecutar.**

### Paso 1: Reconocimiento
```bash
# El atacante descubre el subdominio via Certificate Transparency o OSINT
curl https://api.hackertarget.com/hostsearch/?q=uns.edu.pe
→ orcl.uns.edu.pe,190.119.171.165

# Visita el subdominio y encuentra phpMyAdmin 5.2.3
curl -s https://orcl.uns.edu.pe/ | grep -i "phpmyadmin\|title"
→ <title>phpMyAdmin</title>
→ Versión 5.2.3 confirmada en código fuente (CSS: ?v=5.2.3)

# Lee /README para confirmar versión sin autenticación
curl https://orcl.uns.edu.pe/README
→ phpMyAdmin - Readme / Version 5.2.3
```

### Paso 2: Ataque de Fuerza Bruta al Login
```
Con el panel de login expuesto sin restricción de IP ni rate-limiting visible,
el atacante prueba combinaciones comunes:

Usuario: root     | Contraseña: (vacía)   ← Defecto MySQL frecuente
Usuario: root     | Contraseña: root
Usuario: admin    | Contraseña: admin
Usuario: pma      | Contraseña: pma
Usuario: uns      | Contraseña: uns123
Usuario: sistema  | Contraseña: sistema2024

Herramientas: Hydra, Burp Suite Intruder
```

> [!NOTE]
> Vectores descartados tras verificación: `/setup/` está deshabilitado ("setup is disabled"), `config.inc.php` devuelve 0 bytes, puerto MySQL 3306 filtrado. **El único vector real es el panel de login público.**

### Paso 3: Si obtiene acceso — Impacto total
Una vez dentro de phpMyAdmin, el atacante tiene acceso completo a todas las bases de datos de la universidad:

```sql
SHOW DATABASES;
→ siigaa, sigea, campus_virtual, biblioteca, usuarios...

SELECT username, password FROM usuarios;  -- Extrae credenciales
SELECT nombre, dni, email, telefono FROM estudiantes;  -- Datos personales
UPDATE notas SET nota = 20 WHERE codigo_estudiante = '12345';  -- Altera notas
```

### Impacto Real si se Explota

| Dato expuesto | Cantidad estimada | Ley violada |
|--------------|------------------|-------------|
| Datos personales de estudiantes (nombre, DNI, teléfono, email) | ~10,000+ registros | Ley 29733 — Perú |
| Calificaciones y expedientes académicos | Todos los semestres | Reglamento académico UNS |
| Credenciales de acceso de usuarios | Todos los roles | — |
| Registros de matrícula y pagos | Historial completo | — |
| Datos de docentes y personal | Todos | Ley 29733 |

---

## 5. Remediación — Cómo Parchearlo

### Corrección INMEDIATA (hacer hoy)

#### Opción A — Restricción por IP en Nginx/OpenResty (RECOMENDADA)
```nginx
# Archivo: /etc/nginx/sites-available/orcl.uns.edu.pe
# o en el reverse proxy OpenResty

server {
    listen 443 ssl;
    server_name orcl.uns.edu.pe;

    # OPCIÓN 1: Bloquear acceso público completamente
    # Solo permitir desde la red interna de la universidad
    allow 190.119.171.0/24;   # Red interna UNS
    allow 127.0.0.1;
    deny all;                  # Bloquear a todos los demás

    # OPCIÓN 2: Si necesita acceso remoto, usar autenticación HTTP básica
    # como capa adicional ANTES del login de phpMyAdmin
    auth_basic "Acceso restringido — Solo personal TI";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://localhost:8080;
    }
}
```

#### Opción B — Bloquear /setup/ específicamente
```nginx
# Bloquear la página de configuración definitivamente
location /setup/ {
    deny all;
    return 403;
}

# Bloquear archivos de información
location ~* \.(readme|changelog|txt)$ {
    deny all;
    return 404;
}
```

#### Opción C — Configurar `$cfg['AllowArbitraryServer']` en phpMyAdmin
```php
// En config.inc.php — deshabilitar conexión a servidores arbitrarios
$cfg['AllowArbitraryServer'] = false;

// Configurar IP de acceso en phpMyAdmin (capa adicional)
$cfg['Servers'][$i]['AllowNoPassword'] = false;

// Habilitar límite de intentos de login
$cfg['LoginCookieValidity'] = 3600;
$cfg['blowfish_secret'] = 'clave-aleatoria-muy-larga-y-compleja-aqui';
```

### Corrección DEFINITIVA (hacer en los próximos 30 días)

1. **Mover phpMyAdmin a una ruta no predecible**:
   ```
   # Cambiar la URL de /phpmyadmin o raíz a algo no obvio:
   # https://orcl.uns.edu.pe/db-mgmt-xk7z9p/  (solo el equipo TI sabe esta ruta)
   ```

2. **Implementar autenticación de dos factores** para phpMyAdmin.

3. **Usar una VPN o túnel SSH** en lugar de exponer phpMyAdmin a internet:
   ```bash
   # Acceso seguro vía túnel SSH desde el equipo del administrador:
   ssh -L 3306:localhost:3306 admin@190.119.171.165
   # Luego acceder desde localhost:3306 con cualquier cliente MySQL
   ```

4. **Cambiar las credenciales de la BD** — asumir que pueden estar comprometidas.

5. **Revisar logs de acceso** de phpMyAdmin para detectar intentos previos de acceso no autorizado.

---

## 6. Verificación del Parche

Después de aplicar la corrección, verificar:
```bash
# Desde una IP externa (no de la red UNS):
curl -I https://orcl.uns.edu.pe/
→ HTTP/1.1 403 Forbidden  ✅ (o redirección a login de VPN)

curl -I https://orcl.uns.edu.pe/setup/
→ HTTP/1.1 403 Forbidden  ✅

curl -I https://orcl.uns.edu.pe/README
→ HTTP/1.1 404 Not Found  ✅
```

---

## 7. Referencias

- [OWASP — A05:2021 Security Misconfiguration](https://owasp.org/Top10/A05_2021-Security_Misconfiguration/)
- [phpMyAdmin Security Advisory](https://www.phpmyadmin.net/security/)
- [WSTG-CONF-02: Test Application Platform Configuration](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/02-Test_Application_Platform_Configuration)
- [CWE-284: Improper Access Control](https://cwe.mitre.org/data/definitions/284.html)
- [Ley 29733 — Protección de Datos Personales, Perú](https://www.minjus.gob.pe/transparencia/documentos/Ley29733.pdf)
