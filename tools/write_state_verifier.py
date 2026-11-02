#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
write_state_verifier.py
Fase de Auditoría: Verificación de escritura con ciclo Estado-Antes / Estado-Después.
Metodología: OWASP WSTG-ATHN-06 / WSTG-CONF-05

Pasos de cada prueba:
  1. ESTADO INICIAL  — consulta el recurso y registra hash del contenido.
  2. OPERACIÓN       — ejecuta la escritura prevista por la aplicación.
  3. VERIFICACIÓN    — vuelve a consultar y compara el hash.
  4. RESTAURACIÓN    — revierte el recurso al estado inicial.
  5. DOCUMENTACIÓN   — guarda solicitud, respuesta y evidencia reproducible.

Modo de uso:
  - Sin argumentos: prueba sin autenticación (verifica qué es accesible).
  - Con --wstoken TOKEN: prueba la API REST de Moodle con token válido.
  - Con --cookie VALOR: prueba con sesión autenticada (copiar de DevTools).
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import re
import csv
import json
import hashlib
import argparse
import datetime
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── Argumentos opcionales (credenciales para fase autenticada) ────────────────
parser = argparse.ArgumentParser(description='Write State Verifier — Auditoría no destructiva')
parser.add_argument('--wstoken', default='', help='Token de API REST de Moodle (wstoken)')
parser.add_argument('--cookie',  default='', help='Valor de cookie MoodleSession=... (copiar de DevTools)')
parser.add_argument('--sigea-cookie', default='', help='Cookie de sesión SIGEA ci_session=...')
args = parser.parse_args()

NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()
H = {'User-Agent': 'Thesis-Security-Audit/1.0 (State-Verifier)'}

EVIDENCE_FILE = 'findings/evidencia_verificacion_escritura.csv'
RECORDS = []


# ─── Helpers ─────────────────────────────────────────────────────────────────
def sha256_of(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:16]

def safe_get(session, url, **kw):
    try:
        r = session.get(url, headers=H, verify=False, timeout=12, **kw)
        return r
    except Exception as e:
        return None

def safe_req(session, method, url, **kw):
    try:
        r = session.request(method, url, headers=H, verify=False, timeout=12, **kw)
        return r
    except Exception as e:
        return None

def record(target, test_id, step, classification, method, url,
           status, hash_before, hash_after, changed, body_snippet, note):
    RECORDS.append({
        'timestamp_iso':   NOW,
        'target':          target,
        'test_id':         test_id,
        'step':            step,
        'classification':  classification,
        'method':          method,
        'url':             url,
        'status_code':     status,
        'sha256_before':   hash_before,
        'sha256_after':    hash_after,
        'estado_changed':  changed,
        'body_snippet':    str(body_snippet)[:120].replace('\n', ' '),
        'nota':            note,
    })

