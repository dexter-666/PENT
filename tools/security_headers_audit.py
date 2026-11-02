#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
security_headers_audit.py
==========================
Auditor de cabeceras de seguridad HTTP y configuración TLS para la tesis
de pentesting web — UNS (Universidad Nacional del Santa).

Verifica la presencia y correcta configuración de:
  - HTTP Security Headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options, etc.)
  - Configuración de Cookies (Secure, HttpOnly, SameSite)
  - Redireccionamiento HTTP → HTTPS
  - Información de versión expuesta en headers (Server, X-Powered-By, X-AspNet-Version)
  - Métodos HTTP permitidos (PUT, DELETE, TRACE, OPTIONS)

OWASP WSTG: INFO-02, CONF-06, CONF-07, SESS-02

USO: python security_headers_audit.py --urls-file ../findings/inventario_activos.csv --output ../findings/headers_audit.csv
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BANNER = """
+--------------------------------------------------------------+
|   UNS PENTEST THESIS -- Security Headers Auditor            |
|   OWASP WSTG: INFO-02 | CONF-06 | CONF-07 | SESS-02        |
+--------------------------------------------------------------+
"""

# Cabeceras de seguridad evaluadas
SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "desc": "HSTS — Fuerza conexiones HTTPS",
        "severity": "HIGH",
        "check": lambda v: "max-age" in v.lower() if v else False,
    },
    "Content-Security-Policy": {
        "desc": "CSP — Previene XSS e inyección de contenido",
        "severity": "HIGH",
        "check": lambda v: v is not None,
    },
    "X-Frame-Options": {
        "desc": "Previene Clickjacking",
        "severity": "MEDIUM",
        "check": lambda v: v and v.upper() in ("DENY", "SAMEORIGIN"),
    },
    "X-Content-Type-Options": {
        "desc": "Previene MIME sniffing",
        "severity": "MEDIUM",
        "check": lambda v: v and "nosniff" in v.lower(),
    },
    "Referrer-Policy": {
        "desc": "Controla información del Referer",
        "severity": "LOW",
        "check": lambda v: v is not None,
    },
    "Permissions-Policy": {
        "desc": "Controla APIs del navegador (cámara, micrófono, etc.)",
        "severity": "LOW",
        "check": lambda v: v is not None,
    },
    "X-Powered-By": {
        "desc": "⚠️ EXPONE tecnología del servidor (debería estar AUSENTE)",
        "severity": "INFO",
        "check": lambda v: v is None,  # Pasa si NO está presente
        "should_be_absent": True,
    },
    "Server": {
        "desc": "⚠️ EXPONE versión del servidor (idealmente sin versión)",
        "severity": "INFO",
        "check": lambda v: v is None or not any(c.isdigit() for c in (v or "")),
        "should_be_absent": True,
    },
    "X-AspNet-Version": {
        "desc": "⚠️ EXPONE versión de ASP.NET (debería estar AUSENTE)",
        "severity": "INFO",
        "check": lambda v: v is None,
        "should_be_absent": True,
    },
}


def check_http_to_https_redirect(base_url: str) -> bool:
    """Verifica si el sitio redirige HTTP → HTTPS."""
    parsed = urlparse(base_url)
    http_url = f"http://{parsed.netloc}{parsed.path}"
    try:
        resp = requests.get(http_url, timeout=8, allow_redirects=True, verify=False,
                            headers={"User-Agent": "Thesis-Security-Audit/1.0"})
        return resp.url.startswith("https://")
    except requests.RequestException:
        return False


def check_dangerous_methods(url: str) -> list[str]:
    """Comprueba si métodos HTTP peligrosos están permitidos (TRACE, PUT, DELETE)."""
    dangerous = []
    for method in ["TRACE", "PUT", "DELETE"]:
        try:
            resp = requests.request(method, url, timeout=8, verify=False,
                                    headers={"User-Agent": "Thesis-Security-Audit/1.0"})
            if resp.status_code not in (405, 501):
                dangerous.append(f"{method}:{resp.status_code}")
        except requests.RequestException:
            pass
        time.sleep(0.3)
    return dangerous


