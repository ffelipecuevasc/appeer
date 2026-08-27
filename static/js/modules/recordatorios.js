/**
 * AppEER · static/js/modules/recordatorios.js  (Fase 14, Subfases 14.6 y 14.7)
 * ---------------------------------------------------------------
 * Convierte la línea de tiempo en un CRUD que no recarga la página:
 * la tarjeta se transforma en formulario en el mismo lugar donde
 * está, se envía por fetch y se reemplaza por la tarjeta actualizada
 * que devuelve el servidor.
 *
 * MEJORA PROGRESIVA (requisito no negociable, criterio de la Fase 6):
 * este módulo NO construye ninguna interfaz propia. Cada cosa que
 * intercepta ya funciona sin él:
 *   - "Editar" y "Eliminar" son <a href> a páginas reales.
 *   - Completar es un <form method="post"> real.
 *   - "Nuevo" tiene su <noscript> con el enlace de siempre.
 * Si este archivo no carga, la pantalla sigue siendo funcional; solo
 * recarga en cada acción.
 *
 * TAMPOCO construye el HTML de los formularios: se lo pide al
 * servidor, que los renderiza con la misma plantilla que usa el
 * camino sin JavaScript. Así hay UNA sola definición de campos, en
 * vez de dos que se desincronizan en cuanto alguien agrega uno.
 * ---------------------------------------------------------------
 */
