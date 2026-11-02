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
print("=== HACIENDO CLICK EN 'ESTUDIANTE' ===")
data = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdEstudiante',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r2 = s.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', data=data, timeout=10)
text2 = r2.text

# Find the updated content - look for new inputs
# The AJAX response might update parts of the page
# Check if the form now has username/password fields
print(f"Response: {len(text2)} bytes")

# Look for ALL text in the response
# Check for any input fields that might be username/password
all_inputs = re.findall(r'<input[^>]*>', text2)
print(f"\nInputs en respuesta AJAX ({len(all_inputs)}):")
for inp in all_inputs:
    print(f"  {inp[:200]}")

# Look for form fields that are NOT hidden
for inp in all_inputs:
    if 'hidden' not in inp.lower():
        print(f"  VISIBLE: {inp}")

# Search for ANY credential-like text
text_clean = re.sub(r'<[^>]+>', ' ', text2)
text_clean = re.sub(r'\s+', ' ', text_clean).strip()
for kw in ['usuario', 'password', 'contraseña', 'clave', 'login', 'credencial']:
    if kw in text_clean.lower():
        idx = text_clean.lower().find(kw)
        ctx = text_clean[max(0,idx-50):idx+100]
        print(f"\n  [{kw}]: {ctx}")

# Check the button actions - what does cmdEstudiante do?
print("\n=== Verificando boton cmdEstudiante ===")
cmd_st_idx = text2.find('cmdEstudiante')
if cmd_st_idx > 0:
    ctx = text2[cmd_st_idx-100:cmd_st_idx+500]
    ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
    ctx_clean = re.sub(r'\s+', ' ', ctx_clean).strip()
    print(f"  {ctx_clean[:500]}")

# Now look at the FULL response to find the username/password form
# Search for any form elements
forms = re.findall(r'<form[^>]*id="[^"]*"[^>]*>(.*?)</form>', text2, re.DOTALL)
print(f"\nForms ({len(forms)}):")
for i, f in enumerate(forms):
    form_inputs = re.findall(r'<input[^>]*>', f)
    print(f"  Form {i}: {len(form_inputs)} inputs")
    for fi in form_inputs:
        if 'hidden' not in fi.lower():
            print(f"    VISIBLE: {fi[:200]}")

# Try to find the updated section by looking at what changed
# Compare with original login page
r_orig = s.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
# Find differences in body content
body_orig = re.sub(r'<script[^>]*>.*?</script>', '', r_orig.text, flags=re.DOTALL)
body_new = re.sub(r'<script[^>]*>.*?</script>', '', text2, flags=re.DOTALL)

# Extract text content
text_orig = re.sub(r'<[^>]+>', ' ', body_orig)
text_orig = re.sub(r'\s+', ' ', text_orig).strip()
text_new = re.sub(r'<[^>]+>', ' ', body_new)
text_new = re.sub(r'\s+', ' ', text_new).strip()

print(f"\n=== TEXTO ORIGINAL ===")
print(text_orig[:500])
print(f"\n=== TEXTO DESPUES DE CLICK ===")
print(text_new[:500])

# Check if the buttons changed
# Before: "Ingresar como ESTUDIANTE" should still be there
# After: might have a different section for credentials
if 'cmdEstudiante' not in text_new or 'cmdTrabajador' not in text_new:
    print("\n[!] Los botones de tipo desaparecieron - pagina cambio completamente")

# Look for any form with username/password in the entire response
print("\n=== Buscando campos escondidos en toda la respuesta ===")
# Search for patterns like input type="text" or input type="password"
type_inputs = re.findall(r'<input[^>]*type=["\'](text|password)["\'][^>]*>', text2)
print(f"Inputs text/password visibles: {len(type_inputs)}")
for ti in type_inputs:
    print(f"  {ti}")

# Also look for JSF component fields
jsf_fields = re.findall(r'<h:inputText[^>]*>', text2) + re.findall(r'<p:inputText[^>]*>', text2)
print(f"\nJSF inputText fields: {len(jsf_fields)}")
for jf in jsf_fields[:5]:
    print(f"  {jf[:200]}")

# Check if username/password is in a different format
# Maybe as a JSF component not in standard HTML
for pattern in ['itUsuario', 'itClave', 'txtUsuario', 'txtPassword', 'txtUser', 'txtPass']:
    if pattern in text2:
        idx = text2.find(pattern)
        ctx = text2[max(0,idx-50):idx+150]
        ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
        ctx_clean = re.sub(r'\s+', ' ', ctx_clean).strip()
        print(f"\n  [{pattern}]: {ctx_clean}")

# Final attempt: try to POST with the expected WebAlumno-style fields
print("\n=== PROBANDO LOGIN CON CAMPOS ESPERADOS ===")
s2 = requests.Session()
s2.verify = False
s2.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})
r3 = s2.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
vs3 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r3.text)
vstate3 = vs3.group(1) if vs3 else ""

# Try the most likely field names based on patterns
test_fields = {
    'frmLogueo:itUsuario': 'fake',
    'frmLogueo:itClave': 'fake',
    'frmLogueo:txtUsuario': 'fake',
    'frmLogueo:txtPassword': 'fake',
    'usuario': 'fake',
    'password': 'fake',
    'j_username': 'fake',
    'j_password': 'fake',
}

# Build a full form submission
# Need to click cmdEstudiante first, then submit the login form
# This is complex - let's try a different approach

# Try to POST with all possible field names
for field_name, value in test_fields.items():
    s3 = requests.Session()
    s3.verify = False
    s3.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
        'X-Requested-With': 'XMLHttpRequest',
    })
    # First click estudiante
    r_s = s3.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=5)
    vs_s = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_s.text)
    vs_s_val = vs_s.group(1) if vs_s else ""
    
    # Then click estudiante to load login form
    click_data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': vs_s_val,
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': 'frmLogueo:cmdEstudiante',
        'javax.faces.partial.execute': 'frmLogueo',
        'javax.faces.partial.render': 'frmLogueo',
    }
    r_click = s3.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                        data=click_data, timeout=5)
    
    # Then try to login
    login_data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': '',
        field_name: value,
    }
    r_login = s3.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                        data=login_data, timeout=5)
    tc = re.sub(r'<[^>]+>', ' ', r_login.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    if len(r_login.text) > 12591:
        print(f"  {field_name}={value} -> len={len(r_login.text)} [PODRIA FUNCIONAR]")
    else:
        print(f"  {field_name}={value} -> len={len(r_login.text)}")

print("\n=== CONCLUSION ===")
print("WebPasaporte usa un flujo de 2 pasos:")
print("  1. Seleccionar tipo (Estudiante/Trabajador)")
print("  2. Aparecen campos de usuario/password via JavaScript")
print("  Los campos de login son dinamicos (insertados por JS)")
print("  Para ver los nombres exactos, necesitas abrir el navegador F12")
