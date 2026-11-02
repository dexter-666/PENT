#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
recon_subdomains.py
===================
Script OSINT pasivo para descubrimiento de subdominios de la Universidad Nacional del Santa (UNS).
Fuentes: crt.sh (Certificate Transparency), DNS resolution.

USO: python recon_subdomains.py --domain uns.edu.pe --output ../findings/inventario_activos.csv

Autorización: Vicerrectoría UNS + Grupo de Ingeniería de Seguridad UNS.
"""

import argparse
import csv
import json
import socket
import sys
import time
from datetime import datetime

import requests

BANNER = """
+--------------------------------------------------------------+
|       UNS PENTEST THESIS -- Subdomain Recon Tool             |
|       Autor: Tesista UNS | OWASP WSTG-INFO-03               |
|       Fuentes: crt.sh (Certificate Transparency)            |
+--------------------------------------------------------------+
"""


def get_subdomains_from_crtsh(domain: str) -> list[dict]:
    """Consulta la API pública de crt.sh para obtener subdominios via Certificate Transparency."""
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    print(f"[*] Consultando crt.sh para: {domain}")
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Thesis-Security-Audit/1.0"})
        resp.raise_for_status()
        data = resp.json()
        subdomains = set()
        for entry in data:
            name_value = entry.get("name_value", "")
            for name in name_value.split("\n"):
                name = name.strip().lower()
                if "*" not in name and domain in name:
                    subdomains.add(name)
        return sorted(subdomains)
    except requests.RequestException as e:
        print(f"[!] Error al consultar crt.sh: {e}")
        return []
    except json.JSONDecodeError:
        print("[!] Error al parsear respuesta JSON de crt.sh.")
        return []


def resolve_subdomain(subdomain: str) -> dict:
    """Intenta resolver el subdominio a una dirección IP y verifica disponibilidad HTTP/HTTPS."""
    result = {
        "subdomain": subdomain,
        "ip": None,
        "http_status": None,
        "https_status": None,
        "server": None,
        "live": False,
    }

    # Resolución DNS
    try:
        ip = socket.gethostbyname(subdomain)
        result["ip"] = ip
        result["live"] = True
    except socket.gaierror:
        return result  # No resuelve, no está activo

    # Verificar HTTP
    for scheme in ["https", "http"]:
        try:
            resp = requests.get(
                f"{scheme}://{subdomain}",
                timeout=8,
                allow_redirects=True,
                headers={"User-Agent": "Thesis-Security-Audit/1.0"},
                verify=False,  # Para detectar sitios con certificados inválidos
            )
            status = resp.status_code
            server = resp.headers.get("Server", "Unknown")
            if scheme == "https":
                result["https_status"] = status
            else:
                result["http_status"] = status
            result["server"] = server
        except requests.RequestException:
            pass
        time.sleep(0.5)  # Rate limiting cortés

    return result


def print_result(r: dict) -> None:
    """Imprime el resultado de un subdominio de forma legible."""
    status_str = f"HTTP:{r['http_status']} | HTTPS:{r['https_status']}"
    ip_str = r["ip"] or "No resuelve"
    live_str = "🟢 VIVO" if r["live"] else "🔴 MUERTO"
    print(f"  {live_str} | {r['subdomain']:<45} | IP: {ip_str:<18} | {status_str} | Server: {r['server']}")


def save_to_csv(results: list[dict], output_path: str) -> None:
    """Guarda los resultados en un archivo CSV para el inventario de activos."""
    fieldnames = ["subdomain", "ip", "http_status", "https_status", "server", "live"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[+] Resultados guardados en: {output_path}")


def main():
    print(BANNER)

    parser = argparse.ArgumentParser(description="Descubrimiento OSINT de subdominios para tesis de pentesting UNS.")
    parser.add_argument("--domain", default="uns.edu.pe", help="Dominio raíz a auditar (default: uns.edu.pe)")
    parser.add_argument("--output", default="../findings/inventario_activos.csv", help="Archivo CSV de salida")
    parser.add_argument("--no-resolve", action="store_true", help="Solo listar subdominios sin resolución DNS/HTTP")
    args = parser.parse_args()

    print(f"[*] Dominio objetivo: {args.domain}")
    print(f"[*] Fecha y hora de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[*] Modo: {'Solo enumeración' if args.no_resolve else 'Enumeración + Resolución'}\n")

    # Fase 1: Obtener subdominios
    subdomains = get_subdomains_from_crtsh(args.domain)

    if not subdomains:
        print("[!] No se encontraron subdominios. Verifica tu conexión a internet.")
        sys.exit(1)

    print(f"\n[+] {len(subdomains)} subdominios únicos encontrados en crt.sh:\n")

    if args.no_resolve:
        for sd in subdomains:
            print(f"  - {sd}")
        return

    # Fase 2: Resolución y verificación
    print("[*] Iniciando resolución DNS y verificación HTTP (con rate limiting)...\n")
    results = []

    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    for sd in subdomains:
        result = resolve_subdomain(sd)
        print_result(result)
        results.append(result)

    # Resumen
    live_count = sum(1 for r in results if r["live"])
    print(f"\n{'='*70}")
    print(f"[+] RESUMEN: {live_count}/{len(results)} subdominios activos encontrados.")
    print(f"{'='*70}\n")

    # Guardar CSV
    save_to_csv(results, args.output)


if __name__ == "__main__":
    main()
