# Plantilla de Ficha de Hallazgo — Tesis Pentesting UNS

---

## Información General

| Campo | Valor |
|-------|-------|
| **ID del Hallazgo** | VULN-[NÚMERO] (ej: VULN-001) |
| **Fecha de Descubrimiento** | [AAAA-MM-DD] |
| **URL / Endpoint Afectado** | `https://registro.uns.edu.pe/...` |
| **Sistema** | SIIGAA / Portal UNS / [otro] |
| **Descubierto por** | [Tu nombre] |
| **Estado** | Abierto / Remediado / En proceso |

---

## Clasificación de la Vulnerabilidad

| Campo | Valor |
|-------|-------|
| **Categoría OWASP Top 10** | A01 – Broken Access Control / A05 – Security Misconfiguration / [otra] |
| **OWASP WSTG ID** | WSTG-[CAT]-[NUM] |
| **CWE** | CWE-[número] |
| **Severidad** | 🔴 Crítica / 🟠 Alta / 🟡 Media / 🟢 Baja / ⚪ Informativa |
| **Puntuación CVSS v3.1** | [0.0 – 10.0] |
| **Vector CVSS v3.1** | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |

---

## Descripción Técnica

### ¿Qué es la vulnerabilidad?
[Explicar brevemente en qué consiste la vulnerabilidad. Incluir el contexto del sistema universitario.]

### ¿Dónde se encontró?
[Describir la ruta, parámetro, campo o función específica del sistema SIIGAA donde se identificó la vulnerabilidad.]

### ¿Por qué es un problema?
[Explicar el impacto técnico: qué puede hacer un atacante que explote esta vulnerabilidad.]

---

## Impacto

### Impacto para la Universidad Nacional del Santa
- **Confidencialidad**: [Alto/Medio/Bajo/Ninguno] — [Descripción]
- **Integridad**: [Alto/Medio/Bajo/Ninguno] — [Descripción]
- **Disponibilidad**: [Alto/Medio/Bajo/Ninguno] — [Descripción]

### Datos en Riesgo
- [ ] Información personal de estudiantes (Ley 29733 - Perú)
- [ ] Calificaciones y expedientes académicos
- [ ] Credenciales de acceso
- [ ] Información financiera (matrículas, pagos)
- [ ] Información de docentes y personal
- [ ] Datos de investigación y tesis

---

## Pasos de Reproducción (Proof of Concept — PoC Ética)

> ⚠️ Los pasos de PoC deben ser reproducibles pero no destructivos. Usar únicamente cuentas de prueba autorizadas.

**Pre-condiciones**: [Qué necesita el atacante para explotar: acceso anónimo, cuenta de estudiante, etc.]

**Pasos**:
1. Navegar a: `https://[url del endpoint vulnerable]`
2. [Paso 2 — acción específica]
3. [Paso 3 — resultado observado]
4. [Continuar según sea necesario...]

**Resultado Observado**:
```
[Pegar aquí la respuesta del servidor, error message, o dato expuesto]
```

**Resultado Esperado (correcto)**:
```
[Describir cómo debería responder correctamente el sistema]
```

---

## Evidencia

### Capturas de Pantalla
- `Figura 1`: [Descripción de la captura] — ![Hallazgo VULN-XXX](../evidence/VULN-XXX_fig1.png)
- `Figura 2`: [Descripción]

### Logs / Respuestas HTTP
```http
GET /[ruta vulnerable] HTTP/1.1
Host: registro.uns.edu.pe
[...]

HTTP/1.1 200 OK
[Cabeceras de respuesta]

[Contenido de respuesta con dato sensible]
```

---

## Recomendaciones de Remediación

### Corrección Inmediata (Quick Fix)
[Acción que puede tomarse de inmediato para mitigar el riesgo, aunque no sea la solución definitiva.]

### Corrección Definitiva
[Solución técnica detallada. Incluir ejemplos de código o configuración si aplica.]

**Ejemplo de configuración correcta**:
```
[Código o configuración recomendada]
```

### Referencias
- [OWASP - nombre del artículo relevante](https://owasp.org/...)
- [CWE-XXX: Nombre del CWE](https://cwe.mitre.org/data/definitions/XXX.html)
- [NIST - CVE relacionado si aplica]

---

## Seguimiento

| Campo | Valor |
|-------|-------|
| **Reportado a** | [Nombre del coordinador técnico UNS] |
| **Fecha de reporte** | [AAAA-MM-DD] |
| **Fecha de remediación objetivo** | [AAAA-MM-DD] |
| **Fecha de verificación de remediación** | [Pendiente] |
| **Notas de seguimiento** | [Observaciones] |
