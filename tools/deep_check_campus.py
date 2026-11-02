#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deep_check_campus.py — Verificacion profunda para campus.uns.edu.pe.

1. Compara MD5 entre rutas "halladas" (deteccion de soft-404 real).
2. Inspecciona titulo/content-type de rutas clave.
3. Extrae el action del form de login servido por HTTP (claro).
4. Busca disclosure de version de Moodle.
"""
import hashlib
import io
import re
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
H = {"User-Agent": "Thesis-Security-Audit/1.0"}
BASE = "https://campus.uns.edu.pe"


def get(url, follow=False):
    try:
        return requests.get(url, timeout=12, verify=False, headers=H,
                            allow_redirects=follow)
    except requests.RequestException:
        return None


print("=" * 78)
print("DEEP CHECK — campus.uns.edu.pe")
print("=" * 78)

# 1. MD5 comparison between "found" paths
print("\n[1] COMPARACION DE CONTENIDO ENTRE RUTAS 'HALLADAS'")
md5s = {}
for p in ["/.git/config", "/backup.sql", "/phpmyadmin/", "/actuator",
          "/robots.txt", "/sitemap.xml", "/security.txt", "/crossdomain.xml",
          "/error.log", "/console", "/debug/", "/old/", "/swagger-ui/"]:
    r = get(BASE + p)
    if r is None:
        print(f"  {p:<22} ERROR")
        continue
    md5 = hashlib.md5(r.content).hexdigest()[:10]
    md5s.setdefault(md5, []).append(p)
    t = re.search(r"<title[^>]*>(.*?)</title>", r.text, re.I | re.S)
    title = (t.group(1).strip()[:50] if t else "N/A").replace("\n", " ")
    print(f"  {p:<22} {r.status_code:<4} len={len(r.content):<6} md5={md5} title=\"{title}\"")

print("\n  -> Grupos de contenido IDENTICO:")
for md5, paths in md5s.items():
    if len(paths) > 1:
        print(f"     md5={md5}: {len(paths)} rutas con contenido identico (ej: {paths[0]})")

# 2. Form action over plaintext HTTP
print("\n[2] FORM ACTION DEL LOGIN POR HTTP (CLARO)")
r = get("http://campus.uns.edu.pe/login/index.php", follow=True)
if r:
    m = re.search(r'<form[^>]*action=["\']([^"\']+)', r.text, re.I)
    print(f"  Status final: {r.status_code} | URL final: {r.url}")
    print(f"  Form action: {m.group(1) if m else 'N/A'}")
else:
    print("  No responde por HTTP")

# 3. Moodle version disclosure
print("\n[3] DISCLOSURE DE VERSION (Moodle)")
r = get(BASE + "/login/index.php", follow=True)
if r:
    found = False
    for pat in [r"Moodle\s*[vV]?[0-9]+\.[0-9]+[0-9A-Za-z.\-]*",
                r"moodle/[0-9]+",
                r"version[\"' ]*[=:][\"' ]*[0-9]+\.[0-9]+[0-9A-Za-z.\-]*"]:
        ms = re.findall(pat, r.text, re.I)
        if ms:
            print(f"  Patron /{pat[:25]}/ -> {ms[:4]}")
            found = True
    if not found:
        print("  No se detecta version explicita en el login (sin disclosure).")

# 4. robots.txt / security.txt reales?
print("\n[4] CONTENIDO DE POSITIVOS 'LEGITIMOS'")
for p in ["/robots.txt", "/security.txt", "/sitemap.xml"]:
    r = get(BASE + p)
    if r and r.status_code == 200:
        body = r.text[:200].replace("\n", " | ").strip()
        print(f"  {p}: {body}")
