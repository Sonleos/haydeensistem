import { api, ApiError } from "./api.js";

/* ------------------------------------------------------------------ */
/* Estado                                                              */
/* ------------------------------------------------------------------ */

const state = {
  user: null,
  view: "pacientes",
  pacientes: [],
  tratamientos: [],
  control: { fecha: "", signos: [], dxtx: [], panales: [] },
  busqueda: "",
  controlTab: "signos",
  cargando: false,
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

/* ------------------------------------------------------------------ */
/* Utilidades                                                          */
/* ------------------------------------------------------------------ */

function esc(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function texto(value, fallback = "—") {
  if (value === null || value === undefined) return fallback;
  const limpio = String(value).trim();
  return limpio || fallback;
}

function decimal(value, suffix = "") {
  if (value === null || value === undefined || value === "") return "—";
  const numero = Number(value);
  if (Number.isNaN(numero)) return esc(value);
  return `${numero.toFixed(2)}${suffix}`;
}

function hora(fechaHora) {
  if (!fechaHora) return "—";
  const textoFecha = String(fechaHora);
  if (textoFecha.length >= 16) return textoFecha.slice(11, 16);
  return textoFecha;
}

function fechaLarga(iso) {
  if (!iso) return "";
  const partes = String(iso).split("-");
  if (partes.length !== 3) return iso;
  const fecha = new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
  return fecha.toLocaleDateString("es-MX", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function iniciales(nombre, apellidos) {
  const a = texto(nombre, "").charAt(0);
  const b = texto(apellidos, "").charAt(0);
  return esc(`${a}${b}`.toUpperCase() || "?");
}

function debounce(fn, ms = 250) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

/* ------------------------------------------------------------------ */
/* Toasts                                                              */
/* ------------------------------------------------------------------ */

function toast(message, type = "success") {
  const root = $("#toast-root");
  if (!root) return;

  const estilos = {
    success: "bg-emerald-600",
    error: "bg-rose-600",
    info: "bg-slate-800",
  };

  const nodo = document.createElement("div");
  nodo.className = `${estilos[type] || estilos.info} pointer-events-auto w-full max-w-sm rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-lg transition-opacity duration-300`;
  nodo.textContent = message;
  root.appendChild(nodo);

  setTimeout(() => {
    nodo.style.opacity = "0";
    setTimeout(() => nodo.remove(), 300);
  }, 3200);
}

/* ------------------------------------------------------------------ */
/* Modales                                                             */
/* ------------------------------------------------------------------ */

let modalActual = null;

function abrirModal({ titulo, subtitulo = "", contenido, onSubmit, textoBoton = "Guardar" }) {
  cerrarModal();

  const root = $("#modal-root");
  const formId = `modal-form-${Date.now()}`;
  const overlay = document.createElement("div");
  overlay.className =
    "fixed inset-0 z-50 flex items-end justify-center bg-slate-950/60 px-0 sm:px-4 sm:items-center";
  overlay.innerHTML = `
    <div class="modal-enter w-full max-w-lg rounded-t-3xl sm:rounded-3xl bg-white shadow-2xl max-h-[92vh] flex flex-col">
      <div class="flex items-start justify-between gap-4 px-5 pt-5 pb-3 border-b border-slate-100">
        <div>
          <h2 class="text-lg font-bold text-slate-900">${esc(titulo)}</h2>
          ${subtitulo ? `<p class="text-xs text-slate-500 mt-0.5">${esc(subtitulo)}</p>` : ""}
        </div>
        <button type="button" data-close class="rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-bold text-slate-600 active:bg-slate-200">Cerrar</button>
      </div>
      <form id="${formId}" class="flex-1 overflow-y-auto px-5 py-4 space-y-3" novalidate>
        ${contenido}
        <p data-error class="hidden rounded-xl bg-rose-50 px-3 py-2 text-xs font-medium text-rose-700"></p>
      </form>
      <div class="border-t border-slate-100 px-5 py-3 safe-nav">
        <button type="submit" form="${formId}" data-submit class="w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-blue-600/20 active:scale-[0.99] disabled:opacity-60">
          ${esc(textoBoton)}
        </button>
      </div>
    </div>
  `;

  const form = $(`#${formId}`, overlay);
  const error = $("[data-error]", overlay);
  const submit = $("[data-submit]", overlay);

  const cerrar = () => cerrarModal();
  $("[data-close]", overlay).addEventListener("click", cerrar);
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) cerrar();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    error.classList.add("hidden");
    submit.disabled = true;
    const original = submit.textContent;
    submit.textContent = "Guardando...";

    try {
      const formData = new FormData(form);
      const resultado = await onSubmit(formData, form);
      if (resultado !== false) cerrarModal();
    } catch (err) {
      const mensaje =
        err instanceof ApiError ? err.message : err?.message || "No se pudo guardar.";
      error.textContent = mensaje;
      error.classList.remove("hidden");
    } finally {
      submit.disabled = false;
      submit.textContent = original;
    }
  });

  root.appendChild(overlay);
  modalActual = overlay;

  const primerCampo = $("input, select, textarea", form);
  if (primerCampo) {
    setTimeout(() => primerCampo.focus(), 60);
  }
}

function cerrarModal() {
  if (modalActual) {
    modalActual.remove();
    modalActual = null;
  }
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") cerrarModal();
});

