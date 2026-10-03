import { useState } from "react";
import { X, Sprout, MapPin, Activity } from "lucide-react";
import { api } from "../../services/api";

/** Nombre saisi, ou undefined si le champ est vide (le champ est alors omis du payload). */
const nombreOuVide = (valeur) => (valeur === "" || valeur === null ? undefined : Number(valeur));

export default function AddSpaceModal({ onClose, onSuccess }) {
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const [formData, setFormData] = useState({
    nom: "",
    type_espace: "Parc",
    ville: "",
    latitude: "",
    longitude: "",
    surface_m2: "",
    type_sol: "Argileux",
    ph_actuel: 7.0,
    reserve_utile_max: 100,
    coefficient_cultural: 0.8,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErreur("");
    setEnvoi(true);
    try {
      // Le propriétaire est déduit du jeton côté serveur : aucun user_id envoyé
      await api.createEspace({
        nom: formData.nom.trim(),
        type_espace: formData.type_espace,
        ville: formData.ville.trim() || undefined,
        type_sol: formData.type_sol,
        latitude: Number(formData.latitude),
        longitude: Number(formData.longitude),
        surface_m2: nombreOuVide(formData.surface_m2),
        ph_actuel: nombreOuVide(formData.ph_actuel),
        reserve_utile_max: nombreOuVide(formData.reserve_utile_max),
        coefficient_cultural: nombreOuVide(formData.coefficient_cultural),
      });
      onSuccess();
      onClose();
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
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
                onChange={(e) => setFormData({...formData, ph_actuel: e.target.value})} />
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

          {erreur && (
            <p role="alert" className="bg-red-500/10 border border-red-500/20 text-red-300 p-3 rounded-xl text-sm">{erreur}</p>
          )}
          <button type="submit" disabled={envoi} className="w-full bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white font-black py-4 rounded-2xl shadow-xl transition-all mt-4 uppercase tracking-widest">
            {envoi ? "Enregistrement…" : "Enregistrer le site"}
          </button>
        </form>
      </div>
    </div>
  );
}