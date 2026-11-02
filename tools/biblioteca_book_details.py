import requests, urllib3, re
urllib3.disable_warnings()
h = {'User-Agent': 'Mozilla/5.0'}

r = requests.get('https://biblioteca.uns.edu.pe/alerta_por_titulo.asp?letra=Z', headers=h, verify=False, timeout=8)
links = re.findall(r'<a\s+[^>]*href=["\']?([^"\'\s>]+)["\']?[^>]*>(.*?)</a>', r.text, re.I)
for href, txt in links:
    if 'letra=' not in href and 'index' not in href and 'alerta_por_titulo' not in href:
        clean = re.sub(r'<[^>]+>', '', txt).strip()
        print(f"  {clean} -> {href}")