/* ------------------------------------------------------------------ */
/* Autenticación                                                       */
/* ------------------------------------------------------------------ */

function mostrarLogin(mensaje = "") {
  $("#login-screen").classList.remove("hidden");
  $("#app-screen").classList.add("hidden");
  const error = $("#login-error");
  if (mensaje) {
    error.textContent = mensaje;
    error.classList.remove("hidden");
  } else {
    error.classList.add("hidden");
  }
}

function mostrarApp() {
  $("#login-screen").classList.add("hidden");
  $("#app-screen").classList.remove("hidden");

  const nombre = state.user?.nombre_completo || state.user?.username || "";
  $("#user-name").textContent = nombre;
  $("#user-role").textContent = state.user?.rol || "";

  renderVista();
}

async function iniciarSesion(username, password) {
  const data = await api.login(username, password);
  api.setToken(data.token);
  state.user = data.usuario;
  await cargarTodo();
  mostrarApp();
}

async function restaurarSesion() {
  if (!api.token) {
    mostrarLogin();
    return;
  }

  try {
    state.user = await api.me();
    await cargarTodo();
    mostrarApp();
  } catch (error) {
    api.setToken(null);
    mostrarLogin(
      error instanceof ApiError && error.status === 401
        ? "La sesión expiró. Inicia sesión nuevamente."
        : "No se pudo conectar con la API. Verifica que el servidor esté encendido.",
    );
  }
}

function cerrarSesion() {
  api.setToken(null);
  state.user = null;
  state.pacientes = [];
  state.tratamientos = [];
  state.control = { fecha: "", signos: [], dxtx: [], panales: [] };
  mostrarLogin();
}

/* ------------------------------------------------------------------ */
/* Carga de datos                                                      */
/* ------------------------------------------------------------------ */

async function cargarTodo() {
  const [pacientes, tratamientos, control] = await Promise.all([
    api.pacientes(),
    api.tratamientos(),
    api.controlDiario(),
  ]);
  state.pacientes = Array.isArray(pacientes) ? pacientes : [];
  state.tratamientos = Array.isArray(tratamientos) ? tratamientos : [];
  state.control = control || state.control;
}

async function recargarVista() {
  if (state.cargando) return;
  state.cargando = true;
  renderVista();

  try {
    if (state.view === "pacientes") {
      state.pacientes = (await api.pacientes()) || [];
    } else if (state.view === "tratamientos") {
      state.tratamientos = (await api.tratamientos()) || [];
    } else {
      state.control = (await api.controlDiario()) || state.control;
    }
    renderVista();
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      cerrarSesion();
      mostrarLogin("La sesión expiró. Inicia sesión nuevamente.");
      return;
    }
    toast(error.message || "No se pudieron actualizar los datos.", "error");
  } finally {
    state.cargando = false;
    renderVista();
  }
}

/* ------------------------------------------------------------------ */
/* Navegación                                                          */
/* ------------------------------------------------------------------ */

function navegar(view) {
  state.view = view;
  state.busqueda = "";
  renderVista();
}

function renderVista() {
  $$(".nav-item").forEach((boton) => {
    boton.classList.toggle("active", boton.dataset.nav === state.view);
  });

  const contenedor = $("#view-container");
  if (!contenedor) return;

  if (state.view === "pacientes") {
    contenedor.innerHTML = vistaPacientes();
    enlazarPacientes();
  } else if (state.view === "tratamientos") {
    contenedor.innerHTML = vistaTratamientos();
    enlazarTratamientos();
  } else {
    contenedor.innerHTML = vistaControl();
    enlazarControl();
  }
}

/* ------------------------------------------------------------------ */
/* Vista: Pacientes                                                    */
/* ------------------------------------------------------------------ */

