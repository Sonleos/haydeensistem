"""Panel de administración de Haydeén Sistema.

Interfaz de escritorio preparada para empaquetarse con PyInstaller.
"""

from __future__ import annotations

import os
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk
from typing import Any

import customtkinter as ctk
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api").rstrip("/")

# Paleta visual (claro, oscuro)
BG = ("#F1F5F9", "#0F172A")
SURFACE = ("#FFFFFF", "#1E293B")
SURFACE_ALT = ("#F8FAFC", "#111827")
BORDER = ("#E2E8F0", "#334155")
TEXT = ("#0F172A", "#F8FAFC")
MUTED = ("#64748B", "#94A3B8")
ACCENT = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
SUCCESS = "#16A34A"
DANGER = "#DC2626"
SIDEBAR = ("#0F172A", "#020617")
SIDEBAR_TEXT = "#CBD5E1"

NAV_ITEMS = (
    ("dashboard", "Panel"),
    ("pacientes", "Pacientes"),
    ("personal", "Personal y turnos"),
    ("inventario", "Inventario"),
    ("tratamientos", "Tratamientos"),
    ("signos", "Control diario"),
    ("configuracion", "Configuración"),
)

VIEW_META = {
    "dashboard": ("Panel administrativo", "Resumen operativo del geriátrico"),
    "pacientes": ("Pacientes", "Residenciados y ambulatorios"),
    "personal": ("Personal y turnos", "Roles, disponibilidad y horarios"),
    "inventario": ("Inventario", "Medicamentos, lotes y surtido"),
    "tratamientos": ("Tratamientos", "Dosis, vías y horarios de administración"),
    "signos": ("Control diario", "Signos vitales, DXTX y control de pañales"),
    "configuracion": ("Configuración", "Parámetros del sistema y usuarios"),
}

VIEW_NOTES = {
    "pacientes": (
        "Alta y edición de residentes y pacientes ambulatorios.",
        "Cálculo automático de IMC a partir de peso y talla.",
        "Expediente con alergias, diagnóstico y contacto familiar.",
    ),
    "personal": (
        "Administración de roles y estado activo/libre.",
        "Programación de turnos matutino, vespertino y nocturno.",
        "Control de asistencia y disponibilidad del personal.",
    ),
    "inventario": (
        "Catálogo de medicamentos y control por lotes.",
        "Entradas, salidas, ajustes y alertas de caducidad.",
        "Alertas de stock mínimo y surtido a pacientes.",
    ),
    "tratamientos": (
        "Asignación de medicamentos a cada paciente.",
        "Dosis, frecuencia y vías de administración.",
        "Horarios de medicación y registro de administraciones.",
    ),
    "signos": (
        "Registro de presión arterial, BPM, saturación y respiración.",
        "Controles de glucosa (DXTX) e insulina aplicada.",
        "Control de pañales por turno y observaciones.",
    ),
    "configuracion": (
        "Gestión de usuarios y credenciales.",
        "Parámetros generales del sistema.",
        "Respaldo y mantenimiento de la base de datos.",
    ),
}

MODULE_ENDPOINTS = {
    "pacientes": "/pacientes",
    "personal": "/personal",
    "inventario": "/inventario",
    "tratamientos": "/tratamientos",
    "signos": "/control-diario",
}

MODULE_TITLES = {
    "pacientes": "Pacientes registrados",
    "personal": "Personal y turnos",
    "inventario": "Inventario de medicamentos",
    "tratamientos": "Tratamientos asignados",
    "signos": "Control diario de hoy",
}

