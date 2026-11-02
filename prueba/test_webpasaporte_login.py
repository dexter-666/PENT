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

# Step 1: Get login page
r = s.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r.text)
vstate = vs.group(1) if vs else ""

# Step 2: Click cmdEstudiante
print("=== SELECCIONAR ESTUDIANTE ===")
data = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdEstudiante',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r2 = s.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', data=data, timeout=10)

# Search for ALL inputs and form fields in the AJAX response
text = r2.text
print(f"Response length: {len(text)}")

# Find ALL inputs
all_inputs = re.findall(r'<input[^>]*>', text)
print(f"\nTodos los inputs ({len(all_inputs)}):")
for inp in all_inputs:
    if 'hidden' not in inp.lower():
        print(f"  VISIBLE: {inp[:200]}")

# Find ALL text/password type inputs
for inp in all_inputs:
    if 'password' in inp.lower() or ('type="' not in inp.lower() and 'type=' not in inp.lower()):
        print(f"  INPUT: {inp[:200]}")

# Find ALL form fields by name pattern
fields = re.findall(r'(?:name|id)="([^"]*(?:usuario|user|password|pass|clave|login|email|credential|cred|uname|uid|pwd|passwd)[^"]*)"', text, re.IGNORECASE)
print(f"\nCampos con nombres de credencial:")
for f in fields:
    print(f"  {f}")

# Find all labels/text near inputs
labels = re.findall(r'<label[^>]*>([^<]+)</label>', text)
print(f"\nLabels:")
for l in labels:
    print(f"  {l.strip()}")

# Search for 'usuario' in the text
usuario_matches = list(re.finditer(r'usuario', text, re.IGNORECASE))
for m in usuario_matches[:5]:
    ctx = text[max(0,m.start()-30):m.end()+100]
    ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
    ctx_clean = re.sub(r'\s+', ' ', ctx_clean).strip()
    print(f"\n  [usuario]: {ctx_clean[:200]}")

# Search for 'password' in the text
pass_matches = list(re.finditer(r'password|contraseña|clave', text, re.IGNORECASE))
for m in pass_matches[:5]:
    ctx = text[max(0,m.start()-30):m.end()+100]
    ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
    ctx_clean = re.sub(r'\s+', ' ', ctx_clean).strip()
    print(f"\n  [password]: {ctx_clean[:200]}")

# Look for form fields
all_names = re.findall(r'name="([^"]+)"', text)
print(f"\nTodos los nombres de campos ({len(all_names)}):")
for n in all_names:
    print(f"  {n}")

# Find commandButton for login
login_btns = re.findall(r'<p:commandButton[^>]*>', text) + re.findall(r'<h:commandButton[^>]*>', text) + re.findall(r'<button[^>]*>', text)
print(f"\nBotones de login ({len(login_btns)}):")
for b in login_btns[:10]:
    print(f"  {b[:200]}")

# Look for any form action with login
actions = re.findall(r'action="([^"]+)"', text)
print(f"\nActions: {actions}")

# Check if the AJAX response has a different structure
# Look for the main content area
body_match = re.search(r'<body[^>]*>(.*?)</body>', text, re.DOTALL)
if body_match:
    body = body_match.group(1)
    # Find the login form
    form_match = re.search(r'<form[^>]*>.*?</form>', body, re.DOTALL)
    if form_match:
        form_text = form_match.group(0)
        print(f"\n=== FORMA DE LOGIN ===")
        # Extract inputs from form
        form_inputs = re.findall(r'<input[^>]*>', form_text)
        print(f"Inputs en formulario: {len(form_inputs)}")
        for fi in form_inputs:
            print(f"  {fi[:200]}")

# Now try to POST with fake credentials after selecting estudiante
print("\n\n=== PASO 3: Probar login con fake/fake ===")
s2 = requests.Session()
s2.verify = False
s2.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})

# First get the page with estudiante selected
r3 = s2.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml?tipo=estudiante', timeout=10)
vs3 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r3.text)
vstate3 = vs3.group(1) if vs3 else ""
print(f"ViewState: {vstate3[:50]}...")

# Try to find all possible credential field names
all_field_names = re.findall(r'name="([^"]+)"', r3.text)
cred_fields = [n for n in all_field_names if any(kw in n.lower() for kw in ['usuario', 'user', 'password', 'pass', 'clave', 'login', 'email', 'cred'])]
print(f"Campos de credencial encontrados: {cred_fields}")

# Try login with different field name combos
cred_combos = [
    {'j_username': 'fake', 'j_password': 'fake'},
    {'usuario': 'fake', 'password': 'fake'},
    {'user': 'fake', 'pass': 'fake'},
    {'usuario': 'fake', 'contrasena': 'fake'},
    {'usuario': 'fake', 'clave': 'fake'},
]

print("\nProbando combos:")
for combo in cred_combos:
    data_combo = {'frmLogueo': 'frmLogueo', 'jakarta.faces.ViewState': vstate3}
    data_combo.update(combo)
    r_combo = s2.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml?tipo=estudiante',
                         data=data_combo, timeout=5, allow_redirects=True)
    tc = re.sub(r'<[^>]+>', ' ', r_combo.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    has_success = 'logout' in tc.lower() or 'bienvenida' in tc.lower() or 'inicio' in tc.lower()
    has_error = 'error' in tc.lower() and 'login' not in tc.lower()
    print(f"  {combo} -> len={len(r_combo.text)}, success={has_success}, error={has_error}")

# Also check if there's a separate login endpoint after selecting type
print("\n=== Verificando si hay otro endpoint ===")
for url in [
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/estudiante.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/ingreso.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/autenticar.xhtml',
]:
    try:
        r4 = s2.get(url, timeout=5)
        tc4 = re.sub(r'<[^>]+>', ' ', r4.text)
        tc4 = re.sub(r'\s+', ' ', tc4).strip()
        print(f"  {url.split('/')[-1]} -> {r4.status_code}, len={len(r4.text)}")
    except:
        pass
