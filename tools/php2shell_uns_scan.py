#!/usr/bin/env python3
"""
PHP2Shell Scanner — Integración UNS
=====================================
Pentest autorizado UNS — Wrapper sobre el scanner oficial de Mr-Destroyer/PHP2SHELL
Repo: https://github.com/Mr-Destroyer/PHP2SHELL

Ejecuta el scanner oficial php2shell contra los targets de UNS y genera:
  - Salida en consola con colores
  - JSON detallado de resultados
  - Ficha de hallazgo en formato VULN-XXX.md (si se detecta vulnerabilidad)

USO:
    python php2shell_uns_scan.py
    python php2shell_uns_scan.py --target https://sigea.uns.edu.pe
    python php2shell_uns_scan.py --target https://orcl.uns.edu.pe --max-probe 7
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Agregar el scanner oficial al sys.path ──────────────────────────────────
REPO_DIR = Path(__file__).parent / "php2shell_repo"
SCANNER_DIR = REPO_DIR / "scanner"
if SCANNER_DIR.exists():
    sys.path.insert(0, str(SCANNER_DIR))
else:
    print("[ERROR] No se encontró php2shell_repo/scanner/")
    print("        Ejecuta: git clone https://github.com/Mr-Destroyer/PHP2SHELL.git tools/php2shell_repo")
    sys.exit(1)

try:
    from php2shell.scanner import Scanner, ScanResult
    from php2shell.probe import Verdict, Confidence, Signal
except ImportError as e:
    print(f"[ERROR] No se pudo importar el scanner oficial: {e}")
    sys.exit(1)

# ── Configuración de targets UNS ────────────────────────────────────────────
TARGETS_UNS = [
    "https://sigea.uns.edu.pe",   # PHP 7.1.33 confirmado — EOL, sin parche
    "https://orcl.uns.edu.pe",    # phpMyAdmin expuesto — VULN-001
    "https://campus.uns.edu.pe",  # Moodle — sin headers de seguridad
    "https://registro.uns.edu.pe",
]

FINDINGS_DIR = Path(__file__).parent.parent / "findings"
REPORTS_DIR  = Path(__file__).parent.parent / "reports"

# ── Colores ANSI ─────────────────────────────────────────────────────────────
C_RED    = "\033[91m"
C_YELLOW = "\033[93m"
C_GREEN  = "\033[92m"
C_CYAN   = "\033[96m"
C_BOLD   = "\033[1m"
C_RESET  = "\033[0m"


def color_verdict(verdict: str) -> str:
    mapping = {
        "VULNERABLE":     f"{C_RED}{C_BOLD}🔴 VULNERABLE{C_RESET}",
        "LIKELY":         f"{C_YELLOW}{C_BOLD}🟠 LIKELY VULNERABLE{C_RESET}",
        "FIXED":          f"{C_GREEN}🟢 FIXED{C_RESET}",
        "NOT_VULNERABLE": f"{C_GREEN}✅ NOT VULNERABLE{C_RESET}",
        "INCONCLUSIVE":   f"{C_CYAN}⚪ INCONCLUSIVE{C_RESET}",
        "ERROR":          f"{C_YELLOW}⚠️  ERROR{C_RESET}",
    }
    return mapping.get(verdict, verdict)


def run_scan(target: str, max_probe_mib: int = 7, verify_ssl: bool = False) -> ScanResult:
    """Ejecuta el scanner oficial sobre un target."""
    print(f"\n{'='*65}")
    print(f"  {C_BOLD}TARGET:{C_RESET} {target}")
    print(f"{'='*65}")

    events_log = []

    def on_progress(msg: str) -> None:
        print(f"  [{C_CYAN}*{C_RESET}] {msg}")

    def on_event(event: dict) -> None:
        events_log.append(event)
        if event["type"] == "probe":
            idx    = event.get("index", "?")
            mib    = event.get("size_mib", "?")
            status = event.get("status", "?")
            sig    = event.get("signal")
            detail = event.get("detail", "")
            if sig:
                print(f"  [{C_RED}!!!{C_RESET}] Probe {idx} ({mib} MiB): HTTP {status} — SIGNAL: {sig}")
                if detail:
                    print(f"          {detail}")
            else:
                err = event.get("error", "")
                print(f"  [{'*':1}] Probe {idx} ({mib} MiB): HTTP {status} {('— '+err) if err else ''}")

    scanner = Scanner(
        timeout=90.0,
        connect_timeout=15.0,
        verify_ssl=verify_ssl,
        max_probe_mib=max_probe_mib,
        user_agent="php2shell-scanner/1.1.0 (UNS Pentest Autorizado)",
        on_progress=on_progress,
        on_event=on_event,
    )

    result = scanner.scan(target)
    return result


def print_result(result: ScanResult) -> None:
    """Muestra el resultado en consola."""
    print(f"\n  {'─'*55}")
    print(f"  Veredicto : {color_verdict(result.verdict.value)}")
    print(f"  Confianza : {result.confidence.value}")
    print(f"  Razón     : {result.reason}")
    if result.version:
        print(f"  PHP ver.  : {result.version.describe()}")
    if result.post_max_size:
        print(f"  post_max  : {result.post_max_size:,} bytes")
    print(f"  Tiempo    : {result.elapsed:.1f}s | Enviado: {result.bytes_sent/1024:.0f} KB")
    print(f"  {'─'*55}")


def save_json_results(all_results: list[dict], timestamp: str) -> Path:
    """Guarda todos los resultados en JSON."""
    FINDINGS_DIR.mkdir(exist_ok=True)
    out_path = FINDINGS_DIR / f"php2shell_official_scan_{timestamp}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"scan_date": timestamp, "results": all_results}, f, indent=2, ensure_ascii=False)
    return out_path


def generate_hallazgo(result: ScanResult, vuln_id: str = "VULN-013") -> Path:
    """Genera ficha de hallazgo en formato Markdown para vulnerabilidades detectadas."""
    FINDINGS_DIR.mkdir(exist_ok=True)

    # Determinar severidad según veredicto y confianza
    if result.verdict.value == "VULNERABLE" and result.confidence.value == "HIGH":
        severidad = "🔴 Crítica"
        cvss_score = "9.8"
        cvss_vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"
    elif result.verdict.value in ("VULNERABLE", "LIKELY"):
        severidad = "🟠 Alta"
        cvss_score = "8.1"
        cvss_vector = "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:C/C:H/I:H/A:H"
    else:
        severidad = "🟡 Media"
        cvss_score = "5.9"
        cvss_vector = "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N"

    signal_str = result.signal.value if result.signal else "N/A"
    version_str = result.version.describe() if result.version else "Desconocida / No expuesta"

    probes_table = "\n".join([
        f"| {p.index} | {p.size_mib} MiB | {p.parts} partes | {p.response.status} | {p.signal.value if p.signal else '—'} | {p.detail[:80] if p.detail else '—'} |"
        for p in result.probes
    ]) if result.probes else "| — | — | — | — | — | Sin probes ejecutados |"

    hallazgo_md = f"""# {vuln_id} — PHP2Shell: Vulnerabilidad CVE-2026-109618 / CVE-2026-109619