function tarjetaPaciente(paciente) {
  const estado = String(paciente.estado || "activo").toLowerCase();
  const colorEstado =
    estado === "activo"
      ? "bg-emerald-100 text-emerald-700"
      : estado === "hospitalizado"
        ? "bg-amber-100 text-amber-700"
        : "bg-slate-100 text-slate-600";

  const residencia = texto(paciente.tipo_residencia).replace(/^\w/, (c) => c.toUpperCase());
  const habitacion = paciente.habitacion
    ? `${texto(paciente.habitacion)}${paciente.cama ? ` · ${esc(paciente.cama)}` : ""}`
    : "Sin habitación";

  const imc = paciente.imc !== null && paciente.imc !== undefined ? Number(paciente.imc) : null;
  const imcTexto = imc !== null && !Number.isNaN(imc) ? imc.toFixed(2) : "—";
  const imcColor =
    imc === null || Number.isNaN(imc)
      ? "bg-slate-100 text-slate-600"
      : imc < 18.5
        ? "bg-amber-100 text-amber-700"
        : imc < 25
          ? "bg-emerald-100 text-emerald-700"
          : imc < 30
            ? "bg-amber-100 text-amber-700"
            : "bg-rose-100 text-rose-700";

  const tratamientos = Number(paciente.tratamientos_activos || 0);

  return `
    <article class="rounded-2xl bg-white p-4 shadow-sm border border-slate-100">
      <div class="flex items-start gap-3">
        <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700">
          ${iniciales(paciente.nombre, paciente.apellidos)}
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex items-start justify-between gap-2">
            <h3 class="text-base font-bold leading-tight text-slate-900">
              ${esc(texto(`${paciente.nombre || ""} ${paciente.apellidos || ""}`.trim()))}
            </h3>
            <span class="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${colorEstado}">
              ${esc(estado)}
            </span>
          </div>
          <p class="mt-0.5 text-xs text-slate-500">
            ${esc(residencia)} · ${esc(habitacion)}
          </p>
          <p class="mt-0.5 text-xs text-slate-400">
            ${esc(texto(paciente.documento))} · ${esc(texto(paciente.edad))} años · ${esc(texto(paciente.sexo))}
          </p>
        </div>
      </div>

      <div class="mt-3 grid grid-cols-3 gap-2">
        <div class="rounded-xl bg-slate-50 px-2 py-2 text-center">
          <p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Peso</p>
          <p class="text-sm font-bold text-slate-800">${decimal(paciente.peso_kg, " kg")}</p>
        </div>
        <div class="rounded-xl bg-slate-50 px-2 py-2 text-center">
          <p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Talla</p>
          <p class="text-sm font-bold text-slate-800">${decimal(paciente.talla_m, " m")}</p>
        </div>
        <div class="rounded-xl px-2 py-2 text-center ${imcColor}">
          <p class="text-[10px] font-semibold uppercase tracking-wide opacity-70">IMC</p>
          <p class="text-sm font-bold">${imcTexto}</p>
        </div>
      </div>

      ${
        paciente.diagnostico
          ? `<p class="mt-3 rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-600"><span class="font-bold text-slate-700">Diagnóstico:</span> ${esc(paciente.diagnostico)}</p>`
          : ""
      }

      ${
        paciente.alergias
          ? `<p class="mt-2 rounded-xl bg-rose-50 px-3 py-2 text-xs text-rose-700"><span class="font-bold">Alergias:</span> ${esc(paciente.alergias)}</p>`
          : ""
      }

      <div class="mt-3 flex items-center justify-between gap-2">
        <span class="rounded-full bg-blue-50 px-2.5 py-1 text-[11px] font-bold text-blue-700">
          ${tratamientos} tratamiento${tratamientos === 1 ? "" : "s"} activo${tratamientos === 1 ? "" : "s"}
        </span>
        <button type="button" data-signos="${Number(paciente.id)}"
                class="rounded-xl bg-blue-600 px-3.5 py-2 text-xs font-bold text-white shadow-sm active:bg-blue-700">
          + Signos vitales
        </button>
      </div>
    </article>
  `;
}

function vistaPacientes() {
  const filtro = state.busqueda.trim().toLowerCase();
  const lista = state.pacientes.filter((paciente) => {
    if (!filtro) return true;
    const textoCompleto = `${paciente.nombre || ""} ${paciente.apellidos || ""} ${paciente.documento || ""} ${paciente.habitacion || ""} ${paciente.diagnostico || ""}`.toLowerCase();
    return textoCompleto.includes(filtro);
  });

  const activos = state.pacientes.filter((p) => p.estado === "activo").length;

  return `
    <section class="space-y-3">
      <div class="rounded-2xl bg-slate-900 px-4 py-4 text-white shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[10px] font-bold uppercase tracking-[0.2em] text-blue-400">Pacientes</p>
            <p class="mt-1 text-2xl font-bold">${state.pacientes.length}</p>
          </div>
          <div class="text-right">
            <p class="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-400">Activos</p>
            <p class="mt-1 text-2xl font-bold">${activos}</p>
          </div>
          <button type="button" data-refresh
                  class="rounded-xl border border-slate-700 px-3 py-2 text-xs font-bold text-slate-200 active:bg-slate-800 ${state.cargando ? "opacity-50" : ""}">
            ${state.cargando ? "..." : "Actualizar"}
          </button>
        </div>
      </div>

      <input id="buscador" type="search" value="${esc(state.busqueda)}"
             placeholder="Buscar por nombre, documento o habitación"
             class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-500">

      <p class="px-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
        ${lista.length} resultado${lista.length === 1 ? "" : "s"}
      </p>

      <div class="space-y-3">
        ${lista.length ? lista.map(tarjetaPaciente).join("") : `<p class="rounded-2xl bg-white p-6 text-center text-sm text-slate-500">Sin pacientes que coincidan con la búsqueda.</p>`}
      </div>
    </section>
  `;
}

