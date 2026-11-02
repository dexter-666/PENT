import requests, urllib3, re
urllib3.disable_warnings()

BASE = "https://biblioteca.uns.edu.pe"
h = {"User-Agent": "Mozilla/5.0"}

# Obtener pagina completa y analizar
r = requests.get(BASE + "/", verify=False, timeout=15, headers=h, allow_redirects=True)
print(f"HTTP {r.status_code} | {len(r.content)} bytes")
print(f"X-Powered-By: {r.headers.get('X-Powered-By','N/A')}")
print(f"Server: {r.headers.get('Server','N/A')}")
print()

# Mostrar HTML completo para analizar tecnologia
print("=== HTML SOURCE (primeros 3000 chars) ===")
print(r.text[:3000])
print()
print("=== TODOS LOS LINKS/FORMS ===")
links = re.findall(r'href=["\']([^"\']+)["\']', r.text)
for l in links[:30]:
    print(f"  {l}")

print()
print("=== SCRIPTS/SRC ===")
scripts = re.findall(r'src=["\']([^"\']+)["\']', r.text)
for s in scripts[:20]:
    print(f"  {s}")

print()
print("=== FORMS ===")
forms = re.findall(r'<form[^>]*>', r.text, re.I)
for f in forms:
    print(f"  {f}")
