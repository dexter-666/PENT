#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_exposure.py — Verificación pasiva de superficie de ataque.
Solo realiza GET a páginas públicas. NO ejecuta ataques activos.
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
H = {"User-Agent": "Thesis-Security-Audit/1.0"}
BASE = "https://campus.uns.edu.pe"

def get(path, follow=True):
    try:
        return requests.get(BASE + path, timeout=12, verify=False,
                            headers=H, allow_redirects=follow)
    except requests.RequestException:
        return None

print("=" * 78)
print("VERIFICACIÓN PASIVA DE SUPERFICIE DE ATAQUE")
print("campus.uns.edu.pe — Solo GET a páginas públicas")
print("=" * 78)

# 1. ¿Registro abierto?
print("\n[1] ¿Registro de usuarios abierto?")
r = get("/login/index.php")
if r:
    has_register = bool(re.search(r'(registr|crear cuenta|sign up|register)', r.text, re.I))
    print(f"  Login page status: {r.status_code}")
    print(f"  ¿Muestra opción de registro?: {'SÍ ⚠️' if has_register else 'NO (solo SSO o registro deshabilitado)'}")
    # Buscar enlaces de registro
    links = re.findall(r'href=["\']([^"\']*registr[^"\']*)', r.text, re.I)
    if links:
        print(f"  Enlaces encontrados: {links[:3]}")

# 2. ¿API REST expuesta?
print("\n[2] ¿API REST de Moodle expuesta?")
for path in ["/webservice/rest/server.php", "/webservice/rest/server.php?wstoken=test",
             "/login/token.php", "/admin/tool/rest/"]:
    r = get(path, follow=False)
    if r:
        ct = r.headers.get('Content-Type', '?')[:40]
        print(f"  {path:<45} {r.status_code} | CT: {ct}")
        if r.status_code == 200:
            body = r.text[:150].replace('\n', ' ')
            print(f"    Body: {body}")

# 3. ¿Recuperación de contraseña revela info?
print("\n[3] Página de recuperación de contraseña")
for path in ["/login/forgot_password.php", "/login/index.php?forgot=1"]:
    r = get(path)
    if r:
        print(f"  {path:<40} {r.status_code} | len={len(r.content)}")
        # ¿Revela si el usuario existe?
        if 'no coinciden' in r.text.lower() or 'not found' in r.text.lower():
            print("  ⚠️ Posible user enumeration (mensajes diferentes para usuario existente/inexistente)")

# 4. ¿Moodle version exacta? (CVEs específicos)
print("\n[4] Versión de Moodle (búsqueda de CVEs)")
r = get("/login/index.php")
if r:
    # Buscar en diferentes lugares
    patterns = [
        (r' Moodle\s*([0-9]+\.[0-9]+[0-9A-Za-z.\-]*)', 'Texto visible'),
        (r'moodle[^/]*?([0-9]+\.[0-9]+[0-9A-Za-z.\-]*)', 'Rutas/URLs'),
        (r'version=([0-9]+\.[0-9]+[0-9A-Za-z.\-]*)', 'Query params'),
    ]
    for pat, desc in patterns:
        m = re.search(pat, r.text, re.I)
        if m:
            print(f"  Posible versión: {m.group(1)} (fuente: {desc})")

    # Buscar en /lib/ o /version.php (si está expuesto)
    r2 = get("/version.php", follow=False)
    if r2 and r2.status_code == 200:
        print(f"  /version.php: {r2.status_code} — ¡VERSIÓN EXPUESTA!")
        print(f"  Contenido: {r2.text[:200]}")

# 5. ¿Debug mode activo?
print("\n[5] ¿Modo debug de Moodle activo?")
if r:
    if 'debug' in r.text.lower() and ('error' in r.text.lower() or 'warning' in r.text.lower()):
        print("  ⚠️ Posiblemente SÍ (hay mensajes de debug/warning en la página)")
    else:
        print("  No se detecta debug en la página de login")

# 6. ¿Directorios comunes accesibles?
print("\n[6] Directorios comunes (verificación rápida)")
for path in ["/admin/", "/backup/", "/files/", "/course/", "/user/",
             "/mod/", "/theme/", "/lang/", "/filter/", "/lib/", "/install/"]:
    r = get(path, follow=False)
    if r:
        st = r.status_code
        note = ""
        if st == 200:
            note = "⚠️ ACCESIBLE"
        elif st in (301, 302):
            loc = r.headers.get('Location', '?')[:50]
            note = f"→ redirect a {loc}"
        elif st == 403:
            note = "protegido (403)"
        elif st == 404:
            note = "404 (soft-404 → revisar contenido)"
        print(f"  {path:<20} {st:<4} {note}")

# 7. Headers completos del login
print("\n[7] Headers HTTP completos del login (HTTPS)")
r = get("/login/index.php", follow=False)
if r:
    for k, v in r.headers.items():
        print(f"  {k}: {v[:80]}")

print("\n" + "=" * 78)
print("VERIFICACIÓN COMPLETADA")
print("=" * 78)