MODULE_COLUMNS = {
    "pacientes": (
        ("documento", "Documento", 105, "w"),
        ("paciente", "Paciente", 190, "w"),
        ("residencia", "Residencia", 115, "w"),
        ("habitacion", "Habitación", 100, "w"),
        ("edad", "Edad", 60, "center"),
        ("peso", "Peso", 75, "center"),
        ("talla", "Talla", 70, "center"),
        ("imc", "IMC", 65, "center"),
        ("tratamientos", "Tratamientos", 105, "center"),
        ("estado", "Estado", 90, "center"),
        ("diagnostico", "Diagnóstico", 260, "w"),
    ),
    "personal": (
        ("documento", "Documento", 105, "w"),
        ("nombre", "Nombre", 190, "w"),
        ("rol", "Rol", 110, "w"),
        ("estado", "Estado", 90, "center"),
        ("turno", "Turno de hoy", 190, "w"),
        ("turno_estado", "Estado turno", 110, "center"),
        ("telefono", "Teléfono", 110, "w"),
        ("email", "Correo", 200, "w"),
    ),
    "inventario": (
        ("medicamento", "Medicamento", 190, "w"),
        ("concentracion", "Concentración", 120, "w"),
        ("presentacion", "Presentación", 120, "w"),
        ("stock_minimo", "Stock mínimo", 105, "center"),
        ("disponible", "Disponible", 95, "center"),
        ("lotes", "Lotes", 65, "center"),
        ("caducidad", "Próxima caducidad", 130, "center"),
        ("alerta", "Alerta", 80, "center"),
    ),
    "tratamientos": (
        ("paciente", "Paciente", 180, "w"),
        ("medicamento", "Medicamento", 180, "w"),
        ("dosis", "Dosis", 100, "center"),
        ("via", "Vía", 110, "w"),
        ("frecuencia", "Frecuencia", 100, "center"),
        ("horarios", "Horarios", 140, "w"),
        ("inicio", "Inicio", 130, "center"),
        ("fin", "Fin", 130, "center"),
        ("estado", "Estado", 95, "center"),
        ("prescrito", "Prescrito por", 150, "w"),
    ),
}

CONTROL_COLUMNS = {
    "signos": (
        ("hora", "Hora", 110, "center"),
        ("paciente", "Paciente", 180, "w"),
        ("habitacion", "Habitación", 90, "center"),
        ("ta", "Presión arterial", 120, "center"),
        ("bpm", "BPM", 60, "center"),
        ("sat", "SatO₂", 70, "center"),
        ("fr", "FR", 60, "center"),
        ("temp", "Temp.", 70, "center"),
        ("personal", "Registrado por", 170, "w"),
        ("obs", "Observaciones", 220, "w"),
    ),
    "dxtx": (
        ("hora", "Hora", 110, "center"),
        ("paciente", "Paciente", 190, "w"),
        ("valor", "Glucosa mg/dL", 120, "center"),
        ("tipo", "Tipo", 110, "center"),
        ("insulina", "Insulina", 90, "center"),
        ("personal", "Registrado por", 170, "w"),
        ("obs", "Observaciones", 240, "w"),
    ),
    "panales": (
        ("hora", "Hora", 110, "center"),
        ("paciente", "Paciente", 200, "w"),
        ("tipo", "Tipo", 110, "center"),
        ("personal", "Registrado por", 180, "w"),
        ("obs", "Observaciones", 300, "w"),
    ),
}


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    def __init__(self, base_url: str = API_BASE_URL) -> None:
        self.base_url = base_url
        self.session = requests.Session()

    def request(
        self,
        method: str,
        path: str,
        token: str | None = None,
        **kwargs: Any,
    ) -> Any:
        headers = dict(kwargs.pop("headers", {}))
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = self.session.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                timeout=10,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise ApiError(
                "No se pudo conectar con la API. Verifica que Uvicorn esté en ejecución."
            ) from exc

        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code >= 400:
            detail = data.get("detail") if isinstance(data, dict) else None
            if isinstance(detail, list):
                detail = "; ".join(
                    str(item.get("msg", item)) if isinstance(item, dict) else str(item)
                    for item in detail
                )
            raise ApiError(
                str(detail or f"Error HTTP {response.status_code}"),
                response.status_code,
            )

        return data