---

## Información General

| Campo | Valor |
|-------|-------|
| **ID del Hallazgo** | {vuln_id} |
| **Fecha de Descubrimiento** | {datetime.now().strftime('%Y-%m-%d')} |
| **URL / Endpoint Afectado** | `{result.target}` |
| **URL Testeada** | `{result.tested_url}` |
| **Sistema** | PHP Backend ({result.sapi}) |
| **Descubierto por** | Scanner oficial PHP2SHELL v1.1.0 (Mr-Destroyer/PHP2SHELL) |
| **Estado** | Abierto |

---

## Clasificación de la Vulnerabilidad

| Campo | Valor |
|-------|-------|
| **Categoría OWASP Top 10** | A06 – Vulnerable and Outdated Components |
| **OWASP WSTG ID** | WSTG-INPV-13 |
| **CWE** | CWE-416 (Use After Free) / CWE-789 (Memory Allocation with Excessive Size) |
| **Severidad** | {severidad} |
| **Puntuación CVSS v3.1** | {cvss_score} |
| **Vector CVSS v3.1** | `{cvss_vector}` |
| **CVEs** | CVE-2026-109618, CVE-2026-109619 |

---

## Descripción Técnica

### ¿Qué es PHP2Shell?

PHP2Shell es una vulnerabilidad crítica en el parser multipart de PHP que permite
**Remote Code Execution (RCE)** sin autenticación.

**Mecanismo de explotación:**

1. El atacante envía un POST multipart con un body crafteado (1–7 MiB con estructura
   de headers anidados en profundidad 62 niveles)
