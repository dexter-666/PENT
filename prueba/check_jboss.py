#!/usr/bin/env python3
import requests, urllib3, re
urllib3.disable_warnings()
reg = 'https://registro.uns.edu.pe'
s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0'})

print("=== /management ===")
r = s.get(f'{reg}/management', timeout=5)
print(f"Status: {r.status_code}, len: {len(r.text)}, CT: {r.headers.get('Content-Type', 'N/A')}")
print(r.text[:1000])

print("\n=== /jboss-cli ===")
r2 = s.get(f'{reg}/jboss-cli', timeout=5)
print(f"Status: {r2.status_code}, len: {len(r2.text)}, CT: {r2.headers.get('Content-Type', 'N/A')}")
print(r2.text[:500])

print("\n=== /jmx-console ===")
r3 = s.get(f'{reg}/jmx-console', timeout=5)
print(f"Status: {r3.status_code}, len: {len(r3.text)}")
print(r3.text[:500])

print("\n=== /jmx-console/HtmlAdaptor ===")
r4 = s.get(f'{reg}/jmx-console/HtmlAdaptor?action=inspect', timeout=5)
print(f"Status: {r4.status_code}, len: {len(r4.text)}")
if 'mbean' in r4.text.lower() or 'jmx' in r4.text.lower():
    print("JMX content found!")
else:
    print(r4.text[:500])

# Check if /console/management is different
print("\n=== /console/management ===")
r5 = s.get(f'{reg}/console/management', timeout=5)
print(f"Status: {r5.status_code}, len: {len(r5.text)}")
print(r5.text[:500])

# Check /console/jmx-console
print("\n=== /console/jmx-console ===")
r6 = s.get(f'{reg}/console/jmx-console', timeout=5)
print(f"Status: {r6.status_code}, len: {len(r6.text)}")
print(r6.text[:500])