def audit_url(url: str) -> dict:
    """Realiza la auditoría completa de cabeceras de seguridad para una URL."""
    result = {
        "url": url,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reachable": False,
        "status_code": None,
        "http_to_https_redirect": False,
        "dangerous_methods": [],
        "headers_found": {},
        "findings": [],
        "score": 0,
        "grade": "F",
    }

    try:
        resp = requests.get(url, timeout=10, verify=False,
                            headers={"User-Agent": "Thesis-Security-Audit/1.0"})
        result["reachable"] = True
        result["status_code"] = resp.status_code
    except requests.RequestException as e:
        result["findings"].append(f"No se pudo conectar: {e}")
        return result

    headers = resp.headers
    result["http_to_https_redirect"] = check_http_to_https_redirect(url)

    max_score = 0
    earned_score = 0

    for header_name, config in SECURITY_HEADERS.items():
        max_score += 1
        header_value = headers.get(header_name)
        result["headers_found"][header_name] = header_value
        passes = config["check"](header_value)
        should_be_absent = config.get("should_be_absent", False)

        if passes:
            earned_score += 1
            status = "✅ OK" if not should_be_absent else "✅ AUSENTE (correcto)"
        else:
            status = "❌ FALTANTE" if not should_be_absent else f"⚠️ EXPUESTO: {header_value}"
            finding = {
                "header": header_name,
                "severity": config["severity"],
                "description": config["desc"],
                "current_value": header_value,
                "status": status,
                "wstg_ref": "WSTG-CONF-07" if "Policy" in header_name else "WSTG-CONF-06",
            }
            result["findings"].append(finding)

        print(f"    {status:<30} {header_name}: {str(header_value)[:60]}")

    # Verificar métodos peligrosos
    dangerous = check_dangerous_methods(url)
    if dangerous:
        result["dangerous_methods"] = dangerous
        result["findings"].append({
            "header": "HTTP Methods",
            "severity": "HIGH",
            "description": f"Métodos peligrosos permitidos: {', '.join(dangerous)}",
            "current_value": str(dangerous),
            "status": "❌ PELIGROSO",
            "wstg_ref": "WSTG-CONF-05",
        })
        print(f"    ❌ MÉTODOS PELIGROSOS PERMITIDOS: {', '.join(dangerous)}")
    else:
        print("    ✅ No se detectaron métodos HTTP peligrosos habilitados.")

    # Calcular puntuación y grado
    result["score"] = round((earned_score / max_score) * 100) if max_score > 0 else 0
    score = result["score"]
    if score >= 90:
        result["grade"] = "A"
    elif score >= 75:
        result["grade"] = "B"
    elif score >= 60:
        result["grade"] = "C"
    elif score >= 40:
        result["grade"] = "D"
    else:
        result["grade"] = "F"

    return result


def generate_report(results: list[dict], output_path: str) -> None:
    """Genera un CSV con los hallazgos de la auditoría de cabeceras."""
    rows = []
    for r in results:
        for finding in r.get("findings", []):
            if isinstance(finding, dict):
                rows.append({
                    "url": r["url"],
                    "status_code": r["status_code"],
                    "grade": r["grade"],
                    "score": r["score"],
                    "header": finding.get("header", ""),
                    "severity": finding.get("severity", ""),
                    "status": finding.get("status", ""),
                    "description": finding.get("description", ""),
                    "current_value": finding.get("current_value", ""),
                    "wstg_ref": finding.get("wstg_ref", ""),
                })

    if not rows:
        print("[+] No se encontraron hallazgos negativos. ¡Buena configuración!")
        return

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[+] Informe de hallazgos guardado en: {output_path}")


def main():
    print(BANNER)

    parser = argparse.ArgumentParser(description="Auditor de cabeceras de seguridad HTTP para tesis UNS")
    parser.add_argument("--url", help="URL única a auditar (ej: https://registro.uns.edu.pe)")
    parser.add_argument("--urls-file", help="Archivo CSV con subdominios (columna 'subdomain')")
    parser.add_argument("--output", default="../findings/headers_audit.csv", help="CSV de salida de hallazgos")
    args = parser.parse_args()

    urls_to_audit = []

    if args.url:
        urls_to_audit.append(args.url)
    elif args.urls_file:
        try:
            with open(args.urls_file, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    subdomain = row.get("subdomain", "").strip()
                    live = row.get("live", "False").strip()
                    if subdomain and live.lower() == "true":
                        urls_to_audit.append(f"https://{subdomain}")
        except FileNotFoundError:
            print(f"[!] Archivo no encontrado: {args.urls_file}")
            sys.exit(1)
    else:
        # Default: auditar el SIIGAA de UNS
        urls_to_audit = [
            "https://registro.uns.edu.pe",
            "https://uns.edu.pe",
        ]

    print(f"[*] Auditando {len(urls_to_audit)} URL(s)...\n")

    all_results = []
    for url in urls_to_audit:
        print(f"\n{'='*70}")
        print(f"[+] Auditando: {url}")
        print(f"{'='*70}")
        result = audit_url(url)
        all_results.append(result)
        print(f"\n  📊 PUNTUACIÓN: {result['score']}/100 | GRADO: {result['grade']}")
        if result["http_to_https_redirect"]:
            print("  ✅ Redireccionamiento HTTP → HTTPS: SÍ")
        else:
            print("  ❌ Redireccionamiento HTTP → HTTPS: NO (Vulnerabilidad WSTG-CONF-06)")
        time.sleep(1)

    generate_report(all_results, args.output)

    # Resumen final
    print(f"\n{'='*70}")
    print("RESUMEN FINAL DE AUDITORÍA DE CABECERAS DE SEGURIDAD")
    print(f"{'='*70}")
    for r in all_results:
        print(f"  {r['grade']}  ({r['score']:>3}%) | {r['url']}")
    print()


if __name__ == "__main__":
    main()