2. PHP intenta parsear el body — el proceso consume ~105x memoria (ej: 1 MiB wire → 106 MB RAM)
3. Si se alcanza `memory_limit`, PHP ejecuta `longjmp()` para abortar...
   pero deja **punteros colgantes** en el estado interno de `$_FILES`
4. Requests subsecuentes al mismo worker pueden acceder a memoria liberada → **RCE**

### Versiones Afectadas

- PHP < 8.1.31, < 8.2.27, < 8.3.20, < 8.4.6 (todos los branches EOL)
- **PHP 7.x — sin parche oficial** (EOL desde Nov 2022)

### Resultado del Scan en {result.target}

| Campo | Valor |
|-------|-------|
| **Veredicto** | `{result.verdict.value}` |
| **Confianza** | `{result.confidence.value}` |
| **Señal detectada** | `{signal_str}` |
| **Versión PHP** | {version_str} |
| **post_max_size detectado** | {f'{result.post_max_size:,} bytes' if result.post_max_size else 'No detectado'} |
| **Tiempo de scan** | {result.elapsed:.1f}s |
| **Datos enviados** | {result.bytes_sent / 1024:.0f} KB |

### Razón del Veredicto

> {result.reason}

---

## Resultados de Probes

| # | Tamaño | Partes | HTTP | Señal | Detalle |
|---|--------|--------|------|-------|---------|
{probes_table}

---

## Impacto

### Impacto para la Universidad Nacional del Santa

- **Confidencialidad**: Alto — Un atacante puede ejecutar comandos arbitrarios y
  acceder a bases de datos (SIIGAA, matrículas, calificaciones)
- **Integridad**: Alto — Puede modificar datos académicos, credenciales y configuraciones
- **Disponibilidad**: Alto — Puede crashear workers PHP causando DoS del servicio

### Datos en Riesgo

- [x] Información personal de estudiantes (Ley 29733 - Perú)
- [x] Calificaciones y expedientes académicos
- [x] Credenciales de acceso (SIIGAA, phpMyAdmin)
- [x] Información financiera (matrículas, pagos)
- [x] Información de docentes y personal
- [x] Datos de investigación y tesis

---

## Pasos de Reproducción (Proof of Concept — Comportamental)

> ⚠️ PoC de tipo **detección comportamental** — NO ejecuta comandos en el servidor.
> Detecta la vulnerabilidad midiendo señales de crash del worker PHP.

**Pre-condiciones**: Acceso HTTP/HTTPS al endpoint. Sin autenticación requerida.

**Herramienta**: Scanner oficial PHP2SHELL v1.1.0

```bash
# Instalar el scanner oficial
cd tools/php2shell_repo/scanner
pip install -e .

# O ejecutar el wrapper UNS directamente
python tools/php2shell_uns_scan.py --target {result.target}
```

**Señales de vulnerabilidad detectadas:**

```
Signal: {signal_str}
Reason: {result.reason}
```

**Resultado Esperado (servidor parcheado):**
```
verdict: NOT_VULNERABLE o FIXED
confidence: MEDIUM/HIGH
signal: none
```

---

## Evidencia

### Scan Output

```json
{json.dumps(result.to_dict(), indent=2, ensure_ascii=False)[:2000]}
```

---

## Recomendaciones de Remediación

### Corrección Inmediata (Quick Fix)

1. **Actualizar PHP urgentemente** a una versión parcheada:
   - PHP 8.3 → ≥ 8.3.20
   - PHP 8.2 → ≥ 8.2.27
   - PHP 8.1 → ≥ 8.1.31
   - PHP 7.x → **Migrar a PHP 8.x** (PHP 7.x es EOL sin parche disponible)

2. **Reducir `memory_limit`** en `php.ini` (mitigación parcial):
   ```ini
   memory_limit = 32M   ; Reduce amplificación pero NO elimina la vulnerabilidad
   post_max_size = 2M   ; Limita el tamaño del body que PHP parsea
   ```

3. **Configurar WAF** para rechazar bodies multipart > 2MB en rutas no-upload.

### Corrección Definitiva

```ini
; php.ini — Configuración segura
memory_limit = 256M      ; Suficiente para la app
post_max_size = 8M       ; Valor por defecto
upload_max_filesize = 2M ; Limitar uploads reales
; Actualizar a PHP >= 8.3.20 / 8.2.27 / 8.1.31
```

