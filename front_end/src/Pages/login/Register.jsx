// front_end/src/Pages/login/Register.jsx
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../../services/api";
import { Lock, AtSign, User, UserPlus, ArrowLeft, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: ""
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      return setError("Les mots de passe ne correspondent pas.");
    }
    
    setLoading(true);
    setError("");

    try {
      await api.register({
        name: formData.name,
        email: formData.email,
        password: formData.password
      });
      setSuccess(true);
      setTimeout(() => navigate("/login"), 3000);
    } catch (err) {
      setError(err.message || "Erreur lors de l'inscription.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950">
        <div className="text-center space-y-4 animate-in zoom-in duration-500">
          <CheckCircle2 className="mx-auto text-green-500" size={64} />
          <h2 className="text-2xl font-black text-white italic uppercase tracking-tight">Compte créé !</h2>
          <p className="text-slate-400">Initialisation de votre accès...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950 p-4">
      <div className="w-full max-w-md">
        <form
          onSubmit={handleSubmit}
          className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/50 rounded-3xl shadow-2xl p-8 space-y-6"
        >
          <Link to="/login" className="inline-flex items-center gap-2 text-slate-500 hover:text-white transition-colors text-[10px] font-black uppercase tracking-widest">
            <ArrowLeft size={14} /> Retour
          </Link>

          <div className="text-center">
            <h1 className="text-3xl font-black text-white italic tracking-tight uppercase">S'inscrire</h1>
            <p className="text-slate-400 text-xs mt-2 uppercase tracking-widest font-bold">Enrôlement nouvel opérateur</p>
          </div>
          
          <div className="space-y-4">
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18}/>
              <input
                type="text"
                placeholder="Nom complet"
                required
                className="w-full bg-slate-950/50 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-white focus:ring-2 focus:ring-green-500 outline-none transition-all"
                onChange={(e) => setFormData({...formData, name: e.target.value})}
              />
            </div>

            <div className="relative">
              <AtSign className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18}/>
              <input
                type="email"
                placeholder="Email professionnel"
                required
                className="w-full bg-slate-950/50 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-white focus:ring-2 focus:ring-green-500 outline-none transition-all"
                onChange={(e) => setFormData({...formData, email: e.target.value})}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18}/>
                <input
                  type="password"
                  placeholder="Pass"
                  required
                  className="w-full bg-slate-950/50 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-white focus:ring-2 focus:ring-green-500 outline-none transition-all"
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                />
              </div>
              <div className="relative">
                <input
                  type="password"
                  placeholder="Confirm"
                  required
                  className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-green-500 outline-none transition-all"
                  onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                />
              </div>
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500 text-[10px] font-bold uppercase">
              <AlertCircle size={14} /> {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 hover:bg-green-500 disabled:bg-slate-800 text-white font-black py-4 rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 uppercase tracking-widest text-xs"
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : <><UserPlus size={18} /> Créer mon profil</>}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Register;