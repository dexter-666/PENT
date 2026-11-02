#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_soft404.py — Validador de hallazgos del scanner (anti-falsos positivos).

El scanner de archivos sensibles marca como HIGH cualquier ruta que responde 200.
Muchos servidores (Moodle/OpenResty) responden 200 con la página de login o de
error para rutas inexistentes ("soft 404"). Este script:

  1. Descarga la página de referencia (login).
  2. Descarga cada ruta "hallada" y compara hash MD5 del contenido.
  3. Si el contenido es idéntico al login => SOFT-404 (falso positivo).
  4. Detecta la plataforma (generator meta) y versión expuesta.
  5. Verifica el comportamiento HTTP -> HTTPS (redirección real).

USO: python verify_soft404.py --base-url https://campus.uns.edu.pe
"""
import argparse
import hashlib
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PATHS = [
    "/.git/config", "/.git/COMMIT_EDITMSG", "/.svn/entries", "/.svn/wc.db", "/.hg/",
    "/.env.local", "/.env.production", "/config.php", "/config/database.yml",
    "/application.properties", "/settings.py", "/config/settings.ini", "/web.config",
    "/backup.sql", "/backup.zip", "/backup.tar.gz", "/db.sql", "/database.sql",
    "/dump.sql", "/site.zip", "/www.zip", "/old/", "/backup/",
    "/debug/", "/console", "/actuator", "/actuator/health",
    "/administrator/", "/wp-admin/", "/phpmyadmin/", "/manager/html", "/jmx-console/",
    "/admin-console/", "/swagger-ui/", "/api-docs", "/v2/api-docs", "/openapi.json",
    "/api/swagger.json", "/graphql", "/error.log", "/access.log", "/logs/error.log",
    "/app/logs/application.log", "/storage/logs/laravel.log", "/robots.txt",
    "/sitemap.xml", "/crossdomain.xml", "/security.txt", "/.well-known/security.txt",
]

HEADERS = {"User-Agent": "Thesis-Security-Audit/1.0"}


def get(url, follow=False):
    try:
        return requests.get(url, timeout=12, verify=False, headers=HEADERS,
                            allow_redirects=follow)
    except requests.RequestException:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://campus.uns.edu.pe")
    parser.add_argument("--login-path", default="/login/index.php")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    print("=" * 78)
    print("VERIFICADOR DE SOFT-404 — campus.uns.edu.pe")
    print("=" * 78)

    # ── 1. Página de referencia (login) ─────────────────────────────────
    login = get(base + args.login_path, follow=True)
    if login is None:
        print("[!] No se pudo obtener la página de login. Abortando.")
        sys.exit(1)

    login_md5 = hashlib.md5(login.content).hexdigest()
    print(f"\n[REFERENCIA] {base}{args.login_path}")
    print(f"  Status: {login.status_code} | Length: {len(login.content)} | MD5: {login_md5}")

    import re
    gen = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', login.text, re.I)
    title = re.search(r"<title[^>]*>(.*?)</title>", login.text, re.I | re.S)
    print(f"  Title: {title.group(1).strip()[:80] if title else 'N/A'}")
    print(f"  Generator: {gen.group(1) if gen else 'N/A'}")

    # ── 2. HTTP → HTTPS ─────────────────────────────────────────────────
    http_url = "http://" + base.split("//", 1)[1] + args.login_path
    r = get(http_url, follow=False)
    if r is not None:
        loc = r.headers.get("Location", "")
        print(f"\n[HTTP→HTTPS] GET {http_url}")
        print(f"  Status: {r.status_code} | Location: {loc or '(sin redirección)'}")
        if r.status_code == 200:
            print("  ⚠️ Sirve contenido por HTTP en claro (sin cifrar)")
    else:
        print(f"\n[HTTP→HTTPS] No responde por puerto 80")

    # ── 3. Cookies de la sesión de login ────────────────────────────────
    print(f"\n[COOKIES] Set-Cookie en login:")
    for name, value in login.cookies.items():
        flags = []
        sc = None
        for hdr in login.raw.headers.getlist("Set-Cookie") if hasattr(login.raw.headers, "getlist") else []:
            if hdr.startswith(name + "="):
                sc = hdr
        print(f"  {name} = {value[:20]}...")
        if sc:
            print(f"    Raw: {sc[:120]}")

    # ── 4. Verificación ruta por ruta ───────────────────────────────────
    print(f"\n{'RUTA':<32} {'ST':<4} {'LEN':<8} {'CONTENIDO'}")
    print("-" * 78)
    real_findings = []
    soft404_count = 0
    for p in PATHS:
        r = get(base + p, follow=False)
        if r is None:
            print(f"{p:<32} ERR  -        (timeout/error)")
            continue
        content_md5 = hashlib.md5(r.content).hexdigest()
        if r.status_code == 200 and content_md5 == login_md5:
            verdict = "SOFT-404 (mismo contenido que login) → FALSO POSITIVO"
            soft404_count += 1
        elif r.status_code in (301, 302, 303, 307, 308):
            verdict = f"REDIRECT {r.status_code} → {r.headers.get('Location', '?')[:40]}"
        elif r.status_code in (401, 403):
            verdict = "Protegido (401/403) — existe pero requiere autenticación"
            real_findings.append((p, r.status_code, verdict))
        elif r.status_code == 200:
            verdict = "⚠️ 200 CON CONTENIDO DIFERENTE — REVISAR MANUALMENTE"
            real_findings.append((p, r.status_code, verdict))
        else:
            verdict = f"{r.status_code} (no expuesto)"
        print(f"{p:<32} {r.status_code:<4} {len(r.content):<8} {verdict}")

    # ── 5. Resumen ──────────────────────────────────────────────────────
    print("\n" + "=" * 78)
    print("RESUMEN DE VALIDACIÓN")
    print("=" * 78)
    print(f"  Rutas verificadas:      {len(PATHS)}")
    print(f"  Falsos positivos (soft-404): {soft404_count}")
    print(f"  Hallazgos a revisar:    {len(real_findings)}")
    for p, st, v in real_findings:
        print(f"    - {p} [{st}] {v}")


if __name__ == "__main__":
    main()
