# ~~VULN-004~~ — FALSO POSITIVO: `/console` No es una Consola de Administración Expuesta
## `registro.uns.edu.pe/console` — Universidad Nacional del Santa

---

> [!CAUTION]
> **FALSO POSITIVO CONFIRMADO.** Esta vulnerabilidad ha sido descartada tras verificación manual.
> - `/console` → HTTP 302 redirige a `/noredirect.html` con el mensaje de **WildFly**: *"Console Redirect Unavailable"*
> - No es la consola de Oracle WebLogic — es WildFly/JBoss con la consola correctamente deshabilitada
> - `/management` → 404, `/jboss-cli` → 404, `/jmx-console` → 404
> - Puertos 7001 y 7002 no respondieron desde internet
> - **No hay superficie de ataque real.**

---

| Campo | Detalle |
|-------|---------|
| **ID** | VULN-004 |
| **Estado** | ❌ **FALSO POSITIVO — DESCARTADO** |
| **Severidad original** | 🟠 Media-Alta |
| **Causa del falso positivo** | `/console` → 302 interpretó como consola expuesta, pero es redirección de WildFly con consola deshabilitada |
| **URL Afectada** | `https://registro.uns.edu.pe/console` |
| **Fecha de descubrimiento** | 2026-09-20 |
| **Fecha de descarte** | 2026-09-20 |

---

## 1. Descripción

La ruta `/console` del sistema SIIGAA responde con un **HTTP 302** que redirige a `/noredirect.html`, en lugar de retornar el esperado `404 Not Found`. Este comportamiento confirma que la ruta `/console` **existe** en el servidor de aplicaciones subyacente.

### ¿Qué es `/console`?
La URL `/console` es la ruta estándar de los **paneles de administración** de los servidores de aplicaciones Java más comunes:

| Servidor | Ruta Admin Console | Stack Tech |
|---------|-------------------|-----------|
| **Oracle WebLogic** | `/console` | JSF, ADF |
| **Oracle GlassFish** | `/console` | JSF |
| **IBM WebSphere** | `/ibm/console` | JSF |
| **JBoss EAP** | `/console` | JSF |

El SIIGAA usa **Java Server Faces (JSF)** (confirmado por la URL `/udemsi/faces/modulos.xhtml`), tecnología asociada con Oracle WebLogic y Oracle ADF. Esto hace altamente probable que `/console` sea la **consola de administración de Oracle WebLogic**.

### ¿Por qué el redirect a `/noredirect.html`?
Alguien del equipo TI **conoce** que la consola existe y la ha "protegido" con una redirección de Nginx. Sin embargo, esta protección es **superficial**:
- La ruta existe en el servidor de aplicaciones detrás del proxy.
- Las técnicas de **path traversal** o **bypass de proxy** pueden eludir esta redirección.
- Si el puerto de administración de WebLogic está expuesto directamente, la consola puede estar accesible por otro puerto (ej: `:7001`, `:7002`).

---

## 1. Análisis de la Evidencia (Verificación Manual)

```bash
# Verificación realizada 2026-09-20

GET https://registro.uns.edu.pe/console
→ HTTP/1.1 302 Found
→ Location: /noredirect.html

# Contenido de /noredirect.html:
→ "Console Redirect Unavailable"
   Servidor: WildFly (JBoss) — NO Oracle WebLogic
   La consola de administración está deshabilitada correctamente.

# Endpoints de gestión probados:
GET /management       → 404 Not Found
GET /jboss-cli        → 404 Not Found
GET /jmx-console      → 404 Not Found

# Puertos de administración WildFly:
nc -zv registro.uns.edu.pe 7001  → Connection refused / filtered
nc -zv registro.uns.edu.pe 7002  → Connection refused / filtered
nc -zv registro.uns.edu.pe 9990  → Connection refused / filtered
```

## 2. Por Qué Es un Falso Positivo

| Criterio | Evaluación |
|----------|------------|
| `/console` accesible | El 302 fue interpretado como "ruta existe" — pero el destino confirma que está deshabilitada |
| Servidor identificado | **WildFly**, no Oracle WebLogic (tecnología diferente) |
| Consola de admin disponible | NO — mensaje explícito: *"Console Redirect Unavailable"* |
| Puertos de administración | Filtrados / no accesibles desde internet |
| CVEs de WebLogic aplicables | NO — no es WebLogic |

## 3. Conclusión

El equipo TI de la UNS correctamente deshabilitó la consola de administración de WildFly. El 302 a `/noredirect.html` es el comportamiento esperado y seguro de WildFly cuando la consola está deshabilitada. **No hay superficie de ataque.**

---

## 3. Escenario de Ataque

### Ataque A: Confirmación del Servidor de Aplicaciones
```bash
# El atacante detecta que /console → 302 (no 404)
# Esto le confirma que es WebLogic, GlassFish u otro servidor Java

# Busca el puerto de administración real de WebLogic
nmap -p 7001,7002,7003,9001,9002,4848 registro.uns.edu.pe
→ Si algún puerto está abierto: acceso directo a la consola sin el proxy

# También puede intentar:
curl -I https://registro.uns.edu.pe:7001/console/
→ HTTP/1.1 200 OK  ← Consola accesible en el puerto de administración
```

### Ataque B: Bypass del Proxy con Variaciones de la Ruta
```bash
# Técnicas de path bypass en Nginx:
curl https://registro.uns.edu.pe/%2f/console
curl https://registro.uns.edu.pe/./console
curl https://registro.uns.edu.pe/console/
curl https://registro.uns.edu.pe//console

# O con codificación URL:
curl https://registro.uns.edu.pe/%63%6f%6e%73%6f%6c%65
# (%63%6f%6e%73%6f%6c%65 = "console" en URL encoding)
```

