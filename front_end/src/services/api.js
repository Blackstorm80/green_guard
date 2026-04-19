const BASE_URL = "http://localhost:8000/api/v1";

export const api = {
  // --- AUTHENTIFICATION & UTILISATEURS ---
  
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

  register: async (userData) => {
    const payload = {
      name: userData.name,
      email: userData.email,
      password: userData.password,
      role: "admin" 
    };

    const response = await fetch(`${BASE_URL}/auth/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Échec de la création du compte.");
    }
    return await response.json();
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