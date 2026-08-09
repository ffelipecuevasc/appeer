/**
 * AppEER · static/js/core/notifications.js  (Fase 6, Subfase 6.1)
 * ---------------------------------------------------------------
 * Notificaciones del lado del cliente, con exactamente el mismo
 * lenguaje visual que partials/alerts.html (Fase 5): mismos colores
 * y mismos SVG por tipo, para que una notificación generada por JS
 * después de un fetch sea indistinguible de una server-rendered vía
 * django.contrib.messages.
 *
 * Requiere que el DOM tenga #appeer-alerts (lo agrega
 * partials/alerts.html desde esta subfase, siempre presente aunque
 * no haya mensajes del servidor).
 *
 * Namespace expuesto: window.AppEER.notify
 * ---------------------------------------------------------------
 */
(function () {
    "use strict";

    const ICONS = {
        success: '<svg class="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path fill="currentColor" d="m10.562 15.908l6.396-6.396l-.708-.708l-5.688 5.688l-2.85-2.85l-.708.708zM12.003 21q-1.866 0-3.51-.708q-1.643-.709-2.859-1.924t-1.925-2.856T3 12.003t.709-3.51Q4.417 6.85 5.63 5.634t2.857-1.925T11.997 3t3.51.709q1.643.708 2.859 1.922t1.925 2.857t.709 3.509t-.708 3.51t-1.924 2.859t-2.856 1.925t-3.509.709"/></svg>',
        error: '<svg class="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path fill="currentColor" d="M12.434 16.28q.182-.182.182-.434t-.182-.433T12 15.23t-.434.182t-.182.433t.182.434t.434.181t.434-.181m-.934-3.126h1v-6h-1zM12.003 21q-1.866 0-3.51-.708q-1.643-.709-2.859-1.924t-1.925-2.856T3 12.003t.709-3.51Q4.417 6.85 5.63 5.634t2.857-1.925T11.997 3t3.51.709q1.643.708 2.859 1.922t1.925 2.857t.709 3.509t-.708 3.51t-1.924 2.859t-2.856 1.925t-3.509.709"/></svg>',
        warning: '<svg class="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path fill="currentColor" d="M2.73 20L12 4l9.27 16zm9.704-2.566q.182-.182.182-.434t-.182-.434t-.434-.181t-.434.181t-.181.434t.181.434t.434.181t.434-.181m-.934-2.05h1v-5h-1z"/></svg>',
        info: '<svg class="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path fill="currentColor" d="M11.5 16.5h1V11h-1zm.934-7.1q.182-.177.182-.439t-.178-.438T12 8.346t-.438.177t-.177.439t.181.438t.434.177t.434-.177m-.43 11.6q-1.868 0-3.511-.708q-1.643-.709-2.859-1.924t-1.925-2.856T3 12.003t.709-3.51Q4.417 6.85 5.63 5.634t2.857-1.925T11.997 3t3.51.709q1.643.708 2.859 1.922t1.925 2.857t.709 3.509t-.708 3.51t-1.924 2.859t-2.856 1.925t-3.509.709"/></svg>',
    };

    const STYLES = {
        success: "bg-green-50 text-green-800",
        error: "bg-red-50 text-red-800",
        warning: "bg-amber-50 text-amber-800",
        info: "bg-brand-accent/10 text-brand-dark",
    };

    const DEFAULT_TIMEOUT_MS = 5000;

    function getContainer() {
        return document.getElementById("appeer-alerts");
    }

    /** Escapa texto vía DOM — nunca se inserta el mensaje como HTML crudo. */
    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Muestra una notificación. `type`: "success" | "error" | "warning" | "info".
     * `options.timeout` en ms (0 = no se autodescarta).
     * Devuelve el elemento creado, o null si no había dónde inyectarlo.
     */
    function show(message, type, options) {
        type = type || "info";
        options = options || {};
        const timeout = options.timeout === undefined ? DEFAULT_TIMEOUT_MS : options.timeout;

        const container = getContainer();
        if (!container) {
            if (window.console && console.warn) {
                console.warn("AppEER.notify: no se encontró #appeer-alerts en el DOM.");
            }
            return null;
        }

        const icon = ICONS[type] || ICONS.info;
        const style = STYLES[type] || STYLES.info;

        const el = document.createElement("div");
        el.className = "flex items-start gap-3 px-5 py-3.5 rounded-2xl shadow-card text-sm " + style;
        el.setAttribute("role", "status");
        el.innerHTML = icon + '<p class="pt-0.5">' + escapeHtml(message) + "</p>";

        container.appendChild(el);

        if (timeout) {
            setTimeout(function () {
                el.remove();
            }, timeout);
        }

        return el;
    }

    window.AppEER = window.AppEER || {};
    window.AppEER.notify = {
        show,
        success: (msg, options) => show(msg, "success", options),
        error: (msg, options) => show(msg, "error", options),
        warning: (msg, options) => show(msg, "warning", options),
        info: (msg, options) => show(msg, "info", options),
    };

    /**
     * Auto-descarte de mensajes SERVER-RENDERED (ajuste posterior a la
     * Fase 8). show() ya auto-descarta lo que genera el propio JS
     * (DEFAULT_TIMEOUT_MS más arriba) — esto es lo mismo, pero para los
     * mensajes que llegan directo del framework de Django
     * (django.contrib.messages, vía {% for message in messages %} en
     * partials/alerts.html), que hasta ahora se quedaban en pantalla
     * para siempre. Ejemplo real: "Sesión iniciada como X" tras el login.
     *
     * Corre UNA vez, al cargar el script (que ya está en <script defer>,
     * así que el DOM —incluidos los mensajes server-rendered— ya existe).
     * Toma una foto de los hijos de #appeer-alerts EN ESE MOMENTO nada
     * más: cualquier notificación que JS agregue después pasa por show()
     * y gestiona su propio timeout ahí, no acá — no hay doble manejo.
     */
    const SERVER_MESSAGE_TIMEOUT_MS = 3000;
    const FADE_OUT_MS = 300;

    function autoDescartarMensajesDelServidor() {
        const contenedor = getContainer();
        if (!contenedor) return;

        Array.from(contenedor.children).forEach(function (el) {
            setTimeout(function () {
                el.classList.add("transition-opacity", "duration-300", "opacity-0");
                setTimeout(function () {
                    el.remove();
                }, FADE_OUT_MS);
            }, SERVER_MESSAGE_TIMEOUT_MS);
        });
    }

    autoDescartarMensajesDelServidor();
})();