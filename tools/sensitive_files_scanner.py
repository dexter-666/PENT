#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
sensitive_files_scanner.py
===========================
Scanner ético de archivos y rutas sensibles expuestos en la web universitaria (UNS).
Detecta "fallos tontos pero críticos" — los más comunes en sistemas universitarios:

- Repositorios .git expuestos (permite reconstruir código fuente)
- Archivos de configuración (.env, config.php, database.yml)
- Backups olvidados (.sql, .bak, .tar.gz, .zip)
- Paneles de administración sin autenticación
- Consolas de depuración (phpinfo.php, info.php, test.php)
- Documentación de APIs sin autenticar (swagger.json, api-docs)
- Archivos de registro expuestos (error.log, access.log)
- Archivos de control de versiones (/.svn/, /.hg/)

OWASP WSTG: CONF-03, CONF-04, INFO-04

USO: python sensitive_files_scanner.py --base-url https://registro.uns.edu.pe --output ../findings/sensitive_files.csv
"""

import argparse
import csv
import sys
import time
from datetime import datetime
from urllib.parse import urljoin

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BANNER = """
+--------------------------------------------------------------+
|   UNS PENTEST THESIS -- Sensitive Files Scanner             |
|   OWASP WSTG: CONF-03 | CONF-04 | INFO-04                  |
+--------------------------------------------------------------+
"""

# Lista de rutas sensibles organizadas por categoría
SENSITIVE_PATHS = {
    "🔴 Control de Versiones (CRÍTICO)": [
        ("/.git/HEAD", "Repositorio Git expuesto — permite reconstruir código fuente completo"),
        ("/.git/config", "Configuración Git expuesta — revela remotes y credenciales"),
        ("/.git/COMMIT_EDITMSG", "Git commit expuesto"),
        ("/.svn/entries", "Repositorio SVN expuesto"),
        ("/.svn/wc.db", "Base de datos SVN expuesta"),
        ("/.hg/", "Repositorio Mercurial expuesto"),
    ],
    "🔴 Archivos de Configuración (CRÍTICO)": [
        ("/.env", "Archivo .env con credenciales de base de datos y secretos"),
        ("/.env.local", "Archivo .env.local con configuración sensible"),
        ("/.env.production", "Archivo .env.production con credenciales de producción"),
        ("/config.php", "Archivo de configuración PHP con credenciales"),
        ("/wp-config.php", "Configuración WordPress con credenciales de BD"),
        ("/config/database.yml", "Configuración de base de datos Ruby on Rails"),
        ("/application.properties", "Propiedades de Spring Boot con credenciales"),
        ("/settings.py", "Configuración Django con SECRET_KEY y credenciales"),
        ("/config/settings.ini", "Archivo de configuración con credenciales"),
        ("/web.config", "Configuración IIS/ASP.NET con información sensible"),
    ],
    "🟠 Backups y Archivos Olvidados (ALTO)": [
        ("/backup.sql", "Backup de base de datos SQL expuesto"),
        ("/backup.zip", "Backup comprimido expuesto"),
        ("/backup.tar.gz", "Backup tar expuesto"),
        ("/db.sql", "Volcado de base de datos expuesto"),
        ("/database.sql", "Volcado de base de datos expuesto"),
        ("/dump.sql", "Dump de base de datos expuesto"),
        ("/site.zip", "Backup del sitio web"),
        ("/www.zip", "Backup del directorio web"),
        ("/old/", "Directorio con versión antigua del sitio"),
        ("/backup/", "Directorio de backups expuesto"),
    ],
    "🟠 Consolas de Depuración (ALTO)": [
        ("/phpinfo.php", "phpinfo() expone configuración completa del servidor PHP"),
        ("/info.php", "Archivo de información PHP"),
        ("/test.php", "Archivo de prueba PHP con información sensible"),
        ("/php.php", "Archivo PHP de diagnóstico"),
        ("/debug/", "Panel de depuración expuesto"),
        ("/console", "Consola de administración web"),
        ("/actuator", "Actuator de Spring Boot expuesto (métricas, env, beans)"),
        ("/actuator/env", "Variables de entorno de Spring Boot expuestas"),
        ("/actuator/health", "Endpoint de salud de Spring Boot"),
    ],
    "🟠 Paneles de Administración (ALTO)": [
        ("/admin/", "Panel de administración"),
        ("/administrator/", "Panel de administración Joomla"),
        ("/wp-admin/", "Panel de administración WordPress"),
        ("/phpmyadmin/", "PHPMyAdmin — gestión de base de datos"),
        ("/adminer.php", "Adminer — gestión de base de datos"),
        ("/manager/html", "Tomcat Manager expuesto"),
        ("/jmx-console/", "JBoss JMX Console expuesta"),
        ("/admin-console/", "Consola de administración"),
    ],
    "🟡 Documentación de API (MEDIO)": [
        ("/swagger-ui.html", "Swagger UI — documentación de API expuesta"),
        ("/swagger-ui/", "Swagger UI alternativo"),
        ("/api-docs", "Documentación de API JSON/OpenAPI"),
        ("/v2/api-docs", "Documentación Swagger v2"),
        ("/openapi.json", "Especificación OpenAPI/Swagger expuesta"),
        ("/api/swagger.json", "Swagger API docs"),
        ("/graphql", "Endpoint GraphQL — verificar introspección habilitada"),
    ],
    "🟡 Archivos de Log (MEDIO)": [
        ("/error.log", "Log de errores expuesto — revela stack traces y rutas internas"),
        ("/access.log", "Log de acceso — revela rutas y usuarios"),
        ("/logs/error.log", "Log de errores en directorio /logs"),
        ("/app/logs/application.log", "Log de aplicación"),
        ("/storage/logs/laravel.log", "Log de Laravel expuesto"),
    ],
    "⚪ Archivos de Control (INFO)": [
        ("/robots.txt", "Robots.txt — puede revelar rutas sensibles"),
        ("/sitemap.xml", "Sitemap — mapa completo del sitio"),
        ("/.htaccess", "Configuración Apache — puede contener restricciones y credenciales"),
        ("/crossdomain.xml", "Política de dominio cruzado Flash (legacy)"),
        ("/security.txt", "Política de seguridad de la organización"),
        ("/.well-known/security.txt", "Ubicación estándar de security.txt"),
    ],
}

# Indicadores de contenido que confirman hallazgos verdaderos
CONFIRMATION_PATTERNS = {
    "/.git/HEAD": ["ref: refs/"],
    "/.env": ["DB_PASSWORD", "APP_KEY", "SECRET", "DATABASE_URL", "SMTP_"],
    "/phpinfo.php": ["phpinfo()", "PHP Version"],
    "/info.php": ["phpinfo()", "PHP Version"],
    "/actuator/env": ["activeProfiles", "properties"],
    "/swagger-ui.html": ["swagger", "Swagger UI"],
}


def check_path(base_url: str, path: str, description: str) -> dict | None:
    """Verifica si una ruta sensible está expuesta."""
    url = urljoin(base_url, path)

    try:
        resp = requests.get(url, timeout=8, verify=False,
                            headers={"User-Agent": "Thesis-Security-Audit/1.0"},
                            allow_redirects=False)

        # Filtros para reducir falsos positivos
        if resp.status_code in (401, 403):
            # Existe pero protegido — interesante pero no crítico
            severity = "INFO"
            note = "Protegido (401/403) — Existe pero requiere autenticación"
        elif resp.status_code == 200:
            severity = "HIGH"
            note = "ACCESIBLE SIN AUTENTICACIÓN"

            # Confirmar con patrones de contenido
            patterns = CONFIRMATION_PATTERNS.get(path, [])
            content = resp.text[:2000]
            confirmed = any(p.lower() in content.lower() for p in patterns) if patterns else True

            if not confirmed:
                return None  # Probable página 404 personalizada
        elif resp.status_code in (301, 302):
            severity = "INFO"
            note = f"Redirección a: {resp.headers.get('Location', 'desconocido')}"
        else:
            return None  # 404, 500, etc.

        return {
            "url": url,
            "path": path,
            "status_code": resp.status_code,
            "severity": severity,
            "description": description,
            "note": note,
            "content_length": len(resp.content),
            "content_type": resp.headers.get("Content-Type", ""),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "wstg_ref": "WSTG-CONF-04",
        }
    except requests.RequestException:
        return None


def main():
    print(BANNER)

    parser = argparse.ArgumentParser(description="Scanner de archivos sensibles para tesis UNS")
    parser.add_argument("--base-url", default="https://registro.uns.edu.pe",
                        help="URL base a escanear")
    parser.add_argument("--output", default="../findings/sensitive_files.csv",
                        help="Archivo CSV de hallazgos")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Delay entre peticiones en segundos (default: 0.5)")
    args = parser.parse_args()

    print(f"[*] URL objetivo: {args.base_url}")
    print(f"[*] Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[*] Delay entre peticiones: {args.delay}s (modo ético)\n")

    all_findings = []
    total_paths = sum(len(paths) for paths in SENSITIVE_PATHS.values())
    checked = 0

    for category, paths in SENSITIVE_PATHS.items():
        print(f"\n{'='*70}")
        print(f"Categoría: {category}")
        print(f"{'='*70}")

        for path, description in paths:
            checked += 1
            sys.stdout.write(f"\r  [{checked:>3}/{total_paths}] Verificando: {path:<50}")
            sys.stdout.flush()

            finding = check_path(args.base_url, path, description)
            time.sleep(args.delay)

            if finding:
                all_findings.append(finding)
                severity_emoji = "🔴" if finding["severity"] == "HIGH" else "⚪"
                print(f"\n  {severity_emoji} HALLAZGO [{finding['severity']}]: {path}")
                print(f"     Status: {finding['status_code']} | {finding['note']}")
                print(f"     Descripción: {description}")

    print(f"\n\n{'='*70}")
    print(f"ESCANEO COMPLETADO — {args.base_url}")
    print(f"{'='*70}")
    print(f"  Rutas verificadas: {checked}")
    print(f"  Hallazgos encontrados: {len(all_findings)}")
    high = sum(1 for f in all_findings if f["severity"] == "HIGH")
    print(f"  🔴 Críticos/Altos: {high}")
    print(f"  ⚪ Informativos:   {len(all_findings) - high}")

    if not all_findings:
        print("\n[+] No se encontraron archivos sensibles expuestos.")
        return

    # Guardar CSV
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_findings[0].keys())
        writer.writeheader()
        writer.writerows(all_findings)
    print(f"\n[+] Hallazgos guardados en: {args.output}\n")


if __name__ == "__main__":
    main()
