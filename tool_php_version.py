#!/usr/bin/env python3
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
H = {'User-Agent': 'Thesis-Security-Audit/1.0'}
BASE = 'https://campus.uns.edu.pe'

r = requests.get(BASE + '/login/index.php', timeout=12, verify=False, headers=H)
print('=== campus.uns.edu.pe (Moodle) ===')
print(f'X-Powered-By: {r.headers.get("X-Powered-By", "N/A")}')
print(f'Server: {r.headers.get("Server", "N/A")}')
print()

BASE2 = 'https://sigea.uns.edu.pe'
r2 = requests.get(BASE2 + '/', timeout=12, verify=False, headers=H)
print('=== sigea.uns.edu.pe ===')
print(f'X-Powered-By: {r2.headers.get("X-Powered-By", "N/A")}')
print(f'Server: {r2.headers.get("Server", "N/A")}')