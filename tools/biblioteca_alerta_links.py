import requests, urllib3, re
urllib3.disable_warnings()
h = {'User-Agent': 'Mozilla/5.0'}
r = requests.get('https://biblioteca.uns.edu.pe/alerta_bibliografica.htm', headers=h, verify=False, timeout=8)
links = re.findall(r'<a\s+[^>]*href=["\']?([^"\'\s>]+)["\']?[^>]*>(.*?)</a>', r.text, re.I)
for href, text in links:
    clean_txt = re.sub(r'<[^>]+>', '', text).strip()
    print(f"{clean_txt} -> {href}")