### Referencias

- [PHP2SHELL Scanner (Mr-Destroyer)](https://github.com/Mr-Destroyer/PHP2SHELL)
- [CVE-2026-109618 — NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-109618)
- [GHSA-w8hw-w9fx-j79w](https://github.com/advisories/GHSA-w8hw-w9fx-j79w)
- [Calif.io writeup — php2shell](https://calif.io/php2shell)
- [OWASP WSTG-INPV-13](https://owasp.org/www-project-web-security-testing-guide/)
- [CWE-416: Use After Free](https://cwe.mitre.org/data/definitions/416.html)

---

## Seguimiento

| Campo | Valor |
|-------|-------|
| **Reportado a** | Coordinador técnico UNS |
| **Fecha de reporte** | {datetime.now().strftime('%Y-%m-%d')} |
| **Fecha de remediación objetivo** | {datetime.now().strftime('%Y-%m-%d')} (URGENTE) |
| **Fecha de verificación** | Pendiente |
| **Notas** | Scanner oficial confirma señal comportamental. Confirmar con acceso directo a php.ini/phpinfo. |
"""

    slug = result.target.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "_")
    out_path = FINDINGS_DIR / f"{vuln_id}_php2shell_{slug}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(hallazgo_md)
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="PHP2Shell Scanner — UNS Pentest (wrapper oficial Mr-Destroyer/PHP2SHELL)"
    )
    parser.add_argument(
        "--target", "-t",
        help="URL a escanear (default: todos los targets UNS)",
        default=None,
    )
    parser.add_argument(
        "--max-probe", "-m",
        type=int,
        default=7,
        help="Tamaño máximo del probe en MiB (default: 7, opciones: 1, 4, 7)",
        choices=[1, 4, 7],
    )
    parser.add_argument(
        "--vuln-id",
        default="VULN-013",
        help="ID del hallazgo (default: VULN-013)",
    )
    parser.add_argument(
        "--no-hallazgo",
        action="store_true",
        help="No generar ficha de hallazgo automáticamente",
    )
    args = parser.parse_args()

    targets = [args.target] if args.target else TARGETS_UNS

    print("=" * 65)
    print(f"  {C_BOLD}PHP2Shell Scanner v1.1.0{C_RESET}")
    print("  CVE-2026-109618 / CVE-2026-109619")
    print("  Pentest autorizado — Universidad Nacional del Santa")
    print(f"  Repo: github.com/Mr-Destroyer/PHP2SHELL")
    print("=" * 65)
    print(f"  Targets: {len(targets)}")
    print(f"  Max probe: {args.max_probe} MiB (~{args.max_probe * 105} MB RAM en PHP)")
    print("=" * 65)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_results = []
    vulnerable_targets = []

    for target in targets:
        result = run_scan(target, max_probe_mib=args.max_probe)
        print_result(result)
        all_results.append(result.to_dict())

        if result.is_vulnerable:
            vulnerable_targets.append((target, result))

        time.sleep(3)  # Pausa entre targets

    # ── Resumen final ────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  {C_BOLD}RESUMEN FINAL{C_RESET}")
    print(f"{'='*65}")
    for r in all_results:
        print(f"  {color_verdict(r['verdict'])} — {r['target']}")
        if r.get('version'):
            print(f"    PHP: {r['version']} | Confianza: {r['confidence']}")

    # ── Guardar JSON ─────────────────────────────────────────────────────────
    json_path = save_json_results(all_results, timestamp)
    print(f"\n  [{C_GREEN}+{C_RESET}] JSON guardado: {json_path}")

    # ── Generar fichas de hallazgo ───────────────────────────────────────────
    if not args.no_hallazgo and vulnerable_targets:
        print(f"\n  [{C_YELLOW}!{C_RESET}] Generando fichas de hallazgo para {len(vulnerable_targets)} targets vulnerables...")
        for i, (target, result) in enumerate(vulnerable_targets):
            vuln_id = f"{args.vuln_id}" if i == 0 else f"VULN-{13+i:03d}"
            hallazgo_path = generate_hallazgo(result, vuln_id)
            print(f"  [{C_GREEN}+{C_RESET}] Hallazgo: {hallazgo_path}")

    print(f"\n{'='*65}")
    print(f"  {C_BOLD}Scan completado.{C_RESET}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()

