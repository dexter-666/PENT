import requests, urllib3, re
urllib3.disable_warnings()
h = {'User-Agent': 'Mozilla/5.0'}

r = requests.get('https://biblioteca.uns.edu.pe/alerta_por_titulo.asp?letra=A', headers=h, verify=False, timeout=10)
links = re.findall(r'<a\s+[^>]*href=["\']?([^"\'\s>]+)["\']?[^>]*>(.*?)</a>', r.text, re.I)

print("Links encontrados en alerta_por_titulo:")
for href, text in links:
    clean_txt = re.sub(r'<[^>]+>', '', text).strip()
    if 'alerta' in href.lower() or 'pag' in href.lower() or 'letra' in href.lower():
        print(f"  {clean_txt} -> {href}")
