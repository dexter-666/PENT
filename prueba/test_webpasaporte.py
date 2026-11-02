#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})

# Step 1: Get the login page first
print("=== PASO 1: Obtener pagina de login ===")
r = s.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
print(f"Status: {r.status_code}, len={len(r.text)}")
jsession = re.search(r'JSESSIONID=([^;]+)', r.text)
jsession2 = dict(s.cookies).get('JSESSIONID', '')
print(f"JSESSIONID: {jsession2}")

# Extract ViewState
vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r.text)
vstate = vs.group(1) if vs else ""
print(f"ViewState: {vstate[:50]}...")

# Step 2: Click "Ingresar como ESTUDIANTE" via AJAX
print("\n=== PASO 2: Seleccionar ESTUDIANTE (AJAX) ===")
s.headers['javax.faces.partial.ajax'] = 'true'
s.headers['javax.faces.source'] = 'frmLogueo:cmdEstudiante'

data = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdEstudiante',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}

r2 = s.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
              data=data, timeout=10)
print(f"Status: {r2.status_code}, len={len(r2.text)}")

# Check what page it shows now
text_clean = re.sub(r'<[^>]+>', ' ', r2.text)
text_clean = re.sub(r'\s+', ' ', text_clean).strip()
print(f"\nContenido: {text_clean[:500]}")

# Check if username/password fields appeared
if 'usuario' in text_clean.lower() or 'password' in text_clean.lower() or 'itUsuario' in text_clean or 'itClave' in text_clean:
    print("\n[!] APARECIERON CAMPOS DE USUARIO/CONTRASEÑA!")
    # Find the inputs
    inputs = re.findall(r'<input[^>]*>', r2.text)
    for inp in inputs:
        if 'type' in inp.lower():
            print(f"  {inp[:200]}")

# Also try cmdTrabajador
print("\n=== PASO 3: Seleccionar TRABAJADOR (AJAX) ===")
s2 = requests.Session()
s2.verify = False
s2.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})
r3 = s2.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
vs2 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r3.text)
vstate2 = vs2.group(1) if vs2 else ""

data2 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate2,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdTrabajador',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r4 = s2.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
               data=data2, timeout=10)
text_clean4 = re.sub(r'<[^>]+>', ' ', r4.text)
text_clean4 = re.sub(r'\s+', ' ', text_clean4).strip()
print(f"Status: {r4.status_code}, len={len(r4.text)}")
print(f"Contenido: {text_clean4[:500]}")

# Step 4: Try clicking cmdInstruccion (just to see what happens)
print("\n=== PASO 4: Instrucciones ===")
s3 = requests.Session()
s3.verify = False
s3.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})
r5 = s3.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
vs3 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r5.text)
vstate3 = vs3.group(1) if vs3 else ""

data3 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate3,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdInstruccion',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmInstrucciones',
}
r6 = s3.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
               data=data3, timeout=10)
print(f"Status: {r6.status_code}, len={len(r6.text)}")

# Check if there's any URL parameter-based navigation
print("\n=== PASO 5: Probar URLs con parametros ===")
test_urls = [
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml?tipo=estudiante',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml?tipo=estudiante&user=test',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/estudiante.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/estudiante/login.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/index.xhtml',
]
for url in test_urls:
    try:
        r7 = s.get(url, timeout=5)
        tc = re.sub(r'<[^>]+>', ' ', r7.text)
        tc = re.sub(r'\s+', ' ', tc).strip()
        has_user = 'usuario' in tc.lower() or 'password' in tc.lower() or 'itUsuario' in tc
        has_login = 'logueo' in tc.lower() or 'login' in tc.lower()
        print(f"  {url.split('/')[-1]} -> {r7.status_code}, len={len(r7.text)}, user_field={has_user}")
    except:
        pass

print("\n=== RESUMEN ===")
print("WebPasaporte es un sistema de PASAPORTE WEB")
print("Login tipo seleccion: Estudiante o Trabajador")
print("No tiene formulario de usuario/contraseña visible")
print("Los campos de login aparecen despues de seleccionar el tipo")
print("Usa PrimeFaces AJAX (cmdEstudiante, cmdTrabajador)")
