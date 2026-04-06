import { useState } from "react";
import { X } from "lucide-react";
import { api } from "../../services/api";

export default function AddSpaceModal({ onClose, onSuccess }) {
  // Initialisation avec TOUS les champs requis par le backend
  const [formData, setFormData] = useState({
    nom: "",
    ville: "",
    surface_m2: "",
    latitude: "",
    longitude: "",
    type_espace: "Parc",
    exposition_reelle: "Plein Soleil",
    type_sol: "Sableux",
    ph_sol: 7.0,
    reserve_utile_max: 100,
    coefficient_cultural: 0.8,
    zone: "Zone A1",
    plante_id: 1, // Par defaut pour les tests
    gerant_id: 1  // Ton ID (Nathan)
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Conversion des types pour correspondre au schema Pydantic (float/int)
      const payload = {
        ...formData,
        surface_m2: parseFloat(formData.surface_m2),
        ph_sol: parseFloat(formData.ph_sol),
        reserve_utile_max: parseFloat(formData.reserve_utile_max),
        coefficient_cultural: parseFloat(formData.coefficient_cultural),
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude),
        plante_id: parseInt(formData.plante_id),
        gerant_id: parseInt(formData.gerant_id)
      };

      await api.createEspace(payload);
      onSuccess();
      onClose();
    } catch (err) {
      console.error("Erreur detailed:", err);
    }
  };

  const inputStyle = "w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white outline-none focus:ring-1 focus:ring-green-500 text-sm";
  const labelStyle = "block text-[10px] font-bold text-slate-500 uppercase mb-1";

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 p-4 backdrop-blur-md">
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-black text-white">Fiche Technique Site</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-white"><X size={24} /></button>
        </div>

        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* SECTION 1 : IDENTITE */}
          <div className="space-y-4">
            <h3 className="text-green-500 text-xs font-bold uppercase tracking-widest">Identite & Localisation</h3>
            <div>
              <label className={labelStyle}>Nom de l'espace</label>
              <input required className={inputStyle} onChange={(e) => setFormData({...formData, nom: e.target.value})} />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className={labelStyle}>Ville</label>
                <input required className={inputStyle} onChange={(e) => setFormData({...formData, ville: e.target.value})} />
              </div>
              <div>
                <label className={labelStyle}>Surface (m2)</label>
                <input type="number" required className={inputStyle} onChange={(e) => setFormData({...formData, surface_m2: e.target.value})} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className={labelStyle}>Latitude</label>
                <input type="number" step="any" required className={inputStyle} onChange={(e) => setFormData({...formData, latitude: e.target.value})} />
              </div>
              <div>
                <label className={labelStyle}>Longitude</label>
                <input type="number" step="any" required className={inputStyle} onChange={(e) => setFormData({...formData, longitude: e.target.value})} />
              </div>
            </div>
          </div>

          {/* SECTION 2 : AGRONOMIE */}
          <div className="space-y-4">
            <h3 className="text-green-500 text-xs font-bold uppercase tracking-widest">Donnees Agronomiques</h3>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className={labelStyle}>Type d'espace</label>
                <select className={inputStyle} onChange={(e) => setFormData({...formData, type_espace: e.target.value})}>
                  <option>Parc</option><option>Jardin</option><option>Rond-point</option>
                </select>
              </div>
              <div>
                <label className={labelStyle}>Exposition</label>
                <select className={inputStyle} onChange={(e) => setFormData({...formData, exposition_reelle: e.target.value})}>
                  <option>Plein Soleil</option><option>Ombre</option><option>Mi-Ombre</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className={labelStyle}>Type de sol</label>
                <select className={inputStyle} onChange={(e) => setFormData({...formData, type_sol: e.target.value})}>
                  <option>Sableux</option><option>Argileux</option><option>Limoneux</option>
                </select>
              </div>
              <div>
                <label className={labelStyle}>pH du sol</label>
                <input type="number" step="0.1" className={inputStyle} value={formData.ph_sol} onChange={(e) => setFormData({...formData, ph_sol: e.target.value})} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className={labelStyle}>Reserve Utile (RU)</label>
                <input type="number" className={inputStyle} value={formData.reserve_utile_max} onChange={(e) => setFormData({...formData, reserve_utile_max: e.target.value})} />
              </div>
              <div>
                <label className={labelStyle}>Coeff. Cultural (Kc)</label>
                <input type="number" step="0.1" className={inputStyle} value={formData.coefficient_cultural} onChange={(e) => setFormData({...formData, coefficient_cultural: e.target.value})} />
              </div>
            </div>
          </div>

          <div className="md:col-span-2 pt-4">
            <button type="submit" className="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-4 rounded-xl shadow-lg transition-all">
              Creer l'espace agronomique
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
