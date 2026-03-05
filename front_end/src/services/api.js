const BASE_URL = "http://localhost:8000/api/v1";

async function fetchApi(endpoint, options = {}) {
  const token = localStorage.getItem("access_token");
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    // Gestion spécifique du 401 Unauthorized
    if (response.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = '/login';
      // On lève une erreur pour arrêter l'exécution du code appelant
      throw new Error("Session expirée. Redirection vers la page de connexion.");
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Erreur API");
  }

  return response.json();
}

export const api = {
  // --- AUTH ---
  login: async (email, password) => {
    const formData = new URLSearchParams();
    formData.append("username", email); // FastAPI OAuth2 attend 'username'
    formData.append("password", password);

    const response = await fetch(`${BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
    });
    
    if (!response.ok) {
        // La gestion d'erreur est spécifique ici, car le 401 n'est pas géré par fetchApi
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Identifiants incorrects");
    }
    
    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
    return data;
  },

  // --- METEO ---
  getMeteo: async (ville) => {
    return fetchApi(`/meteo/${ville}`);
  },

  getMeteoByCoords: async (lat, lon) => {
    // NOTE: La clé API OpenWeather ne doit pas être en dur dans le code backend.
    // Elle doit être chargée depuis une variable d'environnement (ex: .env).
    return fetchApi(`/meteo/actuelle?lat=${lat}&lon=${lon}`);
  },

  // --- INTERVENTIONS ---
  getUrgentInterventions: async () => {
    // Cet endpoint doit être créé côté backend
    return fetchApi('/interventions/urgent');
  },

  // --- DIAGNOSTIC ---
  getDashboardStats: async () => {
    return fetchApi("/health/diagnostic", {
      method: "POST",
      body: JSON.stringify({ espace_id: 1 })
    });
  },

  // --- ESPACES VERTS ---
  // On utilise le nom exact attendu par le composant : getEspacesVerts
  getEspacesVerts: async () => {
    return fetchApi("/espaces-verts/");
  },

  // --- ZONES / CLUSTERS ---
  getZones: async () => {
    return fetchApi("/zones");
  },

  createEspace: async (payload) => {
    const payloadComplet = { ...payload, user_id: 1 }; 
    return fetchApi("/espaces-verts/", {
      method: "POST",
      body: JSON.stringify(payloadComplet)
    });
  }
};