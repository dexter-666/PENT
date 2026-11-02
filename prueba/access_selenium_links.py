#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=opts)

try:
    # Access the server/databases page
    driver.get('https://orcl.uns.edu.pe/index.php?route=/server/databases')
    time.sleep(5)
    
    # Look for all links
    links = driver.find_elements(By.TAG_NAME, 'a')
    print(f"Links found: {len(links)}")
    for l in links[:30]:
        href = l.get_attribute('href')
        text = l.text.strip()
        if text or href:
            print(f"  '{text}' -> {href}")
    
    # Look for all forms
    forms = driver.find_elements(By.TAG_NAME, 'form')
    print(f"\nForms found: {len(forms)}")
    for f in forms:
        action = f.get_attribute('action')
        print(f"  Form action: {action}")
    
    # Look for all inputs
    inputs = driver.find_elements(By.TAG_NAME, 'input')
    print(f"\nInputs found: {len(inputs)}")
    for inp in inputs[:20]:
        name = inp.get_attribute('name')
        type_ = inp.get_attribute('type')
        print(f"  Input: name={name}, type={type_}")
    
    # Look for all buttons
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    print(f"\nButtons found: {len(buttons)}")
    for btn in buttons[:10]:
        text = btn.text.strip()
        print(f"  Button: '{text}'")
    
    # Look for any visible text
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    print(f"\nBody text: {body_text[:500]}")
    
    # Try to find and click any link that might lead to the database
    db_links = []
    for l in links:
        href = l.get_attribute('href') or ''
        text = l.text.strip() or ''
        if 'db' in href.lower() or 'mysql' in href.lower() or 'database' in text.lower() or 'sql' in href.lower():
            db_links.append((text, href))
    
    print(f"\nDatabase-related links: {db_links}")
    
    # Try to click on a language to trigger the redirect
    try:
        lang_options = driver.find_elements(By.TAG_NAME, 'option')
        print(f"\nLanguage options: {len(lang_options)}")
        for opt in lang_options[:5]:
            print(f"  Option: {opt.text.strip()} -> value={opt.get_attribute('value')}")
    except:
        print("No language options found")
    
    # Try to access the page with JavaScript to show content
    try:
        driver.execute_script("document.documentElement.style.display = 'block'")
        time.sleep(3)
        
        # Check if content changed
        body_text2 = driver.find_element(By.TAG_NAME, 'body').text
        print(f"\nBody text after JS: {body_text2[:500]}")
        
        # Look for database links again
        links2 = driver.find_elements(By.TAG_NAME, 'a')
        print(f"\nLinks after JS: {len(links2)}")
        for l in links2[:20]:
            href = l.get_attribute('href')
            text = l.text.strip()
            if text or href:
                print(f"  '{text}' -> {href}")
    except Exception as e:
        print(f"JS error: {e}")
    
finally:
    driver.quit()

print("\n=== FIN ===")
