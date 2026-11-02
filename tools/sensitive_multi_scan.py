#!/usr/bin/env python3
"""
Multi-target sensitive files scanner para subdominios UNS
Corre en todos los activos identificados en paralelo.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests, urllib3, csv, time, re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings()

TARGETS = [
    "https://www.uns.edu.pe",
    "https://sigea.uns.edu.pe",
    "https://registro.uns.edu.pe",
    "https://orcl.uns.edu.pe",
    "https://siigaa.uns.edu.pe",
    "https://pure.uns.edu.pe",
]

# Paths de mayor impacto potencial en este stack (WildFly/PHP/Nginx/OpenResty)
PATHS = [
    # Git / VCS
    ("/.git/HEAD",                  "CRIT", "Git expuesto"),
    ("/.git/config",                "CRIT", "Git config expuesto"),
    ("/.svn/entries",               "CRIT", "SVN expuesto"),

    # Configuracion / credenciales
    ("/.env",                       "CRIT", "Variables de entorno con credenciales"),
    ("/.env.local",                 "CRIT", ".env local"),
    ("/.env.production",            "CRIT", ".env produccion"),
    ("/config.php",                 "HIGH", "Config PHP"),
    ("/database.php",               "HIGH", "Config BD PHP"),
    ("/config/database.yml",        "HIGH", "Config BD YAML"),
    ("/application.properties",     "HIGH", "Spring Boot properties"),
    ("/web.config",                 "HIGH", "IIS/ASP.NET config"),
    ("/config.inc.php",             "HIGH", "phpMyAdmin config"),
    ("/configuration.php",          "HIGH", "Joomla config"),
    ("/wp-config.php",              "HIGH", "WordPress config"),
    ("/settings.py",                "HIGH", "Django settings"),

    # Backups
    ("/backup.sql",                 "HIGH", "Backup SQL"),
    ("/dump.sql",                   "HIGH", "Dump SQL"),
    ("/database.sql",               "HIGH", "Database dump"),
    ("/db.sql",                     "HIGH", "DB dump"),
    ("/backup.zip",                 "HIGH", "Backup ZIP"),
    ("/backup.tar.gz",              "HIGH", "Backup tar"),
    ("/site.zip",                   "HIGH", "Site backup"),
    ("/www.zip",                    "HIGH", "WWW backup"),
    ("/htdocs.zip",                 "HIGH", "htdocs backup"),
    ("/public_html.zip",            "HIGH", "public_html backup"),

    # Paneles admin
    ("/phpmyadmin/",                "HIGH", "phpMyAdmin panel"),
    ("/adminer.php",                "HIGH", "Adminer DB manager"),
    ("/manager/html",               "HIGH", "Tomcat Manager"),
    ("/jmx-console/",               "HIGH", "JBoss JMX Console"),
    ("/admin/",                     "MED",  "Panel admin generico"),
    ("/administrator/",             "MED",  "Admin Joomla"),

    # Debug / info disclosure
    ("/phpinfo.php",                "HIGH", "phpinfo expuesto"),
    ("/info.php",                   "HIGH", "PHP info"),
    ("/test.php",                   "MED",  "PHP test file"),
    ("/server-status",              "MED",  "Apache server-status"),
    ("/server-info",                "MED",  "Apache server-info"),

    # Spring Boot actuator
    ("/actuator",                   "HIGH", "Spring actuator"),
    ("/actuator/env",               "CRIT", "Spring env (credenciales)"),
    ("/actuator/heapdump",          "CRIT", "Spring heapdump (memoria)"),
    ("/actuator/beans",             "MED",  "Spring beans"),
    ("/actuator/health",            "INFO", "Spring health"),

    # API docs
    ("/swagger-ui.html",            "MED",  "Swagger UI"),
    ("/swagger-ui/",                "MED",  "Swagger UI alt"),
    ("/v2/api-docs",                "MED",  "OpenAPI v2"),
    ("/v3/api-docs",                "MED",  "OpenAPI v3"),
    ("/openapi.json",               "MED",  "OpenAPI JSON"),
    ("/graphql",                    "MED",  "GraphQL endpoint"),

    # Logs
    ("/error.log",                  "HIGH", "Error log expuesto"),
    ("/access.log",                 "HIGH", "Access log"),
    ("/logs/",                      "MED",  "Directorio logs"),
    ("/log/",                       "MED",  "Directorio log"),

    # Archivos de control
    ("/robots.txt",                 "INFO", "robots.txt"),
    ("/.htaccess",                  "INFO", "htaccess"),
    ("/security.txt",               "INFO", "security.txt"),
    ("/.well-known/security.txt",   "INFO", "security.txt well-known"),
    ("/sitemap.xml",                "INFO", "Sitemap"),
    ("/crossdomain.xml",            "INFO", "crossdomain.xml"),

    # Archivos PDF/docs publicos (directorio archivos)
    ("/archivos/",                  "INFO", "Directorio archivos publico"),
    ("/uploads/",                   "INFO", "Directorio uploads"),
    ("/files/",                     "INFO", "Directorio files"),
    ("/documents/",                 "INFO", "Directorio documents"),

    # WildFly/JBoss especificos
    ("/wildfly-web.xml",            "HIGH", "WildFly web.xml"),
    ("/jboss-web.xml",              "HIGH", "JBoss web.xml"),
    ("/standalone.xml",             "CRIT", "WildFly standalone config"),
    ("/domain.xml",                 "CRIT", "WildFly domain config"),
    ("/WEB-INF/web.xml",            "CRIT", "WEB-INF expuesto"),
    ("/WEB-INF/jboss-web.xml",      "CRIT", "JBoss web.xml"),
]

# Confirmar que no sea soft-404 (paginas que retornan 200 con contenido de error)
SOFT404_PATTERNS = [
    "404", "not found", "no encontrado", "page not found",
    "error", "pagina principal", "cv-uns", "login"
]

def check(target, path, severity, desc):
    url = target.rstrip("/") + path
    try:
        r = requests.get(url, timeout=8, verify=False,
                         headers={"User-Agent": "Security-Audit-Thesis/1.0"},
                         allow_redirects=False)

        if r.status_code in (404, 500, 502, 503):
            return None

        body_low = r.text[:1000].lower()

        # Descartar soft-404 (solo para 200)
        if r.status_code == 200:
            # Si el body parece pagina de error o login, probablemente es soft-404
            soft404_hits = sum(1 for p in SOFT404_PATTERNS if p in body_low)
            if soft404_hits >= 2:
                return None

        loc = r.headers.get("Location", "")
        note = f"HTTP {r.status_code}"
        if loc:
            note += f" -> {loc}"

        return {
            "target":   target,
            "url":      url,
            "path":     path,
            "status":   r.status_code,
            "severity": severity,
            "size_b":   len(r.content),
            "desc":     desc,
            "note":     note,
            "ct":       r.headers.get("Content-Type","")[:60],
            "ts":       datetime.now().strftime("%H:%M:%S"),
            "preview":  r.text[:120].replace("\n"," ").replace("\r",""),
        }
    except Exception:
        return None

print(f"=== Multi-target Sensitive Files Scanner — UNS ===")
print(f"Targets: {len(TARGETS)} | Paths/target: {len(PATHS)} | Total: {len(TARGETS)*len(PATHS)}")
print(f"Iniciado: {datetime.now()}\n")

findings = []

for target in TARGETS:
    print(f"\n--- Escaneando: {target} ---")
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(check, target, p, s, d): (p, s, d) for p, s, d in PATHS}
        for ft in as_completed(futures):
            res = ft.result()
            if res:
                findings.append(res)
                icon = "🔴" if res["severity"] == "CRIT" else ("🟠" if res["severity"] == "HIGH" else "🟡")
                print(f"  {icon} [{res['severity']}] {res['status']} {res['path']} ({res['size_b']}b)")
                if res["preview"] and res["status"] == 200:
                    print(f"       Preview: {res['preview'][:100]}")
    time.sleep(0.5)

print(f"\n\n=== RESULTADO FINAL ===")
print(f"Total hallazgos: {len(findings)}")
crits = [f for f in findings if f["severity"] == "CRIT" and f["status"] == 200]
highs = [f for f in findings if f["severity"] == "HIGH" and f["status"] == 200]
print(f"CRITICOS (200): {len(crits)}")
print(f"ALTOS (200):    {len(highs)}")

# Guardar
out = r"C:\Users\Leguion T\Desktop\plan te pent\findings\sensitive_multi_target.csv"
if findings:
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=findings[0].keys())
        w.writeheader()
        w.writerows(findings)
    print(f"\nGuardado en: {out}")

if crits or highs:
    print("\n=== CRITICOS y ALTOS (200 OK) ===")
    for f in crits + highs:
        print(f"  [{f['severity']}] {f['url']}")
        print(f"         Preview: {f['preview'][:120]}")
