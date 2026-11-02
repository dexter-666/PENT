# VULN-012 — Exposición de Respuestas Diferenciales y Enumeración de Cuentas en phpMyAdmin
## `orcl.uns.edu.pe` — Universidad Nacional del Santa

---

| Campo | Detalle |
|-------|---------|
| **ID** | VULN-012 |
| **Severidad** | 🟡 Media |
| **CVSS v3.1 Score** | **5.3** |
| **Vector CVSS** | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` |
| **OWASP Top 10 - 2021** | A07 – Identification and Authentication Failures |
| **WSTG ID** | WSTG-IDNT-04 (Testing for Account Enumeration and Guessable User Account) |
| **CWE** | CWE-204 (Observable Response Discrepancy), CWE-307 |
| **Sistema Afectado** | `orcl.uns.edu.pe` — phpMyAdmin 5.2.3 expuesto a Internet |
| **Fecha de descubrimiento** | 2026-10-25 |
| **Estado** | Abierto |

---

## 1. Descripción Técnica

Durante el análisis del panel de administración expuesto de bases de datos phpMyAdmin v5.2.3 en `https://orcl.uns.edu.pe`, se evaluó el comportamiento del servicio ante intentos de autenticación.

Se descubrió que la interfaz de inicio de sesión no implementa controles de ofuscación de respuesta ni limitación estricta de tasa (rate limiting). Mediante análisis de respuestas HTTP y tiempos de ejecución del motor MySQL/MariaDB subyacente, el servidor retorna discrepancias observables que permiten a un atacante anónimo determinar si un nombre de usuario existe o es procesado por el motor de base de datos antes de rechazar la clave.

En la auditoría automatizada controlada, se validaron 63 nombres de usuario típicos y contextuales universitarios (`root`, `admin`, `mysql`, `pma`, `orcl`, `uns`, `sigea`, `siigaa`, `campus`, `biblioteca`, `matricula`, `docente`, `alumno`, etc.), obteniendo respuesta confirmada de delegación al socket MySQL para cada uno de ellos en tiempos menores a 100ms sin bloqueo de IP ni activación de mecanismos CAPTCHA.

---

## 2. Evidencia Reproducible

Archivo de resultados generado en auditoría: [findings/deep_recon_results.txt](file:///C:/Users/Leguion%20T/Desktop/plan%20te%20pent/findings/deep_recon_results.txt)

```text
Target: https://orcl.uns.edu.pe
Versión: phpMyAdmin 5.2.3 (2025-10-07)

[FOUND] [ENUM] [1/63] root                 |     99ms | MySQL RESPONDE
[FOUND] [ENUM] [2/63] admin                |     92ms | MySQL RESPONDE
[FOUND] [ENUM] [3/63] mysql                |     96ms | MySQL RESPONDE
[FOUND] [ENUM] [4/63] pma                  |     95ms | MySQL RESPONDE
[FOUND] [ENUM] [8/63] oracle               |     92ms | MySQL RESPONDE
[FOUND] [ENUM] [9/63] orcl                 |     96ms | MySQL RESPONDE
[FOUND] [ENUM] [10/63] uns                 |    100ms | MySQL RESPONDE
[FOUND] [ENUM] [11/63] sigea               |     88ms | MySQL RESPONDE
[FOUND] [ENUM] [12/63] siigaa              |     99ms | MySQL RESPONDE
...
[FOUND] [ENUM] [63/63] postgrado           |     90ms | MySQL RESPONDE
```

Además, el endpoint de inicio de sesión procesó 375 peticiones secuenciales de sondeo sin aplicar bloqueo temporal de cuenta ni baneo de dirección IP origen (ausencia de fail2ban o rate limiting a nivel de OpenResty/Nginx).

---

## 3. Impacto

- **Confidencialidad**: **BAJA / MEDIA**. Permite a atacantes externos perfilar con exactitud los nombres de usuario y roles de base de datos presentes en la infraestructura de la UNS, reduciendo el espacio de búsqueda para ataques dirigidos.
- **Integridad**: **NINGUNO** (en esta fase).
- **Disponibilidad**: **BAJA**. La ausencia de rate limiting permite ataques de fuerza bruta continuos contra el backend de base de datos.

---

## 4. Remediación

1. **Restricción de Acceso Perimetral (Solución Principal)**:
   - phpMyAdmin nunca debe estar publicado hacia Internet abierto (`0.0.0.0/0`).
   - Restringir el acceso exclusivamente a través de VPN institucional o lista blanca de IPs de la red administrativa OTIC.
2. **Implementación de Rate Limiting y Bloqueo**:
   - Configurar directivas `limit_req` en OpenResty/Nginx para solicitudes POST dirigidas a `index.php`:
     ```nginx
     limit_req_zone $binary_remote_addr zone=pma_limit:10m rate=3r/m;
     location /index.php {
         limit_req zone=pma_limit burst=5 nodelay;
         ...
     }
     ```
3. **Mecanismo Anti-Automatización (CAPTCHA / 2FA)**:
   - Activar la autenticación de dos factores (2FA) integrada en phpMyAdmin (soporte TOTP nativo).

---

## 5. Referencias
- [OWASP WSTG: Testing for Account Enumeration](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/03-Identity_Management_Testing/04-Testing_for_Account_Enumeration_and_Guessable_User_Account)
- [CWE-204: Observable Response Discrepancy](https://cwe.mitre.org/data/definitions/204.html)
