import requests, urllib3, re
urllib3.disable_warnings()
BASE = "https://biblioteca.uns.edu.pe"
h = {"User-Agent": "Mozilla/5.0"}

paths = [
    "/inicia_sesion.asp",
    "/registra_comentario.htm",
    "/registra_comentario.asp",
    "/catalogo.htm",
    "/catalogo.asp",
    "/repoins.htm",
    "/sms.htm",
    "/sms.asp",
    "/ayuda.htm",
    "/contacto.htm",
    # ASP clasico - rutas tipicas de admin
    "/admin/",
    "/admin.asp",
    "/admin/login.asp",
    "/login.asp",
    "/default.asp",
    "/index.asp",
    "/panel/",
    "/panel.asp",
    # Archivos de configuracion ASP.NET
    "/web.config",
    "/Web.config",
    "/global.asax",
    "/Global.asax",
    "/.env",
    "/.git/HEAD",
    # Subida de archivos?
    "/upload.asp",
    "/upload.aspx",
    "/fileupload.asp",
    "/uploadfile.asp",
    # Bases de datos tipicas ASP
    "/db.mdb",
    "/database.mdb",
    "/biblioteca.mdb",
    "/data/",
    "/database/",
    "/db/",
    # Backup
    "/backup.zip",
    "/backup.sql",
    "/backup.mdb",
    # Info
    "/robots.txt",
    "/sitemap.xml",
    "/_vti_bin/",       # FrontPage/SharePoint
    "/_vti_pvt/",       # FrontPage privado
    "/fpdb/",           # FrontPage database
    "/_private/",       # FrontPage privado
]

print(f"=== Recon profundo: {BASE} ===\n")
for path in paths:
    try:
        r = requests.get(BASE + path, headers=h, verify=False, timeout=8, allow_redirects=False)
        if r.status_code in (404,):
            continue
        size = len(r.content)
        ct = r.headers.get("Content-Type","")
        loc = r.headers.get("Location","")
        icon = "🔴" if r.status_code == 200 else ("🟡" if r.status_code in (301,302) else "🟠")
        print(f"  {icon} HTTP {r.status_code} | {path} | {size}b | {ct[:40]}")
        if loc:
            print(f"       -> {loc}")
        if r.status_code == 200 and size > 20:
            preview = r.text[:300].replace("\r","").replace("\n"," ")
            # Detectar si es soft-404
            if not any(k in preview.lower() for k in ["404","not found","error 404"]):
                print(f"       Preview: {preview[:200]}")
    except:
        pass

print("\n=== Analizando inicia_sesion.asp ===")
r2 = requests.get(BASE + "/inicia_sesion.asp", headers=h, verify=False, timeout=10, allow_redirects=True)
print(f"HTTP {r2.status_code} | {len(r2.content)} bytes")
print(r2.text[:1500])
