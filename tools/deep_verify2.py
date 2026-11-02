#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, sys, hashlib, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
H = {'User-Agent': 'Thesis-Security-Audit/1.0'}
BASE = 'https://campus.uns.edu.pe'

def get(path):
    try:
        return requests.get(BASE + path, timeout=12, verify=False, headers=H, allow_redirects=False)
    except Exception:
        return None

login = get('/login/index.php')
login_md5 = hashlib.md5(login.content).hexdigest()[:10] if login else 'N/A'
login_len = len(login.content) if login else 0
print(f'Referencia login: md5={login_md5} len={login_len}')
print()

print('=== /version.php ===')
r = get('/version.php')
if r:
    print(f'Status: {r.status_code} | len={len(r.content)}')
    print('Contenido (primeros 500 chars):')
    print(r.text[:500])
    print()

print('=== Directorios (comparacion con login) ===')
for p in ['/course/', '/mod/', '/filter/', '/lib/', '/admin/', '/theme/', '/files/']:
    r = get(p)
    if r:
        md5 = hashlib.md5(r.content).hexdigest()[:10]
        same = 'SOFT-404' if md5 == login_md5 else 'CONTENIDO DIFERENTE'
        title = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I | re.S)
        t = title.group(1).strip()[:40] if title else 'N/A'
        print(f'{p:<15} {r.status_code} len={len(r.content):<6} md5={md5} {same} title="{t}"')

print()
print('=== Busqueda de debug en login ===')
if login:
    debug_patterns = ['debug', 'warning', 'notice', 'fatal error', 'stack trace', 'deprecated']
    for pat in debug_patterns:
        if pat.lower() in login.text.lower():
            idx = login.text.lower().find(pat.lower())
            context = login.text[max(0, idx - 50):idx + 100].replace('\n', ' ')
            print(f'  Encontrado "{pat}": ...{context}...')
