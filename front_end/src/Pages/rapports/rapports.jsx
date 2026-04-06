import { useState, useEffect } from "react";
import { 
  FileText, 
  Download, 
  Calendar, 
  CheckCircle, 
  AlertOctagon,
  Search,
} from "lucide-react";
import { cn } from "../../lib/utils";
import { api } from '../../services/api';

// --- MOCK DATA : Historique des rapports ---
const REPORTS_DATA = [
  {
    id: "R-2023-10-A",
    title: "Rapport d'incident - Mortalité massive",
    date: "24 Oct 2023",
    type: "INCIDENT", // INCIDENT, MONTHLY, INTERVENTION
    zone: "Zone Paris-Nord",
    espace: "Jardin des Plantes",
    author: "Jean Michel (Tech)",
    status: "SIGNED", // SIGNED, PENDING
    size: "2.4 MB"
  },
  {
    id: "R-2023-09-M",
    title: "Bilan Mensuel - Septembre",
    date: "01 Oct 2023",
    type: "MONTHLY",
    zone: "Global",
    espace: "-",
    author: "Système",
    status: "SIGNED",
    size: "5.1 MB"
  },
  {
    id: "R-2023-10-B",
    title: "Intervention Arrosage d'Urgence",
    date: "22 Oct 2023",
    type: "INTERVENTION",
    zone: "Jardins Sud-Ouest",
    espace: "Rond-point Mermoz",
    author: "Sophie D.",
    status: "PENDING",
    size: "1.2 MB"
  },
];

const Rapports = () => {
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    espaceId: '',
    searchTerm: '',
    type: 'ALL',
  });
  const [espaces, setEspaces] = useState([]);

  useEffect(() => {
    const fetchEspaces = async () => {
      try {
        const response = await api.getEspacesVerts();
        setEspaces(response);
      } catch (error) {
        console.error("Impossible de charger les espaces verts", error);
      }
    };
    fetchEspaces();
  }, []);

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };
  
  const handleTypeFilter = (type) => {
    setFilters({ ...filters, type });
  };

  const handlePrint = () => {
    window.print();
  };

  const filteredReports = REPORTS_DATA.filter(report => {
    const reportDate = new Date(report.date);
    const startDate = filters.startDate ? new Date(filters.startDate) : null;
    const endDate = filters.endDate ? new Date(filters.endDate) : null;

    if (startDate && reportDate < startDate) return false;
    if (endDate && reportDate > endDate) return false;
    if (filters.type !== 'ALL' && report.type !== filters.type) return false;
    if (filters.searchTerm && !report.title.toLowerCase().includes(filters.searchTerm.toLowerCase())) return false;
    
    // Le filtre par espace n'est pas appliqué car les données sont mockées
    // Il faudrait l'ID de l'espace dans les données pour que ce soit fonctionnel

    return true;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-500 h-full flex flex-col">
      
      {/* --- EN-TÊTE --- */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shrink-0 no-print">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Rapports & Historique
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Consultez et téléchargez les bilans d'interventions et d'incidents.
          </p>
        </div>
        <button
          onClick={handlePrint}
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2"
        >
          <FileText size={16} />
          <span>Imprimer le Rapport</span>
        </button>
      </div>

      {/* --- LISTE DES RAPPORTS --- */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl flex-1 flex flex-col min-h-0">
        
        {/* Toolbar */}
        <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row gap-4 items-center justify-between no-print">
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-2 rounded-lg border border-slate-800 w-full sm:w-64">
            <Search size={16} className="text-slate-500" />
            <input 
              type="text" 
              name="searchTerm"
              value={filters.searchTerm}
              onChange={handleFilterChange}
              placeholder="Rechercher un rapport..." 
              className="bg-transparent border-none focus:outline-none text-sm text-slate-200 w-full placeholder:text-slate-600"
            />
          </div>
          <div className="flex gap-2 w-full sm:w-auto overflow-x-auto">
            {["ALL", "INCIDENT", "MONTHLY", "INTERVENTION"].map(type => (
              <button
                key={type}
                onClick={() => handleTypeFilter(type)}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors",
                  filters.type === type 
                    ? "bg-slate-800 text-white border-slate-600" 
                    : "text-slate-500 border-transparent hover:bg-slate-800 hover:text-slate-300"
                )}
              >
                {type === "ALL" ? "Tous" : type.charAt(0) + type.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
        </div>
        
        {/* Table */}
        <div className="overflow-auto custom-scrollbar flex-1">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950/80 text-slate-500 uppercase text-xs font-semibold sticky top-0 z-10 backdrop-blur-sm">
              <tr>
                <th className="px-6 py-4">Document</th>
                <th className="px-6 py-4">Zone / Espace</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4">Statut</th>
                <th className="px-6 py-4 text-right no-print">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {filteredReports.map((report) => (
                <tr key={report.id} className="hover:bg-slate-800/50 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-start gap-3">
                      <div className={cn(
                        "p-2 rounded-lg shrink-0",
                        report.type === 'INCIDENT' ? "bg-red-500/10 text-red-400" :
                        report.type === 'MONTHLY' ? "bg-blue-500/10 text-blue-400" :
                        "bg-amber-500/10 text-amber-400"
                      )}>
                        <FileText size={20} />
                      </div>
                      <div>
                        <div className="font-bold text-white group-hover:text-green-400 transition-colors">
                          {report.title}
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5">
                          Par {report.author} • {report.size}
                        </div>
                      </div>
                    </div>
                  </td>

                  <td className="px-6 py-4">
                    <div className="text-slate-300">{report.zone}</div>
                    <div className="text-xs text-slate-500">{report.espace}</div>
                  </td>

                  <td className="px-6 py-4 font-mono text-slate-400">
                    {report.date}
                  </td>

                  <td className="px-6 py-4">
                    {report.status === 'SIGNED' ? (
                      <span className="inline-flex items-center gap-1.5 text-emerald-400 text-xs font-bold bg-emerald-500/10 px-2 py-1 rounded-full border border-emerald-500/20">
                        <CheckCircle size={12} /> Signé
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 text-amber-400 text-xs font-bold bg-amber-500/10 px-2 py-1 rounded-full border border-amber-500/20">
                        <AlertOctagon size={12} /> En attente
                      </span>
                    )}
                  </td>

                  <td className="px-6 py-4 text-right no-print">
                    <button className="text-slate-400 hover:text-white p-2 hover:bg-slate-700 rounded-lg transition-colors border border-transparent hover:border-slate-600">
                      <Download size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Section pour l'impression */}
        <div className="printable-content p-6 hidden">
            <h2 className="text-xl font-semibold mb-4">Graphique de Stress Hydrique</h2>
            <div className="bg-white p-4 rounded-lg shadow-md h-64 w-full">
              <p className="text-center text-gray-500 pt-24">Le graphique s'affichera ici.</p>
            </div>
        </div>

      </div>
    </div>
  );
};

export default Rapports;