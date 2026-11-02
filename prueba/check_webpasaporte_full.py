#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

r = s.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
text = r.text

# Find ALL inputs (including password types)
all_inputs = re.findall(r'<input[^>]*>', text)
print("=== TODOS LOS INPUTS ===")
for inp in all_inputs:
    print(f"  {inp}")

# Find all text/password inputs specifically
text_inputs = re.findall(r'<input[^>]*type=["\']?(text|password|hidden)["\']?[^>]*>', text)
print(f"\n=== INPUTS de texto/contraseña ===")
for ti in text_inputs:
    print(f"  {ti}")

# Find ALL form fields including hidden ones
all_fields = re.findall(r'(?:name|id)="([^"]+)"', text)
print(f"\n=== TODOS LOS CAMPOS ===")
for f in all_fields:
    if any(kw in f.lower() for kw in ['usuario', 'password', 'pass', 'user', 'login', 'user', 'clave', 'user', 'cred', 'user', 'user', 'usr', 'passwd', 'pwd']):
        print(f"  CREDENCIAL: {f}")

# Look for username/password by pattern
for pattern in ['usuario', 'user', 'login', 'uname', 'uid', 'username', 'contrasena', 'password', 'passwd', 'pwd', 'clave', 'cred']:
    matches = list(re.finditer(pattern, text, re.IGNORECASE))
    for m in matches[:3]:
        ctx = text[max(0,m.start()-50):m.end()+100]
        ctx_clean = re.sub(r'<[^>]+>', ' ', ctx)
        ctx_clean = re.sub(r'\s+', ' ', ctx_clean).strip()
        print(f"  [{pattern}]: {ctx_clean[:200]}")

# Find the full form HTML
form_match = re.search(r'<form id="frmLogueo"[^>]*>(.*?)</form>', text, re.DOTALL)
if form_match:
    form_html = form_match.group(1)
    print(f"\n=== FORMA frmLogueo COMPLETA ===")
    # Print cleaned version
    form_clean = re.sub(r'<[^>]+>', '\n', form_html)
    form_clean = re.sub(r'\n\s*\n', '\n', form_clean)
    form_clean = re.sub(r'^\s*$', '', form_clean, flags=re.MULTILINE)
    print(form_clean[:2000])

# Find the full body content
body_match = re.search(r'<body[^>]*>(.*?)</body>', text, re.DOTALL)
if body_match:
    body = body_match.group(1)
    body_clean = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
    body_clean = re.sub(r'<style[^>]*>.*?</style>', '', body_clean, flags=re.DOTALL)
    body_clean = re.sub(r'</?[^>]+>', ' ', body_clean)
    body_clean = re.sub(r'\s+', ' ', body_clean).strip()
    print(f"\n=== BODY TEXT ===")
    print(body_clean[:1000])

# Check for any hidden fields or JS that loads username/password
if 'usuario' in text.lower() and 'password' not in text.lower():
    print("\n=== NOTA: username exists but password might be loaded via JS ===")

# Find any JS functions for authentication
if 'login' in text.lower():
    login_idx = text.lower().find('login')
    print(f"\n=== JS around 'login' ===")
    print(text[max(0,login_idx-100):login_idx+300])

# Check if there's a separate login action
print(f"\n=== FORM ACTION ===")
actions = re.findall(r'action="([^"]+)"', text)
for a in actions:
    print(f"  {a}")

# Look for any username/password input that might be dynamically loaded
if 'input' in text and 'text' in text:
    # Find any input with type not specified (defaults to text)
    no_type_inputs = re.findall(r'<input[^>]*name="[^"]+"[^>]*>', text)
    print(f"\n=== INPUTS sin tipo explicito ===")
    for ni in no_type_inputs:
        print(f"  {ni[:200]}")
