# VULN-007 — 15/20 Sistemas sin HTTP Strict-Transport-Security (HSTS)
## Múltiples subdominios — Universidad Nacional del Santa

---

| Campo | Detalle |
|-------|---------|
| **ID** | VULN-007 |
| **Severidad** | 🟡 Media |
| **CVSS v3.1 Score** | **5.9** |
| **Vector CVSS** | `CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N` |
| **OWASP Top 10 - 2021** | A02 – Cryptographic Failures |
| **WSTG ID** | WSTG-CONF-06 |
| **CWE** | CWE-311 (Missing Encryption of Sensitive Data), CWE-523 (Unprotected Transport of Credentials) |
| **Sistemas sin HSTS** | 15 de 20 auditados (75%) |
| **Fecha de descubrimiento** | 2026-09-20 |

---

## 1. Descripción

**HTTP Strict-Transport-Security (HSTS)** es un mecanismo de seguridad que instruye al navegador web a usar **exclusivamente HTTPS** para comunicarse con el servidor, durante un periodo de tiempo definido.

El **75% de los sistemas de la UNS** no implementan este header, lo que deja a todos sus usuarios expuestos a ataques de **SSL Stripping** donde un atacante de red puede degradar la conexión de HTTPS a HTTP.

### Sistemas sin HSTS:

| Sistema | Score | Grado |
|---------|-------|-------|
| `registro.uns.edu.pe` | 33% | F |
| `revistas.uns.edu.pe` | 0% | F |
| `sgpi.uns.edu.pe` | 0% | F |
| `biblioteca.uns.edu.pe` | 33% | F |
| `cepuns.uns.edu.pe` | 33% | F |
| `hpda.uns.edu.pe` | 33% | F |
| `incuba.uns.edu.pe` | 33% | F |
| `marcaciones.uns.edu.pe` | 33% | F |
| `wmdb.uns.edu.pe` | 33% | F |
| `noradx.uns.edu.pe` | 33% | F |
| `campus.uns.edu.pe` | 44% | D |
| `cecomp.uns.edu.pe` | 44% | D |
| `posgrado.uns.edu.pe` | 44% | D |
| `www.uns.edu.pe` | 44% | D |
| `sistemas.uns.edu.pe` | 67% | C |

### Sistemas CON HSTS (correctamente configurados):
| Sistema | HSTS | Nota |
|---------|------|------|
| `pure.uns.edu.pe` | ✅ `max-age=2592000; preload` | Cloudflare lo aplica |
| `sigea.uns.edu.pe` | ✅ `max-age=63072000; preload` | Correcto |
| `orcl.uns.edu.pe` | ✅ | Correcto |
| `onvsw.uns.edu.pe` | ✅ | Correcto |
| `sigea.uns.edu.pe` | ✅ | Correcto |

---

## 2. Escenario de Ataque — SSL Stripping

El ataque de **SSL Stripping** fue presentado por Moxie Marlinspike en la Black Hat 2009 y sigue siendo efectivo contra sitios sin HSTS.

### Requisito: El atacante debe estar en la misma red que la víctima
(Red Wi-Fi universitaria, laboratorio de cómputo, cafetería)

### Paso a paso:

```
SITUACIÓN NORMAL (con HSTS):
  Usuario escribe: campus.uns.edu.pe (sin https://)
  Navegador recuerda HSTS → automáticamente usa HTTPS
  → El ataque de SSL Stripping es IMPOSIBLE

SITUACIÓN VULNERABLE (sin HSTS):
  Usuario escribe: campus.uns.edu.pe (sin https://)
  Navegador hace petición HTTP primero
  → El atacante intercepta ESA primera petición HTTP
  → Elimina el redirect a HTTPS
  → El usuario navega en HTTP sin saberlo
  → Todas las credenciales van en texto plano
```

```bash
# Herramienta: bettercap (demo educativo)
# Paso 1: ARP spoofing para interceptar el tráfico
sudo bettercap -iface wlan0
bettercap> set arp.spoof.targets 192.168.1.50  # IP del estudiante
bettercap> arp.spoof on

# Paso 2: SSL Stripping
bettercap> set https.proxy.sslstrip true
bettercap> https.proxy on

# Resultado: La víctima accede a campus.uns.edu.pe via HTTP
# bettercap captura en tiempo real:
[http.proxy] [POST http://campus.uns.edu.pe/login]
  usuario: 20182345
  password: Moodle@2024
  [CREDENCIAL CAPTURADA]
```

---

## 3. Remediación Global — Implementación de HSTS en Toda la Infraestructura

### Solución a nivel de OpenResty (afecta todos los subdominios a la vez):

```nginx
# ============================================================
# Agregar HSTS GLOBALMENTE en nginx.conf (bloque http{})
# Esto aplica a TODOS los virtual hosts de una vez
# ============================================================

http {
    # Aplicar HSTS a todos los virtual hosts HTTPS
    map $scheme $hsts_header {
        https "max-age=31536000; includeSubDomains";
    }

    server {
        # Virtual host para cada subdominio
        add_header Strict-Transport-Security $hsts_header always;
    }
}
```

### Solución individual por servidor virtual:
```nginx
# En cada bloque server{} de HTTPS:
server {
    listen 443 ssl;
    server_name campus.uns.edu.pe;

    # HSTS: el navegador usará HTTPS durante 1 año
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Nivel máximo: añadir "preload" y registrar en hstspreload.org
    # add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
}

# Bloque HTTP que redirige a HTTPS:
server {
    listen 80;
    server_name campus.uns.edu.pe;
    return 301 https://$host$request_uri;
}
```

### Script de verificación post-parche:
```bash
#!/bin/bash
# Verificar HSTS en todos los subdominios de la UNS

SUBDOMINIOS=(
    "biblioteca.uns.edu.pe"
    "campus.uns.edu.pe"
    "cecomp.uns.edu.pe"
    "cepuns.uns.edu.pe"
    "hpda.uns.edu.pe"
    "incuba.uns.edu.pe"
    "marcaciones.uns.edu.pe"
    "noradx.uns.edu.pe"
    "posgrado.uns.edu.pe"
    "registro.uns.edu.pe"
    "revistas.uns.edu.pe"
    "sgpi.uns.edu.pe"
    "sigea.uns.edu.pe"
    "sistemas.uns.edu.pe"
    "wmdb.uns.edu.pe"
    "www.uns.edu.pe"
)

echo "Verificando HSTS en subdominios UNS..."
for subdomain in "${SUBDOMINIOS[@]}"; do
    hsts=$(curl -sI "https://$subdomain" 2>/dev/null | grep -i "strict-transport-security")
    if [ -n "$hsts" ]; then
        echo "  ✅ $subdomain → $hsts"
    else
        echo "  ❌ $subdomain → SIN HSTS"
    fi
done
```

---

## 4. Referencias

- [OWASP HSTS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Strict_Transport_Security_Cheat_Sheet.html)
- [HSTS Preload List — hstspreload.org](https://hstspreload.org/)
- [RFC 6797 — HTTP Strict Transport Security (HSTS)](https://www.rfc-editor.org/rfc/rfc6797)
- [Moxie Marlinspike — sslstrip (Black Hat 2009)](https://moxie.org/software/sslstrip/)
- [CWE-311: Missing Encryption of Sensitive Data](https://cwe.mitre.org/data/definitions/311.html)