function enlazarPacientes() {
  $("[data-refresh]")?.addEventListener("click", recargarVista);

  const buscador = $("#buscador");
  if (buscador) {
    buscador.addEventListener(
      "input",
      debounce((event) => {
        state.busqueda = event.target.value;
        const contenedor = $("#view-container");
        contenedor.innerHTML = vistaPacientes();
        enlazarPacientes();
        const nuevo = $("#buscador");
        if (nuevo) {
          nuevo.focus();
          nuevo.setSelectionRange(nuevo.value.length, nuevo.value.length);
        }
      }, 200),
    );
  }

  $$("[data-signos]").forEach((boton) => {
    boton.addEventListener("click", () => {
      const paciente = state.pacientes.find((p) => Number(p.id) === Number(boton.dataset.signos));
      if (paciente) abrirModalSignos(paciente);
    });
  });
}

/* ------------------------------------------------------------------ */
/* Modal: Signos vitales                                               */
/* ------------------------------------------------------------------ */

function abrirModalSignos(paciente) {
  const nombre = `${paciente.nombre || ""} ${paciente.apellidos || ""}`.trim();

  abrirModal({
    titulo: "Signos vitales",
    subtitulo: nombre,
    textoBoton: "Guardar signos",
    contenido: `
      <input type="hidden" name="paciente_id" value="${Number(paciente.id)}">

      <div class="grid grid-cols-2 gap-3">
        <label class="block">
          <span class="mb-1 block text-xs font-bold text-slate-600">Presión sistólica</span>
          <input name="presion_sistolica" type="number" inputmode="numeric" min="40" max="300"
                 class="campo" placeholder="120">
        </label>
        <label class="block">
          <span class="mb-1 block text-xs font-bold text-slate-600">Presión diastólica</span>
          <input name="presion_diastolica" type="number" inputmode="numeric" min="20" max="200"
                 class="campo" placeholder="80">
        </label>
        <label class="block">
          <span class="mb-1 block text-xs font-bold text-slate-600">BPM</span>
          <input name="bpm" type="number" inputmode="numeric" min="20" max="300"
                 class="campo" placeholder="78">
        </label>
        <label class="block">
          <span class="mb-1 block text-xs font-bold text-slate-600">Saturación O₂ (%)</span>
          <input name="saturacion_o2" type="number" inputmode="numeric" min="0" max="100"
                 class="campo" placeholder="96">
        </label>
        <label class="block">
          <span class="mb-1 block text-xs font-bold text-slate-600">Frecuencia resp.</span>
          <input name="frecuencia_respiratoria" type="number" inputmode="numeric" min="4" max="80"
                 class="campo" placeholder="18">
        </label>
        <label class="block">
          <span class="mb-1 block text-xs font-bold text-slate-600">Temperatura (°C)</span>
          <input name="temperatura" type="number" inputmode="decimal" step="0.1" min="30" max="45"
                 class="campo" placeholder="36.5">
        </label>
      </div>

      <label class="block">
        <span class="mb-1 block text-xs font-bold text-slate-600">Observaciones</span>
        <textarea name="observaciones" rows="2" maxlength="255"
                  class="campo" placeholder="Opcional"></textarea>
      </label>

      <p class="text-[11px] text-slate-400">Registra al menos un signo vital. La presión requiere sistólica y diastólica juntas.</p>
    `,
    onSubmit: async (formData) => {
      const payload = { paciente_id: Number(formData.get("paciente_id")) };
      const numericos = [
        "presion_sistolica",
        "presion_diastolica",
        "bpm",
        "saturacion_o2",
        "frecuencia_respiratoria",
        "temperatura",
      ];
      numericos.forEach((campo) => {
        const valor = String(formData.get(campo) || "").trim();
        payload[campo] = valor === "" ? null : Number(valor);
      });
      const observaciones = String(formData.get("observaciones") || "").trim();
      payload.observaciones = observaciones || null;

      await api.crearSignos(payload);
      toast("Signos vitales registrados.", "success");
      await recargarVista();
    },
  });
}

/* ------------------------------------------------------------------ */
/* Vista: Tratamientos                                                 */
/* ------------------------------------------------------------------ */

