/**
 * Plataforma Interactiva · Gestión y Reutilización de RAEE
 * E.A.P.I.S.I. - Universidad Nacional del Santa (UNS) · 2026-II
 */

document.addEventListener("DOMContentLoaded", () => {
  /* =========================================================================
     1. SISTEMA DE NAVEGACIÓN POR VISTAS INDEPENDIENTES
     ========================================================================= */
  const moduleViews = document.querySelectorAll(".module-view");
  const navTabBtns = document.querySelectorAll(".nav-tab-btn");
  const mainNav = document.getElementById("mainNav");
  const mobileMenuBtn = document.getElementById("mobileMenuBtn");

  function showView(viewKey, pushHash = true) {
    if (!viewKey) return;
    let found = false;

    moduleViews.forEach((sec) => {
      if (sec.getAttribute("data-view") === viewKey) {
        sec.classList.add("active");
        found = true;
      } else {
        sec.classList.remove("active");
      }
    });

    if (!found) return;

    navTabBtns.forEach((btn) => {
      if (btn.getAttribute("data-goto-view") === viewKey) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    if (mainNav?.classList.contains("open")) {
      mainNav.classList.remove("open");
      mobileMenuBtn?.setAttribute("aria-expanded", "false");
    }

    if (pushHash) {
      try {
        history.replaceState(null, "", `#${viewKey}`);
      } catch (_) {}
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  document.addEventListener("click", (e) => {
    const trigger = e.target.closest("[data-goto-view]");
    if (trigger) {
      e.preventDefault();
      const targetKey = trigger.getAttribute("data-goto-view");
      showView(targetKey);
      document.getElementById("searchResultsPanel")?.classList.remove("visible");
    }
  });

  const initialHash = window.location.hash.replace("#", "").trim();
  if (initialHash) {
    showView(initialHash, false);
  }

  /* =========================================================================
     2. SUB-PESTAÑAS DEL PROTOCOLO DE DONACIONES (MÓDULO 6)
     ========================================================================= */
  const protocolBtns = document.querySelectorAll(".protocol-subtab-btn");
  const protocolPanels = document.querySelectorAll(".protocol-panel");

  protocolBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-protocol-tab");
      protocolBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      protocolPanels.forEach((p) => {
        if (p.id === targetId) p.classList.add("active");
        else p.classList.remove("active");
      });
    });
  });

  /* =========================================================================
     3. CONTROLES DE ACCESIBILIDAD Y MODO OSCURO
     ========================================================================= */
  const btnFontDec = document.getElementById("btnFontDec");
  const btnFontReset = document.getElementById("btnFontReset");
  const btnFontInc = document.getElementById("btnFontInc");
  const btnThemeToggle = document.getElementById("btnThemeToggle");

  function setFontScale(scale, activeBtn) {
    document.documentElement.style.setProperty("--font-scale", String(scale));
    [btnFontDec, btnFontReset, btnFontInc].forEach((b) => b?.classList.remove("active"));
    activeBtn?.classList.add("active");
  }

  btnFontDec?.addEventListener("click", () => setFontScale(0.92, btnFontDec));
  btnFontReset?.addEventListener("click", () => setFontScale(1, btnFontReset));
  btnFontInc?.addEventListener("click", () => setFontScale(1.12, btnFontInc));

  btnThemeToggle?.addEventListener("click", () => {
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    if (isDark) {
      document.documentElement.removeAttribute("data-theme");
      btnThemeToggle.textContent = "🌙 Modo Oscuro";
    } else {
      document.documentElement.setAttribute("data-theme", "dark");
      btnThemeToggle.textContent = "☀️ Modo Claro";
    }
  });

  mobileMenuBtn?.addEventListener("click", () => {
    const isOpen = mainNav.classList.toggle("open");
    mobileMenuBtn.setAttribute("aria-expanded", String(isOpen));
  });

  /* =========================================================================
     4. MÓDULO 3: REUTILIZACIÓN EN CASA (6 TUTORIALES CON LINKS YOUTUBE)
     ========================================================================= */
  const HOME_TUTORIALS = [
    {
      num: 1,
      icon: "📹",
      tag: "SEGURIDAD DEL HOGAR",
      gradient: "linear-gradient(135deg, #0284c7, #0f172a)",
      title: "1. Convertir un smartphone viejo en cámara de seguridad",
      videoTitle: "Así VIGILO mi CASA remotamente y en TIEMPO Real con un MÓVIL VIEJO — Alfred Camera",
      videoUrl: "https://www.youtube.com/watch?v=fVIladI5PNc",
      summary:
        "Transforma un smartphone antiguo con cámara funcional en una cámara de vigilancia remota en tiempo real con alertas de movimiento usando AlfredCamera.",
      needsTitle: "Qué necesitas",
      needs: [
        "Un teléfono antiguo con cámara funcional y sistema operativo todavía compatible con la app.",
        "Tu teléfono actual, que servirá como visor.",
        "Conexión a internet para ambos teléfonos (Wi‑Fi o datos móviles).",
        "AlfredCamera instalada en los dos dispositivos y una cuenta de acceso (misma cuenta o vinculación por código QR).",
        "Un soporte estable y un punto de alimentación seguro, si el teléfono necesita carga."
      ],
      stepsTitle: "Procedimiento detallado",
      steps: [
        "Comprueba el teléfono antiguo. Abre la cámara normal y confirma que enfoca, que el lente está limpio y que el equipo no se reinicia ni se calienta de forma anormal. Revisa que la batería no esté hinchada ni dañada.",
        "Instala AlfredCamera en ambos teléfonos desde sus tiendas oficiales. Comprueba que la app abra en los dos. Si el sistema antiguo no permite instalarla, el video no ofrece un método alternativo.",
        "Abre la app en cada dispositivo e inicia sesión con la misma cuenta, o usa el flujo de vinculación por QR que aparece en el video. Protege la cuenta con una contraseña única y autenticación adicional si está disponible.",
        "En el teléfono antiguo, selecciona el rol “Cámara”. Acepta los permisos necesarios de cámara y micrófono para habilitar el video en directo y, si lo deseas, el audio.",
        "En el teléfono actual, selecciona “Reproductor” o la opción equivalente de visor. Confirma que el teléfono antiguo aparezca como cámara vinculada y abre la transmisión en vivo.",
        "Coloca el teléfono antiguo sobre una superficie firme, orientado al área que deseas supervisar. Evita apuntarlo hacia ventanas con luz directa o espacios donde no tengas autorización para grabar.",
        "Prueba la imagen desde el visor. Camina por el campo de visión, verifica que la cámara detecte el movimiento y que llegue la notificación. Ajusta sensibilidad según el entorno para reducir alertas por sombras o mascotas.",
        "Prueba el audio bidireccional únicamente si lo necesitas. Comprueba el volumen y evita dejar conversaciones privadas al alcance de otras personas.",
        "Antes de depender del sistema, prueba la conexión durante un periodo prolongado y reinicia ambos teléfonos una vez para verificar que la cámara vuelva a estar disponible."
      ]
    },
    {
      num: 2,
      icon: "🎬",
      tag: "MULTIMEDIA Y STREAMING",
      gradient: "linear-gradient(135deg, #7c3aed, #1e1b4b)",
      title: "2. Crear un centro multimedia con un portátil antiguo",
      videoTitle: "INSTALAR LibreELEC — Convierte tu viejo PC en un centro multimedia Kodi",
      videoUrl: "https://www.youtube.com/watch?v=yFuytcu5BGA",
      summary:
        "Dedica un portátil o PC antiguo exclusivamente a centro multimedia con LibreELEC y Kodi para reproducir películas, series y música conectado a tu televisor.",
      needsTitle: "Qué necesitas",
      needs: [
        "Portátil o PC que quieras dedicar a multimedia, con salida de video para conectarlo a una pantalla y teclado disponible durante la instalación.",
        "Memoria USB vacía o con copia de seguridad de sus archivos.",
        "Conexión a internet para descargar la imagen y configurar la red.",
        "La herramienta oficial LibreELEC USB‑SD Creator y una imagen compatible con la arquitectura del equipo (ej. Generic AMD/Intel/Nvidia x86_64)."
      ],
      stepsTitle: "Procedimiento detallado",
      steps: [
        "En otro equipo, visita el sitio oficial de LibreELEC y descarga USB‑SD Creator para el sistema que estás usando. Elige siempre la versión vigente compatible con tu hardware.",
        "Abre el creador, selecciona la arquitectura del equipo destino y descarga la imagen (para muchos PC x86_64 la opción genérica puede ser apropiada; revisa las especificaciones del portátil).",
        "Inserta la memoria USB y confirma cuidadosamente que la unidad seleccionada sea la correcta. La opción de escribir sobrescribe y formatea esa memoria.",
        "Espera a que termine la escritura. Si Windows ofrece formatear el USB al finalizar, cancela el aviso; no reformatees el medio que acabas de crear.",
        "Con el portátil apagado, inserta el USB y enciéndelo. Abre el menú de arranque con la tecla correspondiente a tu marca y modelo (por ejemplo, en una HP Mini se usa Esc y luego F9).",
        "Selecciona la memoria USB. Cuando aparezca el menú de LibreELEC, elige “Install LibreELEC”. Detente aquí si no confirmaste tu copia de seguridad: los pasos siguientes borran el disco interno.",
        "Selecciona el disco interno correcto como destino. Revisa dos veces el nombre y tamaño del disco y confirma el borrado únicamente si aceptas que el sistema anterior y los archivos desaparezcan.",
        "Al terminar, retira el USB y reinicia. Sigue el asistente inicial de Kodi/LibreELEC: establece un nombre, conecta el Wi‑Fi y activa SSH o Samba solo si los necesitas con credenciales seguras.",
        "Conecta el equipo a la pantalla por HDMI u otra salida compatible, comprueba sonido e imagen y añade contenido o complementos desde fuentes legítimas."
      ],
      extraNoteTitle: "Lo que puede variar",
      extraNote:
        "La tecla de arranque, compatibilidad, controladores y versión de Kodi dependen del hardware y de la fecha (el video menciona Kodi 17.6, versión antigua). Una vez instalado, el portátil queda dedicado principalmente como centro multimedia."
    },
    {
      num: 3,
      icon: "💽",
      tag: "BACKUPS Y ARCHIVOS",
      gradient: "linear-gradient(135deg, #059669, #064e3b)",
      title: "3. Transformar un disco duro antiguo en almacenamiento externo",
      videoTitle: "Convierte tu disco duro viejo en un disco externo USB ¡Fácil y rápido!",
      videoUrl: "https://www.youtube.com/watch?v=RNLtc1AChnw",
      summary:
        "Reutiliza un disco duro SATA de 2,5 pulgadas de una laptop en desuso montándolo en una carcasa USB para guardar backups, fotos y videos familiares.",
      needsTitle: "Materiales",
      needs: [
        "HDD SATA de 2,5 pulgadas que funcione.",
        "Carcasa externa que especifique compatibilidad con SATA de 2,5 pulgadas y con el grosor de tu disco.",
        "Cable USB suministrado y destornillador pequeño.",
        "Computadora para comprobar que lo reconoce y hacer una copia de prueba."
      ],
      stepsTitle: "Procedimiento detallado",
      steps: [
        "Si el disco aún está dentro de la laptop, apaga y desconecta el equipo antes de extraerlo. Si no tienes experiencia abriendo la computadora, solicita ayuda para evitar dañar el disco o el portátil.",
        "Identifica la interfaz y dimensiones impresas en el disco. Este procedimiento trabaja con SATA de 2,5 pulgadas (un disco M.2, IDE o de 3,5 pulgadas requiere una solución distinta).",
        "Antes de montarlo, decide qué hacer con los datos. Si necesitas recuperarlos, no inicialices ni formatees todavía: conéctalo solo para lectura o consulta a un técnico.",
        "Abre la carcasa liberando los clips con cuidado sin usar fuerza excesiva para no quebrar la tapa plástica.",
        "Si el disco tiene un marco lateral de montaje, retira sus tornillos con el destornillador apropiado y aparta el marco.",
        "Alinea los conectores SATA del disco y de la placa adaptadora. Empuja de manera uniforme y suave; no fuerces los pines ni inclines el conector.",
        "Desliza el disco y la placa dentro del cuerpo de la carcasa y fija la placa con los tornillos pequeños incluidos para que no se mueva al transportarlo.",
        "Cierra la tapa y asegúrate de que el cable pueda conectarse sin tensión. Conecta primero al puerto de la carcasa y luego a la computadora.",
        "Comprueba que el sistema detecte la unidad y su capacidad. Copia archivos de prueba no importantes, expulsa la unidad de forma segura y vuelve a conectarla.",
        "Solo si el disco está vacío o ya respaldaste todo y quieres prepararlo para uso nuevo, crea una partición y formatéalo desde el sistema operativo."
      ]
    },
    {
      num: 4,
      icon: "🖼️",
      tag: "DECORACIÓN INTERACTIVA",
      gradient: "linear-gradient(135deg, #d97706, #451a03)",
      title: "4. Usar una tablet antigua como marco digital de fotos",
      videoTitle: "Crea fácil un marco digital con una tablet vieja",
      videoUrl: "https://www.youtube.com/watch?v=ypNWam-sH94",
      summary:
        "Convierte tu tablet antigua en una pieza decorativa interactiva montándola en un marco con paspartú para mostrar una presentación continua de tus fotos favoritas.",
      needsTitle: "Materiales y preparación",
      needs: [
        "Tablet funcional con pantalla legible (prueba Wi‑Fi, carga, botones y reproducción antes de montarla).",
        "Marco con profundidad suficiente, cristal, paspartú y tapa trasera.",
        "Cartón limpio y firme para calzar la tablet sin presionar la pantalla.",
        "Cable y cargador compatibles, considerando cómo saldrá el cable por detrás.",
        "Fotos que tengas permiso de mostrar."
      ],
      stepsTitle: "Procedimiento detallado",
      steps: [
        "Mide la tablet, el área visible de la pantalla y el hueco del paspartú. Comprueba en seco que la pantalla quedará centrada y que el marco no tapa parte importante de la imagen.",
        "Desmonta la parte trasera del marco y retira el soporte interior que estorbe. Conserva el cristal y la tapa evitando astillar la madera o rayar el cristal.",
        "Coloca el paspartú contra el cristal con la abertura orientada correctamente. Sitúa la tablet detrás y céntrala para que la pantalla coincida con el hueco.",
        "Añade tiras de cartón en los bordes para impedir que la tablet se deslice sin apoyar el peso del marco sobre la pantalla ni tapar zonas que disipen calor.",
        "Enciende la presentación antes de cerrar y verifica orientación, recorte, brillo y orden de reproducción usando una app o función de presentación compatible con tu tablet.",
        "Conecta la alimentación si hace falta y haz una salida holgada para el cable. Deja acceso al botón de encendido y controles necesarios.",
        "Coloca una pieza trasera de cartón para mantener la tablet en su posición y vuelve a instalar la tapa sin doblar ni empujar la pantalla.",
        "Prueba el conjunto todavía sobre una mesa. Déjalo encendido y supervisado para comprobar que no se calienta de forma anormal ni se afloja el cable antes de colocarlo en su ubicación final."
      ]
    },
    {
      num: 5,
      icon: "🌱",
      tag: "IOT Y JARDINERÍA",
      gradient: "linear-gradient(135deg, #16a34a, #052e16)",
      title: "5. Crear una maceta tecnológica con sensor de humedad",
      videoTitle: "How to make a smart plant with Arduino and an HW-080 humidity sensor?",
      videoUrl: "https://www.youtube.com/watch?v=B_nb781-J4o",
      summary:
        "Integra una placa Arduino Micro, una pantalla OLED I²C de 128×64 y un sensor de humedad de suelo HW‑080 para monitorear el estado de tu planta.",
      needsTitle: "Componentes",
      needs: [
        "Arduino Micro (el video usa este modelo).",
        "Sensor de humedad de suelo HW‑080 y sus cables.",
        "Pantalla OLED I²C monocromática de 128×64, compatible con 3V.",
        "Cables jumper, cable USB para programar y computador con Arduino IDE.",
        "Maceta con planta y una pequeña cantidad de su sustrato para calibración."
      ],
      wiringTable: [
        { comp: "OLED", term: "VCC / GND", pin: "3V / GND" },
        { comp: "OLED I²C", term: "SDA / SCL", pin: "Pin digital 2 / pin digital 3" },
        { comp: "Sensor HW‑080", term: "VCC / GND / salida analógica", pin: "5V / GND / A1" }
      ],
      wiringWarning:
        "Estos pines corresponden al Arduino Micro mostrado; confirma el pinout de tu placa y el voltaje admitido por tus módulos antes de conectarlos. No coloques Arduino, pantalla ni uniones eléctricas dentro de la tierra o donde puedan mojarse.",
      stepsTitle: "Procedimiento detallado",
      steps: [
        "Revisa la identificación de cada módulo y sus terminales antes de alimentar. Con el USB desconectado, conecta GND común, la OLED según la tabla y la salida analógica del HW‑080 a A1.",
        "Conecta el Arduino al computador por USB. Abre Arduino IDE y selecciona el modelo de placa y puerto correctos.",
        "Instala las librerías gráficas Adafruit_GFX y Adafruit_SSD1306 (el código usa también Wire para I²C). Si no compila, revisa versión de librería, placa y dirección I²C.",
        "Usa la lógica descrita: definir pantalla 128×64, leer la entrada A1, guardar el valor y compararlo con una variable de umbral (el ejemplo inicia en 325) para dibujar una cara diferente según la lectura.",
        "Antes de confiar en el umbral, abre el Monitor Serie y observa la lectura con la sonda al aire o en sustrato seco, y después en sustrato húmedo. No sumerjas el módulo electrónico; solo la sonda para suelo.",
        "Ajusta el umbral entre los valores medidos. Confirma la dirección de lectura de tu módulo e invierte la comparación si tu sensor responde al revés.",
        "Prueba el sensor en la maceta y compara la indicación con el estado real del sustrato en varios días; no uses una lectura aislada como orden automática de riego.",
        "Fija la placa y las conexiones en una caja protegida, con la sonda separada de los componentes. Desconecta el montaje antes de mover o limpiar cables."
      ]
    },
    {
      num: 6,
      icon: "🎮",
      tag: "EDUCACIÓN DIGITAL",
      gradient: "linear-gradient(135deg, #0d9488, #134e4a)",
      title: "6. Preparar una tablet o teléfono para aprendizaje infantil",
      videoTitle: "Tutorial de cómo descargar y usar Khan Academy Kids",
      videoUrl: "https://www.youtube.com/watch?v=bIhEjd-dR1k",
      summary:
        "Convierte una tablet o smartphone antiguo en una herramienta educativa segura para niños instalando y configurando Khan Academy Kids desde tiendas oficiales.",
      needsTitle: "Antes de instalar",
      needs: [
        "Carga el dispositivo y revisa pantalla, altavoces, botones y conexión Wi‑Fi.",
        "Actualiza el sistema si el equipo permite hacerlo y libera espacio suficiente.",
        "Un adulto debe comprobar que la aplicación aparezca en la tienda oficial (App Store o Google Play). No descargues instaladores de sitios desconocidos.",
        "Decide si el uso será en casa o en una clase, y configura el perfil adecuado."
      ],
      stepsTitle: "Instalación y configuración",
      steps: [
        "Abre App Store en iPad/iPhone o Google Play en Android. Busca “Khan Academy Kids” y verifica el nombre del desarrollador y el icono oficial antes de instalar.",
        "Pulsa Descargar/Instalar. Espera a que termine y abre la app (la descarga y configuración inicial requieren internet).",
        "En la pantalla de inicio, elige “At Home” si se usará en casa o “At School” si se usará en un entorno escolar.",
        "Sigue las opciones de perfil vigentes: para uso familiar busca el flujo de estudiante o familiar (no crees una cuenta docente si no corresponde).",
        "Completa cualquier comprobación para adultos (“Grown-Ups Only”) bajo supervisión del adulto responsable. No entregues la contraseña adulta al niño.",
        "Abre una actividad breve (letras, lectura, matemáticas, lógica o libros) y verifica que el audio, los controles y el contenido funcionen bien.",
        "Configura controles parentales del dispositivo, limita compras y revisa permisos innecesarios de micrófono, cámara o ubicación.",
        "Usa la app junto al niño al principio y comprueba si el material en inglés se ajusta a su objetivo (edad de referencia 2–8 años)."
      ],
      extraNoteTitle: "Reutilización responsable",
      extraNote:
        "En un dispositivo antiguo, la compatibilidad de la tienda oficial es el primer filtro. Si la app no está disponible, no es seguro instalar una versión no oficial; prueba otra app educativa reconocida que siga siendo compatible."
    }
  ];

  const homeReuseGrid = document.getElementById("homeReuseGrid");
  if (homeReuseGrid) {
    homeReuseGrid.innerHTML = HOME_TUTORIALS.map((item) => {
      const wiringHtml = item.wiringTable
        ? `
          <h4>Cableado que muestra el video</h4>
          <table class="data-table">
            <thead>
              <tr>
                <th>Componente</th>
                <th>Terminal del módulo</th>
                <th>Arduino Micro (video)</th>
              </tr>
            </thead>
            <tbody>
              ${item.wiringTable
                .map(
                  (row) => `
                  <tr>
                    <td><strong>${row.comp}</strong></td>
                    <td>${row.term}</td>
                    <td>${row.pin}</td>
                  </tr>
                `
                )
                .join("")}
            </tbody>
          </table>
          <p style="font-size:0.8rem; color:var(--brand-amber); margin-bottom:0.6rem;"><strong>⚠️ Nota de seguridad:</strong> ${item.wiringWarning}</p>
        `
        : "";

      const extraNoteHtml = item.extraNote
        ? `
          <h4>${item.extraNoteTitle}</h4>
          <p style="font-size:0.84rem;">${item.extraNote}</p>
        `
        : "";

      return `
        <article class="card">
          <div class="card-thumb" style="background: ${item.gradient}; display:flex; align-items:center; justify-content:center; flex-direction:column; color:#ffffff; padding:1rem; text-align:center;">
            <span class="card-num-badge">Tutorial #${item.num}</span>
            <div style="font-size:2.8rem; line-height:1; margin-bottom:0.35rem;">${item.icon}</div>
            <span style="font-size:0.75rem; font-weight:700; background:rgba(255,255,255,0.18); padding:0.18rem 0.65rem; border-radius:999px;">
              ${item.tag}
            </span>
          </div>

          <h3>${item.title}</h3>
          <p>${item.summary}</p>

          <p style="font-size:0.8rem; color:var(--text-muted); margin-top:0.6rem;">
            <strong>🎥 Video analizado:</strong> ${item.videoTitle}
          </p>

          <div style="display:flex; gap:0.55rem; flex-wrap:wrap; margin-top:0.9rem;">
            <a href="${item.videoUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-youtube" style="flex:1; font-size:0.84rem; padding:0.58rem 0.85rem;">
              ▶️ Abrir Video en YouTube
            </a>
            <button type="button" class="btn btn-secondary toggle-tutorial-btn" data-target="tutorial-panel-${item.num}" style="flex:1; font-size:0.84rem; padding:0.58rem 0.85rem;">
              📖 Ver Procedimiento
            </button>
          </div>

          <div class="tutorial-detail-panel" id="tutorial-panel-${item.num}">
            <h4>${item.needsTitle}</h4>
            <ul class="card-list" style="margin-top:0.25rem; margin-bottom:0.6rem;">
              ${item.needs.map((n) => `<li>${n}</li>`).join("")}
            </ul>
            ${wiringHtml}
            <h4>${item.stepsTitle}</h4>
            <ol class="tutorial-steps-ol">
              ${item.steps.map((s) => `<li>${s}</li>`).join("")}
            </ol>
            ${extraNoteHtml}
          </div>
        </article>
      `;
    }).join("");

    homeReuseGrid.querySelectorAll(".toggle-tutorial-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const panelId = btn.getAttribute("data-target");
        const panel = document.getElementById(panelId);
        if (!panel) return;
        const isOpen = panel.classList.toggle("open");
        btn.textContent = isOpen ? "▲ Ocultar Procedimiento" : "📖 Ver Procedimiento";
      });
    });
  }

  /* =========================================================================
     5. MÓDULO 2: CATÁLOGO DE DISPOSITIVOS DE INGENIERÍA DE SISTEMAS (EPISI)
     ========================================================================= */
  const DEVICE_CATALOG = [
    {
      category: "computo",
      icon: "💻",
      gradient: "linear-gradient(135deg, #1e3a8a, #0f172a)",
      title: "Laptops, Netbooks y PCs de Escritorio",
      riskBadge: "Plomo, Litio y BFR",
      valueBadge: "Oro, Cobre, RAM y SSD",
      description:
        "Equipos principales de programación y desarrollo en la EPISI. Suelen reemplazarse por lentitud de software o desgaste de batería.",
      reuseTip:
        "Amplía la RAM, instala un SSD, conviértela en centro multimedia con LibreELEC/Kodi o instala GNU/Linux.",
      storageTip:
        "Guárdala apagada en lugar seco; si la batería está hinchada, no la cargues ni manipules."
    },
    {
      category: "moviles",
      icon: "📱",
      gradient: "linear-gradient(135deg, #065f46, #0f172a)",
      title: "Smartphones, Celulares y Tablets",
      riskBadge: "Litio, Cobalto y Mercurio",
      valueBadge: "Oro, Plata y Paladio",
      description:
        "Dispositivos de uso diario y pruebas móviles. Tienen alta rotación cada 18 a 24 meses.",
      reuseTip:
        "Transfórmalo en cámara de seguridad Wi-Fi (AlfredCamera), marco digital de fotos o tablet educativa (Khan Academy Kids).",
      storageTip:
        "Retira SIM y MicroSD, borra tus datos personales y guárdalo lejos del calor."
    },
    {
      category: "componentes",
      icon: "💽",
      gradient: "linear-gradient(135deg, #0f766e, #0f172a)",
      title: "Discos Duros (HDD), SSD y Memorias RAM",
      riskBadge: "Níquel y Soldaduras",
      valueBadge: "Contactos de Oro y Aluminio",
      description:
        "Unidades extraídas al actualizar ordenadores portátiles o de escritorio.",
      reuseTip:
        "Coloca tu disco SATA de 2,5 pulgadas en una carcasa USB compatible para convertirlo en almacenamiento externo.",
      storageTip:
        "Verifica primero si contiene datos importantes antes de formatear y guárdalo en bolsa antiestática."
    },
    {
      category: "componentes",
      icon: "🧩",
      gradient: "linear-gradient(135deg, #991b1b, #0f172a)",
      title: "Placas Madre, Sensores y Microcontroladores",
      riskBadge: "Plomo y Cadmio",
      valueBadge: "Oro, Plata, Cobre y Sensores",
      description:
        "Placas base, tarjetas de video y kits de electrónica/IoT (Arduino Micro, sensor HW-080, pantallas OLED).",
      reuseTip:
        "Ideales para crear una maceta tecnológica con sensor de humedad o prácticas de identificación de hardware.",
      storageTip:
        "Nunca quemes ni tritures placas; mantenlas intactas en una caja rígida."
    },
    {
      category: "perifericos",
      icon: "🖥️",
      gradient: "linear-gradient(135deg, #3730a3, #0f172a)",
      title: "Monitores LCD/LED y Pantallas",
      riskBadge: "Mercurio y Plomo",
      valueBadge: "Paneles LCD y Cobre",
      description:
        "Monitores externos de escritorio o pantallas reutilizables como segunda pantalla.",
      reuseTip:
        "Úsalo como segundo monitor para programar o conectarlo a un portátil con LibreELEC.",
      storageTip:
        "No abras monitores ni pantallas en prácticas básicas; evita golpear el cristal."
    },
    {
      category: "perifericos",
      icon: "⌨️",
      gradient: "linear-gradient(135deg, #1d4ed8, #0f172a)",
      title: "Teclados, Mouses, Impresoras y Routers",
      riskBadge: "Plásticos BFR y Tóners",
      valueBadge: "Motores, Switches y Cobre",
      description:
        "Periféricos y routers Wi-Fi descartados por cambios de proveedor o fallas menores.",
      reuseTip:
        "Configura routers antiguos como repetidores Wi-Fi o dona periféricos funcionales para laboratorio.",
      storageTip:
        "Retira cartuchos de tinta o tóner antes de almacenar una impresora."
    },
    {
      category: "energia",
      icon: "🔌",
      gradient: "linear-gradient(135deg, #b45309, #0f172a)",
      title: "Cargadores, Fuentes de Poder y Cables",
      riskBadge: "PVC y Retardantes",
      valueBadge: "Cobre Electrolítico Puro",
      description:
        "Cables USB, HDMI, adaptadores de corriente de laptops y fuentes ATX acumulados en casa.",
      reuseTip:
        "No abras fuentes de poder ni cargadores sellados; entrega los dañados en canales autorizados.",
      storageTip:
        "Enrolla cada cable ordenadamente sin cortarlos ni quemarlos."
    },
    {
      category: "energia",
      icon: "🔋",
      gradient: "linear-gradient(135deg, #be123c, #0f172a)",
      title: "Baterías de Litio, Powerbanks y UPS",
      riskBadge: "Alto Riesgo: Litio y Plomo",
      valueBadge: "Litio, Cobalto y Níquel",
      description:
        "Baterías agotadas o hinchadas de celulares, laptops y sistemas de respaldo eléctrico.",
      reuseTip:
        "Nunca reutilices, cargues ni perfores baterías hinchadas; aíslalas y derívalas a un gestor RAEE.",
      storageTip:
        "Cubre los contactos de baterías intactas extraíbles con cinta aislante."
    }
  ];

  const deviceCatalogGrid = document.getElementById("deviceCatalogGrid");
  const filterTabs = document.querySelectorAll(".filter-tab");

  function renderDeviceCatalog(category = "todos") {
    if (!deviceCatalogGrid) return;
    const filtered =
      category === "todos"
        ? DEVICE_CATALOG
        : DEVICE_CATALOG.filter((item) => item.category === category);

    deviceCatalogGrid.innerHTML = filtered
      .map(
        (dev) => `
        <article class="card">
          <div class="card-thumb" style="background:${dev.gradient}; display:flex; align-items:center; justify-content:center; font-size:2.8rem; height:120px;">
            <span>${dev.icon}</span>
          </div>
          <div class="device-card-meta">
            <span class="badge badge-danger">${dev.riskBadge}</span>
            <span class="badge badge-green">${dev.valueBadge}</span>
          </div>
          <h3>${dev.title}</h3>
          <p>${dev.description}</p>
          <div class="device-detail-box">
            <p><strong>🛠️ Reutilización:</strong> ${dev.reuseTip}</p>
            <p><strong>📦 Almacenamiento:</strong> ${dev.storageTip}</p>
          </div>
        </article>
      `
      )
      .join("");
  }

  filterTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      filterTabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      renderDeviceCatalog(tab.getAttribute("data-category") || "todos");
    });
  });

  renderDeviceCatalog("todos");

  /* =========================================================================
     6. ASISTENTE DE DIAGNÓSTICO Y REPARACIÓN
     ========================================================================= */
  const wizardDeviceSelect = document.getElementById("wizardDeviceSelect");
  const wizardStateSelect = document.getElementById("wizardStateSelect");
  const btnRunDiagnosis = document.getElementById("btnRunDiagnosis");
  const wizardOutput = document.getElementById("wizardOutput");

  const DIAGNOSIS_RULES = {
    lento: {
      badge: "Prioridad 1 · Repotenciación o Reutilización en Casa (No Desechar)",
      summary:
        "Tu equipo sigue siendo funcional. La lentitud suele deberse al disco mecánico o al sistema operativo, por lo que puedes repotenciarlo o darle un nuevo rol en casa.",
      step1Title: "1. Revisión Técnica",
      step1Text:
        "Verifica el estado del disco, la memoria RAM y que la batería no esté hinchada ni presente sobrecalentamiento.",
      step2Title: "2. Tutoriales de Segunda Vida",
      step2Text:
        "Convierte tu portátil en centro multimedia con LibreELEC/Kodi, tu celular en cámara con AlfredCamera o tu tablet en marco digital o herramienta con Khan Academy Kids.",
      step3Title: "3. Donación en la UNS",
      step3Text:
        "Si ya no lo necesitas, comunícate a los números 992863544, 960724968 o 900721790 para donarlo voluntariamente en la EPISI - UNS."
    },
    falla_leve: {
      badge: "Prioridad 2 · Reparación Focalizada o Evaluación Segura",
      summary:
        "Una falla en el cargador, disco o componente modular no justifica desechar el aparato completo.",
      step1Title: "1. Identifica la Pieza Dañada",
      step1Text:
        "Comprueba si el problema proviene del adaptador de corriente, cable desconectado o módulo reemplazable según el manual del fabricante.",
      step2Title: "2. Recupera Piezas Compatibles",
      step2Text:
        "Un disco SATA de 2,5 pulgadas puede aprovecharse en una carcasa USB externa (ver Tutorial #3 en Reutilización en Casa).",
      step3Title: "3. Entrega la Pieza Inservible",
      step3Text:
        "Lleva únicamente la pieza dañada o batería agotada a los canales autorizados de RAEE."
    },
    funcional_antiguo: {
      badge: "Prioridad 3 · Segunda Vida en Casa o Donación en la UNS",
      summary:
        "Los dispositivos guardados en cajones pierden valor útil. Prioriza siempre el equipo completo cuando todavía funciona.",
      step1Title: "1. Borrado Seguro de Datos",
      step1Text:
        "Haz copia de seguridad de tus archivos, cierra tus sesiones y restablece el equipo de fábrica antes de cederlo.",
      step2Title: "2. Reutilización en Casa",
      step2Text:
        "Sigue cualquiera de los 6 tutoriales con video de nuestra sección Reutilización en Casa.",
      step3Title: "3. Donar en la Universidad",
      step3Text:
        "Comunícate al 992863544, 960724968 o 900721790 y revisa nuestro Protocolo de Donaciones EPISI."
    },
    inservible: {
      badge: "Prioridad 4 · Seguridad Primero y Quinta Ruta RAEE en Chimbote",
      summary:
        "Si presenta batería hinchada, calor, fuga o daño irreversible, no lo enciendas ni desarmes: aíslalo y derívalo a un canal formal.",
      step1Title: "1. Regla Principal de Seguridad",
      step1Text:
        "No abras fuentes de poder, monitores, pantallas ni baterías hinchadas; no quemes cables ni intentes extraer metales con químicos.",
      step2Title: "2. Almacenamiento Seguro",
      step2Text:
        "Mantenlo identificado en una caja seca separado de la basura común.",
      step3Title: "3. Quinta Ruta en Chimbote",
      step3Text:
        "Consulta a la Gerencia de Gestión Ambiental de la MPS, el mapa «Trae tu RAEE» del MINAM o EO-RS autorizadas para RAEE."
    }
  };

  function runWizardDiagnosis() {
    if (!wizardDeviceSelect || !wizardStateSelect || !wizardOutput) return;
    const deviceLabel = wizardDeviceSelect.options[wizardDeviceSelect.selectedIndex].text;
    const stateKey = wizardStateSelect.value;
    const rule = DIAGNOSIS_RULES[stateKey] || DIAGNOSIS_RULES.lento;

    wizardOutput.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.5rem;">
        <strong style="font-size:1.05rem;">Diagnóstico para: ${deviceLabel}</strong>
        <span class="badge badge-green">${rule.badge}</span>
      </div>
      <p style="font-size:0.9rem; color:var(--text-secondary);">${rule.summary}</p>
      <div class="wizard-steps-grid">
        <div class="wizard-step-card">
          <h4>${rule.step1Title}</h4>
          <p>${rule.step1Text}</p>
        </div>
        <div class="wizard-step-card">
          <h4>${rule.step2Title}</h4>
          <p>${rule.step2Text}</p>
        </div>
        <div class="wizard-step-card">
          <h4>${rule.step3Title}</h4>
          <p>${rule.step3Text}</p>
        </div>
      </div>
    `;
  }

  btnRunDiagnosis?.addEventListener("click", runWizardDiagnosis);
  wizardDeviceSelect?.addEventListener("change", runWizardDiagnosis);
  wizardStateSelect?.addEventListener("change", runWizardDiagnosis);
  runWizardDiagnosis();

  /* =========================================================================
     7. CHECKLIST DE ALMACENAMIENTO Y BORRADO DE DATOS
     ========================================================================= */
  const storageChecks = document.querySelectorAll(".storage-check");
  const checklistProgressText = document.getElementById("checklistProgressText");

  storageChecks.forEach((chk) => {
    chk.addEventListener("change", () => {
      const total = storageChecks.length;
      const checked = Array.from(storageChecks).filter((c) => c.checked).length;
      const pct = Math.round((checked / total) * 100);
      if (checklistProgressText) {
        checklistProgressText.textContent = `Progreso de preparación: ${checked} de ${total} pasos completados (${pct} %)`;
      }
    });
  });

  /* =========================================================================
     8. CALCULADORA DE IMPACTO RAEE
     ========================================================================= */
  const calcInputs = document.querySelectorAll(".calc-input");
  const calcTotalWeight = document.getElementById("calcTotalWeight");
  const calcComparisonText = document.getElementById("calcComparisonText");
  const calcCopperValue = document.getElementById("calcCopperValue");
  const calcPreciousValue = document.getElementById("calcPreciousValue");
  const calcWaterSaved = document.getElementById("calcWaterSaved");

  function updateCalculator() {
    let totalWeightKg = 0;
    let totalCopperG = 0;
    let totalPreciousG = 0;

    calcInputs.forEach((input) => {
      const qty = Math.max(0, parseInt(input.value || "0", 10));
      const weight = parseFloat(input.getAttribute("data-weight") || "0");
      const copper = parseFloat(input.getAttribute("data-copper") || "0");
      const gold = parseFloat(input.getAttribute("data-gold") || "0");

      totalWeightKg += qty * weight;
      totalCopperG += qty * copper;
      totalPreciousG += qty * gold;
    });

    const pctOfLocal = Math.round((totalWeightKg / 4.01) * 100);
    const waterLiters = Math.round(totalWeightKg * 4000);

    if (calcTotalWeight) {
      calcTotalWeight.textContent = `${totalWeightKg.toFixed(2).replace(".", ",")} kg`;
    }
    if (calcComparisonText) {
      calcComparisonText.textContent = `Equivale al ${pctOfLocal} % de la generación anual promedio por habitante en Nuevo Chimbote (4,01 kg/año, Campos Grijalva, 2026).`;
    }
    if (calcCopperValue) {
      calcCopperValue.textContent = `${Math.round(totalCopperG)} g de Cobre y Aluminio`;
    }
    if (calcPreciousValue) {
      calcPreciousValue.textContent = `${totalPreciousG.toFixed(2).replace(".", ",")} g de Oro, Plata y Paladio`;
    }
    if (calcWaterSaved) {
      calcWaterSaved.textContent = `~${waterLiters.toLocaleString("es-PE")} litros de agua protegidos`;
    }
  }

  calcInputs.forEach((input) => input.addEventListener("input", updateCalculator));
  updateCalculator();

  /* =========================================================================
     9. BUSCADOR GLOBAL DE CONTENIDOS
     ========================================================================= */
  const SEARCH_ITEMS = [
    {
      view: "identificacion",
      title: "1. ¿Qué son los RAEE y Ciclo de Vida (ACV)?",
      desc: "Definición legal D.S. 009-2019-MINAM, riesgos de plomo y mercurio, y recuperación de materiales.",
      keywords: "que son raee ciclo de vida acv plomo mercurio cadmio oro cobre economia circular"
    },
    {
      view: "dispositivos-episi",
      title: "2. Equipos de Ingeniería de Sistemas (EPISI)",
      desc: "Catálogo interactivo de laptops, smartphones, discos duros, RAM, placas madre, monitores y baterías.",
      keywords: "equipos episi sistemas laptop celular smartphone disco duro ssd ram placa monitor router"
    },
    {
      view: "reutilizacion-casa",
      title: "3. Reutilización en Casa (6 Tutoriales Paso a Paso + Videos YouTube)",
      desc: "Alfred Camera, LibreELEC/Kodi, disco duro externo USB, marco digital de fotos, maceta con Arduino HW-080 y OLED, y Khan Academy Kids.",
      keywords: "reutilizacion en casa tutoriales youtube alfred camera camara de seguridad libreelec kodi centro multimedia disco duro externo sata 2.5 marco digital tablet arduino hw-080 oled maceta humedad khan academy kids ninos"
    },
    {
      view: "diagnostico",
      title: "4. Diagnóstico y Reparación de Dispositivos",
      desc: "Asistente paso a paso para evaluar laptops lentas, fallas leves o reutilización antes de desechar.",
      keywords: "diagnostico reparar repotenciar ssd linux laptop lenta falla"
    },
    {
      view: "almacenamiento",
      title: "5. Separación y Almacenamiento Temporal Seguro",
      desc: "Protocolo de almacenamiento en casa, cuidado con baterías hinchadas y borrado seguro de datos.",
      keywords: "separar almacenar bateria hinchada litio cinta aislante borrar datos backup"
    },
    {
      view: "protocolo-donaciones",
      title: "6. Protocolo de Recepción de Donaciones, Evaluación y Destino (EPISI)",
      desc: "Qué hacemos al recibir tu donación: código RAEE-001, 5 destinos posibles, separación segura, qué no abrir, protección de datos, oro y quinta ruta en Chimbote.",
      keywords: "protocolo donaciones recepcion evaluacion separacion segura piezas no abrir fuente de poder oro chimbote quinta ruta eo-rs municipalidad provincial del santa raeecicla"
    },
    {
      view: "puntos-recoleccion",
      title: "7. Puntos de Recogida en Nuevo Chimbote y UNS",
      desc: "Punto de recepción EPISI-UNS, contenedores en Real Plaza Nuevo Chimbote y canales oficiales MINAM.",
      keywords: "puntos de recogida recoleccion nuevo chimbote uns real plaza minam"
    },
    {
      view: "calculadora",
      title: "8. Calculadora de Impacto y Peso RAEE",
      desc: "Calcula cuántos kilos de RAEE acumulas frente al promedio de Nuevo Chimbote (4,01 kg/hab/año).",
      keywords: "calculadora peso kilos impacto cobre oro agua"
    },
    {
      view: "entrega-uns",
      title: "Dejar Dispositivo en la UNS · Contacto: 992863544, 960724968, 900721790",
      desc: "Comunícate a los números 992863544, 960724968 o 900721790 y registra el dispositivo electrónico que quieres donar en la universidad.",
      keywords: "contacto numeros telefono whatsapp 992863544 960724968 900721790 dejar dispositivo universidad uns episi donar entregar"
    },
    {
      view: "fuentes",
      title: "9. Fuentes Oficiales y Marco Legal",
      desc: "Referencias verificadas: Global E-waste Monitor 2024, Campos Grijalva 2026 (UNS), MINAM y OMS.",
      keywords: "fuentes bibliografia minam oms unitar campos grijalva"
    }
  ];

  const globalSearchInput = document.getElementById("globalSearchInput");
  const searchClearBtn = document.getElementById("searchClearBtn");
  const searchResultsPanel = document.getElementById("searchResultsPanel");
  const searchResultsList = document.getElementById("searchResultsList");
  const searchResultsCount = document.getElementById("searchResultsCount");
  const closeSearchPanelBtn = document.getElementById("closeSearchPanelBtn");

  function executeSearch(rawQuery) {
    const query = rawQuery.trim().toLowerCase();
    if (!query) {
      searchResultsPanel?.classList.remove("visible");
      if (searchClearBtn) searchClearBtn.style.display = "none";
      return;
    }

    if (searchClearBtn) searchClearBtn.style.display = "block";

    const matches = SEARCH_ITEMS.filter(
      (item) =>
        item.title.toLowerCase().includes(query) ||
        item.desc.toLowerCase().includes(query) ||
        item.keywords.toLowerCase().includes(query)
    );

    if (searchResultsCount) {
      searchResultsCount.textContent = `Resultados encontrados para "${rawQuery}": ${matches.length}`;
    }

    if (searchResultsList) {
      searchResultsList.innerHTML =
        matches.length === 0
          ? `<div style="font-size:0.86rem; color:var(--text-muted);">No se encontraron coincidencias. Prueba buscando: <strong>Alfred</strong>, <strong>LibreELEC</strong>, <strong>HW-080</strong>, <strong>protocolo</strong> o <strong>992863544</strong>.</div>`
          : matches
              .map(
                (m) => `
              <button type="button" class="search-result-item" data-goto-view="${m.view}">
                <strong>${m.title}</strong>
                <p>${m.desc}</p>
              </button>
            `
              )
              .join("");
    }

    searchResultsPanel?.classList.add("visible");
  }

  globalSearchInput?.addEventListener("input", (e) => executeSearch(e.target.value));
  searchClearBtn?.addEventListener("click", () => {
    if (globalSearchInput) globalSearchInput.value = "";
    executeSearch("");
  });
  closeSearchPanelBtn?.addEventListener("click", () =>
    searchResultsPanel?.classList.remove("visible")
  );

  /* =========================================================================
     10. RECEPCIÓN DE DONACIONES EN LA UNS (992863544, 960724968, 900721790)
     ========================================================================= */
  const STORAGE_DROPOFF_LIST = "episi_uns_dropoff_devices_v3_2026";
  const dropDeliveryDate = document.getElementById("dropDeliveryDate");

  if (dropDeliveryDate) {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    dropDeliveryDate.value = tomorrow.toISOString().split("T")[0];
  }

  let uploadedPhotoDataUrl = "";
  const dropDevicePhoto = document.getElementById("dropDevicePhoto");
  dropDevicePhoto?.addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    if (!file) {
      uploadedPhotoDataUrl = "";
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      uploadedPhotoDataUrl = String(reader.result || "");
    };
    reader.readAsDataURL(file);
  });

  const DEFAULT_DROPOFFS = [
    {
      ticketId: "RAEE-001",
      name: "Luis Danilo Córdova Ramírez",
      phone: "992863544",
      coordinator: "992863544",
      category: "Disco Duro (HDD/SSD) o Memoria RAM",
      brand: "1 Disco Duro SATA 2,5\" 500 GB + 2 módulos RAM DDR3",
      condition: "Operativo (Para donación o reutilización académica)",
      date: "2026-11-24",
      shift: "Mañana (08:30 a.m. - 12:30 p.m.)",
      notes: "Donación voluntaria; sin datos personales, listo para evaluación en carcasa USB."
    },
    {
      ticketId: "RAEE-002",
      name: "Jesús Sebastián Ramírez Espada",
      phone: "960724968",
      coordinator: "960724968",
      category: "Smartphone / Teléfono Celular",
      brand: "1 Smartphone Xiaomi Redmi Note 8",
      condition: "Operativo (Para donación o reutilización académica)",
      date: "2026-11-25",
      shift: "Tarde (02:30 p.m. - 06:00 p.m.)",
      notes: "Cuentas cerradas y restablecido de fábrica; batería intacta."
    },
    {
      ticketId: "RAEE-003",
      name: "Patrick Silva Llaure",
      phone: "900721790",
      coordinator: "900721790",
      category: "Placa Madre, Arduino o Componentes",
      brand: "1 PC de escritorio antigua (para identificación de componentes)",
      condition: "Con falla (Para evaluación estudiantil bajo supervisión)",
      date: "2026-11-26",
      shift: "Mañana (08:30 a.m. - 12:30 p.m.)",
      notes: "Autorizada para práctica supervisada de identificación modular en la EPISI."
    },
    {
      ticketId: "RAEE-004",
      name: "Leguion_666",
      phone: "",
      coordinator: "992863544",
      category: "Dispositivo Electrónico",
      brand: "Leguion_666",
      condition: "Operativo",
      date: "2026-11-24",
      shift: "Mañana (08:30 a.m. - 12:30 p.m.)",
      notes: "Registrado desde la lista de disponibles de la plataforma."
    }
  ];

  let registeredDevices = [...DEFAULT_DROPOFFS];
  try {
    const savedList = localStorage.getItem(STORAGE_DROPOFF_LIST);
    if (savedList) {
      const parsed = JSON.parse(savedList);
      if (Array.isArray(parsed) && parsed.length > 0) {
        registeredDevices = parsed;
      }
    }
  } catch (_) {}

  const registeredDevicesList = document.getElementById("registeredDevicesList");
  const totalRegisteredDevicesBadge = document.getElementById("totalRegisteredDevicesBadge");
  const universityDropoffForm = document.getElementById("universityDropoffForm");
  const btnSendWhatsAppDirect = document.getElementById("btnSendWhatsAppDirect");
  const dropStatusMsg = document.getElementById("dropStatusMsg");
  const generatedTicketContainer = document.getElementById("generatedTicketContainer");

  function renderRegisteredDevices() {
    if (totalRegisteredDevicesBadge) {
      totalRegisteredDevicesBadge.textContent = `${registeredDevices.length} equipos registrados`;
    }
    if (!registeredDevicesList) return;
    registeredDevicesList.innerHTML = registeredDevices
      .map(
        (item) => `
        <article class="card" style="padding:1.1rem;">
          <div class="device-card-meta">
            <span class="badge badge-danger">${item.ticketId}</span>
            <span class="badge badge-green">Coordinación: ${item.coordinator}</span>
          </div>
          <h4 style="font-size:0.98rem; margin-bottom:0.25rem;">${item.category}</h4>
          <p style="font-size:0.86rem; font-weight:700; color:var(--text-primary); margin-bottom:0.3rem;">${item.brand}</p>
          <p style="font-size:0.82rem;">${item.notes}</p>
          <div class="device-detail-box" style="margin-top:0.75rem;">
            <p><strong>👤 Donante:</strong> ${item.name} (Tel.: ${item.phone})</p>
            <p><strong>📅 Entrega en EPISI:</strong> ${item.date} · ${item.shift}</p>
            <p><strong>📌 Estado:</strong> ${item.condition}</p>
          </div>
        </article>
      `
      )
      .join("");
  }

  renderRegisteredDevices();

  function getFormPayload() {
    return {
      name: document.getElementById("dropUserName")?.value.trim() || "Donante UNS",
      phone: document.getElementById("dropUserPhone")?.value.trim() || "",
      coordinator: document.getElementById("dropCoordinatorNumber")?.value || "992863544",
      category: document.getElementById("dropDeviceCategory")?.value || "Dispositivo Electrónico",
      brand: document.getElementById("dropDeviceBrand")?.value.trim() || "",
      condition: document.getElementById("dropDeviceCondition")?.value || "",
      date: document.getElementById("dropDeliveryDate")?.value || "",
      shift: document.getElementById("dropDeliveryShift")?.value || "",
      notes: document.getElementById("dropDeviceNotes")?.value.trim() || ""
    };
  }

  btnSendWhatsAppDirect?.addEventListener("click", () => {
    const data = getFormPayload();
    if (!data.name || !data.brand) {
      if (dropStatusMsg) {
        dropStatusMsg.textContent = "ℹ️ Ingresa tu nombre y el dispositivo que deseas donar antes de enviar por WhatsApp.";
      }
      return;
    }
    const text = `Hola, soy *${data.name}* (${data.phone}). Quiero donar un dispositivo en la EPISI - UNS:\n- *Dispositivo:* ${data.category}\n- *Marca/Modelo:* ${data.brand}\n- *Estado:* ${data.condition}\n- *Fecha/Turno:* ${data.date} (${data.shift})\n- *Detalle:* ${data.notes}`;
    const waUrl = `https://wa.me/51${data.coordinator}?text=${encodeURIComponent(text)}`;
    window.open(waUrl, "_blank", "noopener,noreferrer");
  });

  universityDropoffForm?.addEventListener("submit", (e) => {
    e.preventDefault();
    const data = getFormPayload();

    const nextNum = String(registeredDevices.length + 1).padStart(3, "0");
    const ticketId = `RAEE-${nextNum}`;
    const newEntry = {
      ticketId,
      ...data,
      photo: uploadedPhotoDataUrl
    };

    registeredDevices.unshift(newEntry);
    try {
      localStorage.setItem(STORAGE_DROPOFF_LIST, JSON.stringify(registeredDevices));
    } catch (_) {}

    renderRegisteredDevices();

    if (dropStatusMsg) {
      dropStatusMsg.textContent = `✅ ¡Donación registrada! Comunícate al ${data.coordinator} con tu código ${ticketId}.`;
    }

    const waText = `Hola, registré mi donación con código *${ticketId}* para dejarla en la EPISI - UNS (${data.category}: ${data.brand}).`;
    const waLink = `https://wa.me/51${data.coordinator}?text=${encodeURIComponent(waText)}`;

    if (generatedTicketContainer) {
      generatedTicketContainer.style.display = "block";
      generatedTicketContainer.innerHTML = `
        <div class="dropoff-ticket">
          <div class="ticket-header">
            <div style="display:flex; align-items:center; gap:0.75rem;">
              <img src="assets/logo-uns.png" alt="Logo UNS" style="height:38px; width:auto; background:#fff; padding:4px; border-radius:6px;" />
              <img src="assets/logo-episi.png" alt="Logo EPISI" style="height:38px; width:auto; background:#fff; padding:4px; border-radius:6px;" />
              <div>
                <strong style="display:block; font-size:1rem;">CONSTANCIA DE DONACIÓN DE DISPOSITIVO · EPISI - UNS</strong>
                <span style="font-size:0.8rem; color:var(--text-muted);">Proyecto de Gestión y Reutilización de RAEE · Nuevo Chimbote · 2026-II</span>
              </div>
            </div>
            <span class="badge badge-danger" style="font-size:0.9rem; padding:0.35rem 0.75rem;">Código: ${ticketId}</span>
          </div>

          <div class="grid-2" style="font-size:0.88rem;">
            <div>
              <p><strong>👤 Donante:</strong> ${data.name}</p>
              <p><strong>📱 Teléfono del Donante:</strong> ${data.phone}</p>
              <p><strong>📞 Línea de Coordinación UNS:</strong> ${data.coordinator} (992863544 · 960724968 · 900721790)</p>
              <p><strong>📅 Fecha y Turno de Entrega:</strong> ${data.date} (${data.shift})</p>
            </div>
            <div>
              <p><strong>💻 Dispositivo donado:</strong> ${data.category}</p>
              <p><strong>🏷️ Marca / Modelo / Cant.:</strong> ${data.brand}</p>
              <p><strong>🔍 Estado exterior:</strong> ${data.condition}</p>
              <p><strong>📝 Observaciones:</strong> ${data.notes}</p>
            </div>
          </div>

          ${
            uploadedPhotoDataUrl
              ? `<div style="margin-top:0.9rem;"><strong style="font-size:0.82rem; display:block; margin-bottom:0.3rem;">📷 Fotografía adjunta del dispositivo:</strong><img src="${uploadedPhotoDataUrl}" alt="Foto del dispositivo" style="max-height:140px; border-radius:8px; border:1px solid var(--border-color);" /></div>`
              : ""
          }

          <div style="margin-top:1rem; padding-top:0.8rem; border-top:1px solid var(--border-subtle); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.75rem;">
            <span style="font-size:0.8rem; color:var(--text-muted);">📍 Pabellón EPISI – Ciudad Universitaria UNS, Av. Pacífico 508, Nuevo Chimbote. (Donación voluntaria; no incluye reparación por encargo ni registro de contraseñas).</span>
            <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
              <a href="${waLink}" target="_blank" rel="noopener noreferrer" class="btn btn-primary">💬 Confirmar por WhatsApp (${data.coordinator})</a>
              <button type="button" class="btn btn-secondary" onclick="window.print()">🖨️ Imprimir Constancia</button>
            </div>
          </div>
        </div>
      `;
    }
  });
});
