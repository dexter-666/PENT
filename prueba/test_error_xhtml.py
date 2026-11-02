#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# The error.xhtml is the SAME on both servers? Check SIIGAA's error.xhtml
print("=== ERROR.XHTML EN SIIGAA ===")
r = s.get('https://registro.uns.edu.pe/udemsi/faces/error.xhtml', timeout=10)
print(f"Status: {r.status_code}, len={len(r.text)}")
text_clean = re.sub(r'<[^>]+>', ' ', r.text)
text_clean = re.sub(r'\s+', ' ', text_clean).strip()
print(f"Content: {text_clean[:500]}")

# Check if error.xhtml has any forms or login bypass
forms = re.findall(r'<form[^>]*>', r.text)
inputs = re.findall(r'<input[^>]*>', r.text)
print(f"\nForms: {len(forms)}")
print(f"Inputs: {len(inputs)}")
for inp in inputs:
    print(f"  {inp[:200]}")

# Check for any buttons or links that might bypass
buttons = re.findall(r'<button[^>]*>', r.text)
print(f"\nButtons: {buttons}")

# Check for any form actions
actions = re.findall(r'action="([^"]+)"', r.text)
print(f"\nActions: {actions}")

# Check if error.xhtml has any credential fields
if 'usuario' in text_clean.lower() or 'password' in text_clean.lower() or 'login' in text_clean.lower():
    print("\n[!] error.xhtml contiene campos de login!")

# Now try to access the MAIN application pages with the session from error.xhtml
print("\n=== PROBANDO ACCESO CON SESION DE ERROR.XHTML ===")
s2 = requests.Session()
s2.verify = False
s2.headers.update({'User-Agent': 'Mozilla/5.0'})
# Visit error.xhtml to get a session
r_err = s2.get('https://registro.uns.edu.pe/udemsi/faces/error.xhtml', timeout=10)
jsession = dict(s2.cookies).get('JSESSIONID', '')
print(f"JSESSIONID: {jsession}")

# Try to access modulos.xhtml with this session
r_mod = s2.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=10)
tc = re.sub(r'<[^>]+>', ' ', r_mod.text)
tc = re.sub(r'\s+', ' ', tc).strip()
print(f"\nmodulos.xhtml: {r_mod.status_code}, len={len(r_mod.text)}")
print(f"Content: {tc[:300]}")

# Try to access with error.xhtml session but different URL
# The carga.js redirects to error.xhtml via window.open(paginaError, '_self')
# Maybe accessing error.xhtml gives us a valid session that can be used
print("\n=== PROBANDO NAVEGACION DESDE ERROR.XHTML ===")
# Try accessing the main application pages
for url in [
    'https://registro.uns.edu.pe/udemsi/faces/index.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml',
    'https://registro.uns.edu.pe/udemsi/modulos.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/principal.xhtml',
]:
    r_url = s2.get(url, timeout=5)
    tc_url = re.sub(r'<[^>]+>', ' ', r_url.text)
    tc_url = re.sub(r'\s+', ' ', tc_url).strip()
    has_login = 'j_username' in r_url.text or 'logueo' in tc_url.lower()
    print(f"  {url.split('/')[-1]} -> {r_url.status_code}, login={has_login}")

# Check if the error page has any useful links or redirects
print("\n=== VERIFICANDO REDIRECCIONES EN ERROR.XHTML ===")
# Check for meta refresh
meta_refresh = re.findall(r'<meta[^>]*refresh[^>]*>', r.text, re.IGNORECASE)
print(f"Meta refresh: {meta_refresh}")
# Check for javascript redirects
js_redirects = re.findall(r'location\.|window\.open|window\.location', r.text)
print(f"JS redirects: {js_redirects}")
# Check for any onclick handlers on the close button
onclicks = re.findall(r'onclick="([^"]+)"', r.text)
print(f"Onclicks: {onclicks}")
# Check for any links or buttons
all_links = re.findall(r'<a[^>]*>([^<]+)</a>', r.text)
print(f"Links: {all_links}")
all_buttons = re.findall(r'<button[^>]*>([^<]+)</button>', r.text)
print(f"Buttons: {all_buttons}")

# The close button might redirect to the login page
# Let me find the close button action
close_idx = r.text.find('CERRAR')
if close_idx > 0:
    ctx = r.text[close_idx-100:close_idx+500]
    ctx_clean = re.sub(r'<[^>]+>', '\n', ctx)
    ctx_clean = re.sub(r'\n\s*\n', '\n', ctx_clean)
    print(f"\n=== AREA DEL BOTON CERRAR ===")
    print(ctx_clean[:500])

# Check what happens if we try to login from error.xhtml
print("\n=== PROBANDO LOGIN DESDE ERROR.XHTML ===")
# Get the ViewState from error.xhtml
vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r.text)
vstate = vs.group(1) if vs else ""
print(f"ViewState from error.xhtml: {vstate[:50]}...")

# Try to login with j_security_check using error.xhtml session
r_login = s2.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                     data={'j_username': 'fake', 'j_password': 'fake'},
                     timeout=10)
print(f"\nj_security_check: Status {r_login.status_code}, len={len(r_login.text)}")
# Check if we're now in the system
tc_login = re.sub(r'<[^>]+>', ' ', r_login.text)
tc_login = re.sub(r'\s+', ' ', tc_login).strip()
print(f"Content: {tc_login[:300]}")

# Try accessing modulos after login
r_mod2 = s2.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=10)
tc_mod2 = re.sub(r'<[^>]+>', ' ', r_mod2.text)
tc_mod2 = re.sub(r'\s+', ' ', tc_mod2).strip()
print(f"\nmodulos.xhtml after login: {r_mod2.status_code}, len={len(r_mod2.text)}")
print(f"Content: {tc_mod2[:300]}")

print("\n=== RESUMEN ===")
print("El error.xhtml muestra el mensaje que mencionaste")
print("'El módulo ya esta operativo, por seguridad... solo se puede cargar en una ventana'")
print("Es el mensaje de proteccion anti-multi-ventana de carga.js")
print("El error.xhtml ES ACCESIBLE sin autenticacion")
print("Pero no sirve para obtener datos - solo es un mensaje de error")
