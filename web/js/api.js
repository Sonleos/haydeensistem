const isFile = window.location.protocol === "file:";

export const API_BASE = isFile
  ? "http://127.0.0.1:8000/api"
  : `${window.location.origin}/api`;

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

class ApiClient {
  constructor() {
    this.token = localStorage.getItem("haydeen_token") || null;
  }

  setToken(token) {
    this.token = token || null;
    if (this.token) {
      localStorage.setItem("haydeen_token", this.token);
    } else {
      localStorage.removeItem("haydeen_token");
    }
  }

  async request(path, { method = "GET", body = null, auth = true } = {}) {
    const headers = { Accept: "application/json" };
    if (body !== null) {
      headers["Content-Type"] = "application/json";
    }
    if (auth && this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    let response;
    try {
      response = await fetch(`${API_BASE}${path}`, {
        method,
        headers,
        body: body !== null ? JSON.stringify(body) : undefined,
      });
    } catch (error) {
      throw new ApiError("No se pudo conectar con la API.", 0);
    }

    const text = await response.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (error) {
        data = text;
      }
    }

    if (!response.ok) {
      let detail = data && data.detail ? data.detail : `Error HTTP ${response.status}`;
      if (Array.isArray(detail)) {
        detail = detail
          .map((item) => (item && item.msg ? item.msg : String(item)))
          .join("; ");
      }
      if (response.status === 401) {
        this.setToken(null);
      }
      throw new ApiError(String(detail), response.status);
    }

    return data;
  }

  login(username, password) {
    return this.request("/auth/login", {
      method: "POST",
      body: { username, password },
      auth: false,
    });
  }

  me() {
    return this.request("/auth/me");
  }

  pacientes() {
    return this.request("/pacientes");
  }

  tratamientos() {
    return this.request("/tratamientos");
  }

  controlDiario() {
    return this.request("/control-diario");
  }

  inventarioLotes(medicamentoId) {
    const query = new URLSearchParams({
      medicamento_id: String(medicamentoId),
      solo_disponibles: "true",
    });
    return this.request(`/inventario/lotes?${query.toString()}`);
  }

  crearSignos(payload) {
    return this.request("/signos-vitales", { method: "POST", body: payload });
  }

  administrar(payload) {
    return this.request("/administraciones", { method: "POST", body: payload });
  }
}

export const api = new ApiClient();