function tarjetaTratamiento(tratamiento) {
  const estado = String(tratamiento.estado || "activo").toLowerCase();
  const colorEstado =
    estado === "activo"
      ? "bg-emerald-100 text-emerald-700"
      : estado === "suspendido"
        ? "bg-amber-100 text-amber-700"
        : "bg-slate-100 text-slate-600";

  const medicamento = `${texto(tratamiento.medicamento, "")}${
    tratamiento.concentracion ? ` ${tratamiento.concentracion}` : ""
  }`.trim();

  const dosis = `${decimal(tratamiento.dosis)}${tratamiento.unidad_dosis ? ` ${tratamiento.unidad_dosis}` : ""}`;
  const frecuencia = tratamiento.frecuencia_horas
    ? `Cada ${tratamiento.frecuencia_horas} h`
    : "PRN";

  const activo = estado === "activo";

  return `
    <article class="rounded-2xl bg-white p-4 shadow-sm border border-slate-100">
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <h3 class="text-sm font-bold leading-tight text-slate-900">${esc(texto(tratamiento.paciente))}</h3>
          <p class="mt-0.5 text-xs text-slate-500">
            ${esc(texto(tratamiento.tipo_residencia).replace(/^\w/, (c) => c.toUpperCase()))}${
              tratamiento.habitacion ? ` · Hab. ${esc(tratamiento.habitacion)}` : ""
            }
          </p>
        </div>
        <span class="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${colorEstado}">
          ${esc(estado)}
        </span>
      </div>

      <div class="mt-3 rounded-xl bg-blue-50 px-3 py-2">
        <p class="text-sm font-bold text-blue-900">${esc(medicamento || "Medicamento")}</p>
        <p class="mt-0.5 text-xs text-blue-700">
          ${esc(dosis)} · ${esc(texto(tratamiento.via_administracion).replace(/^\w/, (c) => c.toUpperCase()))} · ${esc(frecuencia)}
        </p>
      </div>

      <div class="mt-2 grid grid-cols-2 gap-2 text-[11px] text-slate-500">
        <p><span class="font-bold text-slate-600">Horarios:</span> ${esc(texto(tratamiento.horarios))}</p>
        <p><span class="font-bold text-slate-600">Inicio:</span> ${esc(texto(tratamiento.fecha_inicio))}</p>
      </div>

      ${
        tratamiento.indicaciones
          ? `<p class="mt-2 rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-600">${esc(tratamiento.indicaciones)}</p>`
          : ""
      }

      <div class="mt-3 flex items-center justify-between gap-2">
        <span class="text-[11px] text-slate-400">Prescrito por: ${esc(texto(tratamiento.prescrito_por))}</span>
        <button type="button" data-administrar="${Number(tratamiento.id)}"
                ${activo ? "" : "disabled"}
                class="rounded-xl px-3.5 py-2 text-xs font-bold text-white shadow-sm ${
                  activo
                    ? "bg-emerald-600 active:bg-emerald-700"
                    : "bg-slate-300 cursor-not-allowed"
                }">
          ${activo ? "Administrar" : "No disponible"}
        </button>
      </div>
    </article>
  `;
}

function vistaTratamientos() {
  const filtro = state.busqueda.trim().toLowerCase();
  const lista = state.tratamientos.filter((tratamiento) => {
    if (!filtro) return true;
    const textoCompleto = `${tratamiento.paciente || ""} ${tratamiento.medicamento || ""} ${tratamiento.estado || ""}`.toLowerCase();
    return textoCompleto.includes(filtro);
  });

  const activos = state.tratamientos.filter((t) => t.estado === "activo").length;

  return `
    <section class="space-y-3">
      <div class="rounded-2xl bg-slate-900 px-4 py-4 text-white shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[10px] font-bold uppercase tracking-[0.2em] text-blue-400">Tratamientos</p>
            <p class="mt-1 text-2xl font-bold">${state.tratamientos.length}</p>
          </div>
          <div class="text-right">
            <p class="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-400">Activos</p>
            <p class="mt-1 text-2xl font-bold">${activos}</p>
          </div>
          <button type="button" data-refresh
                  class="rounded-xl border border-slate-700 px-3 py-2 text-xs font-bold text-slate-200 active:bg-slate-800 ${state.cargando ? "opacity-50" : ""}">
            ${state.cargando ? "..." : "Actualizar"}
          </button>
        </div>
      </div>

      <input id="buscador" type="search" value="${esc(state.busqueda)}"
             placeholder="Buscar por paciente o medicamento"
             class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-500">

      <p class="px-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
        ${lista.length} resultado${lista.length === 1 ? "" : "s"}
      </p>

      <div class="space-y-3">
        ${lista.length ? lista.map(tarjetaTratamiento).join("") : `<p class="rounded-2xl bg-white p-6 text-center text-sm text-slate-500">Sin tratamientos que coincidan con la búsqueda.</p>`}
      </div>
    </section>
  `;
}

function enlazarTratamientos() {
  $("[data-refresh]")?.addEventListener("click", recargarVista);

  const buscador = $("#buscador");
  if (buscador) {
    buscador.addEventListener(
      "input",
      debounce((event) => {
        state.busqueda = event.target.value;
        const contenedor = $("#view-container");
        contenedor.innerHTML = vistaTratamientos();
        enlazarTratamientos();
        const nuevo = $("#buscador");
        if (nuevo) {
          nuevo.focus();
          nuevo.setSelectionRange(nuevo.value.length, nuevo.value.length);
        }
      }, 200),
    );
  }

  $$("[data-administrar]").forEach((boton) => {
    boton.addEventListener("click", () => {
      const tratamiento = state.tratamientos.find(
        (t) => Number(t.id) === Number(boton.dataset.administrar),
      );
      if (tratamiento) abrirModalAdministracion(tratamiento);
    });
  });
}

