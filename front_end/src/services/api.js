const BASE_URL = "http://localhost:8000/api/v1";

export const api = {
  // --- AUTHENTIFICATION ---
  login: async (email, password) => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);
    const response = await fetch(`${BASE_URL}/auth/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    });
    if (!response.ok) throw new Error("Échec de l'authentification");
    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
    return data;
  },

  getCurrentUser: async (token) => {
    const response = await fetch(`${BASE_URL}/users/me`, {
      headers: { "Authorization": `Bearer ${token}` },
    });
    return response.json();
  },

  // --- DASHBOARD & CAPTEURS ---
  getDashboardStats: async (espaceIds = []) => {
    const token = localStorage.getItem("access_token");
    const params = new URLSearchParams();
    espaceIds.forEach(id => params.append("espace_ids", id));
    
    // On garde le double /capteurs car c'est ainsi que ton router est configuré
    const url = `${BASE_URL}/capteurs/capteurs/dashboard?${params.toString()}`;
    
    const response = await fetch(url, {
      headers: { "Authorization": `Bearer ${token}` },
    });
    if (!response.ok) throw new Error(`Erreur Capteurs: ${response.status}`);
    return response.json();
  },

  // --- ESPACES & ZONES ---
  getEspacesVerts: async () => {
    const token = localStorage.getItem("access_token");
    const response = await fetch(`${BASE_URL}/espaces-verts/`, {
      headers: { "Authorization": `Bearer ${token}` },
    });
    return response.json();
  },

  getZones: async () => {
    const token = localStorage.getItem("access_token");
    const response = await fetch(`${BASE_URL}/zones/zones`, {
      headers: { "Authorization": `Bearer ${token}` },
    });
    return response.json();
  },

  // --- CATALOGUES ---
  getCataloguePlantes: async () => {
    const response = await fetch(`${BASE_URL}/catalogue/plantes`);
    return response.json();
  },

  getCatalogueAuxiliaires: async () => {
    const response = await fetch(`${BASE_URL}/catalogue/auxiliaires`);
    return response.json();
  },

  // --- LOGOUT ---
  logout: () => {
    localStorage.removeItem("access_token");
  }
};