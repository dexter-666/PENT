# VULN-011 — Plataforma Legacy ASP Clásico, Hash MD5 Client-Side y Depuración en Producción
## `biblioteca.uns.edu.pe` — Universidad Nacional del Santa

---

| Campo | Detalle |
|-------|---------|
| **ID** | VULN-011 |
| **Severidad** | 🟠 Alta |
| **CVSS v3.1 Score** | **7.5** |
| **Vector CVSS** | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` |
| **OWASP Top 10 - 2021** | A02 – Cryptographic Failures / A05 – Security Misconfiguration |
| **WSTG ID** | WSTG-CRYP-04, WSTG-CONF-04, WSTG-INFO-08 |
| **CWE** | CWE-327 (Broken Cryptographic Algorithm), CWE-489 (Active Debug Code), CWE-1104 |
| **Sistema Afectado** | `biblioteca.uns.edu.pe` — Portal Biblioteca Central (IIS / ASP Clásico) |
| **Fecha de descubrimiento** | 2026-10-25 |
| **Estado** | Abierto |

---

## 1. Descripción Técnica

Durante la fase de reconocimiento de activos en el dominio `uns.edu.pe`, se identificó y analizó el subdominio `biblioteca.uns.edu.pe`. El activo presenta un conjunto de malas prácticas de configuración, desarrollo y obsolescencia tecnológica severa:

1. **Tecnología Obsoleta y Descontinuada**:
   - Backend basado en **ASP Clásico (Active Server Pages)** sobre Microsoft IIS (proxy inverso OpenResty).
   - Estructura de plantillas Macromedia Dreamweaver (`Templates/plantilla_master.dwt`).
   - Recursos Adobe Flash embebidos (`swf/finta1.swf`), tecnología oficialmente descontinuada y sin soporte en navegadores modernos.
   - Codificación `iso-8859-1` sin cabeceras modernas de protección.

2. **Criptografía Débil y Vulnerable (MD5 del Lado del Cliente)**:
   - En la página de autenticación (`inicia_sesion.asp`), las contraseñas no se transmiten ni procesan mediante funciones de derivación seguras (Argon2, bcrypt, PBKDF2), sino mediante un hash MD5 calculado en el navegador mediante JavaScript (`css/md5.js`):
     ```javascript
     document.form1.t_clave.value = hex_md5(document.form1.t_clave.value);
     ```
   - Al no utilizar salt ni nonce específico de sesión, el hash MD5 resultante actúa como contraseña equivalente (pass-the-hash en capa de aplicación) y es trivialmente reversible mediante tablas rainbow o ataques de diccionario offline.

3. **Código de Depuración Activo en Producción (`alert()` con hash de clave)**:
   - El script de validación incluye una instrucción de depuración dejada por el programador:
     ```javascript
     alert(document.form1.t_clave.value + '*********//////*************');
     ```
   - Esta ventana emergente expone visualmente el valor hash de la credencial en pantalla ante cualquier usuario presente, confirmando la ausencia de un ciclo de vida de desarrollo seguro (SDLC) y control de calidad previo al pase a producción.

4. **Control de Acceso / Rol Basado en Selección del Cliente**:
   - El formulario de login expone un radio button para seleccionar el nivel de privilegio:
     ```html
     <input name="modo" type="radio" value="U" checked> (Usuario)
     <input type="radio" name="modo" value="A"> (Administrador)
     ```
   - La asignación de roles a nivel de frontend (`modo=A` vs `modo=U`) delega decisiones de autorización al cliente si el backend no valida rígidamente la pertenencia al rol en la base de datos.

5. **Exposición de Catálogo Dinámico sin Control de Tasa (DDoS / DoS Lógico)**:
   - El endpoint `alerta_por_titulo.asp?letra=` ejecuta consultas a la base de datos de libros (+2,279 registros). Cuando el parámetro `letra` se envía vacío, el hilo de ejecución ASP en IIS agota el timeout por lectura masiva sin paginación optimizada, permitiendo degradación del servicio con peticiones concurrentes mínimas.

---

## 2. Evidencia Reproducible

### A. Fragmento de `https://biblioteca.uns.edu.pe/inicia_sesion.asp`
```html
<SCRIPT language=JavaScript src="css/secur.js"></SCRIPT> 
<SCRIPT language=JavaScript src="css/md5.js"></SCRIPT> 
<SCRIPT LANGUAGE=javascript>
function validar() { 
  var texto1,texto2,criter;
  texto1=document.form1.t_usuario.value;
  texto2=document.form1.t_clave.value;
  ...
  document.form1.t_clave.value=hex_md5(document.form1.t_clave.value);
  alert(document.form1.t_clave.value+ '*********//////*************');
  return true;
}
</SCRIPT>

<form method="POST" name="form1" action="login.asp" onSubmit="return validar()">
  <input name="t_usuario" type="text" id="t_usuario">
  <input name="t_clave" type="password" id="t_clave">
  <input name="modo" type="radio" value="U" checked>
  <input type="radio" name="modo" value="A">
  <input type="submit" value="Iniciar Sesión" name="B1">
</form>
```

