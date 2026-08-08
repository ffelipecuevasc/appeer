/**
 * AppEER · static/js/modules/pareja-form.js  (Fase 6)
 * ---------------------------------------------------------------
 * Envía el formulario de "nueva pareja" por fetch, consumiendo el
 * endpoint de la Subfase 6.4 (201 + fragmento de confirmación, o
 * 422 + fragmento del form con errores). Gestiona el estado de
 * carga del botón y muestra el resultado con AppEER.notify
 * (Subfase 6.1).
 *
 * Detalle importante de por qué el listener NO se cuelga del
 * <form> directamente: cuando la respuesta trae un fragmento nuevo
 * (éxito o error), #pareja-form-container.innerHTML se reemplaza
 * por completo — el <form id="pareja-form"> original queda
 * destruido y aparece uno nuevo en su lugar dentro del mismo
 * contenedor. Un listener atado al nodo viejo no se entera de nada
 * de lo que pase con el nuevo. Por eso el listener vive en
 * #pareja-form-container (que nunca se destruye) y usa delegación:
 * 'submit' burbujea, así que sigue capturando el evento incluso
 * después de que el form interno haya sido reemplazado — incluyendo
 * un segundo intento tras corregir un error de validación.
 *
 * Mejora progresiva: si este script no carga, el <form> sigue
 * siendo un POST normal (Subfase 6.4) — recarga la página, pero
 * funciona igual.
 * ---------------------------------------------------------------
 */
(function () {
    "use strict";

    const container = document.getElementById("pareja-form-container");
    if (!container) {
        return; // esta página no tiene el formulario de pareja; nada que hacer
    }
    if (!window.AppEER || !window.AppEER.http) {
        if (window.console && console.warn) {
            console.warn("pareja-form.js: AppEER.http no está disponible.");
        }
        return;
    }

    function setLoading(form, isLoading) {
        const button = form.querySelector('button[type="submit"]');
        if (!button) return;
        if (isLoading) {
            button.dataset.originalText = button.textContent;
            button.textContent = "Guardando…";
            button.disabled = true;
            button.classList.add("opacity-60", "cursor-not-allowed");
        } else {
            button.textContent = button.dataset.originalText || "Guardar";
            button.disabled = false;
            button.classList.remove("opacity-60", "cursor-not-allowed");
        }
    }

    function focusFirstField() {
        const field = container.querySelector("select, input, textarea");
        if (field) {
            field.focus();
        }
    }

    container.addEventListener("submit", function (event) {
        const form = event.target;
        if (!form || form.id !== "pareja-form") {
            return; // delegación: solo nos interesa el submit de este form puntual
        }
        event.preventDefault();

        const formData = new FormData(form);
        const url = form.action || window.location.href;

        setLoading(form, true);

        window.AppEER.http
            .postForm(url, formData)
            .then(function (response) {
                return response.text().then(function (html) {
                    return {ok: response.ok, html: html};
                });
            })
            .then(function (result) {
                // Reemplaza el form viejo (o la confirmación) por el fragmento
                // recibido. A partir de acá el <form id="pareja-form"> de esta
                // clausura queda obsoleto; el próximo submit lo captura el
                // mismo listener, vía delegación, sobre el form nuevo.
                container.innerHTML = result.html;

                if (result.ok) {
                    window.AppEER.notify.success("Pareja creada correctamente.");
                } else {
                    window.AppEER.notify.error("Revisa los datos del formulario e intenta de nuevo.");
                    focusFirstField();
                }
            })
            .catch(function (err) {
                if (window.console && console.error) {
                    console.error("pareja-form.js:", err);
                }
                window.AppEER.notify.error("No se pudo guardar la pareja. Revisa tu conexión e intenta de nuevo.");
                setLoading(form, false);
            });
    });
})();