/* ------------------------------------------------------------------ */
/* Modal: Administración de medicamento                                */
/* ------------------------------------------------------------------ */

async function abrirModalAdministracion(tratamiento) {
  let lotes = [];
  try {
    lotes = (await api.inventarioLotes(tratamiento.medicamento_id)) || [];
  } catch (error) {
    toast(error.message || "No se pudieron cargar los lotes.", "error");
  }

  const opcionesLotes = lotes.length
    ? lotes
        .map(
          (lote) =>
            `<option value="${Number(lote.id)}">Lote ${esc(lote.codigo_lote)} · ${esc(lote.cantidad_disponible)} disp. · cad. ${esc(lote.fecha_caducidad)}</option>`,
        )
        .join("")
    : `<option value="">Sin lotes disponibles</option>`;

  const dosisSugerida =
    tratamiento.dosis !== null && tratamiento.dosis !== undefined ? Number(tratamiento.dosis) : "";

  abrirModal({
    titulo: "Registrar administración",
    subtitulo: `${tratamiento.paciente || ""} · ${tratamiento.medicamento || ""}`,
    textoBoton: "Registrar administración",
    contenido: `
      <input type="hidden" name="tratamiento_id" value="${Number(tratamiento.id)}">

      <div class="rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-600">
        <p><span class="font-bold">Medicamento:</span> ${esc(texto(tratamiento.medicamento))} ${esc(texto(tratamiento.concentracion, ""))}</p>
        <p class="mt-0.5"><span class="font-bold">Pauta:</span> ${esc(decimal(tratamiento.dosis))} ${esc(texto(tratamiento.unidad_dosis, ""))} · ${esc(texto(tratamiento.via_administracion))} · ${tratamiento.frecuencia_horas ? `cada ${esc(tratamiento.frecuencia_horas)} h` : "PRN"}</p>
      </div>

      <label class="block">
        <span class="mb-1 block text-xs font-bold text-slate-600">Lote a descontar</span>
        <select name="lote_id" class="campo">
          <option value="">No descontar inventario</option>
          ${opcionesLotes}
        </select>
      </label>

      <div class="grid grid-cols-2 gap-3">
        <label class="block">
          <span class="mb-1 block text-xs font-bold text-slate-600">Dosis aplicada</span>
          <input name="dosis_aplicada" type="number" inputmode="decimal" step="0.01" min="0"
                 value="${esc(dosisSugerida)}" class="campo">
        </label>
        <label class="block">
          <span class="mb-1 block text-xs font-bold text-slate-600">Estado</span>
          <select name="estado" class="campo">
            <option value="administrado">Administrado</option>
            <option value="retrasado">Retrasado</option>
            <option value="omitido">Omitido</option>
          </select>
        </label>
      </div>

      <label class="block">
        <span class="mb-1 block text-xs font-bold text-slate-600">Vía de administración</span>
        <select name="via_administracion" class="campo">
          <option value="">Usar la del tratamiento (${esc(texto(tratamiento.via_administracion))})</option>
          <option value="oral">Oral</option>
          <option value="venosa">Venosa</option>
          <option value="intramuscular">Intramuscular</option>
          <option value="subcutanea">Subcutánea</option>
          <option value="topica">Tópica</option>
          <option value="rectal">Rectal</option>
          <option value="inhalatoria">Inhalatoria</option>
          <option value="sublingual">Sublingual</option>
          <option value="otra">Otra</option>
        </select>
      </label>

      <label class="block">
        <span class="mb-1 block text-xs font-bold text-slate-600">Observaciones</span>
        <textarea name="observaciones" rows="2" maxlength="255" class="campo" placeholder="Opcional"></textarea>
      </label>

      <p class="text-[11px] text-slate-400">Si seleccionas un lote, se descuenta 1 unidad de presentación del inventario.</p>
    `,
    onSubmit: async (formData) => {
      const estado = String(formData.get("estado") || "administrado");
      const loteValor = String(formData.get("lote_id") || "").trim();
      const dosisValor = String(formData.get("dosis_aplicada") || "").trim();
      const via = String(formData.get("via_administracion") || "").trim();
      const observaciones = String(formData.get("observaciones") || "").trim();

      const payload = {
        tratamiento_id: Number(formData.get("tratamiento_id")),
        horario_id: null,
        lote_id: loteValor ? Number(loteValor) : null,
        dosis_aplicada: dosisValor === "" ? 0 : Number(dosisValor),
        via_administracion: via || null,
        estado,
        observaciones: observaciones || null,
      };

      await api.administrar(payload);
      toast("Administración registrada.", "success");
      await recargarVista();
    },
  });
}

