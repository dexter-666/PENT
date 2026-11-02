#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
})

# Get modulos.xhtml
r = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=10)
text = r.text

# Look for ALL JavaScript in the page
scripts = re.findall(r'<script[^>]*>(.*?)</script>', text, re.DOTALL)
print(f"Number of script blocks: {len(scripts)}")
print()

# Look for frame-busting / anti-framing code
print("=== Buscando proteccion anti-framing ===")
for i, script in enumerate(scripts):
    if any(kw in script.lower() for kw in ['frame', 'iframe', 'top', 'self', 'parent', 'bust', 'redirect', 'location']):
        print(f"\nScript {i} (frame-busting):")
        # Find the relevant lines
        lines = script.split('\n')
        for line in lines:
            if any(kw in line.lower() for kw in ['frame', 'iframe', 'top', 'self', 'parent', 'bust', 'location', 'redirect', 'window']):
                print(f"  {line.strip()[:200]}")

# Look for any blocking messages or alerts
print("\n\n=== Buscando mensajes de bloqueo ===")
# Look for any text that contains "solo", "ventana", "una", "window", "cargar", "bloque"
blocking_patterns = ['solo', 'ventana', 'una', 'cargar', 'bloque', 'proteccion', 'seguridad', 'warning', 'alert']
for pattern in blocking_patterns:
    # Find context around the word
    matches = re.finditer(pattern, text, re.IGNORECASE)
    for m in matches:
        start = max(0, m.start() - 50)
        end = min(len(text), m.end() + 100)
        context = text[start:end].strip()
        # Only show if it looks like a message (has text around it, not just code)
        if len(context) > 20 and '<script' not in context[:10]:
            print(f"  Pattern '{pattern}': {context}")
            print()

# Look for any meta refresh or redirect
print("\n=== Buscando redirecciones ===")
meta_refresh = re.findall(r'<meta[^>]*refresh[^>]*>', text, re.IGNORECASE)
if meta_refresh:
    print(f"  Meta refresh: {meta_refresh}")
javascript_redirect = re.findall(r'window\.location|document\.location|location\.href', text)
if javascript_redirect:
    print(f"  JavaScript redirect found: {javascript_redirect}")

# Look for any anti-automation code
print("\n=== Buscando proteccion anti-automacion ===")
anti_auto_patterns = ['webdriver', 'selenium', 'phantom', 'headless', 'bot', 'crawler', 'spider', 'automation']
for pattern in anti_auto_patterns:
    if pattern in text.lower():
        idx = text.lower().find(pattern)
        context = text[max(0,idx-50):idx+100]
        print(f"  Found '{pattern}': {context}")

# Show the body text (without scripts)
print("\n=== Cuerpo de la pagina ===")
body_match = re.search(r'<body[^>]*>(.*?)</body>', text, re.DOTALL)
if body_match:
    body = body_match.group(1)
    # Remove scripts
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
    # Remove script tags
    body = re.sub(r'</?script[^>]*>', '', body)
    # Remove style tags  
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    # Remove HTML tags
    body = re.sub(r'<[^>]+>', ' ', body)
    body = re.sub(r'\s+', ' ', body).strip()
    print(f"  {body[:500]}")

# Check for any noscript or fallback content
print("\n=== Buscando noscript ===")
noscript = re.findall(r'<noscript[^>]*>(.*?)</noscript>', text, re.DOTALL)
if noscript:
    for ns in noscript[:3]:
        print(f"  {ns[:200]}")

# Check for any hidden inputs with special values
print("\n=== Buscando inputs ocultos ===")
hidden_inputs = re.findall(r'<input[^>]*type=["\']hidden["\'][^>]*>', text)
for inp in hidden_inputs:
    print(f"  {inp[:200]}")
