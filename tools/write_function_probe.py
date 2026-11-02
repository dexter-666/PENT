#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
write_function_probe.py
Fase de Auditoría: Identificación y prueba de funciones de escritura.
Metodología: OWASP WSTG-CONF-05 / WSTG-AUTH-02 — No Destructiva.

Objetivo:
  1. Identificar endpoints de escritura en la aplicación (formularios, uploads, APIs).
  2. Comprobar qué permisos requiere (anónimo / autenticado / admin).
  3. Verificar si el servidor acepta la operación o la rechaza.
  4. Registrar solicitud, respuesta y estado de restauración.
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import re
import csv
import datetime
import hashlib
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

H = {'User-Agent': 'Thesis-Security-Audit/1.0'}
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()
EVIDENCE_FILE = 'findings/evidencia_write_functions.csv'

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get(url, **kw):
    try:
        return requests.get(url, headers=H, verify=False, timeout=10, **kw)
    except Exception as e:
        return None

def req(method, url, **kw):
    try:
        return requests.request(method, url, headers=H, verify=False, timeout=10, **kw)
    except Exception as e:
        return None


RECORDS = []

def record(target, test_id, classification, method, url, status, observed, snippet, remediation):
    RECORDS.append({
        'timestamp_iso': NOW,
        'target': target,
        'test_id': test_id,
        'classification': classification,
        'http_method': method,
        'url': url,
        'status_code': status,
        'observed_headers': observed,
        'response_snippet': snippet[:120].replace('\n', ' '),
        'expected_remediation': remediation,
    })

