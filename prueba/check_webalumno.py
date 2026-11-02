#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# Test the new URL with port 80
print("=== URL CON PUERTO 80 ===")
r = s.get('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml', timeout=10)
print(f"Status: {r.status_code}")
print(f"URL: {r.url}")
print(f"Len: {len(r.text)}")
print(f"Content-Type: {r.headers.get('Content-Type')}")
print(f"Server: {r.headers.get('Server')}")

# Check redirects
if r.history:
    print(f"Redirected from: {[h.url for h in r.history]}")

text = r.text
if 'j_username' in text.lower() or 'j_password' in text.lower():
    print("-> Es pagina de LOGIN")
    forms = re.findall(r'<form[^>]*>', text)
    for f in forms[:3]:
        print(f"  Form: {f[:200]}")
    inputs = re.findall(r'<input[^>]*>', text)
    for i in inputs[:10]:
        print(f"  Input: {i[:150]}")
elif 'error' in text.lower() or 'bloque' in text.lower() or 'solo' in text.lower():
    print("-> Bloqueado o error")
    print(text[:500])
else:
    print(f"Preview: {text[:500]}")

# Try without port 80
print("\n=== URL SIN PUERTO 80 ===")
r2 = s.get('https://registro.uns.edu.pe/WebAlumno/faces/login.xhtml', timeout=10)
print(f"Status: {r2.status_code}, len={len(r2.text)}")
text2 = r2.text
if 'j_username' in text2.lower():
    print("-> Es pagina de LOGIN")
    forms2 = re.findall(r'<form[^>]*>', text2)
    for f in forms2[:2]:
        print(f"  Form: {f[:200]}")

# Check if WebAlumno is a different application
print("\n=== WEBALUMINO ENDPOINTS ===")
for url in [
    'https://registro.uns.edu.pe/WebAlumno/',
    'https://registro.uns.edu.pe/WebAlumno/faces/',
    'https://registro.uns.edu.pe/WebAlumno/faces/modulos.xhtml',
]:
    try:
        r3 = s.get(url, timeout=5)
        print(f"  {url} -> {r3.status_code}, len={len(r3.text)}")
    except:
        pass

# Check WebPasaporte
print("\n=== WEB PASAPORTE ===")
for url in [
    'https://registro.uns.edu.pe/WebPasaporte',
    'https://registro.uns.edu.pe/WebPasaporte/',
]:
    try:
        r4 = s.get(url, timeout=5)
        print(f"  {url} -> {r4.status_code}, len={len(r4.text)}")
    except:
        pass

# Check if it's the same application with different path
print("\n=== COMPARANDO ===")
print(f"SIIGAA login: {len(s.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5).text)} bytes")
print(f"WebAlumno login: {len(r.text)} bytes")
print(f"WebAlumno (sin faces): {len(r2.text)} bytes")
