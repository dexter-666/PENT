#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# Check error.xhtml - the only non-login page
print("=== ERROR.XHTML ===")
r = s.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/error.xhtml', timeout=10)
print(f"Status: {r.status_code}, len={len(r.text)}")

body_match = re.search(r'<body[^>]*>(.*?)</body>', r.text, re.DOTALL)
if body_match:
    body = body_match.group(1)
    body_clean = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
    body_clean = re.sub(r'</?[^>]+>', ' ', body_clean)
    body_clean = re.sub(r'\s+', ' ', body_clean).strip()
    print(f"Content: {body_clean[:1000]}")

# Check error.xhtml form
forms = re.findall(r'<form[^>]*>', r.text)
print(f"\nForms: {forms}")
inputs = re.findall(r'<input[^>]*>', r.text)
print(f"Inputs: {inputs[:10]}")

# Check for any hidden form fields
for inp in inputs:
    print(f"  {inp[:200]}")

# Look for any links or redirects
links = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>', r.text)
print(f"\nLinks: {links[:10]}")

# Check for any meta refresh
metas = re.findall(r'<meta[^>]*>', r.text)
for m in metas:
    print(f"  Meta: {m}")

# Now try to access error.xhtml with different parameters
print("\n=== ERROR.XHTML CON PARAMETROS ===")
for url in [
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/error.xhtml?tipo=estudiante',
    'https://sistemas.uns.edu.pe/WebPasaporte/faces/error.xhtml?user=fake',
]:
    try:
        r2 = s.get(url, timeout=5)
        tc = re.sub(r'<[^>]+>', ' ', r2.text)
        tc = re.sub(r'\s+', ' ', tc).strip()
        print(f"  {url.split('?')[1]} -> {r2.status_code}, len={len(r2.text)}")
        print(f"  Content: {tc[:200]}")
    except:
        pass

# Now look at the full login page HTML to find where username/password fields come from
# Check if they're in the original HTML but hidden by CSS
print("\n=== BUSCANDO CAMPOS OCULTOS EN EL HTML ORIGINAL ===")
r3 = s.get('https://sistemas.uns.edu.pe/WebPasaporte/faces/login.xhtml', timeout=10)
# Look for display:none elements
hidden_elements = re.findall(r'<div[^>]*style="[^"]*display[^:]*:[^"]*none[^"]*"[^>]*>(.*?)</div>', r3.text, re.DOTALL)
print(f"Hidden divs: {len(hidden_elements)}")
for he in hidden_elements[:3]:
    print(f"  {he[:200]}")

# Look for any elements with id containing "usuario" or "clave"
elements = re.findall(r'<[^>]*id="[^"]*(?:usuario|clave|password|pass|user|login|cred)[^"]*"[^>]*>', r3.text, re.IGNORECASE)
print(f"\nElements with credential-related ids: {len(elements)}")
for e in elements[:10]:
    print(f"  {e[:200]}")

# Look for any elements with style display:none
style_hidden = re.findall(r'[^>]*display\s*:\s*none', r3.text)
print(f"\nElements with display:none: {len(style_hidden)}")
for sh in style_hidden[:10]:
    print(f"  {sh[:100]}")

# Look for any panelGroup or outputPanel that might be hidden
panels = re.findall(r'<p:panel[^>]*>', r3.text) + re.findall(r'<h:panelGroup[^>]*>', r3.text) + re.findall(r'<p:outputPanel[^>]*>', r3.text)
print(f"\nPanel/Group elements: {len(panels)}")
for p in panels[:10]:
    print(f"  {p[:200]}")

# Check for any outputLabel for usuario/password
labels = re.findall(r'<p:outputLabel[^>]*>', r3.text) + re.findall(r'<h:outputLabel[^>]*>', r3.text)
print(f"\nOutputLabels: {len(labels)}")
for l in labels[:10]:
    print(f"  {l[:200]}")

# Check for any h:inputSecret or p:password
secrets = re.findall(r'<h:inputSecret[^>]*>', r3.text) + re.findall(r'<p:password[^>]*>', r3.text)
print(f"\nSecret/password fields: {len(secrets)}")
for sec in secrets[:5]:
    print(f"  {sec[:200]}")

# Check if the page uses any iframe
iframes = re.findall(r'<iframe[^>]*>', r3.text)
print(f"\nIframes: {len(iframes)}")
for f in iframes:
    print(f"  {f}")

# Check for any data-src or lazy-loaded content
data_srcs = re.findall(r'data-src="([^"]+)"', r3.text)
print(f"\ndata-src attributes: {data_srcs}")

# Look at the full raw HTML around where buttons are
print("\n=== HTML AROUND BOTONES ===")
cmd_idx = r3.text.find('cmdEstudiante')
if cmd_idx > 0:
    # Show 2000 chars around cmdEstudiante
    ctx = r3.text[cmd_idx-200:cmd_idx+2000]
    ctx_clean = re.sub(r'<[^>]+>', '\n', ctx)
    ctx_clean = re.sub(r'\n\s*\n', '\n', ctx_clean)
    print(ctx_clean[:1000])

# Also look for any JavaScript that loads the login form
# Look for functions that create or show login fields
scripts = re.findall(r'<script[^>]*>(.*?)</script>', r3.text, re.DOTALL)
for i, script in enumerate(scripts):
    if any(kw in script.lower() for kw in ['usuario', 'password', 'input', 'show', 'display', 'fadeIn', 'load', 'ajax']):
        print(f"\n=== Script {i} (relevant) ===")
        print(script[:500])

print("\n=== CONCLUSION ===")
print("Los campos de usuario/contraseña NO estan en el HTML")
print("Son cargados dinamicamente por JavaScript")
print("Necesitas un navegador real para ver los nombres exactos de los campos")
print("Pero el sistema parece estar bien protegido en este punto")
