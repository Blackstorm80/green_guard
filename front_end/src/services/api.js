const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
const TOKEN_KEY = "access_token";

/** Événement émis sur toute réponse 401 : AuthContext déconnecte et redirige. */
export const SESSION_EXPIREE = "greenguard:session-expiree";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

/** Transforme une erreur FastAPI (texte ou liste Pydantic 422) en message lisible. */
function messageErreur(detail, status) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e) => {
        const champ = Array.isArray(e.loc) ? e.loc.filter((p) => p !== "body").join(".") : "";
        return champ ? `${champ} : ${e.msg}` : e.msg;
      })
      .join(" ; ");
  }
  return `Erreur ${status}`;
}

async function request(path, { method = "GET", body, form, auth = true, signal } = {}) {
  const headers = {};
  const token = tokenStorage.get();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let payload;
  if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    payload = new URLSearchParams(form);
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, { method, headers, body: payload, signal });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new ApiError("Serveur injoignable. Vérifiez votre connexion.", 0);
  }

  if (response.status === 401 && auth) {
    window.dispatchEvent(new Event(SESSION_EXPIREE));
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(messageErreur(data.detail, response.status), response.status);
  }
  return response.status === 204 ? null : response.json();
}

const query = (params) => {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (Array.isArray(v)) v.forEach((x) => qs.append(k, x));
    else if (v !== undefined && v !== null) qs.append(k, v);
  });
  const s = qs.toString();
  return s ? `?${s}` : "";
};

export const api = {
  // --- AUTHENTIFICATION & UTILISATEURS ---
  login: async (email, password) => {
    const data = await request("/auth/login", {
      method: "POST",
      form: { username: email, password },
      auth: false,
    });
    tokenStorage.set(data.access_token);
    return data;
  },
  register: ({ name, email, password }) =>
    request("/auth/register", { method: "POST", body: { name, email, password }, auth: false }),
  getCurrentUser: (signal) => request("/users/me", { signal }),
  logout: () => tokenStorage.clear(),

  // --- DASHBOARD & CAPTEURS ---
  getDashboardStats: (espaceIds = [], signal) =>
    request(`/capteurs/dashboard${query({ espace_ids: espaceIds })}`, { signal }),
  diagnostiquerEspace: (espaceId) =>
    request("/health/diagnostic", { method: "POST", body: { espace_id: espaceId } }),

  // --- ESPACES VERTS ---
  getEspacesVerts: (signal) => request("/espaces-verts/", { signal }),
  getEspaceVertById: (id, signal) => request(`/espaces-verts/${id}`, { signal }),
  createEspace: (data) => request("/espaces-verts/", { method: "POST", body: data }),
  updateEspace: (id, data) => request(`/espaces-verts/${id}`, { method: "PUT", body: data }),
  deleteEspace: (id) => request(`/espaces-verts/${id}`, { method: "DELETE" }),

  // --- ZONES INTELLIGENTES ---
  getZones: (signal) => request("/zones/", { signal }),
  rebuildZones: () => request("/zones/clustering/rebuild", { method: "POST" }),

  // --- INTERVENTIONS ---
  getInterventionsUrgentes: (limit = 5, signal) => request(`/interventions/urgent${query({ limit })}`, { signal }),
  getInterventions: (espaceId, signal) => request(`/interventions/${query({ espace_id: espaceId })}`, { signal }),
  createIntervention: (data) => request("/interventions/", { method: "POST", body: data }),
  updateIntervention: (id, data) => request(`/interventions/${id}`, { method: "PUT", body: data }),

  // --- NOTIFICATIONS ---
  getNotifications: (signal) => request("/notifications/", { signal }),
  markNotificationAsRead: (id) => request(`/notifications/${id}/mark-as-read`, { method: "POST" }),

  // --- CATALOGUES ---
  getCataloguePlantes: (signal) => request("/catalogue/plantes", { signal }),
  getCatalogueAuxiliaires: (signal) => request("/catalogue/auxiliaires", { signal }),

  // --- MÉTÉO (source unique : backend Open-Meteo) ---
  getMeteoByCoords: (lat, lon, signal) => request(`/meteo/actuelle${query({ lat, lon })}`, { signal }),
  getMeteo: (ville, signal) => request(`/meteo/${encodeURIComponent(ville)}`, { signal }),
};
