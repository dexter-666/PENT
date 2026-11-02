import requests, urllib3, re
urllib3.disable_warnings()
h = {'User-Agent': 'Mozilla/5.0'}

for page in ['alerta_bibliografica.asp', 'cat_alerta_por_titulo.asp']:
    url = f"https://biblioteca.uns.edu.pe/{page}"
    try:
        print(f"Probando {page} con timeout de 12s...")
        r = requests.get(url, headers=h, verify=False, timeout=12)
        print(f"=== {page} (status={r.status_code}, len={len(r.content)}) ===")
    except requests.exceptions.Timeout:
        print(f"=== {page} TIMEOUT (script ASP bloqueado o esperando DB) ===")
    except Exception as e:
        print(f"=== {page} Error: {e} ===")
