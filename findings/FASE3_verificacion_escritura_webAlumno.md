# FASE: Verificación de Escritura Autorizada — Portal WebAlumno UNS
## Informe de Verificación de Estado Antes/Después

| Campo            | Valor                                                             |
|------------------|-------------------------------------------------------------------|
| **Objetivo**     | `registro.uns.edu.pe` — Portal WebAlumno (JSF/PrimeFaces)        |
| **Aplicación**   | UDEMSI WebAlumno V1.0.4 @PRODUCCION                               |
| **Cuenta usada** | Alumno autenticado — código 0202533453                            |
| **Método**       | Inspección autenticada con navegador (caja gris)                  |
| **Fecha**        | 2026-10-25                                                        |

---

## Metodología Aplicada

Ciclo completo por cada función identificada:

```
ESTADO INICIAL (snapshot/hash)
        ↓
OPERACIÓN (escritura prevista por la aplicación)
        ↓
VERIFICACIÓN INDEPENDIENTE (¿cambió el recurso?)
        ↓
RESTAURACIÓN (volver al estado original)
        ↓
DOCUMENTACIÓN (solicitud · respuesta · diff)
```

---

## Menú Completo del Portal (post-login)

| Sección        | Subsecciones                  | Tipo       |
|----------------|-------------------------------|------------|
| EXPEDIENTE     | Personal, Académico           | Solo lectura |
| CURRÍCULA      | (plan de estudios)            | Solo lectura |
| HORARIO        | (horario de clases)           | Solo lectura |
| MATRÍCULA      | (historial de matrículas)     | Solo lectura |
| NOTAS          | (calificaciones)              | Solo lectura |
| RECURSOS       | (recursos académicos)         | Solo lectura |

**Observación:** Ninguna sección del menú lateral expone operaciones de escritura para el rol de alumno.

---

## Análisis de Campos del Expediente Personal

Todos los campos de la pantalla `/faces/pages/expedientePersonal.xhtml` son **display-only**:

| Campo             | ID HTML                | Tipo en DOM               | ¿Editable? |
|-------------------|------------------------|---------------------------|------------|
| DNI               | (ui-inputtext)         | `ui-state-filled` (readonly) | ❌ No    |
| Apellido Paterno  | (ui-inputtext)         | `ui-state-filled` (readonly) | ❌ No    |
| Apellido Materno  | (ui-inputtext)         | `ui-state-filled` (readonly) | ❌ No    |
| Nombre            | (ui-inputtext)         | `ui-state-filled` (readonly) | ❌ No    |
| Fecha Nacimiento  | (ui-inputtext)         | `ui-state-filled` (readonly) | ❌ No    |
| Dirección         | (ui-inputtext)         | `ui-state-filled` (readonly) | ❌ No    |
| Distrito          | (ui-inputtext)         | `ui-state-filled` (readonly) | ❌ No    |
| Teléfono          | (ui-inputtext)         | `ui-state-filled` (readonly) | ❌ No    |
| Celular           | (ui-inputtext)         | `ui-state-filled` (readonly) | ❌ No    |
| Correo Electrónico| (ui-inputtext)         | `ui-state-filled` (readonly) | ❌ No    |

**El botón "Nota" (?)** abre un panel de ayuda contextual, no un formulario de edición.

---

## Prueba de Endpoints de Escritura — Resultado

| URL intentada                                    | Resultado                             | Observación                  |
|--------------------------------------------------|---------------------------------------|------------------------------|
| `/faces/pages/cambiarClave.xhtml`               | ❌ `Not Found in ExternalContext`      | Función no disponible en este módulo |
| `/faces/pages/actualizarDatos.xhtml`            | ❌ No existe                          | No implementado              |
| `/faces/pages/subirFoto.xhtml`                  | ❌ No existe                          | No implementado              |
| `/faces/pages/expedientePersonal.xhtml`         | ✅ 200 — todos los campos readonly    | Solo consulta                |

---

## Verificación de Estado: Resultado Formal

> **Ninguna función de escritura estuvo disponible para el rol de alumno en el portal `registro.uns.edu.pe/WebAlumno`.**

| Paso del ciclo  | Resultado                                                          |
|-----------------|--------------------------------------------------------------------|
| ESTADO INICIAL  | Datos del expediente visibles y consistentes                       |
| OPERACIÓN       | No ejecutada — no existen formularios de escritura para este rol   |
| VERIFICACIÓN    | N/A — sin operación no hay estado que verificar                    |
| RESTAURACIÓN    | N/A                                                                |

---

## Hallazgos de Seguridad del Portal

### INFO-003 — Tecnología identificada: JSF/PrimeFaces expuesto

| Campo        | Valor                                      |
|--------------|--------------------------------------------|
| **Severidad**| Informativa                                |
| **URL**      | `https://registro.uns.edu.pe:80/WebAlumno/`|
| **Evidencia**| `javax.faces.ViewState` en formularios; error JSF: *"Not Found in ExternalContext as a Resource"* |
| **Riesgo**   | La versión de PrimeFaces y el tipo de error JSF son visibles. Si la versión es antigua, puede ser vulnerable a EL Injection (CVE-2013-3827) o ViewState tampering. |
| **Recomendación** | Activar cifrado del ViewState (`<context-param>javax.faces.STATE_SAVING_METHOD`), suprimir mensajes de error internos, actualizar PrimeFaces a ≥ 12.x |

### CONF-001 — Puerto no estándar en producción (HTTP :80)

| Campo        | Valor                                      |
|--------------|--------------------------------------------|
| **Severidad**| Media                                      |
| **Evidencia**| El enlace usa `registro.uns.edu.pe:80` — el puerto se especifica explícitamente, sugiriendo que el servidor no redirige automáticamente al 443 |
| **Riesgo**   | La sesión podría transmitirse en claro si el usuario accede sin HTTPS |
| **Recomendación** | Forzar HTTPS en el servidor de aplicaciones y suprimir el acceso al puerto 80 |

---

## Conclusión para el Informe de Auditoría

La prueba de escritura con cuenta autorizada confirma que el portal `WebAlumno` implementa **separación de roles efectiva**: el rol de alumno solo puede consultar sus propios datos y no tiene acceso a ninguna función de escritura, carga de archivos ni modificación de perfil.

La verificación de escritura **no pudo ejecutarse** en este objetivo porque el diseño de la aplicación no expone funciones de escritura para este rol. Esto es una **configuración correcta** desde el punto de vista de seguridad.

> Para completar la fase de verificación de escritura en `sigea.uns.edu.pe` o `campus.uns.edu.pe` se requeriría una cuenta con rol de docente, administrador o usuario con permisos de edición en esas aplicaciones.

---

## Evidencia Reproducible

```
Fecha/Hora : 2026-10-25T07:12–07:18 UTC
Cuenta     : 0202533453 (alumno autenticado)
Navegador  : Chromium (herramienta de auditoría)
Método     : Inspección autenticada de DOM + navegación manual
Artefacto  : alumno_uns_cambiar_clave_writetest_1792912639239.webp
```

**Formulario de login (JSF PrimeFaces) — campos identificados:**

```
frmLogueo:itUsuario  — input text (código de alumno)
frmLogueo:itSeguridad — input text (DNI)
frmLogueo:kbClave    — keypad virtual (contraseña)
javax.faces.ViewState — token anti-CSRF del ViewState
Action: POST /WebAlumno/faces/login.xhtml
```
