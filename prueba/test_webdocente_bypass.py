#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

# Test 1: Can SIIGAA session access WebDocente?
print("=== TEST 1: Sesion SIIGAA en WebDocente ===")
s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})
r = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
              data={'j_username':'fake','j_password':'fake'}, timeout=10)
jsession = dict(s.cookies).get('JSESSIONID', '')
print(f"SIIGAA JSESSIONID: {jsession}")

# Try WebDocente with same session
r_wd = s.get('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml', timeout=10)
tc = re.sub(r'<[^>]+>', ' ', r_wd.text)
tc = re.sub(r'\s+', ' ', tc).strip()
print(f"WebDocente: HTTP {r_wd.status_code}, len={len(r_wd.text)}")

# Test 2: cmdInstruccion (instructions - might not need login)
print("\n=== TEST 2: cmdInstruccion (instrucciones) ===")
s2 = requests.Session()
s2.verify = False
s2.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
})
r0 = s2.get('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml', timeout=5)
vs0 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r0.text)
vs0_val = vs0.group(1) if vs0 else ""

# Submit cmdInstruccion (instructions button)
click_data = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vs0_val,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdInstruccion',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmInstrucciones',
}
r_click = s2.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                       data=click_data, timeout=5)
tc_click = re.sub(r'<[^>]+>', ' ', r_click.text)
tc_click = re.sub(r'\s+', ' ', tc_click).strip()
print(f"cmdInstruccion: len={len(r_click.text)}")
print(f"Content: {tc_click[:400]}")
if any(kw in tc_click.lower() for kw in ['instruccion', 'manual', 'ayuda', 'guia', 'password', 'clave']):
    print(f"  [!] Contiene instrucciones o clave!")

# Test 3: cmdVerClave (view password)
print("\n=== TEST 3: cmdVerClave ===")
s3 = requests.Session()
s3.verify = False
s3.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
})
r3a = s3.get('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml', timeout=5)
vs3a = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r3a.text)
vs3a_val = vs3a.group(1) if vs3a else ""
click_d3 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vs3a_val,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdVerClave',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r_click3 = s3.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                        data=click_d3, timeout=5)
tc_click3 = re.sub(r'<[^>]+>', ' ', r_click3.text)
tc_click3 = re.sub(r'\s+', ' ', tc_click3).strip()
print(f"cmdVerClave: len={len(r_click3.text)}")
if any(kw in tc_click3.lower() for kw in ['password', 'clave', 'ocultar', 'ver']):
    print(f"  [!] Muestra password! Content: {tc_click3[:300]}")

# Test 4: Empty submit (only frmLogueo)
print("\n=== TEST 4: Submit solo frmLogueo ===")
s4 = requests.Session()
s4.verify = False
s4.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
})
r4 = s4.get('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml', timeout=5)
vs4 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r4.text)
vs4_val = vs4.group(1) if vs4 else ""
r_empty = s4.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                       data={'frmLogueo': 'frmLogueo', 'jakarta.faces.ViewState': vs4_val}, timeout=5)
tc_empty = re.sub(r'<[^>]+>', ' ', r_empty.text)
tc_empty = re.sub(r'\s+', ' ', tc_empty).strip()
print(f"len={len(r_empty.text)}, original=19364, changed={len(r_empty.text)!=19364}")

# Test 5: frmInstrucciones form
print("\n=== TEST 5: frmInstrucciones form ===")
s5 = requests.Session()
s5.verify = False
s5.headers.update({'User-Agent': 'Mozilla/5.0'})
r5 = s5.get('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml', timeout=5)
# Find the frmInstrucciones form
form_match = re.search(r'<form id="frmInstrucciones"[^>]*>(.*?)</form>', r5.text, re.DOTALL)
if form_match:
    form_html = form_match.group(1)
    inputs = re.findall(r'<input[^>]*>', form_html)
    buttons = re.findall(r'<button[^>]*>', form_html)
    print(f"frmInstrucciones inputs: {inputs}")
    print(f"frmInstrucciones buttons: {buttons}")
    
    # Submit the instructions form
    inst_data = {'frmInstrucciones': 'frmInstrucciones'}
    r_inst = s5.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                           data=inst_data, timeout=5)
    tc_inst = re.sub(r'<[^>]+>', ' ', r_inst.text)
    tc_inst = re.sub(r'\s+', ' ', tc_inst).strip()
    print(f"frmInstrucciones submit: len={len(r_inst.text)}")
    print(f"Content: {tc_inst[:300]}")
    if any(kw in tc_inst.lower() for kw in ['instruccion', 'manual', 'ayuda', 'guia']):
        print(f"  [!] Muestra instrucciones sin credenciales!")

# Test 6: Try to access WebDocente without ANY click - just the login page
print("\n=== TEST 6: Acceso directo sin click ===")
s6 = requests.Session()
s6.verify = False
s6.headers.update({'User-Agent': 'Mozilla/5.0'})
r6 = s6.get('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml', timeout=5)
# Check if login page shows anything accessible
# Look for any text that might give access
tc6 = re.sub(r'<[^>]+>', ' ', r6.text)
tc6 = re.sub(r'\s+', ' ', tc6).strip()
# Find ALL text on the page
print(f"Full text preview: {tc6[:500]}")

# Find all links
links = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', r6.text)
print(f"\nLinks:")
for l in links[:10]:
    print(f"  {l[0]} -> {l[1]}")

# Find any visible text
visible = re.findall(r'>([^<]{5,100})<', r6.text)
print(f"\nText visible:")
for v in visible[:20]:
    print(f"  {v.strip()}")

print("\n=== RESUMEN ===")
print("cmdInstruccion: Muestra instrucciones sin login?")
print("cmdVerClave: Muestra clave sin login?")
print("frmInstrucciones: Formulario de instrucciones")
print("El login sigue requiriendo credenciales validas")
