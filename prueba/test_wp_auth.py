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

# Get the page and click estudiante first
r = s.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r.text)
vstate = vs.group(1) if vs else ""

# Click cmdEstudiante to load the login form
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

# Now try login with itUsuario
print("=== PROBANDO frmLogueo:itUsuario = fake ===")
login_data = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate,
    'frmLogueo:itUsuario': 'fake',
    'frmLogueo:itClave': 'fake',
}
r_login = s.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                     data=login_data, timeout=10, allow_redirects=True)
print(f"Status: {r_login.status_code}, len={len(r_login.text)}")

# Check what's in the response
text = r_login.text
text_clean = re.sub(r'<[^>]+>', ' ', text)
text_clean = re.sub(r'\s+', ' ', text_clean).strip()
print(f"\nContenido: {text_clean[:500]}")

# Check if it contains login page, dashboard, or error
if 'logueo' in text_clean.lower() and 'cmdEstudiante' in text_clean:
    print("-> Todavia en la pagina de login")
elif 'error' in text_clean.lower() and 'logueo' not in text_clean.lower():
    print("-> Error de login")
elif any(kw in text_clean.lower() for kw in ['bienvenido', 'inicio', 'modulo', 'dashboard', 'logout']):
    print("-> ACCESO CONCEDIDO!")
elif len(text_clean) > 5000:
    print("-> Contenido extenso - verificar")

# Check if it's an error page
if 'error.xhtml' in text or 'Error' in text_clean[:200]:
    print("-> Es pagina de error")

# Look for any messages
messages = re.findall(r'(?:error|acceso|denegado|autorizado|exito|falla|correcto)[^<]{0,100}', text_clean, re.IGNORECASE)
for m in messages[:5]:
    print(f"  Mensaje: {m}")

# Check for specific text
for kw in ['usuario', 'contraseña', 'incorrecto', 'invalido', 'correcto', 'bienvenido', 'error', 'acceso', 'denegado']:
    idx = text_clean.lower().find(kw)
    if idx > 0:
        ctx = text_clean[max(0,idx-50):idx+100]
        print(f"  [{kw}]: {ctx}")

# Check headers
print(f"\nHeaders: {dict(r_login.headers)}")
print(f"Cookies: {dict(s.cookies)}")

# Check if the response is a redirect
print(f"\nHistory: {[h.url for h in r_login.history]}")
print(f"Final URL: {r_login.url}")

# Look at the actual HTML - strip everything to find meaningful content
print("\n=== CONTENIDO REAL ===")
body_match = re.search(r'<body[^>]*>(.*?)</body>', text, re.DOTALL)
if body_match:
    body = body_match.group(1)
    body_clean = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
    body_clean = re.sub(r'</?[^>]+>', ' ', body_clean)
    body_clean = re.sub(r'\s+', ' ', body_clean).strip()
    print(f"  {body_clean[:1000]}")

# Try the original login page without clicking estudiante first
print("\n=== PROBANDO SIN CLICK PREVIO ===")
s2 = requests.Session()
s2.verify = False
s2.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
})
r2 = s2.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
vs2 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r2.text)
vstate2 = vs2.group(1) if vs2 else ""

# Try login directly without clicking estudiante
login_data2 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vstate2,
    'frmLogueo:itUsuario': 'fake',
    'frmLogueo:itClave': 'fake',
}
r3 = s2.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                 data=login_data2, timeout=10)
print(f"Direct POST: Status {r3.status_code}, len={len(r3.text)}")
tc3 = re.sub(r'<[^>]+>', ' ', r3.text)
tc3 = re.sub(r'\s+', ' ', tc3).strip()
print(f"Content: {tc3[:300]}")

# Try with just the username (like j_security_check style)
print("\n=== PROBANDO j_username style ===")
s3 = requests.Session()
s3.verify = False
s3.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
})
r4 = s3.post('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
                data={'j_username': 'fake', 'j_password': 'fake'}, timeout=10)
print(f"j_username: Status {r4.status_code}, len={len(r4.text)}")
