# README — Proyecto de Tesis: Auditoría de Seguridad Web UNS

> **⚠️ ADVERTENCIA**: Este proyecto fue realizado con autorización formal de la Vicerrectoría  
> y el Grupo de Ingeniería de Seguridad de la Universidad Nacional del Santa (UNS).  
> Las herramientas aquí incluidas son para uso académico y de investigación autorizada.

---

## 🎯 Objetivo del Proyecto

Realizar una auditoría de seguridad web sobre el ecosistema digital de la **Universidad Nacional del Santa (UNS)** — especialmente el sistema **SIIGAA** (`registro.uns.edu.pe`) — para identificar vulnerabilidades, concientizar sobre el estado de la seguridad institucional, y presentar los hallazgos como producto de tesis.

## 📁 Estructura del Proyecto

```
plan te pent/
├── docs/
│   ├── 01_marco_metodologico_owasp.md   # Metodología OWASP WSTG v4.2 + PTES
│   └── 02_reglas_de_compromiso_roe.md   # Scope, RoE y exclusiones formales
│
├── tools/
│   ├── requirements.txt                  # Dependencias Python
│   ├── recon_subdomains.py              # OSINT — Descubrimiento de subdominios (crt.sh)
│   ├── security_headers_audit.py        # Auditoría de cabeceras HTTP y TLS
│   └── sensitive_files_scanner.py       # Scanner de archivos/rutas sensibles expuestos
│
├── findings/
│   ├── plantilla_hallazgo.md            # Ficha estandarizada por vulnerabilidad
│   ├── inventario_activos.csv           # Registro de activos descubiertos
│   └── evidence/                        # Capturas de pantalla y evidencias (crear manualmente)
│
└── reports/
    ├── informe_ejecutivo_concientizacion.md  # Para directivos/autoridades universitarias
    └── informe_tecnico_completo.md           # Informe técnico detallado para tesis
```

---

## 🚀 Cómo Ejecutar las Herramientas

### Instalación de dependencias
```bash
cd tools
pip install -r requirements.txt
```

### 1. Reconocimiento de Subdominios (OSINT Pasivo)
```bash
# Descubrir todos los subdominios de uns.edu.pe
python tools/recon_subdomains.py --domain uns.edu.pe --output findings/inventario_activos.csv

# Solo listar sin resolver (más rápido)
python tools/recon_subdomains.py --domain uns.edu.pe --no-resolve
```

### 2. Auditoría de Cabeceras de Seguridad HTTP
```bash
# Auditar una URL específica
python tools/security_headers_audit.py --url https://registro.uns.edu.pe

# Auditar todos los subdominios activos del inventario
python tools/security_headers_audit.py --urls-file findings/inventario_activos.csv --output findings/headers_audit.csv
```

### 3. Scanner de Archivos Sensibles Expuestos
```bash
# Escanear SIIGAA
python tools/sensitive_files_scanner.py --base-url https://registro.uns.edu.pe --output findings/sensitive_files.csv

# Escanear portal principal
python tools/sensitive_files_scanner.py --base-url https://uns.edu.pe --output findings/sensitive_files_portal.csv

# Con delay mayor (más sigiloso / amigable con el servidor)
python tools/sensitive_files_scanner.py --base-url https://registro.uns.edu.pe --delay 1.0
```

---

## 📋 Flujo de Trabajo Recomendado

```
1. Ejecutar recon_subdomains.py    → Obtener inventario de activos
2. Ejecutar security_headers_audit.py → Auditar cabeceras en todos los activos
3. Ejecutar sensitive_files_scanner.py → Buscar archivos sensibles expuestos
4. Análisis manual con Burp Suite   → Pruebas de autenticación, IDOR, SQLi, XSS
5. Documentar hallazgos            → Usar plantilla_hallazgo.md por cada VULN
6. Redactar informes               → Completar plantillas en reports/
```

---

## 📚 Referencias

- [OWASP WSTG v4.2](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Top 10 — 2021](https://owasp.org/Top10/)
- [PTES - Penetration Testing Execution Standard](http://www.pentest-standard.org/)
- [CVSS v3.1 Calculator](https://www.first.org/cvss/calculator/3.1)
- [CWE — Common Weakness Enumeration](https://cwe.mitre.org/)
- [Ley 29733 — Protección de Datos Personales, Perú](https://www.minjus.gob.pe/transparencia/documentos/Ley29733.pdf)

---

*Tesis — Universidad Nacional del Santa — [Año]*
