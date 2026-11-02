#!/usr/bin/env python3
import requests, urllib3, gzip
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    'Accept-Encoding': 'gzip, deflate',
    'User-Agent': 'Mozilla/5.0'
})

# Try to get config.inc.php with raw bytes (no decompression)
r = s.get('https://orcl.uns.edu.pe/config.inc.php', timeout=5)
print(f"Status: {r.status_code}")
print(f"len(text): {len(r.text)}")
print(f"len(content): {len(r.content)}")
print(f"Content-Encoding: {r.headers.get('Content-Encoding')}")
print(f"Content-Type: {r.headers.get('Content-Type')}")
print(f"Content-Length header: {r.headers.get('Content-Length')}")
print()
print(f"Content raw (first 200 bytes):")
print(r.content[:200])
print()
print(f"Content text (first 200 chars):")
print(r.text[:200])
print()

# Try with no Accept-Encoding
s2 = requests.Session()
s2.verify = False
s2.headers.update({'User-Agent': 'Mozilla/5.0'})
r2 = s2.get('https://orcl.uns.edu.pe/config.inc.php', timeout=5)
print(f"\n--- Without Accept-Encoding ---")
print(f"Status: {r2.status_code}, len: {len(r2.text)}")
print(f"Content: {r2.content[:200]}")

# Try with explicit Accept-Encoding: identity
s3 = requests.Session()
s3.verify = False
s3.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Accept-Encoding': 'identity'
})
r3 = s3.get('https://orcl.uns.edu.pe/config.inc.php', timeout=5)
print(f"\n--- With Accept-Encoding: identity ---")
print(f"Status: {r3.status_code}, len: {len(r3.text)}")
print(f"Content: {r3.content[:200]}")

# Check response headers in detail
print(f"\n--- All Response Headers ---")
for k, v in r.headers.items():
    print(f"  {k}: {v}")
