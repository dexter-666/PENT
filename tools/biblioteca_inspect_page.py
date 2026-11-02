import requests, urllib3, re
urllib3.disable_warnings()
h = {'User-Agent': 'Mozilla/5.0'}
r = requests.get('https://biblioteca.uns.edu.pe/cat_alerta_por_titulo.asp', headers=h, verify=False, timeout=10)
forms = re.findall(r'<form[\s\S]*?</form>', r.text, re.I)
print(f"Forms found: {len(forms)}")
for f in forms:
    print(f[:600])

clean_text = re.sub(r'<[^>]+>', ' ', r.text)
clean_lines = [l.strip() for l in clean_text.splitlines() if l.strip()]
print("\n--- Texto visible ---")
print("\n".join(clean_lines[15:45]))
