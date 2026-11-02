# INFORME EJECUTIVO DE SEGURIDAD
## Auditoría de Seguridad Web — Universidad Nacional del Santa (UNS)
### [Año] — Confidencial

---

> **Clasificación**: CONFIDENCIAL — Para uso exclusivo de autoridades universitarias  
> **Preparado por**: [Nombre del Tesista]  
> **Revisado por**: [Asesor de Tesis / Coordinador de Seguridad UNS]  
> **Fecha**: [Fecha de emisión]  

---

## 1. Resumen Ejecutivo

La presente auditoría de seguridad web fue realizada sobre la infraestructura digital de la **Universidad Nacional del Santa (UNS)** durante el período [fechas], en el marco del proyecto de tesis titulado: *"[Título de la tesis]"*.

El objetivo fue evaluar la postura de seguridad del ecosistema web universitario, identificar vulnerabilidades existentes y proporcionar recomendaciones concretas que permitan a la institución fortalecer la protección de la información de su comunidad universitaria.

### Resultados en Cifras

| Métrica | Valor |
|---------|-------|
| **Sistemas evaluados** | [N] aplicaciones / subdominios |
| **Vulnerabilidades identificadas** | [N] en total |
| 🔴 Críticas | [N] |
| 🟠 Altas | [N] |
| 🟡 Medias | [N] |
| 🟢 Bajas | [N] |
| ⚪ Informativas | [N] |
| **Exposición de datos sensibles** | Sí / No |
| **Sistemas sin cifrado HTTPS** | [N] |

---

## 2. Hallazgos Principales (Resumen para Directivos)

### 🔴 Hallazgos Críticos
> *Requieren atención inmediata — Riesgo de exposición de datos de toda la comunidad universitaria*

**[VULN-001] — [Nombre descriptivo del hallazgo]**
- **Impacto**: Un atacante externo podría [describir impacto en lenguaje no técnico]
- **Afecta a**: Datos de [X] estudiantes / docentes
- **Sistema**: SIIGAA / Portal UNS

[Repetir para cada hallazgo crítico]

### 🟠 Hallazgos Altos
[Resumen de hallazgos de severidad alta]

### 🟡 Hallazgos Medios
[Resumen de hallazgos de severidad media]

---

## 3. ¿Por qué esto es importante? — Concientización Institucional

Las vulnerabilidades identificadas no son fallos técnicos menores. Representan riesgos reales para:

### 3.1 Privacidad de Estudiantes y Docentes
La Ley N° 29733 — **Ley de Protección de Datos Personales del Perú** — establece que las instituciones que administran datos personales tienen la obligación de garantizar su seguridad. Las vulnerabilidades encontradas podrían:
- Exponer nombres, DNI, domicilios y datos académicos de miles de estudiantes.
- Comprometer información financiera vinculada a matrículas y pagos.
- Violar el derecho fundamental a la privacidad de la comunidad universitaria.

### 3.2 Integridad Académica
Un atacante con acceso a los sistemas de registro podría:
- Modificar calificaciones y expedientes académicos.
- Alterar registros de matrícula y cursos.
- Comprometer la autenticidad de los títulos expedidos por la UNS.

### 3.3 Reputación Institucional
En el contexto de acreditación universitaria (SUNEDU, SINEACE), una brecha de seguridad puede:
- Generar desconfianza en la comunidad universitaria.
- Comprometer los procesos de acreditación y licenciamiento.
- Resultar en sanciones y responsabilidades legales para la institución.

### 3.4 Continuidad del Servicio Educativo
Los sistemas afectados son críticos para la operación académica:
- Matrícula en línea de [N] estudiantes por semestre.
- Registro y publicación de calificaciones.
- Acceso al campus virtual y recursos académicos.

---

## 4. Comparación con Estándares Internacionales

| Control de Seguridad | Estado Actual | Estándar Recomendado |
|---------------------|--------------|----------------------|
| Cifrado HTTPS en todos los servicios | ❌ / ✅ | OWASP A02 / HSTS |
| Gestión de contraseñas seguras | ❌ / ✅ | NIST SP 800-63B |
| Cabeceras de seguridad HTTP | ❌ / ✅ | OWASP Secure Headers |
| Protección contra XSS | ❌ / ✅ | OWASP A03 |
| Control de acceso basado en roles | ❌ / ✅ | OWASP A01 |
| Gestión de errores y logging seguro | ❌ / ✅ | OWASP A09 |
| Actualizaciones de software | ❌ / ✅ | OWASP A06 |

---

## 5. Plan de Remediación Recomendado

### Prioridad 1 — Inmediata (0-30 días)
1. [Acción correctiva para hallazgo crítico 1]
2. [Acción correctiva para hallazgo crítico 2]
3. Establecer un proceso de respuesta ante incidentes de seguridad.

### Prioridad 2 — Corto Plazo (30-90 días)
1. [Corrección de vulnerabilidades de severidad alta]
2. Implementar un programa de auditorías de seguridad periódicas.
3. Capacitar al equipo de TI en desarrollo seguro (OWASP Top 10).

### Prioridad 3 — Mediano Plazo (90-180 días)
1. [Corrección de vulnerabilidades medias]
2. Implementar un programa de gestión de vulnerabilidades continuo.
3. Establecer una política formal de seguridad de la información.
4. Considerar la adopción del estándar ISO 27001 para gestión de seguridad.

---

## 6. Conclusión

La auditoría reveló que la infraestructura web de la UNS presenta oportunidades de mejora significativas en materia de seguridad. La buena noticia es que la mayoría de las vulnerabilidades identificadas tienen soluciones conocidas y bien documentadas que pueden implementarse con recursos limitados.

La inversión en seguridad de la información no es un gasto, sino una **protección de los activos más valiosos de la institución**: los datos y la confianza de su comunidad universitaria.

Se recomienda que la UNS establezca un programa continuo de seguridad que incluya auditorías periódicas, capacitación del equipo técnico y la adopción de estándares internacionales de seguridad.

---

## 7. Información de Contacto

| Tesista | [Nombre completo] |
|---------|-----------------|
| Escuela/Facultad | [Nombre] |
| Email | [email] |
| Asesor de Tesis | [Nombre] |

---

*Este informe ha sido elaborado de conformidad con los estándares OWASP Web Security Testing Guide v4.2 y el Penetration Testing Execution Standard (PTES), bajo autorización formal de la vicerrectoría de la Universidad Nacional del Santa.*
