#!/usr/bin/env python3
"""
Recon completo de biblioteca.uns.edu.pe
Subdominio recien descubierto - sin explorar previo
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests, urllib3, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings()

BASE = "https://biblioteca.uns.edu.pe"
SESS = requests.Session()
SESS.verify = False
SESS.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

def get(path, allow_redirects=False, timeout=10):
    try:
        r = SESS.get(BASE + path, timeout=timeout, allow_redirects=allow_redirects)
        return r
    except Exception as e:
        return None

print(f"=== RECON: {BASE} ===\n")

# ─── 1. Fingerprint principal ───────────────────────────────
print("--- 1. Fingerprint ---")
r = get("/", allow_redirects=True)
if r:
    title = re.search(r'<title>([^<]+)</title>', r.text, re.I)
    server = r.headers.get("Server","N/A")
    powered = r.headers.get("X-Powered-By","N/A")
    cms = "N/A"
    # Detectar CMS
    if "wordpress" in r.text.lower() or "wp-content" in r.text.lower():
        cms = "WordPress"
    elif "joomla" in r.text.lower():
        cms = "Joomla"
    elif "drupal" in r.text.lower():
        cms = "Drupal"
    elif "moodle" in r.text.lower():
        cms = "Moodle"
    elif "koha" in r.text.lower() or "opac" in r.text.lower():
        cms = "Koha (Library ILS)"
    elif "dspace" in r.text.lower():
        cms = "DSpace (Repository)"
    elif "greenstone" in r.text.lower():
        cms = "Greenstone"

    print(f"  Title:     {title.group(1).strip() if title else 'N/A'}")
    print(f"  Server:    {server}")
    print(f"  Powered:   {powered}")
    print(f"  CMS/App:   {cms}")
    print(f"  HTTP:      {r.status_code} | {len(r.content)} bytes")
    print(f"  Final URL: {r.url}")

    # Headers de seguridad
    print("\n  Headers de seguridad:")
    sec_headers = {
        "Strict-Transport-Security": "HSTS",
        "Content-Security-Policy": "CSP",
        "X-Frame-Options": "XFO",
        "X-Content-Type-Options": "XCTO",
        "Referrer-Policy": "Referrer",
        "Permissions-Policy": "Permissions",
    }
    for h, label in sec_headers.items():
        val = r.headers.get(h)
        icon = "✅" if val else "❌"
        print(f"    {icon} {label}: {val or 'AUSENTE'}")

print()

# ─── 2. Paths clave de sistemas de biblioteca ────────────────
print("--- 2. Paths especificos de sistemas de biblioteca ---")
lib_paths = [
    # Koha ILS (sistema mas comun en universidades peruanas)
    ("/cgi-bin/koha/opac-main.pl",      "Koha OPAC"),
    ("/cgi-bin/koha/",                   "Koha CGI"),
    ("/cgi-bin/",                         "CGI directory"),
    ("/opac/",                            "OPAC generico"),
    ("/opac-search.pl",                   "OPAC search"),
    # DSpace (repositorio institucional)
    ("/xmlui/",                           "DSpace XMLUI"),
    ("/jspui/",                           "DSpace JSPUI"),
    ("/rest/",                            "DSpace REST API"),
    ("/oai/",                             "OAI-PMH endpoint"),
    ("/handle/",                          "DSpace handle"),
    # Admin panels
    ("/admin",                            "Admin panel"),
    ("/administrator",                    "Admin alt"),
    ("/intranet",                         "Koha Intranet (staff)"),
    ("/cgi-bin/koha/intranet-main.pl",    "Koha Intranet CGI"),
    # WordPress (muchas biblios peruanas usan WP)
    ("/wp-admin/",                        "WordPress admin"),
    ("/wp-login.php",                     "WordPress login"),
    ("/wp-json/wp/v2/",                   "WordPress REST API"),
    ("/wp-json/",                         "WordPress JSON API"),
    ("/wp-content/uploads/",              "WordPress uploads"),
    ("/xmlrpc.php",                       "WordPress XMLRPC"),
    # Config / sensibles
    ("/.env",                             ".env credenciales"),
    ("/.git/HEAD",                        "Git expuesto"),
    ("/config.php",                       "Config PHP"),
    ("/robots.txt",                       "robots.txt"),
    ("/sitemap.xml",                      "Sitemap"),
    ("/.htaccess",                        ".htaccess"),
    ("/phpinfo.php",                      "phpinfo"),
    ("/info.php",                         "PHP info"),
    ("/backup.sql",                       "Backup SQL"),
    ("/backup.zip",                       "Backup ZIP"),
    # API / servicios
    ("/api/",                             "API endpoint"),
    ("/api/v1/",                          "API v1"),
    ("/api/v2/",                          "API v2"),
    ("/swagger-ui.html",                  "Swagger UI"),
    # Uploads / archivos
    ("/uploads/",                         "Uploads dir"),
    ("/files/",                           "Files dir"),
    ("/documents/",                       "Documents dir"),
    ("/repositorio/",                     "Repositorio"),
    # Logs
    ("/error.log",                        "Error log"),
    ("/access.log",                       "Access log"),
]

def check_path(path, desc):
    r = get(path, allow_redirects=False)
    if not r:
        return None
    if r.status_code in (404, 500, 502):
        return None
    return (path, desc, r.status_code, len(r.content),
            r.headers.get("Content-Type",""), r.headers.get("Location",""),
            r.text[:200].replace("\n"," ").replace("\r",""))

with ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(check_path, p, d): (p, d) for p, d in lib_paths}
    results = []
    for ft in as_completed(futures):
        res = ft.result()
        if res:
            results.append(res)

# Ordenar por status
results.sort(key=lambda x: x[2])
for path, desc, status, size, ct, loc, preview in results:
    icon = "🔴" if status == 200 else ("🟡" if status in (301,302) else "🟠")
    loc_str = f" -> {loc}" if loc else ""
    print(f"  {icon} HTTP {status} | {path} | {desc} ({size}b){loc_str}")
    if status == 200 and size > 50:
        # Filtrar soft-404
        preview_low = preview.lower()
        is_soft404 = any(k in preview_low for k in ["404","not found","no encontrado"])
        if not is_soft404:
            print(f"         Preview: {preview[:120]}")

print()

# ─── 3. Tecnologia / versiones ──────────────────────────────
print("--- 3. Fingerprint tecnologico profundo ---")
r_main = get("/", allow_redirects=True)
if r_main:
    src = r_main.text

    # WordPress version
    wp_ver = re.search(r'ver=(\d+\.\d+[\.\d]*)', src)
    wp_ver2 = re.search(r'wordpress[/-](\d+\.\d+[\.\d]*)', src, re.I)
    if wp_ver or wp_ver2:
        v = (wp_ver or wp_ver2).group(1)
        print(f"  WordPress version detectada: {v}")

    # Koha version
    koha_ver = re.search(r'Koha[\s/]+([\d.]+)', src, re.I)
    if koha_ver:
        print(f"  Koha version: {koha_ver.group(1)}")

    # DSpace version
    dspace_ver = re.search(r'DSpace[\s/]+([\d.]+)', src, re.I)
    if dspace_ver:
        print(f"  DSpace version: {dspace_ver.group(1)}")

    # PHP version en headers
    php_ver = r_main.headers.get("X-Powered-By","")
    if "php" in php_ver.lower():
        print(f"  PHP version (headers): {php_ver}")

    # Links externos relevantes
    ext_links = re.findall(r'https?://([^/"\'\s>]+)', src)
    ext_domains = set(l.split("/")[0] for l in ext_links if "uns.edu.pe" not in l)
    if ext_domains:
        print(f"  Dominios externos: {list(ext_domains)[:10]}")

    # Formularios
    forms = re.findall(r'<form[^>]*action=["\']([^"\']+)["\']', src, re.I)
    if forms:
        print(f"  Forms/actions: {forms[:5]}")

    # Meta generator
    gen = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)["\']', src, re.I)
    if gen:
        print(f"  Generator: {gen.group(1)}")

print()
print("=== Recon biblioteca completado ===")