def save_all():
    fields = ['timestamp_iso','target','test_id','classification','http_method',
              'url','status_code','observed_headers','response_snippet','expected_remediation']
    with open(EVIDENCE_FILE, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(RECORDS)
    print(f"\n[OK] Evidencia guardada en: {EVIDENCE_FILE}")

def classify_response(r, baseline_len, method):
    """Clasifica la respuesta del servidor según reglas estrictas."""
    if r is None:
        return "ERROR_CONEXION", "Sin respuesta del servidor"

    is_soft_404 = r.status_code == 200 and abs(len(r.content) - baseline_len) < 60
    body = r.text[:200].replace('\n', ' ')

    if is_soft_404:
        return "FALSO_POSITIVO_SOFT404", body
    if method in ('PUT','POST','PATCH') and r.status_code in (200,201,204):
        return "ESCRITURA_POSIBLEMENTE_ACEPTADA", body
    if r.status_code in (401, 403):
        return "CONFIGURACION_SEGURA_AUTENTICACION", body
    if r.status_code == 405:
        return "CONFIGURACION_SEGURA_METODO_BLOQUEADO", body
    if r.status_code in (404, 302):
        return "RECURSO_NO_EXPUESTO", body
    return f"ESTADO_HTTP_{r.status_code}", body


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 1: sigea.uns.edu.pe (CodeIgniter)
# ─────────────────────────────────────────────────────────────────────────────
TARGET_A = "sigea.uns.edu.pe"
BASE_A = f"https://{TARGET_A}"

print("=" * 78)
print(f" PRUEBA DE FUNCIONES DE ESCRITURA — {TARGET_A}")
print("=" * 78)

r_home = get(BASE_A + '/')
baseline_a = len(r_home.content) if r_home else 0

# 1.1 Extracción de formularios HTML
print("\n[1.1] Identificación de formularios en la página principal")
if r_home:
    forms = re.findall(r'<form[^>]+action=["\']([^"\']+)["\']', r_home.text, re.I)
    methods_form = re.findall(r'<form[^>]+method=["\']([^"\']+)["\']', r_home.text, re.I)
    file_inputs = re.findall(r'<input[^>]+type=["\']file["\']', r_home.text, re.I)
    print(f"  Formularios detectados : {len(forms)}")
    print(f"  Métodos de formularios : {set(m.upper() for m in methods_form)}")
    print(f"  Inputs type=file       : {len(file_inputs)}")
    for f in forms[:6]:
        print(f"    → action: {f}")

# 1.2 Rutas típicas de CodeIgniter con funciones de escritura
print("\n[1.2] Sondeo de rutas de escritura (CodeIgniter — caja negra)")
rutas_ci = [
    ('/upload',           'POST', 'Endpoint genérico de upload'),
    ('/upload/file',      'POST', 'Endpoint de subida de archivos'),
    ('/archivos/subir',   'POST', 'Ruta de subida en español'),
    ('/api/upload',       'POST', 'API REST de upload'),
    ('/admin/upload',     'POST', 'Upload en panel admin'),
    ('/index.php/upload', 'POST', 'Upload bajo index.php (CodeIgniter)'),
    ('/config',           'GET',  'Exposición de configuración'),
    ('/phpinfo.php',      'GET',  'Exposición de phpinfo'),
    ('/test.php',         'GET',  'Archivo de prueba expuesto'),
]
for path, method, desc in rutas_ci:
    url = BASE_A + path
    r = req(method, url)
    status = r.status_code if r else 'ERR'
    clsf, snippet = classify_response(r, baseline_a, method)
    allow = r.headers.get('Allow','') if r else ''
    print(f"  [{clsf:<40}] {method} {path} -> HTTP {status}")
    record(TARGET_A, f"WRITE-CI-{path.replace('/','_')}", clsf, method, url,
           status, f"Allow: {allow}", snippet, desc)

# 1.3 Prueba controlada de PUT en ruta sin registro previo
print("\n[1.3] Prueba no destructiva de PUT (recurso que no existe)")
probe_url_a = BASE_A + '/audit_probe_nonexistent_resource_0x1F4A9.txt'
fake_content = b'AUDIT-PROBE-SAFE-TO-DELETE'

r_put = req('PUT', probe_url_a, data=fake_content, headers={**H, 'Content-Type': 'text/plain'})
status_put = r_put.status_code if r_put else 'ERR'
clsf_put, snip_put = classify_response(r_put, baseline_a, 'PUT')
print(f"  PUT {probe_url_a}")
print(f"  -> HTTP {status_put} | Clasificación: [{clsf_put}]")
record(TARGET_A, "WRITE-PUT-PROBE", clsf_put, 'PUT', probe_url_a,
       status_put, '', snip_put, 'Confirmar si el servidor permite creación de archivos arbitrarios')

# Verificar si el archivo fue creado (alcance de permiso)
r_get_after = get(probe_url_a)
created = r_get_after and r_get_after.status_code == 200 and fake_content in r_get_after.content
print(f"  GET posterior: HTTP {r_get_after.status_code if r_get_after else 'ERR'} | ¿Archivo creado?: {'SÍ ⚠️' if created else 'NO ✅'}")
if created:
    # Intentar eliminar el recurso creado (restauración)
    r_del = req('DELETE', probe_url_a)
    print(f"  DELETE (restauración): HTTP {r_del.status_code if r_del else 'ERR'}")


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 2: campus.uns.edu.pe (Moodle LMS)
# ─────────────────────────────────────────────────────────────────────────────
TARGET_B = "campus.uns.edu.pe"
BASE_B = f"https://{TARGET_B}"

print()
print("=" * 78)
print(f" PRUEBA DE FUNCIONES DE ESCRITURA — {TARGET_B}")
print("=" * 78)

r_home_b = get(BASE_B + '/')
baseline_b = len(r_home_b.content) if r_home_b else 0

# 2.1 Rutas de escritura conocidas de Moodle LMS
print("\n[2.1] Sondeo de rutas de escritura en Moodle (caja negra, sin autenticación)")
rutas_moodle = [
    ('/user/files.php',                    'GET',  'Repositorio privado de usuario'),
    ('/repository/draftfiles.php',          'GET',  'API de archivos en borrador'),
    ('/mod/resource/view.php',             'GET',  'Módulo de recursos'),
    ('/mod/assign/view.php',               'GET',  'Módulo de entregas/tareas'),
    ('/lib/editor/tiny/plugins/',          'GET',  'Plugins del editor TinyMCE'),
    ('/webservice/upload.php',             'POST', 'Endpoint de upload via API REST'),
    ('/draftfile.php',                     'GET',  'Servicio de archivos temporales'),
    ('/tokenpluginfile.php',               'GET',  'Archivos con token de acceso'),
    ('/admin/tool/uploadcourse/',          'GET',  'Herramienta de importación (admin)'),
    ('/admin/tool/uploaduser/',            'GET',  'Herramienta de importación usuarios (admin)'),
    ('/files/index.php',                   'GET',  'Listado de archivos del sistema'),
]
for path, method, desc in rutas_moodle:
    url = BASE_B + path
    r = req(method, url, allow_redirects=False)
    status = r.status_code if r else 'ERR'
    clsf, snippet = classify_response(r, baseline_b, method)
    location = r.headers.get('Location', '') if r else ''
    print(f"  [{clsf:<40}] {method} {path:<45} -> HTTP {status}{' → ' + location if location else ''}")
    record(TARGET_B, f"WRITE-MDL-{path.replace('/','_').strip('_')}", clsf, method, url,
           status, f"Location: {location}" if location else '', snippet, desc)

# 2.2 Prueba de POST al endpoint de upload de la API REST de Moodle (sin token)
print("\n[2.2] Prueba de upload en webservice/upload.php sin autenticación")
upload_url = BASE_B + '/webservice/upload.php'
r_upload = req('POST', upload_url,
               files={'file': ('audit_probe.txt', b'AUDIT-PROBE-SAFE', 'text/plain')},
               allow_redirects=False)
status_up = r_upload.status_code if r_upload else 'ERR'
body_up = r_upload.text[:200] if r_upload else 'ERR'
clsf_up, snip_up = classify_response(r_upload, baseline_b, 'POST')
print(f"  POST /webservice/upload.php -> HTTP {status_up}")
print(f"  Body: {body_up[:120]}")
print(f"  Clasificación: [{clsf_up}]")
record(TARGET_B, "WRITE-API-UPLOAD-NOAUTH", clsf_up, 'POST', upload_url,
       status_up, '', snip_up, 'La API de upload debe requerir token wstoken válido')

# 2.3 Verificar si existe un formulario de carga en la página de login
print("\n[2.3] Análisis del formulario de login (vectores de escritura anónima)")
r_login = get(BASE_B + '/login/index.php')
if r_login:
    forms_b = re.findall(r'<form[^>]+action=["\']([^"\']+)["\']', r_login.text, re.I)
    file_inp_b = re.findall(r'<input[^>]+type=["\']file["\']', r_login.text, re.I)
    token_inp = re.findall(r'<input[^>]+name=["\']logintoken["\']', r_login.text, re.I)
    print(f"  Formularios en /login: {forms_b[:4]}")
    print(f"  Inputs type=file: {len(file_inp_b)}")
    print(f"  CSRF logintoken presente: {'SÍ ✅' if token_inp else 'NO ⚠️'}")
    record(TARGET_B, "WRITE-LOGIN-FORM", "CONFIGURACION_SEGURA" if token_inp else "EXPOSICION_INFO",
           'GET', BASE_B + '/login/index.php', r_login.status_code,
           '', f"CSRF token: {'presente' if token_inp else 'ausente'}",
           'Mantener logintoken en todos los formularios de autenticación')

# ─────────────────────────────────────────────────────────────────────────────
save_all()