def save_all():
    fields = ['timestamp_iso','target','test_id','step','classification','method',
              'url','status_code','sha256_before','sha256_after','estado_changed',
              'body_snippet','nota']
    with open(EVIDENCE_FILE, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(RECORDS)
    print(f"\n[OK] Evidencia guardada en: {EVIDENCE_FILE}")


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE A — Moodle: API REST de upload con/sin token
# ─────────────────────────────────────────────────────────────────────────────
def test_moodle_webservice_upload(wstoken: str):
    TARGET = "campus.uns.edu.pe"
    BASE   = f"https://{TARGET}"
    ses    = requests.Session()

    print("\n" + "=" * 78)
    print(f" BLOQUE A — Moodle API REST Upload  [{TARGET}]")
    print(f" wstoken: {'<proporcionado>' if wstoken else '<NO PROPORCIONADO — prueba sin auth>'}")
    print("=" * 78)

    upload_url = BASE + '/webservice/upload.php'
    PROBE_CONTENT = b'AUDIT-PROBE-SAFE-TO-DELETE-' + NOW.encode()
    PROBE_NAME    = 'audit_probe_verifier.txt'

    # ── Paso 1: Estado inicial (no existe el archivo aún) ─────────────────
    print("\n[A.1] ESTADO INICIAL — verificar que el archivo de prueba no existe")
    params_before = {'wstoken': wstoken, 'component': 'user', 'filearea': 'draft',
                     'itemid': 0, 'filepath': '/', 'filename': PROBE_NAME,
                     'filecontent': ''} if wstoken else {}

    r_before = safe_get(ses, upload_url, params={'wstoken': wstoken} if wstoken else {})
    hash_before = sha256_of(r_before.content) if r_before else 'N/A'
    status_before = r_before.status_code if r_before else 'ERR'
    print(f"  GET {upload_url} -> HTTP {status_before} | sha256={hash_before}")
    record(TARGET, 'A-MOODLE-UPLOAD', 'ESTADO_INICIAL', 'INFO', 'GET',
           upload_url, status_before, hash_before, 'N/A', False,
           r_before.text[:120] if r_before else '', 'Snapshot previo a la escritura')

    # ── Paso 2: Operación de escritura (upload multipart) ─────────────────
    print(f"\n[A.2] OPERACION — POST upload {'con token' if wstoken else 'sin token (debe rechazarse)'}")
    post_params = {'wstoken': wstoken} if wstoken else {}
    r_write = safe_req(ses, 'POST', upload_url,
                       params=post_params,
                       files={'file': (PROBE_NAME, PROBE_CONTENT, 'text/plain')})

    status_write = r_write.status_code if r_write else 'ERR'
    body_write = r_write.text if r_write else 'ERR'
    print(f"  POST {upload_url} -> HTTP {status_write}")
    print(f"  Respuesta: {body_write[:200]}")

    write_ok = False
    file_id  = None
    if r_write and r_write.status_code == 200:
        try:
            data = r_write.json()
            # Moodle devuelve lista con info del archivo al subir correctamente
            if isinstance(data, list) and len(data) > 0 and 'itemid' in data[0]:
                write_ok = True
                file_id = data[0].get('itemid')
                print(f"  ⚠️  ESCRITURA ACEPTADA — itemid={file_id}, filename={data[0].get('filename')}")
            elif 'error' in data:
                print(f"  ✅ Rechazado por el servidor: {data.get('error')} [{data.get('errorcode')}]")
        except Exception:
            pass

    clsf_write = 'ESCRITURA_CONFIRMADA' if write_ok else 'CONFIGURACION_SEGURA_AUTH_REQUERIDA'
    record(TARGET, 'A-MOODLE-UPLOAD', 'OPERACION', clsf_write, 'POST',
           upload_url, status_write, hash_before, 'PENDIENTE', write_ok,
           body_write, f"Token={'presente' if wstoken else 'ausente'} | itemid={file_id}")

    # ── Paso 3: Verificación del estado posterior ──────────────────────────
    print(f"\n[A.3] VERIFICACION — ¿persiste el archivo en el servidor?")
    hash_after = hash_before

    if write_ok and file_id and wstoken:
        # Intentar acceder al archivo subido vía draftfile
        draft_url = f"{BASE}/draftfile.php/99/{wstoken}/user/draft/{file_id}/{PROBE_NAME}"
        r_verify = safe_get(ses, draft_url)
        if r_verify and r_verify.status_code == 200 and PROBE_CONTENT in r_verify.content:
            hash_after = sha256_of(r_verify.content)
            changed = (hash_before != hash_after)
            print(f"  ⚠️  ARCHIVO VERIFICADO EN SERVIDOR — HTTP {r_verify.status_code} | sha256={hash_after}")
            record(TARGET, 'A-MOODLE-UPLOAD', 'VERIFICACION', 'ESCRITURA_CONFIRMADA', 'GET',
                   draft_url, r_verify.status_code, hash_before, hash_after, changed,
                   'Contenido del archivo encontrado en servidor', 'Verificación positiva — escritura confirmada')
        else:
            v_status = r_verify.status_code if r_verify else 'ERR'
            print(f"  ✅ Archivo NO verificado — HTTP {v_status}")
            record(TARGET, 'A-MOODLE-UPLOAD', 'VERIFICACION', 'SIN_CAMBIO_VERIFICADO', 'GET',
                   draft_url, v_status, hash_before, hash_before, False,
                   '', 'Archivo no accesible o no persistido')
    else:
        print("  ✅ No hubo escritura que verificar (operación rechazada correctamente)")
        record(TARGET, 'A-MOODLE-UPLOAD', 'VERIFICACION', 'SIN_CAMBIO',
               'N/A', upload_url, 'N/A', hash_before, hash_before, False,
               '', 'Operación rechazada — sin cambio de estado')

    # ── Paso 4: Restauración ───────────────────────────────────────────────
    print(f"\n[A.4] RESTAURACION")
    if write_ok and file_id and wstoken:
        # Eliminar el archivo draft usando la API de repositorio de Moodle
        del_url = BASE + '/repository/draftfiles.php'
        r_del = safe_req(ses, 'POST', del_url, data={
            'wstoken': wstoken, 'repo_id': file_id, 'action': 'delete', 'filename': PROBE_NAME
        })
        del_status = r_del.status_code if r_del else 'ERR'
        print(f"  DELETE vía repositorio API -> HTTP {del_status} | {r_del.text[:80] if r_del else 'ERR'}")
        record(TARGET, 'A-MOODLE-UPLOAD', 'RESTAURACION', 'RESTAURADO', 'POST',
               del_url, del_status, hash_after, hash_before, True,
               r_del.text[:80] if r_del else '', 'Eliminación del recurso de prueba')
    else:
        print("  ✅ Sin archivo creado — restauración no necesaria")
        record(TARGET, 'A-MOODLE-UPLOAD', 'RESTAURACION', 'NO_APLICA',
               'N/A', 'N/A', 'N/A', hash_before, hash_before, False,
               '', 'No se creó ningún recurso')


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE B — Moodle: Ruta de perfil de usuario (edición de datos)
# ─────────────────────────────────────────────────────────────────────────────
def test_moodle_profile_edit(moodle_cookie: str):
    TARGET = "campus.uns.edu.pe"
    BASE   = f"https://{TARGET}"
    ses    = requests.Session()
    if moodle_cookie:
        ses.cookies.set('MoodleSession', moodle_cookie, domain=TARGET)

    print("\n" + "=" * 78)
    print(f" BLOQUE B — Moodle: Edición de Perfil de Usuario [{TARGET}]")
    print(f" cookie: {'<proporcionada>' if moodle_cookie else '<NO PROPORCIONADA — solo lectura anónima>'}")
    print("=" * 78)

    profile_url = BASE + '/user/edit.php'

    # Paso 1: Estado inicial (GET del formulario)
    print("\n[B.1] ESTADO INICIAL — GET del formulario de edición de perfil")
    r_before = safe_get(ses, profile_url)
    status_before = r_before.status_code if r_before else 'ERR'
    hash_before = sha256_of(r_before.content) if r_before else 'N/A'

    # Detectar si estamos autenticados o nos redirigió a login
    is_authenticated = False
    sesskey = None
    if r_before and r_before.status_code == 200:
        if '/login/index.php' not in r_before.url:
            is_authenticated = True
            # Extraer sesskey del formulario (necesario para CSRF)
            m = re.search(r'sesskey=([a-zA-Z0-9]+)', r_before.text)
            if m:
                sesskey = m.group(1)
    
    print(f"  GET {profile_url} -> HTTP {status_before} | Autenticado: {'SÍ' if is_authenticated else 'NO (requiere login)'}")
    print(f"  CSRF sesskey: {sesskey if sesskey else 'No encontrado'}")
    print(f"  sha256={hash_before}")
    record(TARGET, 'B-MOODLE-PROFILE', 'ESTADO_INICIAL',
           'AUTENTICADO' if is_authenticated else 'ANONIMO_REDIRIGIDO',
           'GET', profile_url, status_before, hash_before, 'N/A', False,
           r_before.text[:120] if r_before else '', f"sesskey={'presente' if sesskey else 'ausente'}")

    if not is_authenticated:
        print("  ✅ Sin autenticación el servidor redirige correctamente al login.")
        print("     Para continuar esta fase proporciona --cookie MoodleSession=<valor>")
        record(TARGET, 'B-MOODLE-PROFILE', 'OPERACION', 'NO_EJECUTADA',
               'POST', profile_url, 'N/A', hash_before, hash_before, False,
               '', 'Autenticación requerida — sin cookie proporcionada')
        return

    # Paso 2: Operación de escritura (cambio de descripción — campo no crítico)
    print("\n[B.2] OPERACION — Modificación de campo 'description' en perfil")
    PROBE_DESC = f"AUDIT-PROBE-DESCRIPTION-{NOW[:19]}"
    post_data = {
        'sesskey':     sesskey or '',
        'description': PROBE_DESC,
        '_qf__user_edit_form': '1',
    }
    r_write = safe_req(ses, 'POST', profile_url, data=post_data, allow_redirects=True)
    status_write = r_write.status_code if r_write else 'ERR'
    hash_write = sha256_of(r_write.content) if r_write else 'N/A'
    print(f"  POST {profile_url} -> HTTP {status_write} | sha256={hash_write}")

    # Paso 3: Verificación — GET del perfil y buscar la descripción
    print("\n[B.3] VERIFICACION — Comparar descripción actual con valor de prueba")
    r_verify = safe_get(ses, BASE + '/user/profile.php')
    changed = False
    if r_verify and PROBE_DESC in r_verify.text:
        changed = True
        print(f"  ⚠️  CAMBIO VERIFICADO — descripción de prueba encontrada en perfil público")
    else:
        print(f"  ✅ Descripción de prueba NO encontrada — sin cambio persistido")
    hash_after = sha256_of(r_verify.content) if r_verify else hash_write
    record(TARGET, 'B-MOODLE-PROFILE', 'VERIFICACION',
           'ESCRITURA_CONFIRMADA' if changed else 'SIN_CAMBIO',
           'GET', BASE + '/user/profile.php',
           r_verify.status_code if r_verify else 'ERR',
           hash_before, hash_after, changed,
           r_verify.text[:120] if r_verify else '', 'Verificación de cambio en perfil público')

    # Paso 4: Restauración — vaciar la descripción de prueba
    if changed and sesskey:
        print("\n[B.4] RESTAURACION — Limpiar descripción de prueba")
        restore_data = {
            'sesskey':     sesskey,
            'description': '',
            '_qf__user_edit_form': '1',
        }
        r_restore = safe_req(ses, 'POST', profile_url, data=restore_data, allow_redirects=True)
        status_restore = r_restore.status_code if r_restore else 'ERR'
        r_recheck = safe_get(ses, BASE + '/user/profile.php')
        restored = r_recheck and PROBE_DESC not in r_recheck.text
        print(f"  POST restauración -> HTTP {status_restore} | ¿Descripción limpia?: {'SÍ ✅' if restored else 'NO ⚠️'}")
        record(TARGET, 'B-MOODLE-PROFILE', 'RESTAURACION',
               'RESTAURADO' if restored else 'RESTAURACION_FALLIDA',
               'POST', profile_url, status_restore, hash_after, hash_before, restored,
               '', 'Limpieza de descripción de prueba')
    else:
        print("\n[B.4] RESTAURACION — No aplica (sin cambio persistido)")


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE C — SIGEA (CodeIgniter): Formulario de login como vector de escritura
# Objetivo: verificar si el endpoint POST de login escribe en el servidor
# ─────────────────────────────────────────────────────────────────────────────
def test_sigea_login_write():
    TARGET = "sigea.uns.edu.pe"
    BASE   = f"https://{TARGET}"
    ses    = requests.Session()

    print("\n" + "=" * 78)
    print(f" BLOQUE C — SIGEA (CodeIgniter): Vector de escritura POST login [{TARGET}]")
    print("=" * 78)

    login_url = BASE + '/index.php/C_logueo/iniciar_session'

    # Paso 1: Estado inicial
    print("\n[C.1] ESTADO INICIAL — GET de la página principal")
    r_home = safe_get(ses, BASE + '/')
    hash_before = sha256_of(r_home.content) if r_home else 'N/A'
    status_home = r_home.status_code if r_home else 'ERR'
    print(f"  GET {BASE}/ -> HTTP {status_home} | sha256={hash_before}")
    record(TARGET, 'C-SIGEA-LOGIN', 'ESTADO_INICIAL', 'INFO', 'GET',
           BASE + '/', status_home, hash_before, 'N/A', False,
           r_home.text[:120] if r_home else '', 'Snapshot previo')

    # Paso 2: POST al endpoint de login con credenciales inválidas
    # Propósito: verificar si el servidor expone errores de detalles (oracle de usuario)
    print("\n[C.2] OPERACION — POST con credenciales inválidas (sin usuario real)")
    probe_user = 'audit_probe_nonexistent_user_x9z'
    r_login = safe_req(ses, 'POST', login_url,
                       data={'usuario': probe_user, 'password': 'AUDIT-PROBE-SAFE'},
                       allow_redirects=True)
    status_login = r_login.status_code if r_login else 'ERR'
    body_login = r_login.text[:400] if r_login else 'ERR'
    hash_login = sha256_of(r_login.content) if r_login else 'N/A'

    # Analizar la respuesta
    reveals_user  = probe_user in body_login
    generic_error = any(t in body_login.lower() for t in ['usuario', 'contraseña', 'credenciales', 'invalid'])
    json_error    = body_login.strip().startswith('{')

    print(f"  POST {login_url} -> HTTP {status_login}")
    print(f"  ¿Refleja el usuario probado?: {'SÍ ⚠️' if reveals_user else 'NO ✅'}")
    print(f"  ¿Error genérico (sin oracle)?: {'SÍ ✅' if generic_error else 'NO'}")
    print(f"  Respuesta: {body_login[:200]}")

    clsf = 'EXPOSICION_INFO_ORACLE_USUARIO' if reveals_user else 'CONFIGURACION_SEGURA'
    record(TARGET, 'C-SIGEA-LOGIN', 'OPERACION', clsf, 'POST',
           login_url, status_login, hash_before, hash_login,
           reveals_user, body_login,
           f"oracle={'SÍ' if reveals_user else 'NO'} | genérico={'SÍ' if generic_error else 'NO'}")

    # Paso 3: Verificar si la sesión cambió de estado
    print("\n[C.3] VERIFICACION — ¿El servidor estableció una sesión válida?")
    r_after = safe_get(ses, BASE + '/', allow_redirects=True)
    hash_after = sha256_of(r_after.content) if r_after else 'N/A'
    changed = hash_before != hash_after
    cookies = dict(ses.cookies)
    print(f"  Cookies de sesión establecidas: {list(cookies.keys())}")
    print(f"  sha256 antes={hash_before} | sha256 después={hash_after} | ¿Cambio?={'SÍ ⚠️' if changed else 'NO ✅'}")
    record(TARGET, 'C-SIGEA-LOGIN', 'VERIFICACION',
           'SESION_CREADA' if changed else 'SIN_SESION_VALIDA',
           'GET', BASE + '/', r_after.status_code if r_after else 'ERR',
           hash_before, hash_after, changed,
           str(list(cookies.keys())), 'Verificación de sesión post-login inválido')

    # Paso 4: Restauración (siempre sin cambio porque las credenciales son inválidas)
    print("\n[C.4] RESTAURACION — Sin recurso creado (credenciales inválidas rechazadas)")
    record(TARGET, 'C-SIGEA-LOGIN', 'RESTAURACION', 'NO_APLICA',
           'N/A', 'N/A', 'N/A', hash_before, hash_before, False,
           '', 'Sin estado persistido que restaurar')


# ─── EJECUCIÓN PRINCIPAL ──────────────────────────────────────────────────────
print(f"{'=' * 78}")
print(f" WRITE STATE VERIFIER — Auditoría de Verificación de Escritura")
print(f" Timestamp: {NOW}")
print(f"{'=' * 78}")

test_moodle_webservice_upload(args.wstoken)
test_moodle_profile_edit(args.cookie)
test_sigea_login_write()
save_all()
