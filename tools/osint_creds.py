#!/usr/bin/env python3
"""
OSINT de credenciales filtradas para uns.edu.pe
Busca en fuentes publicas: HaveIBeenPwned API, crt.sh, GitHub, Pastebin dorks
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests, urllib3, re, json, time
urllib3.disable_warnings()

DOMAIN = "uns.edu.pe"
HEADERS = {"User-Agent": "Security-Research/1.0"}

print(f"=== OSINT Credenciales — {DOMAIN} ===\n")

# ─────────────────────────────────────────────
# 1. crt.sh — subdominios adicionales
# ─────────────────────────────────────────────
print("--- 1. crt.sh: Subdominios via Certificate Transparency ---")
try:
    r = requests.get(f"https://crt.sh/?q=%.{DOMAIN}&output=json",
                     timeout=20, headers=HEADERS)
    if r.status_code == 200:
        certs = r.json()
        subdomains = set()
        for c in certs:
            names = c.get("name_value","").split("\n")
            for n in names:
                n = n.strip().lstrip("*.")
                if DOMAIN in n and n != DOMAIN:
                    subdomains.add(n)
        print(f"  Subdominios encontrados via CT logs: {len(subdomains)}")
        for s in sorted(subdomains)[:40]:
            print(f"    {s}")
    else:
        print(f"  Error: HTTP {r.status_code}")
except Exception as e:
    print(f"  Error crt.sh: {e}")

print()

# ─────────────────────────────────────────────
# 2. HaveIBeenPwned — dominio en breaches
# ─────────────────────────────────────────────
print("--- 2. HIBP Domain Search (breach summary) ---")
try:
    # HIBP API v3 requiere API key para breach lookup por dominio
    # Usamos el endpoint publico de pastes (limitado)
    r = requests.get(
        f"https://haveibeenpwned.com/api/v3/breaches",
        timeout=15,
        headers={**HEADERS, "hibp-api-key": "none"}
    )
    # Sin key solo podemos ver breaches publicos, no por dominio
    # Reportamos el estado
    print(f"  HIBP requiere API key para busqueda por dominio.")
    print(f"  Recomendacion: verificar manualmente en https://haveibeenpwned.com/DomainSearch")
    print(f"  URL directa: https://haveibeenpwned.com/DomainSearch/{DOMAIN}")
except Exception as e:
    print(f"  Error: {e}")

print()

# ─────────────────────────────────────────────
# 3. GitHub dorks via busqueda de API publica
# ─────────────────────────────────────────────
print("--- 3. GitHub Code Search Dorks (sin auth — primeros resultados) ---")
dorks = [
    f"uns.edu.pe password",
    f"uns.edu.pe DB_PASSWORD",
    f"uns.edu.pe database",
    f"uns.edu.pe secret",
    f"siigaa OR sigea uns.edu.pe",
    f"orcl.uns.edu.pe",
]
print("  Dorks recomendados para busqueda manual en GitHub:")
for d in dorks:
    encoded = d.replace(" ", "+")
    print(f"    https://github.com/search?q={encoded}&type=code")

print()

# ─────────────────────────────────────────────
# 4. Buscar archivos de configuracion expuestos
#    directamente en los servidores
# ─────────────────────────────────────────────
print("--- 4. Busqueda de composer.json / package.json / requirements.txt ---")
# Estos archivos revelan versiones exactas de dependencias (fingerprinting)
targets_config = [
    ("https://sigea.uns.edu.pe/composer.json",         "Composer (PHP deps)"),
    ("https://sigea.uns.edu.pe/composer.lock",         "Composer lock (versiones exactas)"),
    ("https://sigea.uns.edu.pe/package.json",          "NPM package"),
    ("https://sigea.uns.edu.pe/requirements.txt",      "Python requirements"),
    ("https://www.uns.edu.pe/composer.json",           "Composer (web principal)"),
    ("https://www.uns.edu.pe/composer.lock",           "Composer lock (web principal)"),
    ("https://www.uns.edu.pe/package.json",            "NPM (web principal)"),
    ("https://campus.uns.edu.pe/composer.json",        "Composer (Moodle)"),
    ("https://campus.uns.edu.pe/version.php",          "Moodle version.php (version exacta)"),
    ("https://campus.uns.edu.pe/admin/environment.php","Moodle environment check"),
    ("https://registro.uns.edu.pe/WebAlumno/WEB-INF/web.xml", "WEB-INF web.xml"),
    ("https://registro.uns.edu.pe/WebAlumno/WEB-INF/beans.xml", "CDI beans.xml"),
    ("https://registro.uns.edu.pe/WebAlumno/WEB-INF/faces-config.xml", "JSF config"),
]

config_found = []
for url, desc in targets_config:
    try:
        r = requests.get(url, timeout=8, verify=False,
                        headers=HEADERS, allow_redirects=False)
        if r.status_code == 200 and len(r.content) > 10:
            body = r.text[:500].lower()
            # Filtrar soft-404
            soft = sum(1 for p in ["not found","404","login","pagina principal"] if p in body)
            if soft < 2:
                print(f"  [+] HTTP 200 | {url}")
                print(f"      Desc: {desc}")
                print(f"      Preview: {r.text[:150].strip()}")
                print()
                config_found.append(url)
        elif r.status_code == 403:
            print(f"  [?] HTTP 403 (existe, protegido): {url}")
    except:
        pass
    time.sleep(0.3)

if not config_found:
    print("  No se encontraron archivos de configuracion expuestos.")

print()

# ─────────────────────────────────────────────
# 5. Shodan dorks (manual)
# ─────────────────────────────────────────────
print("--- 5. Shodan / Censys Dorks (busqueda manual recomendada) ---")
shodan_dorks = [
    f"hostname:{DOMAIN}",
    f"ssl:{DOMAIN}",
    "org:Universidad Nacional del Santa",
    "ip:190.119.171.165",
]
print("  Buscar en https://www.shodan.io/search?query=...")
for d in shodan_dorks:
    print(f"    {d}")

print()
print("  Buscar en https://search.censys.io/:")
print(f"    labels.domain: {DOMAIN}")

print()

# ─────────────────────────────────────────────
# 6. Wayback Machine — URLs historicas
# ─────────────────────────────────────────────
print("--- 6. Wayback Machine — URLs historicas expuestas ---")
try:
    r = requests.get(
        f"http://web.archive.org/cdx/search/cdx?url=*.{DOMAIN}&output=json&fl=original&collapse=urlkey&limit=50&filter=statuscode:200",
        timeout=20, headers=HEADERS
    )
    if r.status_code == 200 and r.text.strip():
        urls = r.json()
        # Filtrar URLs con paths interesantes
        interesting = []
        keywords = [".env", "config", "backup", "admin", "sql", "log", "password",
                    "credentials", "secret", ".zip", ".tar", "phpmyadmin", "setup"]
        for row in urls[1:]:  # skip header
            url = row[0] if row else ""
            if any(k in url.lower() for k in keywords):
                interesting.append(url)
        print(f"  URLs historicas totales: {len(urls)-1}")
        print(f"  URLs con keywords sensibles: {len(interesting)}")
        for u in interesting[:20]:
            print(f"    {u}")
    else:
        print("  Sin resultados o error en Wayback CDX")
except Exception as e:
    print(f"  Error Wayback: {e}")

print()
print("=== OSINT completado ===")
print(f"Tiempo: {time.strftime('%Y-%m-%d %H:%M:%S')}")
