#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests, time, csv
import urllib3
urllib3.disable_warnings()

SUBDOMAINS = [
    ("biblioteca.uns.edu.pe",   "190.119.171.165"),
    ("campus.uns.edu.pe",       "190.119.171.165"),
    ("cecomp.uns.edu.pe",       "190.119.171.165"),
    ("cepuns.uns.edu.pe",       "190.119.171.165"),
    ("cspf.uns.edu.pe",         "190.119.171.165"),
    ("hpda.uns.edu.pe",         "190.119.171.165"),
    ("incuba.uns.edu.pe",       "190.119.171.165"),
    ("marcaciones.uns.edu.pe",  "190.119.171.165"),
    ("noradx.uns.edu.pe",       "190.119.171.165"),
    ("onvsw.uns.edu.pe",        "190.119.171.165"),
    ("orcl.uns.edu.pe",         "190.119.171.165"),
    ("posgrado.uns.edu.pe",     "190.119.171.165"),
    ("pruebas.uns.edu.pe",      "190.119.171.170"),
    ("pure.uns.edu.pe",         "104.18.39.240"),
    ("registro.uns.edu.pe",     "190.119.171.166"),
    ("repositorio.uns.edu.pe",  "190.119.171.167"),
    ("revistas.uns.edu.pe",     "190.119.171.165"),
    ("sgpi.uns.edu.pe",         "190.119.171.165"),
    ("sigea.uns.edu.pe",        "190.119.171.165"),
    ("sistemas.uns.edu.pe",     "190.119.171.165"),
    ("wmdb.uns.edu.pe",         "190.119.171.165"),
    ("www.uns.edu.pe",          "190.119.171.172"),
]

HEADERS = {"User-Agent": "Thesis-Security-Audit/1.0 (authorized pentest)"}
results = []

print(f"[*] Verificando {len(SUBDOMAINS)} subdominios de uns.edu.pe...\n")
print(f"{'SUBDOMINIO':<35} {'IP':<18} {'HTTP':>5} {'HTTPS':>6}  SERVER")
print("-" * 90)

for subdomain, ip in SUBDOMAINS:
    r = {
        "subdomain": subdomain,
        "ip": ip,
        "http_status": None,
        "https_status": None,
        "server": None,
        "live": False,
    }

    for scheme in ["https", "http"]:
        try:
            resp = requests.get(
                f"{scheme}://{subdomain}",
                timeout=10,
                allow_redirects=True,
                headers=HEADERS,
                verify=False,
            )
            code = resp.status_code
            if scheme == "https":
                r["https_status"] = code
            else:
                r["http_status"] = code
            if not r["server"]:
                r["server"] = resp.headers.get("Server", resp.headers.get("X-Powered-By", "?"))
            r["live"] = True
        except Exception:
            pass
        time.sleep(0.3)

    http_s  = str(r["http_status"])  if r["http_status"]  else "---"
    https_s = str(r["https_status"]) if r["https_status"] else "---"
    flag    = "[OK]" if r["live"] else "[--]"
    srv     = (r["server"] or "?")[:30]
    print(f"{flag} {subdomain:<33} {ip:<18} {http_s:>5} {https_s:>6}  {srv}")
    results.append(r)

active = [r for r in results if r["live"]]
print(f"\n[RESUMEN] {len(active)}/{len(results)} subdominios con respuesta HTTP activa")

with open(r"..\findings\inventario_activos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["subdomain", "ip", "http_status", "https_status", "server", "live"])
    w.writeheader()
    w.writerows(results)

print("[+] Inventario guardado -> findings/inventario_activos.csv")