(function () {
    "use strict";

    if (!window.AppEER || !window.AppEER.http) {
        // Sin el núcleo de la Fase 6 no hay CSRF automático; es
        // preferible no hacer nada y dejar el camino sin JS intacto.
        return;
    }

    const contenedorAlta = document.getElementById("recordatorio-zona-alta");
    const botonNuevo = document.getElementById("recordatorio-nuevo");

    // ---- utilidades ----

    function notificarError(mensaje) {
        if (window.AppEER.notify) {
            window.AppEER.notify.error(mensaje);
        }
    }

    function botonesDeFormulario(textoGuardar) {
        return (
            '<div class="mt-4 flex justify-end gap-2">' +
            '<button type="button" data-cancelar class="rounded-full border border-brand-border px-4 py-2 text-sm font-medium text-brand-dark">Cancelar</button>' +
            '<button type="submit" class="rounded-full bg-brand-accent px-5 py-2 text-sm font-medium text-white">' + textoGuardar + "</button>" +
            "</div>"
        );
    }

    /**
     * Monta un formulario dentro de `zona`, pidiéndole el HTML de los
     * campos al servidor. `alEnviar` recibe el FormData y decide qué
     * hacer con la respuesta.
     */
    function montarFormulario(zona, urlCampos, action, textoGuardar, alEnviar) {
        window.AppEER.http
            .get(urlCampos)
            .then(function (r) {
                if (!r.ok) throw new Error("HTTP " + r.status);
                return r.text();
            })
            .then(function (html) {
                zona.innerHTML =
                    '<form class="rounded-2xl border border-brand-accent/30 bg-white p-4">' +
                    html + botonesDeFormulario(textoGuardar) + "</form>";
                zona.classList.remove("hidden");

                const form = zona.querySelector("form");
                const primerCampo = form.querySelector("input, select, textarea");
                if (primerCampo) primerCampo.focus();

                form.querySelector("[data-cancelar]").addEventListener("click", function () {
                    zona.innerHTML = "";
                    zona.classList.add("hidden");
                });

                form.addEventListener("submit", function (evento) {
                    evento.preventDefault();
                    const boton = form.querySelector('button[type="submit"]');
                    boton.disabled = true;
                    boton.textContent = "Guardando…";

                    window.AppEER.http
                        .post(action, new FormData(form))
                        .then(function (respuesta) {
                            if (respuesta.status === 422) {
                                // Datos inválidos: el servidor devuelve el
                                // mismo formulario con sus errores ya
                                // renderizados. Se reemplazan solo los
                                // campos, conservando los botones.
                                return respuesta.text().then(function (htmlErrores) {
                                    const contenedorCampos = form.querySelector("div.grid").parentNode;
                                    form.innerHTML = htmlErrores + botonesDeFormulario(textoGuardar);
                                    montarBotonesTrasError(zona, form, action, textoGuardar, alEnviar);
                                    throw {manejado: true};
                                });
                            }
                            if (!respuesta.ok) throw new Error("HTTP " + respuesta.status);
                            return respuesta.text().then(function (htmlTarjeta) {
                                alEnviar(htmlTarjeta);
                            });
                        })
                        .catch(function (err) {
                            if (err && err.manejado) return;
                            notificarError("No se pudo guardar el recordatorio. Intenta de nuevo.");
                            boton.disabled = false;
                            boton.textContent = textoGuardar;
                        });
                });
            })
            .catch(function () {
                notificarError("No se pudo abrir el formulario.");
            });
    }

    // Tras un 422 se reemplaza el interior del <form>, así que hay que
    // volver a enganchar los botones nuevos.
    function montarBotonesTrasError(zona, form, action, textoGuardar, alEnviar) {
        form.querySelector("[data-cancelar]").addEventListener("click", function () {
            zona.innerHTML = "";
            zona.classList.add("hidden");
        });
    }

    // ---- alta ----

    if (botonNuevo && contenedorAlta) {
        botonNuevo.addEventListener("click", function () {
            montarFormulario(
                contenedorAlta,
                botonNuevo.dataset.url,
                botonNuevo.dataset.action,
                "Crear",
                function () {
                    // Una tarea nueva puede caer en cualquier semana, y
                    // esa semana quizá ni siquiera existe como bloque
                    // todavía. Insertarla en el lugar correcto desde JS
                    // implicaría reimplementar acá la lógica de
                    // agrupación que ya vive en el Selector. Recargar es
                    // más honesto y garantiza que el orden y los
                    // contadores queden bien.
                    window.location.reload();
                }
            );
        });
    }

    // ---- delegación de eventos ----
    // Un solo listener en el documento en vez de uno por tarjeta: las
    // tarjetas se reemplazan constantemente, y con listeners
    // individuales habría que reengancharlos cada vez (y los viejos
    // quedarían colgando en memoria).

    document.addEventListener("click", function (evento) {
        const tarjeta = evento.target.closest(".recordatorio-tarjeta");
        if (!tarjeta) return;

        // --- editar en línea ---
        const enlaceEditar = evento.target.closest(".recordatorio-editar");
        if (enlaceEditar) {
            evento.preventDefault();
            const zona = tarjeta.querySelector(".recordatorio-zona-edicion");
            const id = tarjeta.dataset.id;
            const action = enlaceEditar.getAttribute("href");
            const urlCampos = action.replace(/editar\/$/, "form/");
            montarFormulario(zona, urlCampos, action, "Guardar", function (htmlTarjeta) {
                tarjeta.outerHTML = htmlTarjeta;
            });
            return;
        }

        // --- eliminar, con confirmación EN LÍNEA ---
        // No window.confirm(): bloquea el navegador entero y se ve
        // ajeno al sistema visual. La confirmación vive dentro de la
        // propia tarjeta (Subfase 14.7).
        const enlaceEliminar = evento.target.closest(".recordatorio-eliminar");
        if (enlaceEliminar) {
            evento.preventDefault();
            const zona = tarjeta.querySelector(".recordatorio-zona-edicion");
            zona.innerHTML =
                '<div class="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-red-50 px-4 py-3">' +
                '<p class="text-sm text-red-800">¿Eliminar este recordatorio?</p>' +
                '<div class="flex gap-2">' +
                '<button type="button" data-cancelar class="rounded-full border border-red-200 px-4 py-1.5 text-sm text-red-800">Cancelar</button>' +
                '<button type="button" data-confirmar class="rounded-full bg-red-600 px-4 py-1.5 text-sm font-medium text-white">Eliminar</button>' +
                "</div></div>";
            zona.classList.remove("hidden");

            zona.querySelector("[data-cancelar]").addEventListener("click", function () {
                zona.innerHTML = "";
                zona.classList.add("hidden");
            });
            zona.querySelector("[data-confirmar]").addEventListener("click", function () {
                window.AppEER.http
                    .post(enlaceEliminar.getAttribute("href"), new FormData())
                    .then(function (respuesta) {
                        // 204 Sin Contenido: se borró, no hay fragmento
                        // que devolver.
                        if (respuesta.status !== 204 && !respuesta.ok) {
                            throw new Error("HTTP " + respuesta.status);
                        }
                        tarjeta.remove();
                        if (window.AppEER.notify) {
                            window.AppEER.notify.success("Recordatorio eliminado.");
                        }
                    })
                    .catch(function () {
                        notificarError("No se pudo eliminar el recordatorio.");
                    });
            });
            return;
        }
    });

    // --- completar / descompletar ---
    // Se intercepta el submit del <form> de la casilla, no el clic del
    // botón: así el camino sin JS (submit normal) queda intacto.
    document.addEventListener("submit", function (evento) {
        const form = evento.target.closest(".recordatorio-toggle");
        if (!form) return;
        evento.preventDefault();

        const tarjeta = form.closest(".recordatorio-tarjeta");
        window.AppEER.http
            .post(form.getAttribute("action"), new FormData(form))
            .then(function (respuesta) {
                if (!respuesta.ok) throw new Error("HTTP " + respuesta.status);
                return respuesta.text();
            })
            .then(function (htmlTarjeta) {
                // El servidor devuelve la tarjeta ya re-renderizada, con
                // el tachado, la opacidad y el estado de "vencida"
                // recalculados. El navegador no decide nada de eso.
                tarjeta.outerHTML = htmlTarjeta;
            })
            .catch(function () {
                notificarError("No se pudo actualizar el recordatorio.");
            });
    });
})();