/* ------------------------------------------------------------------ */
/* Vista: Control diario                                               */
/* ------------------------------------------------------------------ */

const TABS = [
  { id: "signos", label: "Signos" },
  { id: "dxtx", label: "DXTX" },
  { id: "panales", label: "Pañales" },
];

function filaSigno(item) {
  const presion =
    item.presion_sistolica !== null && item.presion_diastolica !== null
      ? `${esc(item.presion_sistolica)}/${esc(item.presion_diastolica)}`
      : "—";
  return `
    <article class="rounded-2xl bg-white p-3 shadow-sm border border-slate-100">
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <p class="text-sm font-bold text-slate-900">${esc(texto(item.paciente))}</p>
          <p class="text-[11px] text-slate-500">${esc(texto(item.habitacion, "Sin habitación"))} · ${esc(hora(item.fecha_hora))}</p>
        </div>
        <span class="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-bold text-blue-700">${presion} mmHg</span>
      </div>
      <div class="mt-2 grid grid-cols-4 gap-1.5 text-center">
        <div class="rounded-lg bg-slate-50 py-1.5"><p class="text-[9px] uppercase text-slate-400">BPM</p><p class="text-xs font-bold">${esc(texto(item.bpm))}</p></div>
        <div class="rounded-lg bg-slate-50 py-1.5"><p class="text-[9px] uppercase text-slate-400">SatO₂</p><p class="text-xs font-bold">${item.saturacion_o2 !== null ? `${esc(item.saturacion_o2)}%` : "—"}</p></div>
        <div class="rounded-lg bg-slate-50 py-1.5"><p class="text-[9px] uppercase text-slate-400">FR</p><p class="text-xs font-bold">${esc(texto(item.frecuencia_respiratoria))}</p></div>
        <div class="rounded-lg bg-slate-50 py-1.5"><p class="text-[9px] uppercase text-slate-400">Temp</p><p class="text-xs font-bold">${item.temperatura !== null ? `${esc(item.temperatura)}°` : "—"}</p></div>
      </div>
      ${item.observaciones ? `<p class="mt-2 text-[11px] text-slate-500">${esc(item.observaciones)}</p>` : ""}
      <p class="mt-1 text-[10px] text-slate-400">Registró: ${esc(texto(item.personal))}</p>
    </article>
  `;
}

function filaDxtx(item) {
  return `
    <article class="rounded-2xl bg-white p-3 shadow-sm border border-slate-100">
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <p class="text-sm font-bold text-slate-900">${esc(texto(item.paciente))}</p>
          <p class="text-[11px] text-slate-500">${esc(texto(item.tipo).replace(/^\w/, (c) => c.toUpperCase()))} · ${esc(hora(item.fecha_hora))}</p>
        </div>
        <span class="rounded-full bg-violet-50 px-2.5 py-1 text-xs font-bold text-violet-700">${esc(texto(item.valor_mg_dl))} mg/dL</span>
      </div>
      ${item.insulina_aplicada ? `<p class="mt-2 rounded-lg bg-slate-50 px-2 py-1.5 text-[11px] text-slate-600">Insulina aplicada: <span class="font-bold">${esc(item.insulina_aplicada)}</span></p>` : ""}
      ${item.observaciones ? `<p class="mt-2 text-[11px] text-slate-500">${esc(item.observaciones)}</p>` : ""}
      <p class="mt-1 text-[10px] text-slate-400">Registró: ${esc(texto(item.personal))}</p>
    </article>
  `;
}

function filaPanales(item) {
  return `
    <article class="rounded-2xl bg-white p-3 shadow-sm border border-slate-100">
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <p class="text-sm font-bold text-slate-900">${esc(texto(item.paciente))}</p>
          <p class="text-[11px] text-slate-500">${esc(hora(item.fecha_hora))}</p>
        </div>
        <span class="rounded-full bg-teal-50 px-2.5 py-1 text-[11px] font-bold text-teal-700">${esc(texto(item.tipo).replace(/^\w/, (c) => c.toUpperCase()))}</span>
      </div>
      ${item.observaciones ? `<p class="mt-2 text-[11px] text-slate-500">${esc(item.observaciones)}</p>` : ""}
      <p class="mt-1 text-[10px] text-slate-400">Registró: ${esc(texto(item.personal))}</p>
    </article>
  `;
}