### Ataque C: Si accede a la consola — Oracle WebLogic RCE
Oracle WebLogic tiene múltiples vulnerabilidades **críticas conocidas** de ejecución remota de código:

| CVE | CVSS | Tipo |
|-----|------|------|
| **CVE-2020-14882** | **9.8** | RCE sin autenticación via GET request |
| **CVE-2020-14750** | 9.8 | Bypass de autenticación de la consola |
| **CVE-2021-2109** | 7.2 | JNDI Injection RCE |
| **CVE-2019-2725** | 9.8 | Deserialización Java RCE |
| **CVE-2023-21839** | 7.5 | LDAP RCE sin autenticación |

```bash
# CVE-2020-14882: RCE en WebLogic sin autenticación
# Solo con un GET request al endpoint de la consola:
curl "https://registro.uns.edu.pe:7001/console/css/%252E%252E%252Fconsole.portal"
→ Si vulnerable: responde con el contenido de la consola sin autenticación

# CVE-2021-2109: Ejecutar comandos via JNDI injection
curl -X GET "https://registro.uns.edu.pe/console/consolejndi.portal?_nfpb=true&_pageLabel=JNDIBindingPageGeneral&handle=java:comp/env"
→ Si vulnerable: revela información del servidor y permite inyección
```

### Ataque D: Credenciales por Defecto de WebLogic
```
Si la consola es accesible, el atacante prueba credenciales por defecto:

Usuario: weblogic    | Contraseña: weblogic
Usuario: weblogic    | Contraseña: weblogic1
Usuario: weblogic    | Contraseña: Welcome1
Usuario: weblogic    | Contraseña: Oracle@123
Usuario: admin       | Contraseña: admin
Usuario: system      | Contraseña: password

Si obtiene acceso a la consola WebLogic:
→ Deploy de WAR malicioso (webshell) al servidor de aplicaciones
→ Acceso completo al servidor: código fuente, BD, archivos de configuración
→ Control total del SIIGAA
```

---

## 4. Remediación

### Corrección Inmediata — Bloqueo Total en Nginx/OpenResty

```nginx
server {
    listen 443 ssl;
    server_name registro.uns.edu.pe;

    # BLOQUEAR completamente la consola de administración
    # Retornar 404 (no 302) para no confirmar la existencia de la ruta
    location = /console {
        return 404;
    }

    location ^~ /console/ {
        return 404;
    }

    # Bloquear variaciones con encoding y path traversal
    location ~* /console {
        return 404;
    }

    # Bloquear también endpoints típicos de WebLogic
    location ~* ^/(bea_wls|wl_proxy|weblogic|j2eemanagement) {
        return 404;
    }
}
```

### Corrección Definitiva en el Servidor de Aplicaciones (WebLogic)

```xml
<!-- En weblogic.xml o la configuración del servidor: -->

<!-- 1. Deshabilitar la consola de administración si no es necesaria -->
<server>
    <server-name>AdminServer</server-name>
    <!-- Deshabilitar Administration Port si no se usa -->
    <administration-port-enabled>false</administration-port-enabled>
</server>

<!-- 2. Restringir acceso a la consola solo a IPs internas -->
<connection-filter>weblogic.security.net.ConnectionFilterImpl</connection-filter>
<connection-filter-rule>190.119.171.0/255.255.255.0 * * allow</connection-filter-rule>
<connection-filter-rule>* * 7001 deny</connection-filter-rule>
<connection-filter-rule>* * 7002 deny</connection-filter-rule>
```

```bash
# Regla de firewall para bloquear el puerto de administración desde internet:
# UFW:
sudo ufw deny 7001/tcp
sudo ufw deny 7002/tcp

# iptables:
iptables -A INPUT -p tcp --dport 7001 -s 190.119.171.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 7001 -j DROP
iptables -A INPUT -p tcp --dport 7002 -s 190.119.171.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 7002 -j DROP
```

### Parches de Seguridad de Oracle WebLogic
```
Aplicar el Critical Patch Update (CPU) de Oracle más reciente:
https://www.oracle.com/security-alerts/

Prioridad: parchear CVE-2020-14882 y CVE-2020-14750 inmediatamente.
```

---

## 5. Verificación del Parche

```bash
# Verificar que /console retorna 404 (no 302):
curl -I https://registro.uns.edu.pe/console
→ HTTP/1.1 404 Not Found   ✅ (no debe retornar 302)

# Verificar que el puerto de administración no es accesible:
nc -zv registro.uns.edu.pe 7001
→ Connection refused   ✅

nc -zv registro.uns.edu.pe 7002
→ Connection refused   ✅
```

---

## 6. Referencias

- [CVE-2020-14882 — WebLogic RCE sin autenticación](https://nvd.nist.gov/vuln/detail/CVE-2020-14882)
- [CVE-2021-2109 — WebLogic JNDI Injection](https://nvd.nist.gov/vuln/detail/CVE-2021-2109)
- [Oracle Critical Patch Updates](https://www.oracle.com/security-alerts/)
- [WSTG-CONF-02: Test Application Platform Configuration](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/02-Test_Application_Platform_Configuration)
- [OWASP — A05:2021 Security Misconfiguration](https://owasp.org/Top10/A05_2021-Security_Misconfiguration/)
