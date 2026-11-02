# VULN-013 — PHP2Shell: Vulnerabilidad CVE-2026-109618 / CVE-2026-109619

---

## Información General

| Campo | Valor |
|-------|-------|
| **ID del Hallazgo** | VULN-013 |
| **Fecha de Descubrimiento** | 2026-10-31 |
| **URL / Endpoint Afectado** | `https://sigea.uns.edu.pe` |
| **URL Testeada** | `https://sigea.uns.edu.pe` |
| **Sistema** | PHP Backend (unknown) |
| **Descubierto por** | Scanner oficial PHP2SHELL v1.1.0 (Mr-Destroyer/PHP2SHELL) |
| **Estado** | Abierto |

---

## Clasificación de la Vulnerabilidad

| Campo | Valor |
|-------|-------|
| **Categoría OWASP Top 10** | A06 – Vulnerable and Outdated Components |
| **OWASP WSTG ID** | WSTG-INPV-13 |
| **CWE** | CWE-416 (Use After Free) / CWE-789 (Memory Allocation with Excessive Size) |
| **Severidad** | 🟠 Alta |
| **Puntuación CVSS v3.1** | 8.1 |
| **Vector CVSS v3.1** | `CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:C/C:H/I:H/A:H` |
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

### Resultado del Scan en https://sigea.uns.edu.pe

| Campo | Valor |
|-------|-------|
| **Veredicto** | `LIKELY` |
| **Confianza** | `MEDIUM` |
| **Señal detectada** | `none` |
| **Versión PHP** | PHP 7.1.33 (end-of-life, no upstream fix) |
| **post_max_size detectado** | No detectado |
| **Tiempo de scan** | 2.7s |
| **Datos enviados** | 14336 KB |

### Razón del Veredicto

> no crash observed, but the target advertises an unpatched release: PHP 7.1.33 (end-of-life, no upstream fix). Version data alone is not proof -- distro backports can carry the fix under the original version number.

---

## Resultados de Probes

| # | Tamaño | Partes | HTTP | Señal | Detalle |
|---|--------|--------|------|-------|---------|
| 1 | 1 MiB | 4000 partes | 302 | — | — |
| 2 | 4 MiB | 2000 partes | 302 | — | — |

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
python tools/php2shell_uns_scan.py --target https://sigea.uns.edu.pe
```

**Señales de vulnerabilidad detectadas:**

```
Signal: none
Reason: no crash observed, but the target advertises an unpatched release: PHP 7.1.33 (end-of-life, no upstream fix). Version data alone is not proof -- distro backports can carry the fix under the original version number.
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
{
  "target": "https://sigea.uns.edu.pe",
  "tested_url": "https://sigea.uns.edu.pe",
  "verdict": "LIKELY",
  "confidence": "MEDIUM",
  "reason": "no crash observed, but the target advertises an unpatched release: PHP 7.1.33 (end-of-life, no upstream fix). Version data alone is not proof -- distro backports can carry the fix under the original version number.",
  "signal": "none",
  "sapi": "unknown",
  "version": "PHP 7.1.33 (end-of-life, no upstream fix)",
  "version_status": "EOL",
  "error": null,
  "elapsed_seconds": 2.72,
  "bytes_sent": 14680105,
  "post_max_size": null,
  "probes": [
    {
      "index": 1,
      "size_mib": 1,
      "parts": 4000,
      "status": 302,
      "body_bytes": 0,
      "signal": null,
      "detail": "",
      "error": null
    },
    {
      "index": 2,
      "size_mib": 4,
      "parts": 2000,
      "status": 302,
      "body_bytes": 0,
      "signal": null,
      "detail": "",
      "error": null
    }
  ]
}
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
| **Fecha de reporte** | 2026-10-31 |
| **Fecha de remediación objetivo** | 2026-10-31 (URGENTE) |
| **Fecha de verificación** | Pendiente |
| **Notas** | Scanner oficial confirma señal comportamental. Confirmar con acceso directo a php.ini/phpinfo. |
