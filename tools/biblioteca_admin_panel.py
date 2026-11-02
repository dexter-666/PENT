import requests, urllib3, re, hashlib
urllib3.disable_warnings()

BASE = "https://biblioteca.uns.edu.pe"
h = {'User-Agent': 'Mozilla/5.0'}

print("="*60)
print("HALLAZGO CRITICO: menu_admin.asp EXISTE (302->inicia_sesion)")
print("="*60)

# Confirmar: menu_admin.asp existe con 302 -> auth wall
r = requests.get(BASE + '/menu_admin.asp', headers=h, verify=False, timeout=8, allow_redirects=False)
print(f"\nGET /menu_admin.asp sin sesion: status={r.status_code}, Location={r.headers.get('Location','')}")

# Buscar mas endpoints del panel admin
print("\n[+] Buscando mas endpoints del panel de administracion:")
admin_paths = [
    '/menu_admin.asp',
    '/admin_menu.asp',
    '/alta_usuario.asp',
    '/alta_libro.asp',
    '/baja_usuario.asp',
    '/mod_usuario.asp',
    '/mod_libro.asp',
    '/ingresar.asp',
    '/ingreso.asp',
    '/catalogacion.asp',
    '/catalogo_admin.asp',
    '/libros_admin.asp',
    '/gestion_libros.asp',
    '/gestion_usuarios.asp',
    '/lista_usuarios.asp',
    '/lista_libros.asp',
    '/reportes.asp',
    '/reporte.asp',
    '/prestamos_admin.asp',
    '/devoluciones.asp',
    '/menu_usuario.asp',
    '/bienvenido.asp',
    '/inicio.asp',
    '/home.asp',
    '/panel.asp',
    '/configuracion.asp',
    '/config.asp',
    '/editar_libro.asp',
    '/nuevo_libro.asp',
]

found_auth_wall = []
found_open = []

for path in admin_paths:
    try:
        r = requests.get(BASE + path, headers=h, verify=False, timeout=4, allow_redirects=False)
        if r.status_code == 404:
            continue
        loc = r.headers.get('Location', '')
        if r.status_code in (301, 302) and 'inicia_sesion' in loc.lower():
            found_auth_wall.append(path)
            print(f"  [WALL] {path} -> {r.status_code} => {loc}")
        elif r.status_code == 200:
            found_open.append((path, len(r.content)))
            print(f"  [OPEN] {path} -> {r.status_code}, {len(r.content)}b")
        else:
            print(f"  [???] {path} -> {r.status_code}")
    except Exception as e:
        pass

print(f"\n=== RESUMEN ===")
print(f"Endpoints con muro de auth (302->inicia_sesion): {len(found_auth_wall)}")
for p in found_auth_wall:
    print(f"  - {p}")
print(f"Endpoints abiertos (200): {len(found_open)}")
for p, sz in found_open:
    print(f"  - {p} ({sz}b)")

# ==============================
# Checar si modo=A salta el muro de auth
# ==============================
print("\n[+] Probe: acceso a menu_admin.asp con cookie de sesion falsa:")
fake_cookies = {'ASPSESSIONIDCQCSQRSC': 'AAAAAAAAAAAAAAAAAAAAAAAA'}
r_fake = requests.get(BASE + '/menu_admin.asp', headers=h, cookies=fake_cookies, verify=False, timeout=8, allow_redirects=False)
print(f"  Con cookie inventada: status={r_fake.status_code}, Location={r_fake.headers.get('Location','')}")
