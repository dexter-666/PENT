import requests, urllib3, re
urllib3.disable_warnings()
h = {'User-Agent': 'Mozilla/5.0'}

r = requests.get('https://biblioteca.uns.edu.pe/', headers=h, verify=False, timeout=8)
links = set(re.findall(r'(?:href|action|src)=["\']([^"\']+)["\']', r.text, re.I))

print(f"Total links encontrados: {len(links)}")
internal = set()
external = set()
for l in sorted(links):
    if l.startswith("http://") or l.startswith("https://"):
        if "biblioteca.uns.edu.pe" in l:
            internal.add(l)
        else:
            external.add(l)
    elif not l.startswith("javascript:") and not l.startswith("#") and not l.startswith("mailto:"):
        internal.add(l)

print("\n--- Enlaces Internos ---")
for l in sorted(internal):
    print(l)

print("\n--- Enlaces Externos ---")
for l in sorted(external):
    print(l)
