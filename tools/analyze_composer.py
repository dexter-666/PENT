#!/usr/bin/env python3
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests, urllib3, json
urllib3.disable_warnings()

r = requests.get('https://orcl.uns.edu.pe/composer.lock', verify=False, timeout=15)
data = json.loads(r.text)

packages = data.get("packages", [])
print(f"=== DEPENDENCIAS phpMyAdmin 5.2.3 ({len(packages)} paquetes) ===\n")

deps = []
for pkg in packages:
    name = pkg.get("name", "")
    version = pkg.get("version", "")
    desc = pkg.get("description", "")[:60]
    deps.append((name, version, desc))
    print(f"  {name:45s} {version:15s} {desc}")

print(f"\nTotal: {len(deps)} dependencias\n")

print("=== DEPENDENCIAS CRITICAS DE SEGURIDAD ===\n")
critical_keywords = ["crypto", "auth", "sql", "security", "session", "password", "twig", "symfony", "guzzle"]
for name, version, desc in deps:
    for kw in critical_keywords:
        if kw in name.lower() or kw in desc.lower():
            print(f"  [!] {name} {version} - {desc}")
            break
