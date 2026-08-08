/**
 * AppEER · static/js/modules/estudiantes-search.js  (Fase 6, Subfase 6.3)
 * ---------------------------------------------------------------
 * Búsqueda en vivo del listado de estudiantes. Consume el endpoint
 * parcial de la Subfase 6.2 (?q=... + header X-Requested-With, que
 * AppEER.http ya inyecta) y reemplaza #estudiante-rows con el
 * fragmento recibido, sin recargar la página.
 *
 * Mejora progresiva: si este script no carga o falla, el <form
 * id="estudiante-search-form"> de estudiante_list.html sigue
 * funcionando como un GET normal (Subfase 6.2) — este módulo solo
 * intercepta ese mismo flujo para no recargar la página.
 *
 * Dos decisiones de robustez, no solo "felices":
 *   - Debounce: espera a que la persona deje de tipear antes de
 *     disparar la petición.
 *   - Cancelación de peticiones obsoletas (AbortController): si el
 *     usuario tipea rápido, una respuesta vieja que llega tarde NO
 *     debe pisar el resultado de la búsqueda más reciente.
 * ---------------------------------------------------------------
 */
(function () {
    "use strict";

    const DEBOUNCE_MS = 350;

    const input = document.getElementById("estudiante-search");
    const form = document.getElementById("estudiante-search-form");
    const rows = document.getElementById("estudiante-rows");
    const pagination = document.getElementById("estudiante-pagination");

    if (!input || !form || !rows) {
        return; // esta página no tiene buscador de estudiantes; nada que hacer
    }
    if (!window.AppEER || !window.AppEER.http) {
        if (window.console && console.warn) {
            console.warn("estudiantes-search.js: AppEER.http no está disponible.");
        }
        return;
    }

    let debounceTimer = null;
    let activeController = null;

    function buildUrl(query) {
        const url = new URL(form.action || window.location.href, window.location.origin);
        if (query) {
            url.searchParams.set("q", query);
        } else {
            url.searchParams.delete("q");
        }
        return url.pathname + url.search;
    }

    function setLoading(isLoading) {
        rows.classList.toggle("opacity-50", isLoading);
        if (isLoading) {
            rows.setAttribute("aria-busy", "true");
        } else {
            rows.removeAttribute("aria-busy");
        }
    }

    function search(query) {
        if (activeController) {
            activeController.abort();
        }
        activeController = new AbortController();
        const thisController = activeController;

        setLoading(true);

        // La paginación server-rendered de la carga inicial ya no
        // describe correctamente el resultado de una búsqueda en vivo
        // (el fragmento parcial no trae su propia paginación). Se
        // oculta en cuanto hay una búsqueda en curso, en vez de mostrar
        // números que ya no corresponden a lo que se ve en pantalla.
        if (pagination) {
            pagination.classList.add("hidden");
        }

        window.AppEER.http
            .get(buildUrl(query), {signal: thisController.signal})
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("HTTP " + response.status);
                }
                return response.text();
            })
            .then(function (html) {
                rows.innerHTML = html;
            })
            .catch(function (err) {
                if (err.name === "AbortError") {
                    return; // una búsqueda más nueva ya está en curso; ignorar esta respuesta vieja
                }
                if (window.console && console.error) {
                    console.error("estudiantes-search.js:", err);
                }
                if (window.AppEER.notify) {
                    window.AppEER.notify.error("No se pudo actualizar la búsqueda. Intenta de nuevo.");
                }
            })
            .finally(function () {
                if (thisController === activeController) {
                    setLoading(false);
                }
            });
    }

    input.addEventListener("input", function () {
        window.clearTimeout(debounceTimer);
        const query = input.value.trim();
        debounceTimer = window.setTimeout(function () {
            search(query);
        }, DEBOUNCE_MS);
    });

    // Con JS activo, el buscador es 100% en vivo: el submit tradicional
    // (Enter, o el envío del <form>) también pasa por fetch en vez de
    // recargar. Sin JS, este listener nunca se registra y el <form>
    // hace su GET normal de toda la vida (Subfase 6.2).
    form.addEventListener("submit", function (event) {
        event.preventDefault();
        window.clearTimeout(debounceTimer);
        search(input.value.trim());
    });
})();