### B. Mapeo de Endpoints Dinámicos Descubiertos
- `https://biblioteca.uns.edu.pe/inicia_sesion.asp` → Formulario de autenticación con MD5 cliente
- `https://biblioteca.uns.edu.pe/login.asp` → Procesador de credenciales
- `https://biblioteca.uns.edu.pe/registra_comentario.htm` → Formulario de sugerencias (sin CSRF/Captcha)
- `https://biblioteca.uns.edu.pe/registra_comentario.asp` → Receptor de comentarios
- `https://biblioteca.uns.edu.pe/cat_alerta_por_titulo.asp` → Índice alfabético
- `https://biblioteca.uns.edu.pe/alerta_por_titulo.asp?letra=A` → Consulta dinámica a DB (2,279 registros)
- `https://biblioteca.uns.edu.pe/ver_libro.asp?idm=371` → Ficha técnica de ejemplar

---

## 3. Impacto

- **Confidencialidad**: **ALTA**. La utilización de MD5 débil sin salting expone contraseñas de usuarios a descifrado inmediato. Código de depuración expone valores en pantalla.
- **Integridad**: **MEDIA**. Formularios sin tokens anti-CSRF permiten falsificación de comentarios y peticiones no autorizadas.
- **Disponibilidad**: **MEDIA**. Consultas pesadas no sanitizadas en endpoints ASP pueden provocar agotamiento de recursos del pool IIS.
- **Superficie Tecnológica**: Riesgo crítico por componentes de software legados sin parches de seguridad desde hace más de una década.

---

## 4. Remediación

1. **Migración de Plataforma**:
   - Desmantelar la aplicación en ASP Clásico y migrar el catálogo a un Sistema Integrado de Gestión de Bibliotecas moderno y de código abierto (ej. **Koha ILS** o **DSpace** para repositorios).
2. **Eliminación de Código de Depuración**:
   - Retirar de inmediato la sentencia `alert(...)` de `inicia_sesion.asp`.
3. **Criptografía Segura en Servidor**:
   - Reemplazar el hashing MD5 en cliente por hashing en backend utilizando **Argon2id** o **bcrypt** con factores de trabajo adecuados, forzando transporte HTTPS seguro.
4. **Validación de Roles en Backend**:
   - No delegar el rol (`modo=A`/`modo=U`) a parámetros del cliente; determinar el perfil del usuario exclusivamente desde la sesión autenticada en base de datos.
5. **Implementación de Cabeceras de Seguridad**:
   - Añadir HSTS, CSP, X-Frame-Options (`DENY`), y X-Content-Type-Options en el frontend OpenResty.

---

## 5. Referencias
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [CWE-327: Use of a Broken or Risky Cryptographic Algorithm](https://cwe.mitre.org/data/definitions/327.html)
- [CWE-489: Active Debug Code](https://cwe.mitre.org/data/definitions/489.html)
