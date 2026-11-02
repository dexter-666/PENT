import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import re, requests, urllib3
urllib3.disable_warnings()

H = {'User-Agent': 'Thesis-Security-Audit/1.0'}
ses = requests.Session()

# Login con usuario inexistente
r1 = ses.post('https://sigea.uns.edu.pe/index.php/C_logueo/iniciar_session',
              headers=H, verify=False, timeout=12,
              data={'usuario': 'audit_probe_nonexistent', 'password': 'PROBE'},
              allow_redirects=True)

print(f'HTTP: {r1.status_code}  URL: {r1.url}')
print(f'Cookies: {dict(ses.cookies)}')

# Buscar mensajes de error visibles en el HTML
# Fragmentos que pueden indicar diferenciacion de usuario vs password
body = r1.text
# Extraer el titulo y primeros 800 chars del body
start = body.find('<body')
snippet = body[start:start+800] if start >= 0 else body[:800]
print('=== Body snippet ===')
print(snippet)
print()

# Buscar JS alerts o variables de error en el JS
js_alerts = re.findall(r"(?:alert|swal|toastr|toast|notify)\s*\(['\"]([^'\"]{0,200})['\"]", body)
print(f'JS alerts/notifications: {js_alerts[:5]}')

# Buscar data-message u otros atributos de error
data_msg = re.findall(r'data-(?:message|msg|content|text)=["\']([^"\']{0,100})["\']', body)
print(f'data-message attrs: {data_msg[:5]}')
