#!/usr/bin/env python3
"""
registro.uns.edu.pe — WildFly/JBoss Recon
Pentest autorizado UNS
"""
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests, urllib3, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
urllib3.disable_warnings()

TARGET = "https://registro.uns.edu.pe"

print(f"=== Recon WildFly: {TARGET} ===\n")

# 1. Request base
r = requests.get(TARGET, verify=False, timeout=15, allow_redirects=True)
print(f"HTTP {r.status_code} | {len(r.content)} bytes | URL: {r.url}")
print("Headers:")
for h, v in r.headers.items():
    print(f"  {h}: {v}")

title_m = re.search(r'<title>([^<]+)</title>', r.text, re.I)
title = title_m.group(1).strip() if title_m else "N/A"
print(f"Title: {title}")
print()

# 2. Buscar endpoints WildFly/JBoss/Java
paths = [
    # WildFly Management Console
    "/console", "/console/", "/console/index.html",
    "/management", "/management/", 
    "/management/subsystem/datasources",
    
    # JBoss legacy
    "/jmx-console/", "/jmx-console/HtmlAdaptor",
    "/web-console/", "/invoker/JMXInvokerServlet",
    "/invoker/readonly", "/admin-console/",
    "/status", "/status/",
    
    # Jolokia (JMX over HTTP - muy explotable)
    "/jolokia/", "/jolokia/read/java.lang:type=Runtime",
    "/jolokia/exec/java.lang:type=Runtime/exec/id",
    
    # Spring Boot Actuator (si lo usan)
    "/actuator", "/actuator/health", "/actuator/env",
    "/actuator/beans", "/actuator/mappings",
    "/actuator/info", "/actuator/metrics",
    "/actuator/heapdump", "/actuator/threaddump",
    "/actuator/loggers", "/actuator/shutdown",
    
    # Aplicaciones UNS conocidas
    "/WebAlumno/", "/WebAlumno",
    "/WebAlumno/faces/pages/login.xhtml",
    "/WebAlumno/faces/pages/expedientePersonal.xhtml",
    "/sigea/", "/sigea",
    "/registro/", "/registro",
    "/matricula/", "/matricula",
    "/alumno/", "/alumno",
    
    # Archivos comunes Java
    "/index.jsp", "/index.html", "/index.htm",
    "/login.jsp", "/login.html",
    "/WEB-INF/web.xml",
    "/robots.txt", "/sitemap.xml",
    "/.well-known/security.txt",
    
    # REST APIs comunes
    "/api/", "/api/v1/", "/api/v2/",
    "/rest/", "/ws/", "/services/",
    "/swagger-ui.html", "/swagger-ui/",
    "/swagger.json", "/openapi.json", "/v2/api-docs",
    "/v3/api-docs",
    
    # Health checks
    "/health", "/health/", "/ping",
    "/metrics", "/info",
    
    # Rutas que ya viste en el browser state  
    "/WebAlumno/faces/pages/expedientePersonal.xhtml",
    "/WebAlumno/javax.faces.resource/",
]

print("=== Escaneando paths ===")

def check(path):
    try:
        r2 = requests.get(
            f"{TARGET}{path}",
            verify=False, timeout=8, allow_redirects=False,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if r2.status_code not in [404]:
            title_m = re.search(r'<title>([^<]+)</title>', r2.text, re.I)
            t = title_m.group(1).strip() if title_m else r2.text[:60].replace('\n', ' ')
            server = r2.headers.get("Server", "N/A")
            location = r2.headers.get("Location", "")
            powered = r2.headers.get("X-Powered-By", "")
            extra = f" -> {location}" if location else ""
            extra += f" | {powered}" if powered else ""
            return (r2.status_code, path, t[:80], server, extra)
    except:
        pass
    return None

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(check, p): p for p in paths}
    for future in as_completed(futures):
        result = future.result()
        if result:
            code, path, title, server, extra = result
            icon = "[+]" if code == 200 else "[?]"
            print(f"  {icon} HTTP {code} | {path} | {title[:60]} | {server}{extra}")

# 3. Chequear puertos alternativos
print("\n=== Puertos WildFly tipicos ===")
ports = [8080, 8443, 9990, 9993, 4848, 8181, 7001, 7002, 4000, 3000, 8000]
for port in ports:
    for scheme in ["https", "http"]:
        try:
            url = f"{scheme}://registro.uns.edu.pe:{port}/"
            r3 = requests.get(url, verify=False, timeout=4, allow_redirects=False)
            title_m = re.search(r'<title>([^<]+)</title>', r3.text, re.I)
            t = title_m.group(1).strip() if title_m else r3.text[:50].replace('\n', ' ')
            print(f"  [+] {scheme}://registro.uns.edu.pe:{port}/ => HTTP {r3.status_code} | {t[:60]}")
            break
        except:
            continue

print("\n=== Recon completado ===")
