#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
})

# Get modulos.xhtml and print ALL script blocks
r = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=10)
scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)

print("=== TODOS LOS SCRIPTS ===")
for i, script in enumerate(scripts):
    print(f"\n--- Script {i} ---")
    print(script[:500])

# Check for the stop() function specifically
print("\n\n=== Funcion stop() ===")
for script in scripts:
    if 'function stop' in script:
        # Find the stop function
        start = script.find('function stop')
        end = script.find('}', start) + 1
        print(script[start:end+100])

# Also check for any onload or onerror
print("\n\n=== Event handlers ===")
handlers = re.findall(r'on(load|error|click|load|resize|hashchange)\s*=\s*["\']([^"\']+)["\']', r.text)
if handlers:
    for h in handlers:
        print(f"  on{h[0]}: {h[1]}")

# Check for any meta refresh
print("\n=== Meta tags ===")
metas = re.findall(r'<meta[^>]*>', r.text)
for m in metas[:10]:
    print(f"  {m}")

# Check for any redirect or location changes
print("\n=== Location/redirect ===")
locations = re.findall(r'location\.(?:href|replace|assign|reload)\s*=', r.text)
if locations:
    print(f"  Found: {locations}")
# Check for any window.open
window_opens = re.findall(r'window\.open\s*\(', r.text)
if window_opens:
    print(f"  window.open found: {len(window_opens)} times")
# Check for any window.close
window_closes = re.findall(r'window\.close\s*\(', r.text)
if window_closes:
    print(f"  window.close found: {len(window_closes)} times")
# Check for any single window check
single_window = re.findall(r'(?:single|one|only|unique).{0,30}window', r.text, re.IGNORECASE)
if single_window:
    print(f"  Single window check: {single_window}")

# Check if there's any message about "una ventana" or similar
text_messages = re.findall(r'[^\n]{20,200}', r.text)
for msg in text_messages:
    if any(kw in msg.lower() for kw in ['ventana', 'solo', 'cargar', 'una', 'window', 'bloqueo', 'bloqueado', 'prohibido', 'permitido']):
        print(f"  Mensaje: {msg.strip()[:200]}")

print("\n\n=== TAMAÑO DE LA RESPUESTA ===")
print(f"Content-Length: {len(r.text)} bytes")
print(f"Content-Type: {r.headers.get('Content-Type')}")
print(f"Status: {r.status_code}")
