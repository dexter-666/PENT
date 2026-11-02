import requests, urllib3, re
urllib3.disable_warnings()
h = {'User-Agent': 'Mozilla/5.0'}

for page in ['catalogo.htm', 'sms.htm', 'repoins.htm', 'base_datos.htm', 'alerta_bibliografica.htm']:
    url = f"https://biblioteca.uns.edu.pe/{page}"
    r = requests.get(url, headers=h, verify=False, timeout=8)
    forms = re.findall(r'<form[\s\S]*?</form>', r.text, re.I)
    links = re.findall(r'href=["\']([^"\']+)["\']', r.text, re.I)
    asp_links = [l for l in links if '.asp' in l.lower()]
    print(f"\n=== {page} (status={r.status_code}, len={len(r.content)}) ===")
    print(f"Forms count: {len(forms)}")
    for f in forms:
        action = re.search(r'action=["\']([^"\']+)["\']', f, re.I)
        method = re.search(r'method=["\']([^"\']+)["\']', f, re.I)
        inputs = re.findall(r'name=["\']([^"\']+)["\']', f, re.I)
        print(f"  Form action={action.group(1) if action else 'none'}, method={method.group(1) if method else 'get'}, inputs={inputs}")
    if asp_links:
        print(f"  ASP links: {asp_links}")
