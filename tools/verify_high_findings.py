import requests, urllib3
urllib3.disable_warnings()
h = {"User-Agent": "Mozilla/5.0"}

urls = [
    "https://www.uns.edu.pe/config.php",
    "https://orcl.uns.edu.pe/config.inc.php",
    "https://www.uns.edu.pe/archivos/",
    "https://sigea.uns.edu.pe/phpmyadmin/",
    "https://sigea.uns.edu.pe/server-status",
]

for url in urls:
    r = requests.get(url, headers=h, verify=False, timeout=10, allow_redirects=True)
    ct = r.headers.get("Content-Type", "N/A")
    print(f"=== {url}")
    print(f"HTTP {r.status_code} | {len(r.content)} bytes | CT: {ct}")
    print(f"Body: {repr(r.text[:300])}")
    print()
