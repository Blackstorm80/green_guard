import { useState } from "react";
import { X, Sprout, MapPin, Activity } from "lucide-react";
import { api } from "../../services/api";
import { useAuth } from "../../context/AuthContext";

export default function AddSpaceModal({ onClose, onSuccess }) {
  const { user } = useAuth();
  
  const [formData, setFormData] = useState({
    // 1. Général & DTO
    nom: "",
    type_espace: "Parc",
    localisation: "", // Sera rempli par ville + coordonées
    ville: "",
    latitude: "",
    longitude: "",
    
    // 2. Agronomie (Champs requis par ton DTO)
    plante_id: 1, 
    surface_m2: "",
    type_sol: "argileux",
    ph_sol: 7.0,
    exposition_reelle: "Soleil",
    
    // 3. Paramètres Techniques
    reserve_utile_max: 100,
    coefficient_cultural: 0.8,
    zone: "",
    gerant_id: null
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user?.id) return;

    try {
      const payload = {
        ...formData,
        user_id: user.id,
        // Conversion explicite pour le DTO (Strings -> Numbers)
        surface_m2: parseFloat(formData.surface_m2) || 0,
        latitude: parseFloat(formData.latitude) || 0,
        longitude: parseFloat(formData.longitude) || 0,
        ph_sol: parseFloat(formData.ph_sol) || 7.0,
        reserve_utile_max: parseFloat(formData.reserve_utile_max) || 100,
        coefficient_cultural: parseFloat(formData.coefficient_cultural) || 0.8,
        plante_id: parseInt(formData.plante_id) || 1,
        // Fusion pour le champ 'localisation' du DTO
        localisation: `${formData.ville} (${formData.latitude}, ${formData.longitude})`
      };

      await api.createEspace(payload);
      onSuccess();
      onClose();
    } catch (err) {
      console.error("Erreur DTO détaillée :", err);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
      <div className="w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl max-h-[95vh] overflow-y-auto">
        
        <div className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-2xl font-black text-white">Configuration du Site</h2>
            <p className="text-slate-500 text-sm">Paramétrage complet des données agronomiques</p>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          
          {/* SECTION 1 : IDENTITÉ & TYPE */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-[10px] font-bold text-slate-500 uppercase mb-2">Nom de l'espace</label>
              <input required className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:ring-1 focus:ring-green-500"
                onChange={(e) => setFormData({...formData, nom: e.target.value})} />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase mb-2">Type d'espace</label>
              <select className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none"
                onChange={(e) => setFormData({...formData, type_espace: e.target.value})}>
                <option value="Parc">Parc Public</option>
                <option value="Jardin">Jardin Privé</option>
                <option value="Toiture">Toiture Végétalisée</option>
              </select>
            </div>
          </div>

          {/* SECTION 2 : GÉO-LOCALISATION */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-slate-950/50 p-4 rounded-2xl border border-slate-800/50">
            <div className="col-span-2">
              <label className="block text-[10px] font-bold text-slate-500 uppercase mb-2">Ville / Commune</label>
              <input required className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none"
                onChange={(e) => setFormData({...formData, ville: e.target.value})} />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase mb-2">Lat</label>
              <input type="number" step="any" required className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none"
                onChange={(e) => setFormData({...formData, latitude: e.target.value})} />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase mb-2">Long</label>
              <input type="number" step="any" required className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none"
                onChange={(e) => setFormData({...formData, longitude: e.target.value})} />
            </div>
          </div>

          {/* SECTION 3 : PARAMÈTRES AGRONOMIQUES  */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-[10px] font-bold text-green-500 uppercase mb-2">Type de Sol</label>
              <select className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white text-sm"
                onChange={(e) => setFormData({...formData, type_sol: e.target.value})}>
                <option value="Argileux">Argileux</option>
                <option value="Sableux">Sableux</option>
                <option value="Limoneux">Limoneux</option>
              </select>
            </div>
            <div>
              <label className="block text-[10px] font-bold text-green-500 uppercase mb-2">pH Sol</label>
              <input type="number" step="0.1" defaultValue="7.0" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white"
                onChange={(e) => setFormData({...formData, ph_sol: e.target.value})} />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-amber-500 uppercase mb-2">Réserv. Utile (mm)</label>
              <input type="number" defaultValue="100" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white"
                onChange={(e) => setFormData({...formData, reserve_utile_max: e.target.value})} />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-blue-500 uppercase mb-2">Coeff. Cultural</label>
              <input type="number" step="0.01" defaultValue="0.80" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white"
                onChange={(e) => setFormData({...formData, coefficient_cultural: e.target.value})} />
            </div>
          </div>

          <button type="submit" className="w-full bg-green-600 hover:bg-green-500 text-white font-black py-4 rounded-2xl shadow-xl transition-all mt-4 uppercase tracking-widest">
            Enregistrer le site 
          </button>
        </form>
      </div>
    </div>
  );
}