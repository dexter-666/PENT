#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

print("=== WEBPASAPORTE - sistemas.uns.edu.pe ===")
r = s.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
print(f"Status: {r.status_code}")
print(f"Len: {len(r.text)}")
print(f"URL: {r.url}")
print()

for k,v in r.headers.items():
    if k.lower() in ['server', 'x-frame-options', 'x-content-type-options', 'referrer-policy', 'content-type', 'set-cookie']:
        print(f"  {k}: {v}")

text = r.text
if any(kw in text.lower() for kw in ['j_username', 'itUsuario', 'frmLogin', 'login', 'username', 'password']):
    print("-> Es pagina de LOGIN")
    forms = re.findall(r'<form[^>]*>', text)
    print(f"\nForms ({len(forms)}):")
    for f in forms[:5]:
        print(f"  {f[:200]}")
    inputs = re.findall(r'<input[^>]*>', text)
    print(f"\nInputs ({len(inputs)}):")
    for inp in inputs[:20]:
        print(f"  {inp[:200]}")
    
    # Extract all form fields
    print("\nForm fields:")
    field_names = re.findall(r'name="([^"]+)"', text)
    for fn in field_names:
        print(f"  {fn}")
    
    # Check for buttons
    buttons = re.findall(r'<button[^>]*>', text)
    buttons2 = re.findall(r'<p:commandButton[^>]*>', text)
    buttons3 = re.findall(r'<h:commandButton[^>]*>', text)
    print(f"\nButtons: {len(buttons)}")
    print(f"PrimeFaces buttons: {len(buttons2)}")
    print(f"JSF buttons: {len(buttons3)}")
    for b in buttons2[:5]:
        print(f"  PF: {b[:200]}")
    for b in buttons3[:5]:
        print(f"  JSF: {b[:200]}")
    
    # Check for onclick functions
    onclicks = re.findall(r'onclick="([^"]+)"', text)
    print(f"\nOnclick handlers:")
    for oc in onclicks[:5]:
        print(f"  {oc[:200]}")

elif len(text) < 500:
    print("-> Error o pagina vacia")
    print(text)
else:
    print(f"Preview: {text[:500]}")
    # Check if it's already authenticated
    if 'logout' in text.lower() or 'logout' in text.lower():
        print("-> Ya esta autenticado!")