class AdminPanel(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Haydeén Sistema · Administración")
        self.geometry("1220x780")
        self.minsize(1040, 680)
        self.configure(fg_color=BG)

        self.api = ApiClient()
        self.token: str | None = None
        self.user: dict[str, Any] = {}
        self.active_view = "dashboard"

        self._stat_labels: dict[str, ctk.CTkLabel] = {}
        self._status_label: ctk.CTkLabel | None = None
        self._login_button: ctk.CTkButton | None = None
        self._login_error: ctk.CTkLabel | None = None
        self._username_entry: ctk.CTkEntry | None = None
        self._password_entry: ctk.CTkEntry | None = None

        self._module_tree: ttk.Treeview | None = None
        self._module_table_frame: ctk.CTkFrame | None = None
        self._module_status: ctk.CTkLabel | None = None
        self._module_data: Any = None
        self._control_tab = "Signos vitales"

        self._configure_table_style()
        self.show_login()

    # ------------------------------------------------------------------
    # Utilidades de interfaz
    # ------------------------------------------------------------------

    def _clear(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        self._stat_labels.clear()
        self._status_label = None
        self._login_button = None
        self._login_error = None
        self._username_entry = None
        self._password_entry = None
        self._module_tree = None
        self._module_table_frame = None
        self._module_status = None
        self._module_data = None

    def _set_login_error(self, message: str) -> None:
        if self._login_error is not None:
            self._login_error.configure(text=message)

    def _safe_after(self, callback, *args: Any) -> None:
        """Programa una actualización de UI sin fallar si la ventana se cerró."""
        try:
            self.after(0, callback, *args)
        except (RuntimeError, tk.TclError):
            pass

    def _configure_table_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Admin.Treeview",
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground="#0F172A",
            rowheight=34,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Admin.Treeview.Heading",
            background="#F1F5F9",
            foreground="#475569",
            relief="flat",
            padding=(8, 8),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Admin.Treeview",
            background=[("selected", "#DBEAFE")],
            foreground=[("selected", "#1D4ED8")],
        )
        style.map(
            "Admin.Treeview.Heading",
            background=[("active", "#E2E8F0")],
        )

    # ------------------------------------------------------------------
    # Inicio de sesión
    # ------------------------------------------------------------------

    def show_login(self, message: str | None = None) -> None:
        self.token = None
        self.user = {}
        self._clear()

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=0, column=0, padx=24, pady=24)

        card = ctk.CTkFrame(
            wrapper,
            corner_radius=20,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )
        card.pack()

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(padx=40, pady=36)

        ctk.CTkLabel(
            body,
            text="HAYDEÉN",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=ACCENT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            body,
            text="Sistema de Gestión Geriátrica",
            font=ctk.CTkFont(size=13),
            text_color=MUTED,
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            body,
            text="  ADMINISTRACIÓN  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#1D4ED8",
            fg_color="#DBEAFE",
            corner_radius=6,
        ).pack(anchor="w", pady=(16, 26))

        ctk.CTkLabel(
            body,
            text="Usuario",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT,
        ).pack(anchor="w")

        self._username_entry = ctk.CTkEntry(
            body,
            width=340,
            height=44,
            corner_radius=10,
            placeholder_text="Ingresa tu usuario",
            font=ctk.CTkFont(size=13),
        )
        self._username_entry.pack(fill="x", pady=(6, 16))

        ctk.CTkLabel(
            body,
            text="Contraseña",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT,
        ).pack(anchor="w")

        self._password_entry = ctk.CTkEntry(
            body,
            width=340,
            height=44,
            corner_radius=10,
            placeholder_text="Ingresa tu contraseña",
            show="*",
            font=ctk.CTkFont(size=13),
        )
        self._password_entry.pack(fill="x", pady=(6, 10))

        self._login_error = ctk.CTkLabel(
            body,
            text=message or "",
            font=ctk.CTkFont(size=12),
            text_color=DANGER,
            wraplength=340,
            justify="left",
        )
        self._login_error.pack(anchor="w", pady=(0, 10))

        self._login_button = ctk.CTkButton(
            body,
            text="Iniciar sesión",
            width=340,
            height=46,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._submit_login,
        )
        self._login_button.pack(fill="x", pady=(2, 18))

        ctk.CTkLabel(
            body,
            text=f"API: {self.api.base_url}",
            font=ctk.CTkFont(size=10),
            text_color=MUTED,
        ).pack(anchor="w")

        for entry in (self._username_entry, self._password_entry):
            entry.bind("<Return>", lambda _event: self._submit_login())

        self._username_entry.focus_set()

    def _submit_login(self) -> None:
        if self._login_button is None:
            return
        if str(self._login_button.cget("state")) == "disabled":
            return

        username = self._username_entry.get().strip() if self._username_entry else ""
        password = self._password_entry.get() if self._password_entry else ""

        if not username or not password:
            self._set_login_error("Ingresa usuario y contraseña.")
            return

        self._set_login_error("")
        self._login_button.configure(state="disabled", text="Verificando...")

        threading.Thread(
            target=self._login_worker,
            args=(username, password),
            daemon=True,
        ).start()

    def _login_worker(self, username: str, password: str) -> None:
        try:
            data = self.api.request(
                "POST",
                "/auth/login",
                json={"username": username, "password": password},
            )
        except ApiError as exc:
            self._safe_after(self._login_failed, str(exc))
            return
        except Exception as exc:
            self._safe_after(self._login_failed, f"Error inesperado: {exc}")
            return

        self._safe_after(self._login_ok, data)

    def _login_ok(self, data: dict[str, Any]) -> None:
        token = data.get("token")
        if not token:
            self._login_failed("La API no devolvió un token válido.")
            return

        self.token = token
        self.user = data.get("usuario", {})
        self.show_dashboard("dashboard")

    def _login_failed(self, message: str) -> None:
        if self._login_button is not None:
            self._login_button.configure(state="normal", text="Iniciar sesión")
        self._set_login_error(message)

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def show_dashboard(self, view: str = "dashboard") -> None:
        if view not in VIEW_META:
            view = "dashboard"

        self.active_view = view
        self._clear()

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main(view)

        if view == "dashboard" and self.token:
            self.refresh_stats()

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=SIDEBAR)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=22, pady=(28, 24))

        ctk.CTkLabel(
            brand,
            text="HAYDEÉN",
            font=ctk.CTkFont(size=25, weight="bold"),
            text_color="#FFFFFF",
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand,
            text="Administración",
            font=ctk.CTkFont(size=11),
            text_color=SIDEBAR_TEXT,
        ).pack(anchor="w", pady=(2, 0))

        nav = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav.pack(fill="x", padx=14)

        for key, label in NAV_ITEMS:
            is_active = key == self.active_view
            ctk.CTkButton(
                nav,
                text=f"  {label}",
                anchor="w",
                height=42,
                corner_radius=10,
                font=ctk.CTkFont(size=13, weight="bold" if is_active else "normal"),
                fg_color=ACCENT if is_active else "transparent",
                hover_color=ACCENT_HOVER if is_active else "#1E293B",
                text_color="#FFFFFF" if is_active else SIDEBAR_TEXT,
                command=lambda selected=key: self.show_dashboard(selected),
            ).pack(fill="x", pady=3)

        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=18, pady=20)

        name = self.user.get("nombre_completo") or self.user.get("username") or "Administrador"
        role = str(self.user.get("rol", "admin")).capitalize()

        ctk.CTkLabel(
            footer,
            text=name,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F8FAFC",
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            footer,
            text=role,
            font=ctk.CTkFont(size=11),
            text_color=SIDEBAR_TEXT,
            anchor="w",
        ).pack(fill="x", pady=(2, 10))

        ctk.CTkButton(
            footer,
            text="Cerrar sesión",
            height=38,
            corner_radius=9,
            fg_color="transparent",
            hover_color="#1E293B",
            border_width=1,
            border_color="#334155",
            text_color="#FCA5A5",
            font=ctk.CTkFont(size=12),
            command=self.show_login,
        ).pack(fill="x")

    def _build_main(self, view: str) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        title, subtitle = VIEW_META[view]

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(26, 18))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text=subtitle,
            font=ctk.CTkFont(size=12),
            text_color=MUTED,
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.grid(row=0, column=1, rowspan=2, sticky="e")

        ctk.CTkLabel(
            right,
            text=datetime.now().strftime("%d/%m/%Y"),
            font=ctk.CTkFont(size=12),
            text_color=MUTED,
        ).pack(side="right", padx=(0, 14))

        ctk.CTkButton(
            right,
            text="Actualizar",
            width=108,
            height=38,
            corner_radius=9,
            fg_color=SURFACE,
            hover_color=SURFACE_ALT,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.show_dashboard(self.active_view),
        ).pack(side="right")

        if view == "dashboard":
            content = ctk.CTkScrollableFrame(main, fg_color="transparent")
            content.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 24))
            content.grid_columnconfigure(0, weight=1)
            self._build_dashboard(content)
        elif view in {"pacientes", "personal", "inventario", "tratamientos", "signos"}:
            content = ctk.CTkFrame(main, fg_color="transparent")
            content.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 24))
            content.grid_columnconfigure(0, weight=1)
            content.grid_rowconfigure(0, weight=1)
            self._build_module_view(content, view)
        else:
            content = ctk.CTkFrame(main, fg_color="transparent")
            content.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 24))
            content.grid_columnconfigure(0, weight=1)
            content.grid_rowconfigure(0, weight=1)
            self._build_placeholder(content, view)

    def _build_dashboard(self, content: ctk.CTkScrollableFrame) -> None:
        stats_grid = ctk.CTkFrame(content, fg_color="transparent")
        stats_grid.grid(row=0, column=0, sticky="ew")

        for column in range(4):
            stats_grid.grid_columnconfigure(column, weight=1, uniform="stats")

        cards = (
            ("pacientes_activos", "Pacientes activos", "Residenciados y ambulatorios"),
            ("personal_activo", "Personal disponible", "Estado activo o libre"),
            ("tratamientos_activos", "Tratamientos activos", "Medicación vigente"),
            ("stock_bajo", "Stock bajo", "Bajo el mínimo definido"),
            ("signos_hoy", "Signos hoy", "Controles registrados"),
            ("dxtx_hoy", "DXTX hoy", "Glucosas registradas"),
            ("panales_hoy", "Pañales hoy", "Controles de cambio"),
            ("turnos_hoy", "Turnos hoy", "Programados o en curso"),
        )

        for index, (key, title, hint) in enumerate(cards):
            row, column = divmod(index, 4)
            card, value_label = self._stat_card(stats_grid, title, hint)
            card.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else 8, 0),
                pady=(0 if row == 0 else 12, 0),
            )
            self._stat_labels[key] = value_label

        bottom = ctk.CTkFrame(content, fg_color="transparent")
        bottom.grid(row=1, column=0, sticky="ew", pady=(22, 0))
        bottom.grid_columnconfigure(0, weight=3)
        bottom.grid_columnconfigure(1, weight=2)

        self._build_quick_actions(bottom)
        self._build_system_card(bottom)

    def _stat_card(
        self,
        parent: ctk.CTkFrame,
        title: str,
        hint: str,
    ) -> tuple[ctk.CTkFrame, ctk.CTkLabel]:
        card = ctk.CTkFrame(
            parent,
            corner_radius=14,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            body,
            text=title.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=MUTED,
            anchor="w",
        ).pack(fill="x")

        value = ctk.CTkLabel(
            body,
            text="—",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=TEXT,
            anchor="w",
        )
        value.pack(fill="x", pady=(4, 0))

        ctk.CTkLabel(
            body,
            text=hint,
            font=ctk.CTkFont(size=10),
            text_color=MUTED,
            wraplength=180,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        return card, value

    def _build_quick_actions(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            parent,
            corner_radius=14,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            card,
            text="Accesos rápidos",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(18, 12))

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 20))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        actions = (
            ("Registrar signos vitales", "signos"),
            ("Surtir medicamento", "inventario"),
            ("Nuevo paciente", "pacientes"),
            ("Programar turno", "personal"),
        )

        for index, (label, target) in enumerate(actions):
            row, column = divmod(index, 2)
            ctk.CTkButton(
                grid,
                text=label,
                height=44,
                corner_radius=10,
                fg_color=SURFACE_ALT,
                hover_color="#DBEAFE",
                border_width=1,
                border_color=BORDER,
                text_color=TEXT,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda selected=target: self.show_dashboard(selected),
            ).grid(
                row=row,
                column=column,
                sticky="ew",
                padx=(0 if column == 0 else 8, 0),
                pady=(0 if row == 0 else 8, 0),
            )

    def _build_system_card(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            parent,
            corner_radius=14,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            card,
            text="Estado del sistema",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(18, 10))

        self._status_label = ctk.CTkLabel(
            card,
            text="Consultando API...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=MUTED,
            anchor="w",
        )
        self._status_label.pack(fill="x", padx=20)

        ctk.CTkLabel(
            card,
            text=f"API: {self.api.base_url}",
            font=ctk.CTkFont(size=10),
            text_color=MUTED,
            anchor="w",
            wraplength=280,
            justify="left",
        ).pack(fill="x", padx=20, pady=(8, 2))

        ctk.CTkLabel(
            card,
            text="Base de datos: MySQL local · Laragon",
            font=ctk.CTkFont(size=10),
            text_color=MUTED,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 18))

    # ------------------------------------------------------------------
    # Listados de módulos
    # ------------------------------------------------------------------

    def _build_module_view(self, content: ctk.CTkFrame, view: str) -> None:
        card = ctk.CTkFrame(
            content,
            corner_radius=16,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(card, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 10))
        toolbar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            toolbar,
            text=MODULE_TITLES[view],
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._module_status = ctk.CTkLabel(
            toolbar,
            text="Cargando...",
            font=ctk.CTkFont(size=11),
            text_color=MUTED,
            anchor="e",
        )
        self._module_status.grid(row=0, column=1, padx=(0, 12), sticky="e")

        ctk.CTkButton(
            toolbar,
            text="Actualizar",
            width=100,
            height=34,
            corner_radius=8,
            fg_color=SURFACE_ALT,
            hover_color="#DBEAFE",
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._load_module(view),
        ).grid(row=0, column=2, sticky="e")

        table_row = 1
        if view == "signos":
            self._control_segmented = ctk.CTkSegmentedButton(
                toolbar,
                values=["Signos vitales", "DXTX", "Pañales"],
                height=34,
                corner_radius=8,
                font=ctk.CTkFont(size=11, weight="bold"),
                selected_color=ACCENT,
                selected_hover_color=ACCENT_HOVER,
                unselected_color=SURFACE_ALT,
                unselected_hover_color="#E2E8F0",
                text_color=TEXT,
                command=self._on_control_tab,
            )
            self._control_segmented.set(self._control_tab)
            self._control_segmented.grid(
                row=1,
                column=0,
                columnspan=3,
                sticky="w",
                pady=(12, 0),
            )
            table_row = 2

        card.grid_rowconfigure(table_row, weight=1)

        self._module_table_frame = ctk.CTkFrame(card, fg_color="transparent")
        self._module_table_frame.grid(
            row=table_row,
            column=0,
            sticky="nsew",
            padx=18,
            pady=(0, 18),
        )
        self._module_table_frame.grid_rowconfigure(0, weight=1)
        self._module_table_frame.grid_columnconfigure(0, weight=1)

        columns = (
            CONTROL_COLUMNS["signos"]
            if view == "signos"
            else MODULE_COLUMNS[view]
        )
        self._module_tree = self._create_table(self._module_table_frame, columns)
        self._load_module(view)

    def _create_table(
        self,
        parent: ctk.CTkFrame,
        columns: tuple[tuple[str, str, int, str], ...],
    ) -> ttk.Treeview:
        for child in parent.winfo_children():
            child.destroy()

        tree = ttk.Treeview(
            parent,
            columns=[column[0] for column in columns],
            show="headings",
            style="Admin.Treeview",
            selectmode="browse",
        )

        for key, label, width, anchor in columns:
            tree.heading(key, text=label, anchor=anchor)
            tree.column(
                key,
                width=width,
                minwidth=60,
                anchor=anchor,
                stretch=False,
            )

        vertical = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")

        tree.tag_configure("odd", background="#FFFFFF")
        tree.tag_configure("even", background="#F8FAFC")
        tree.tag_configure("alert", foreground="#B91C1C")
        tree.tag_configure("warning", foreground="#B45309")
        tree.tag_configure("muted", foreground="#64748B")
        return tree

    def _load_module(self, view: str) -> None:
        if self._module_status is not None:
            self._module_status.configure(text="Cargando...", text_color=MUTED)

        threading.Thread(
            target=self._module_worker,
            args=(view,),
            daemon=True,
        ).start()

    def _module_worker(self, view: str) -> None:
        try:
            data = self.api.request(
                "GET",
                MODULE_ENDPOINTS[view],
                token=self.token,
            )
        except ApiError as exc:
            self._safe_after(self._module_failed, view, str(exc), exc.status_code)
            return
        except Exception as exc:
            self._safe_after(self._module_failed, view, str(exc), None)
            return

        self._safe_after(self._module_loaded, view, data)

    def _module_loaded(self, view: str, data: Any) -> None:
        if not self.winfo_exists() or self.active_view != view:
            return

        self._module_data = data
        self._render_module(view)

    def _module_failed(
        self,
        view: str,
        message: str,
        status_code: int | None,
    ) -> None:
        if not self.winfo_exists():
            return

        if status_code == 401:
            self.show_login("La sesión expiró. Inicia sesión nuevamente.")
            return

        if self.active_view != view:
            return

        if self._module_tree is not None:
            for item in self._module_tree.get_children():
                self._module_tree.delete(item)

        if self._module_status is not None:
            self._module_status.configure(
                text=f"No se pudo cargar: {message}",
                text_color=DANGER,
            )

    def _render_module(self, view: str) -> None:
        if self._module_table_frame is None:
            return

        if view == "signos":
            self._render_control()
            return

        rows = self._module_rows(view, self._module_data or [])
        self._render_table(MODULE_COLUMNS[view], rows)

    def _render_control(self) -> None:
        data = self._module_data if isinstance(self._module_data, dict) else {}
        mapping = {
            "Signos vitales": "signos",
            "DXTX": "dxtx",
            "Pañales": "panales",
        }
        kind = mapping.get(self._control_tab, "signos")
        rows = self._control_rows(kind, data.get(kind, []))
        self._render_table(CONTROL_COLUMNS[kind], rows)

    def _on_control_tab(self, value: str) -> None:
        self._control_tab = value
        if self.active_view == "signos" and isinstance(self._module_data, dict):
            self._render_control()

    def _render_table(
        self,
        columns: tuple[tuple[str, str, int, str], ...],
        rows: list[tuple[tuple[str, ...], str | None]],
    ) -> None:
        if self._module_table_frame is None:
            return

        self._module_tree = self._create_table(self._module_table_frame, columns)

        for index, (values, tag) in enumerate(rows):
            tags = tuple(
                value
                for value in (tag, "even" if index % 2 else "odd")
                if value
            )
            self._module_tree.insert("", "end", values=values, tags=tags)

        if self._module_status is not None:
            if not rows:
                text = "Sin registros"
            elif len(rows) == 1:
                text = "1 registro"
            else:
                text = f"{len(rows)} registros"
            self._module_status.configure(text=text, text_color=MUTED)

    def _module_rows(
        self,
        view: str,
        data: list[dict],
    ) -> list[tuple[tuple[str, ...], str | None]]:
        if view == "pacientes":
            rows = []
            for item in data:
                habitacion = self._text(item.get("habitacion"))
                if item.get("cama"):
                    habitacion = f"{habitacion} · {item['cama']}"
                values = (
                    self._text(item.get("documento")),
                    f"{item.get('nombre', '')} {item.get('apellidos', '')}".strip(),
                    self._text(item.get("tipo_residencia")).capitalize(),
                    habitacion,
                    self._text(item.get("edad")),
                    self._decimal(item.get("peso_kg"), " kg"),
                    self._decimal(item.get("talla_m"), " m"),
                    self._decimal(item.get("imc")),
                    self._text(item.get("tratamientos_activos")),
                    self._text(item.get("estado")).capitalize(),
                    self._text(item.get("diagnostico")),
                )
                estado = item.get("estado")
                tag = (
                    "muted"
                    if estado in {"alta", "fallecido"}
                    else ("warning" if estado == "hospitalizado" else None)
                )
                rows.append((values, tag))
            return rows

        if view == "personal":
            rows = []
            for item in data:
                estado = item.get("estado")
                values = (
                    self._text(item.get("documento")),
                    f"{item.get('nombre', '')} {item.get('apellidos', '')}".strip(),
                    self._text(item.get("rol")).capitalize(),
                    self._text(estado).capitalize(),
                    self._text(item.get("turno_hoy"), "Sin turno hoy"),
                    self._text(item.get("estado_turno")).capitalize(),
                    self._text(item.get("telefono")),
                    self._text(item.get("email")),
                )
                tag = (
                    "alert"
                    if estado == "inactivo"
                    else ("warning" if estado == "libre" else None)
                )
                rows.append((values, tag))
            return rows

        if view == "inventario":
            rows = []
            for item in data:
                bajo = bool(item.get("stock_bajo"))
                values = (
                    self._text(item.get("nombre")),
                    self._text(item.get("concentracion")),
                    self._text(item.get("presentacion")),
                    self._text(item.get("stock_minimo")),
                    self._text(item.get("disponible")),
                    self._text(item.get("lotes")),
                    self._text(item.get("proxima_caducidad")),
                    "BAJO" if bajo else "OK",
                )
                rows.append((values, "alert" if bajo else None))
            return rows

        if view == "tratamientos":
            rows = []
            for item in data:
                medicamento = self._text(item.get("medicamento"))
                if item.get("concentracion"):
                    medicamento = f"{medicamento} {item['concentracion']}"
                dosis = self._decimal(item.get("dosis"))
                if item.get("unidad_dosis"):
                    dosis = f"{dosis} {item['unidad_dosis']}"
                frecuencia = (
                    f"{item['frecuencia_horas']} h"
                    if item.get("frecuencia_horas")
                    else "PRN"
                )
                estado = item.get("estado")
                values = (
                    self._text(item.get("paciente")),
                    medicamento,
                    dosis,
                    self._text(item.get("via_administracion")).capitalize(),
                    frecuencia,
                    self._text(item.get("horarios")),
                    self._text(item.get("fecha_inicio")),
                    self._text(item.get("fecha_fin")),
                    self._text(estado).capitalize(),
                    self._text(item.get("prescrito_por")),
                )
                tag = (
                    "warning"
                    if estado == "suspendido"
                    else ("muted" if estado == "finalizado" else None)
                )
                rows.append((values, tag))
            return rows

        return []

    def _control_rows(
        self,
        kind: str,
        data: list[dict],
    ) -> list[tuple[tuple[str, ...], str | None]]:
        rows = []
        for item in data:
            hora = self._time_part(item.get("fecha_hora"))
            if kind == "signos":
                sistolica = item.get("presion_sistolica")
                diastolica = item.get("presion_diastolica")
                presion = (
                    f"{sistolica}/{diastolica}"
                    if sistolica is not None and diastolica is not None
                    else "—"
                )
                values = (
                    hora,
                    self._text(item.get("paciente")),
                    self._text(item.get("habitacion")),
                    presion,
                    self._text(item.get("bpm")),
                    f"{item['saturacion_o2']}%" if item.get("saturacion_o2") is not None else "—",
                    self._text(item.get("frecuencia_respiratoria")),
                    f"{item['temperatura']} °C" if item.get("temperatura") is not None else "—",
                    self._text(item.get("personal")),
                    self._text(item.get("observaciones")),
                )
            elif kind == "dxtx":
                values = (
                    hora,
                    self._text(item.get("paciente")),
                    self._text(item.get("valor_mg_dl")),
                    self._text(item.get("tipo")).capitalize(),
                    self._text(item.get("insulina_aplicada")),
                    self._text(item.get("personal")),
                    self._text(item.get("observaciones")),
                )
            else:
                values = (
                    hora,
                    self._text(item.get("paciente")),
                    self._text(item.get("tipo")).capitalize(),
                    self._text(item.get("personal")),
                    self._text(item.get("observaciones")),
                )
            rows.append((values, None))
        return rows

    @staticmethod
    def _text(value: Any, default: str = "—") -> str:
        if value is None:
            return default
        text = str(value).strip()
        return text if text else default

    @staticmethod
    def _decimal(value: Any, suffix: str = "") -> str:
        if value is None:
            return "—"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        return f"{number:.2f}{suffix}"

    @staticmethod
    def _time_part(value: Any) -> str:
        text = str(value or "")
        if len(text) >= 16 and text[10] == " ":
            return text[11:16]
        return text or "—"

    def _build_placeholder(
        self,
        content: ctk.CTkScrollableFrame,
        view: str,
    ) -> None:
        title, _ = VIEW_META[view]

        card = ctk.CTkFrame(
            content,
            corner_radius=16,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=0, column=0, sticky="ew")

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=36, pady=38)

        ctk.CTkLabel(
            body,
            text=title,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT,
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            body,
            text="Módulo preparado para la siguiente iteración del sistema.",
            font=ctk.CTkFont(size=12),
            text_color=MUTED,
            anchor="w",
        ).pack(fill="x", pady=(4, 20))

        for note in VIEW_NOTES.get(view, ()):
            ctk.CTkLabel(
                body,
                text=f"•  {note}",
                font=ctk.CTkFont(size=13),
                text_color=TEXT,
                anchor="w",
                justify="left",
            ).pack(fill="x", pady=3)

        ctk.CTkButton(
            body,
            text="Volver al panel",
            width=150,
            height=40,
            corner_radius=9,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.show_dashboard("dashboard"),
        ).pack(anchor="w", pady=(24, 0))

    # ------------------------------------------------------------------
    # Estadísticas
    # ------------------------------------------------------------------

    def refresh_stats(self) -> None:
        if not self.token:
            return

        if self._status_label is not None:
            self._status_label.configure(
                text="Actualizando datos...",
                text_color=MUTED,
            )

        threading.Thread(target=self._stats_worker, daemon=True).start()

    def _stats_worker(self) -> None:
        try:
            data = self.api.request(
                "GET",
                "/dashboard/stats",
                token=self.token,
            )
        except ApiError as exc:
            self._safe_after(self._stats_failed, str(exc), exc.status_code)
            return
        except Exception as exc:
            self._safe_after(self._stats_failed, str(exc), None)
            return

        self._safe_after(self._stats_ok, data)

    def _stats_ok(self, data: dict[str, Any]) -> None:
        if not self.winfo_exists():
            return

        for key, label in self._stat_labels.items():
            label.configure(text=self._format_number(data.get(key)))

        if self._status_label is not None:
            generated = str(data.get("generado_en", "")).replace("T", " ")
            self._status_label.configure(
                text=f"Conectado · {generated}".rstrip(" ·"),
                text_color=SUCCESS,
            )

    def _stats_failed(self, message: str, status_code: int | None) -> None:
        if not self.winfo_exists():
            return

        if status_code == 401:
            self.show_login("La sesión expiró. Inicia sesión nuevamente.")
            return

        for label in self._stat_labels.values():
            label.configure(text="—")

        if self._status_label is not None:
            self._status_label.configure(
                text="Sin conexión con la API",
                text_color=DANGER,
            )

    @staticmethod
    def _format_number(value: Any) -> str:
        if value is None:
            return "—"
        if isinstance(value, (int, float)):
            return f"{value:,}".replace(",", ".")
        return str(value)


def main() -> None:
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    app = AdminPanel()
    app.mainloop()


if __name__ == "__main__":
    main()
