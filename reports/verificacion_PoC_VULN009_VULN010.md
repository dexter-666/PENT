# VERIFICACIÓN INDEPENDIENTE — PoC VULN-009 y VULN-010 (`campus.uns.edu.pe`)

**Fecha de verificación**: 2026-10-11
**Método**: Solo comprobaciones pasivas (lectura de cabeceras/respuestas HTTP públicas + consulta de bases de datos de CVEs). **No se ejecutó explotación activa** (ni SSL stripping, ni inyección XSS, ni MITM, ni fuerza bruta).
**Herramientas**: `curl` (HTTP/HTTPS), `tools/security_headers_audit.py`, NVD/OSV/GitHub Advisories.

---

## ✅ PARTE REAL — Confirmado y reproducible

| Afirmación del PoC | Resultado de la verificación |
|---|---|
| `http://campus.uns.edu.pe/login/index.php` responde **200 en claro** sin redirigir a HTTPS | ✅ **CONFIRMADO** — `HTTP/1.1 200 OK`, `Server: openresty`, sin `Location` |
| **Sin HSTS** (HTTP y HTTPS) | ✅ **CONFIRMADO** — header ausente en ambos esquemas |
| **Sin CSP**, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy` | ✅ **CONFIRMADO** — auditoría propia: **44/100, grado D** (idéntico a `findings/headers_campus.csv`) |
| Página de login completa (form + `logintoken`) servida por HTTP en claro | ✅ **CONFIRMADO** — GET por HTTP devuelve el formulario íntegro |
| Cookie `MoodleSession` con `Secure; HttpOnly` **sin SameSite** | ✅ **CONFIRMADO** |
| `X-Frame-Options: sameorigin` presente | ✅ **CONFIRMADO** (el PoC no lo mencionaba) |
| YUI 3.18.1, tema `academi`, revision `1791579687`, `"debug":false`, `/version.php` vacío | ✅ **CONFIRMADO** en el HTML de la página |
| No expone `X-Powered-By` ni versión en `Server`; no hay PUT/DELETE/TRACE habilitados | ✅ **CONFIRMADO** |

**Conclusión parcial**: los hallazgos de **configuración** (VULN-009 y VULN-010 como *ausencia de cabeceras / HTTP claro*) son **reales y reproducibles hoy**.

---

## ❌ PARTE FAKE / ERRÓNEA — No verificada o falsa

| Afirmación del PoC | Verificación |
|---|---|
| **CVE-2020-14338** "XSS en gestión de badges" | ❌ **FALSO** — ese CVE es de **WildFly/Xerces** (validación XML en JBoss), no tiene relación con Moodle |
| **CVE-2020-14339** "CSRF en gestión de usuarios" | ❌ **FALSO** — ese CVE es de **libvirt/QEMU** (fuga de file descriptor), no es de Moodle |
| **CVE-2021-36393** "SQLi en reportes" | ⚠️ **CVE real** (SQLi en la librería de cursos recientes; afecta 3.9.x<3.9.8, 3.10.x, 3.11.0-3.11.1), pero la descripción "en reportes" es incorrecta |
| **CVE-2020-25627** "XSS en foros" | ⚠️ **CVE real** (XSS almacenado en campo de perfil `moodlenetprofile`; 3.9.0–3.9.1), pero **no es de foros** |
| **"50-200 credenciales robables/día"** | ❌ **INVENTADO** — sin medición ni fuente |
| **Escenario "XSS en PDF" (§3.1 y §4)** | ❌ **Técnicamente inválido** — un PDF con `<script>` no ejecuta XSS en el origen Moodle; el navegador lo renderiza en su visor/sandbox. XSS almacenado requeriría inyección en campos HTML, y **no fue demostrado** |
| **Multa $25,000-$80,000 (Ley 29733)** | ❌ **INVENTADO** — las sanciones del SNDDP se determinan caso por caso, no hay rango fijo |
| **"~15,000 estudiantes + 800 docentes"** | ⚠️ Dato sin verificar presentado como estimado oficial |
| **"Moodle 3.5-3.9 probable"** | ⚠️ **Inferencia débil** — YUI 3.18.1 se usó desde Moodle 3.5 hasta 3.11+. No se puede precisar la versión sin más evidencia |
| **"Un payload → miles de víctimas" / spear phishing de 47 estudiantes** | ❌ Narrativa hipotética, no evidencia |

---

## 🔎 Matices importantes (para que el informe sea defendible)

1. **El `<form action>` del login apunta a `https://...`** → el POST de credenciales va cifrado por defecto. El riesgo real (SSL stripping) requiere: atacante MITM en la **misma red Wi-Fi** + usuario que escriba el dominio **sin protocolo**. Navegadores modernos hacen *HTTPS-upgrade* automático, lo que reduce (no elimina) la explotabilidad práctica. El hallazgo sigue siendo válido (CWE-319), pero el impacto "trivial" del PoC está **sobredimensionado**.
2. **Ningún XSS fue demostrado** — VULN-010 es *ausencia de cabeceras de protección*, no una XSS confirmada. El documento mezcla ambos conceptos.
3. **`docs/` está vacío** — el README lista `01_marco_metodologico_owasp.md` y `02_reglas_de_compromiso_roe.md`, pero **no existen**. La "autorización formal de la Vicerrectoría" no es verificable desde el proyecto; para la tesis conviene adjuntar el oficio real.
4. No se ejecutaron los scripts de `prueba/` (fuerza bruta, SQLi, exploits a WebLogic/phpMyAdmin/JBoss, etc.) — son **ataques activos** fuera del alcance de esta verificación y requieren autorización explícita documentada.

---

## 📌 Veredicto final

**Mitad real, mitad fake:**
- **Real**: las vulnerabilidades de configuración (HTTP en claro sin HSTS, ausencia de CSP y otras cabeceras, cookie sin SameSite). Reproduce con `curl -I` y con la herramienta del proyecto. Remediación correcta y de costo ~$0.
- **Fake**: 2 de los 4 CVEs listados son de **otros productos** (WildFly/libvirt), las cifras de impacto están **inventadas**, y el escenario estrella de **XSS-vía-PDF no funciona** técnicamente.

**Recomendación para la tesis**: reescribir el PoC eliminando los CVE-2020-14338/14339, corregir las descripciones de CVE-2021-36393 y CVE-2020-25627, quitar los números inventados (50-200/día, $25k-80k, 15,000 usuarios) o marcarlos claramente como supuestos, y cambiar el escenario XSS-en-PDF por un escenario válido (inyección en campos de texto enriquecido, no demostrado).

---

*Evidencia de esta verificación: `findings/verificacion_PoC_campus.csv` (salida de `security_headers_audit.py`, 2026-10-11).*
