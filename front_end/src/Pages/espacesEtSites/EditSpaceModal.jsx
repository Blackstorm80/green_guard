import { useState } from "react";
import { X } from "lucide-react";
import { api } from "../../services/api";

const CHAMPS_NUMERIQUES = new Set([
  "surface_m2", "ph_actuel", "humidite_cible", "frequence_arrosage_auto", "profondeur_racinaire",
]);

const valeursInitiales = (espace) => ({
  nom: espace?.nom || "",
  ville: espace?.ville || "",
  surface_m2: espace?.surface_m2 ?? "",
  type_sol: espace?.type_sol || "Limon-Argileux",
  ph_actuel: espace?.ph_actuel ?? 7.0,
  exposition: espace?.exposition || "Soleil",
  drainage: espace?.drainage || "Moyen",
  humidite_cible: espace?.humidite_cible ?? 60,
  frequence_arrosage_auto: espace?.frequence_arrosage_auto ?? 48,
  profondeur_racinaire: espace?.profondeur_racinaire ?? 30,
  type_irrigation: espace?.type_irrigation || "Goutte-à-goutte",
  date_derniere_fertilisation: espace?.date_derniere_fertilisation
    ? new Date(espace.date_derniere_fertilisation).toISOString().split("T")[0]
    : "",
});

export default function EditSpaceModal({ espace, onClose, onSuccess }) {
  // Le parent monte la modale avec l'espace sélectionné : l'état initial suffit
  const [formData, setFormData] = useState(() => valeursInitiales(espace));
  const [erreur, setErreur] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErreur("");
    // Champs vides omis (inchangés côté serveur), champs numériques convertis
    const payload = Object.fromEntries(
      Object.entries(formData)
        .filter(([, v]) => v !== "" && v !== null && v !== undefined)
        .map(([k, v]) => [k, CHAMPS_NUMERIQUES.has(k) ? Number(v) : v])
    );
    try {
      await api.updateEspace(espace.id, payload);
      onSuccess(); // Recharge la liste
      onClose();   // Ferme la modale
    } catch (err) {
      setErreur(err.message);
    }
  };
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  if (!espace) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-black text-white">Éditer: {espace.nom}</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
            {/* Infos Générales */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Nom du site</label>
                    <input name="nom" value={formData.nom} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:ring-1 focus:ring-green-500"/>
                </div>
                <div>
                    <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Ville</label>
                    <input name="ville" value={formData.ville} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:ring-1 focus:ring-green-500"/>
                </div>
                <div>
                    <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Surface (m²)</label>
                    <input type="number" name="surface_m2" value={formData.surface_m2} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:ring-1 focus:ring-green-500"/>
                </div>
            </div>

            <div className="pt-4 border-t border-slate-800">
                 <h3 className="text-lg font-bold text-slate-300 mb-4">Données Agronomiques</h3>
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
                    {/* Colonne 1 */}
                    <div className="space-y-4">
                        <div>
                            <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Type de Sol</label>
                            <select name="type_sol" value={formData.type_sol} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:ring-1 focus:ring-green-500">
                                <option>Argileux</option>
                                <option>Limon-Argileux</option>
                                <option>Sableux</option>
                                <option>Tourbeux</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">pH Actuel</label>
                            <input type="number" step="0.1" name="ph_actuel" value={formData.ph_actuel} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:ring-1 focus:ring-green-500"/>
                        </div>
                        <div>
                            <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Drainage</label>
                             <select name="drainage" value={formData.drainage} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:ring-1 focus:ring-green-500">
                                <option>Faible</option>
                                <option>Moyen</option>
                                <option>Bon</option>
                                <option>Excellent</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Type d'irrigation</label>
                            <input name="type_irrigation" value={formData.type_irrigation} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:ring-1 focus:ring-green-500"/>
                        </div>
                    </div>
                    {/* Colonne 2 */}
                    <div className="space-y-4">
                        <div>
                            <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Exposition</label>
                            <select name="exposition" value={formData.exposition} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:ring-1 focus:ring-green-500">
                                <option>Soleil</option>
                                <option>Mi-ombre</option>
                                <option>Ombre</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Humidité Cible (%)</label>
                            <input type="number" name="humidite_cible" value={formData.humidite_cible} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:ring-1 focus:ring-green-500"/>
                        </div>
                        <div>
                            <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Fréquence Arrosage (h)</label>
                            <input type="number" name="frequence_arrosage_auto" value={formData.frequence_arrosage_auto} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:ring-1 focus:ring-green-500"/>
                        </div>
                        <div>
                            <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Dernière Fertilisation</label>
                            <input type="date" name="date_derniere_fertilisation" value={formData.date_derniere_fertilisation} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:ring-1 focus:ring-green-500"/>
                        </div>
                    </div>
                 </div>
            </div>

          {erreur && (
            <p role="alert" className="bg-red-500/10 border border-red-500/20 text-red-300 p-3 rounded-xl text-sm">{erreur}</p>
          )}
          <button
            type="submit"
            className="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-4 rounded-xl shadow-lg transition-all mt-4"
          >
            Sauvegarder les modifications
          </button>
        </form>
      </div>
    </div>
  );
}
