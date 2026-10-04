const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

/** Événement émis sur toute réponse 401 : AuthContext déconnecte et redirige. */
export const SESSION_EXPIREE = "greenguard:session-expiree";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

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

/**
 * Session : cookie httpOnly posé par le serveur (illisible par JavaScript, donc à l'abri d'un vol par XSS).
 * X-Requested-With est exigé par l'API pour toute écriture authentifiée par cookie (protection CSRF).
 */
async function request(path, { method = "GET", body, form, signalerExpiration = true, signal } = {}) {
  const headers = { "X-Requested-With": "greenguard" };

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
    response = await fetch(`${BASE_URL}${path}`, { method, headers, body: payload, signal, credentials: "include" });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new ApiError("Serveur injoignable. Vérifiez votre connexion.", 0);
  }

  if (response.status === 401 && signalerExpiration) {
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
  // Le jeton renvoyé dans le corps (pour Swagger/scripts) est volontairement ignoré : seul le cookie sert.
  login: (email, password) =>
    request("/auth/login", { method: "POST", form: { username: email, password }, signalerExpiration: false }),
  // Provisoire : l'inscription crée une nouvelle organisation dont le compte est administrateur
  register: ({ name, email, password, organisation }) =>
    request("/auth/register", {
      method: "POST",
      body: { name, email, password, organisation: organisation || undefined },
      signalerExpiration: false,
    }),
  // Vérification de session au chargement : un 401 signifie simplement « non connecté »
  getCurrentUser: (signal) => request("/users/me", { signal, signalerExpiration: false }),
  logout: () => request("/auth/logout", { method: "POST", signalerExpiration: false }),

  // --- ORGANISATION & MEMBRES ---
  getOrganisation: (signal) => request("/organisations/moi", { signal }),
  updateOrganisation: (data) => request("/organisations/moi", { method: "PUT", body: data }),
  getMembres: (signal) => request("/organisations/moi/membres", { signal }),
  updateMembre: (id, data) => request(`/organisations/moi/membres/${id}`, { method: "PUT", body: data }),

  // --- DASHBOARD & CAPTEURS ---
  // Chaque lecture porte dose_recommandee {mm, litres|null, minutes|null} (bilan FAO-56 seulement)
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
  // Historique des bilans hydriques et de leurs termes (FAO-56), par date croissante ; jours ≤ 365
  getBilansEspace: (id, jours = 30, signal) => request(`/espaces-verts/${id}/bilans${query({ jours })}`, { signal }),

  // --- ZONES INTELLIGENTES ---
  getZones: (signal) => request("/zones/", { signal }),
  rebuildZones: () => request("/zones/clustering/rebuild", { method: "POST" }),

  // --- INTERVENTIONS ---
  getInterventionsUrgentes: (limit = 5, signal) => request(`/interventions/urgent${query({ limit })}`, { signal }),
  getInterventions: (espaceId, signal) => request(`/interventions/${query({ espace_id: espaceId })}`, { signal }),
  // Arrosage terminé avec volume_eau_l (créé avec statut « terminee » ou terminé par PUT) : compté aussitôt
  // dans le bilan (arrosage_compte_mm en retour) ; 422 si la surface de l'espace est inconnue.
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
