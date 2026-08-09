/**
 * AppEER · static/js/modules/splash.js  (Adenda 8)
 * ---------------------------------------------------------------
 * Transición de salida de la página de bienvenida: al pulsar el
 * botón, la página se desvanece antes de navegar, en vez de cortar
 * en seco.
 *
 * Es puramente cosmético y así está construido a propósito. Si este
 * archivo no carga, falla, o el usuario tiene JavaScript desactivado,
 * el botón sigue siendo un <a href> normal que navega igual — mejora
 * progresiva, el mismo criterio que rige desde la Fase 6. La decisión
 * de A DÓNDE navegar no vive acá: la resolvió el servidor y ya viene
 * en el href (ver AppEER/views.py::bienvenida).
 *
 * No usa AppEER.http ni AppEER.notify: esta página no hace ninguna
 * petición fetch ni muestra notificaciones, así que no carga el
 * núcleo de static/js/core/.
 * ---------------------------------------------------------------
 */
(function () {
    "use strict";

    const DURACION_MS = 350; // debe coincidir con .appeer-saliendo del template

    const enlace = document.getElementById("appeer-entrar");
    const contenedor = document.getElementById("appeer-bienvenida");

    if (!enlace || !contenedor) {
        return; // no estamos en la bienvenida; nada que hacer
    }

    function prefiereMenosMovimiento() {
        return window.matchMedia
            && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }

    enlace.addEventListener("click", function (event) {
        // Respeta la preferencia del sistema: sin animación, navegación
        // inmediata y sin retrasos artificiales.
        if (prefiereMenosMovimiento()) {
            return;
        }

        // Clic con modificador (Ctrl/Cmd/Shift) o botón central: el
        // usuario quiere abrir en otra pestaña. Desvanecer esta página
        // sería justo lo contrario de lo que pidió.
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) {
            return;
        }

        event.preventDefault();
        const destino = enlace.getAttribute("href");

        contenedor.classList.add("appeer-saliendo");

        // Red de seguridad: si por cualquier motivo el evento
        // transitionend no llegara (pestaña en segundo plano, por
        // ejemplo), este temporizador garantiza que la navegación
        // ocurra igual. El usuario nunca queda atrapado en una
        // pantalla a medio desvanecer.
        window.setTimeout(function () {
            window.location.href = destino;
        }, DURACION_MS);
    });
})();