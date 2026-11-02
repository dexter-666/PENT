import requests, urllib3, re
urllib3.disable_warnings()
h = {'User-Agent': 'Mozilla/5.0'}

r = requests.get('https://biblioteca.uns.edu.pe/ver_libro.asp?idm=371', headers=h, verify=False, timeout=8)
clean_text = re.sub(r'<[^>]+>', ' ', r.text)
clean_lines = [l.strip() for l in clean_text.splitlines() if l.strip()]
print(f"Status: {r.status_code}, Bytes: {len(r.content)}")
print("\n".join(clean_lines[20:60]))
