/**
 * AppEER · static/js/core/http.js  (Fase 6, Subfase 6.1)
 * ---------------------------------------------------------------
 * Envoltorio mínimo sobre fetch. Dos responsabilidades, nada más:
 *
 *   1. Inyecta automáticamente el token CSRF (header X-CSRFToken)
 *      en toda petición de escritura (POST/PUT/PATCH/DELETE). Las
 *      vistas de Django solo aceptan escritura con este token
 *      presente — sin esto, cualquier fetch de escritura falla con
 *      403 Forbidden.
 *   2. Marca toda petición con X-Requested-With: XMLHttpRequest,
 *      para que una vista pueda distinguir "esto es una petición
 *      fetch" de "esto es una carga de página completa" (lo que
 *      necesitan las Subfases 6.2 y 6.4 para responder con un
 *      fragmento HTML parcial en vez de la página entera).
 *
 * No decide QUÉ hacer con la respuesta — eso es responsabilidad de
 * cada módulo de página (Subfases 6.3, 6.5). Este archivo solo
 * resuelve el "cómo pedir", no el "qué hacer con lo pedido".
 *
 * Requiere que base.html incluya {% csrf_token %} en algún punto de
 * la página (ya lo hace desde esta subfase) para que la cookie
 * "csrftoken" exista sin importar si la página tiene o no un <form>
 * propio.
 *
 * Namespace expuesto: window.AppEER.http
 * ---------------------------------------------------------------
 */
(function () {
    "use strict";

    const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS", "TRACE"]);

    function getCsrfToken() {
        const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : null;
    }

    /**
     * Petición base. `options` acepta lo mismo que el segundo
     * argumento de fetch() (method, body, headers, etc.).
     */
    async function request(url, options = {}) {
        const method = (options.method || "GET").toUpperCase();
        const headers = new Headers(options.headers || {});
        headers.set("X-Requested-With", "XMLHttpRequest");

        if (!SAFE_METHODS.has(method)) {
            const token = getCsrfToken();
            if (token) {
                headers.set("X-CSRFToken", token);
            } else if (window.console && console.warn) {
                console.warn(
                    "AppEER.http: no se encontró la cookie csrftoken. " +
                    "Esta petición de escritura probablemente sea rechazada con 403."
                );
            }
        }

        return fetch(url, {
            ...options,
            method,
            headers,
            credentials: "same-origin",
        });
    }

    window.AppEER = window.AppEER || {};
    window.AppEER.http = {
        get(url, options) {
            return request(url, {...options, method: "GET"});
        },
        post(url, options) {
            return request(url, {...options, method: "POST"});
        },
        /** Atajo para enviar un <form> completo (FormData) por POST. */
        postForm(url, formData, options = {}) {
            return request(url, {...options, method: "POST", body: formData});
        },
        request,
    };
})();