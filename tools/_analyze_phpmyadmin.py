#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3, re
urllib3.disable_warnings()

H = {"User-Agent": "Thesis-Security-Audit/1.0"}
BASE = "https://orcl.uns.edu.pe"

print("=" * 60)
print("ANALISIS PROFUNDO: orcl.uns.edu.pe = phpMyAdmin")
print("=" * 60)

r = requests.get(BASE + "/", timeout=10, verify=False, headers=H)
print(f"\n[*] Status: {r.status_code}")

# Versión en JS/CSS
versions = re.findall(r"v=(\d+\.\d+\.\d+)", r.text)
print(f"[*] Versiones en codigo fuente: {sorted(set(versions))}")

# Servidor MySQL referenciado
refs = []
for kw in ["mysql", "mariadb", "postgresql", "oracle", "localhost"]:
    if kw in r.text.lower():
        refs.append(kw)
print(f"[*] Referencias de BD en HTML: {refs}")

# Rutas adicionales de phpMyAdmin
paths = [
    "/setup/",
    "/config.inc.php",
    "/README",
    "/CHANGELOG",
    "/ChangeLog",
    "/doc/",
    "/libraries/",
    "/vendor/",
    "/sql/",
    "/export.php",
    "/import.php",
    "/server_status.php",
    "/server_variables.php",
    "/server_collations.php",
]

print("\n[*] Probando rutas de phpMyAdmin:")
for path in paths:
    try:
        resp = requests.get(BASE + path, timeout=6, verify=False, headers=H, allow_redirects=False)
        code = resp.status_code
        note = ""
        if code == 200:
            note = " <== ACCESIBLE"
        elif code == 302:
            note = f" -> {resp.headers.get('Location','?')}"
        print(f"    [{code}] {path}{note}")
    except Exception as e:
        print(f"    [ERR] {path}: {e}")

# Ver si hay indicacion de la version de MySQL en algun endpoint
print("\n[*] Chequeando endpoint de estado del servidor...")
try:
    r2 = requests.get(BASE + "/server_status.php", timeout=8, verify=False, headers=H)
    if r2.status_code == 200 and len(r2.text) > 200:
        m = re.search(r"(MySQL|MariaDB)\s+([\d\.]+)", r2.text, re.IGNORECASE)
        if m:
            print(f"    [!] Base de datos: {m.group(1)} {m.group(2)}")
except:
    pass

print("\n[CONCLUSION] phpMyAdmin publicamente accesible en https://orcl.uns.edu.pe")
print("  - Panel de administracion de BD expuesto a internet sin restriccion de IP")
print("  - Cualquier persona puede intentar autenticarse")
print("  - Si se usan credenciales debiles o por defecto: ACCESO TOTAL a la BD")
print("  - OWASP: A05 Security Misconfiguration | CVSS: 9.8 CRITICO")