function vistaControl() {
  const control = state.control || {};
  const datos = control[state.controlTab] || [];
  const totales = {
    signos: (control.signos || []).length,
    dxtx: (control.dxtx || []).length,
    panales: (control.panales || []).length,
  };

  const render = {
    signos: filaSigno,
    dxtx: filaDxtx,
    panales: filaPanales,
  }[state.controlTab];

  return `
    <section class="space-y-3">
      <div class="rounded-2xl bg-slate-900 px-4 py-4 text-white shadow-lg">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-[10px] font-bold uppercase tracking-[0.2em] text-blue-400">Control de hoy</p>
            <p class="mt-1 text-sm font-bold">${esc(fechaLarga(control.fecha))}</p>
          </div>
          <button type="button" data-refresh
                  class="rounded-xl border border-slate-700 px-3 py-2 text-xs font-bold text-slate-200 active:bg-slate-800 ${state.cargando ? "opacity-50" : ""}">
            ${state.cargando ? "..." : "Actualizar"}
          </button>
        </div>
        <div class="mt-3 grid grid-cols-3 gap-2 text-center">
          <div class="rounded-xl bg-slate-800 py-2"><p class="text-lg font-bold">${totales.signos}</p><p class="text-[10px] uppercase tracking-wide text-slate-400">Signos</p></div>
          <div class="rounded-xl bg-slate-800 py-2"><p class="text-lg font-bold">${totales.dxtx}</p><p class="text-[10px] uppercase tracking-wide text-slate-400">DXTX</p></div>
          <div class="rounded-xl bg-slate-800 py-2"><p class="text-lg font-bold">${totales.panales}</p><p class="text-[10px] uppercase tracking-wide text-slate-400">Pañales</p></div>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-2">
        ${TABS.map(
          (tab) => `
          <button type="button" data-tab="${tab.id}"
                  class="rounded-xl px-2 py-2.5 text-xs font-bold ${
                    state.controlTab === tab.id
                      ? "bg-blue-600 text-white shadow"
                      : "bg-white text-slate-600 border border-slate-200"
                  }">
            ${tab.label} (${totales[tab.id]})
          </button>`,
        ).join("")}
      </div>

      <button type="button" data-nuevo-signo
              class="w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-blue-600/20 active:scale-[0.99]">
        + Registrar signos vitales
      </button>

      <div class="space-y-3">
        ${datos.length ? datos.map(render).join("") : `<p class="rounded-2xl bg-white p-6 text-center text-sm text-slate-500">Sin registros de ${esc(TABS.find((t) => t.id === state.controlTab)?.label || "")} hoy.</p>`}
      </div>
    </section>
  `;
}

function enlazarControl() {
  $("[data-refresh]")?.addEventListener("click", recargarVista);

  $$("[data-tab]").forEach((boton) => {
    boton.addEventListener("click", () => {
      state.controlTab = boton.dataset.tab;
      renderVista();
    });
  });

  $("[data-nuevo-signo]")?.addEventListener("click", () => {
    const activos = state.pacientes.filter((p) => p.estado === "activo");
    if (!activos.length) {
      toast("No hay pacientes activos para registrar signos.", "error");
      return;
    }
    abrirModalSeleccionPaciente(activos);
  });
}

function abrirModalSeleccionPaciente(pacientes) {
  const opciones = pacientes
    .map(
      (paciente) =>
        `<option value="${Number(paciente.id)}">${esc(`${paciente.nombre || ""} ${paciente.apellidos || ""}`.trim())}${paciente.habitacion ? ` · Hab. ${esc(paciente.habitacion)}` : ""}</option>`,
    )
    .join("");

  abrirModal({
    titulo: "Signos vitales",
    subtitulo: "Selecciona al paciente",
    textoBoton: "Continuar",
    contenido: `
      <label class="block">
        <span class="mb-1 block text-xs font-bold text-slate-600">Paciente</span>
        <select name="paciente_id" class="campo">${opciones}</select>
      </label>
    `,
    onSubmit: async (formData) => {
      const paciente = pacientes.find(
        (p) => Number(p.id) === Number(formData.get("paciente_id")),
      );
      if (!paciente) return false;
      cerrarModal();
      setTimeout(() => abrirModalSignos(paciente), 60);
      return false;
    },
  });
}

/* ------------------------------------------------------------------ */
/* Arranque                                                            */
/* ------------------------------------------------------------------ */

function enlazarGlobales() {
  $("#login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const username = $("#username").value.trim();
    const password = $("#password").value;
    const boton = $("#login-button");
    const error = $("#login-error");

    if (!username || !password) {
      error.textContent = "Escribe usuario y contraseña.";
      error.classList.remove("hidden");
      return;
    }

    error.classList.add("hidden");
    boton.disabled = true;
    boton.textContent = "Entrando...";

    try {
      await iniciarSesion(username, password);
      $("#login-form").reset();
    } catch (err) {
      error.textContent =
        err instanceof ApiError
          ? err.message
          : "No se pudo iniciar sesión. Verifica la conexión.";
      error.classList.remove("hidden");
    } finally {
      boton.disabled = false;
      boton.textContent = "Entrar";
    }
  });

  $("#logout-button").addEventListener("click", cerrarSesion);

  $$(".nav-item").forEach((boton) => {
    boton.addEventListener("click", () => navegar(boton.dataset.nav));
  });
}

enlazarGlobales();
restaurarSesion();
