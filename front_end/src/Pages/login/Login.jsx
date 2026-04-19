import { useAuth } from "../../context/AuthContext";
import { Lock, AtSign, Eye, EyeOff, Loader2, UserPlus } from "lucide-react"; // Ajout de UserPlus
import { useNavigate, Link } from "react-router-dom";
import { useState } from "react";

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("admin@greenguard.com");
  const [password, setPassword] = useState("password");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    
    try {
      await login(email, password);
      navigate("/dashboard"); 
    } catch (err) {
      setError(err.message || "Identifiants incorrects.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950 px-4">
      <form onSubmit={handleLogin} className="bg-slate-900 border border-slate-800 rounded-3xl p-8 space-y-6 w-full max-w-md shadow-2xl relative overflow-hidden">
        {/* Petit effet de halo pour le style */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-green-600/10 blur-3xl rounded-full"></div>
        
        <div className="text-center relative">
          <div className="w-16 h-16 bg-green-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-green-900/20">
            <span className="text-white font-bold text-4xl italic">G</span>
          </div>
          <h1 className="text-3xl font-black text-white italic">Green Guard</h1>
          <p className="text-slate-500 text-sm mt-2">Connectez-vous pour surveiller vos écosystèmes</p>
        </div>

        <div className="space-y-4">
          <div className="relative">
            <AtSign className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-white focus:ring-2 focus:ring-green-500 outline-none transition-all placeholder:text-slate-700" 
              placeholder="Email professionnel" 
              required 
            />
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input 
              type={showPassword ? "text" : "password"} 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-11 py-3 text-white focus:ring-2 focus:ring-green-500 outline-none transition-all placeholder:text-slate-700" 
              placeholder="Mot de passe" 
              required 
            />
            <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors">
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 py-2 rounded-lg">
            <p className="text-red-500 text-[10px] text-center font-black uppercase tracking-tighter">{error}</p>
          </div>
        )}

        <div className="space-y-4">
          <button 
            type="submit" 
            disabled={loading} 
            className="w-full bg-green-600 hover:bg-green-500 text-white font-black py-4 rounded-xl uppercase tracking-widest text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-green-600/20 active:scale-[0.98]"
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : "Accéder au dashboard"}
          </button>

          {/* --- SECTION REGISTER --- */}
          <div className="pt-4 border-t border-slate-800 text-center">
            <p className="text-slate-500 text-sm">
              Nouveau sur le projet ? 
              <Link 
                to="/register" 
                className="ml-2 text-green-500 hover:text-green-400 font-bold transition-colors inline-flex items-center gap-1"
              >
                Créer un compte
                <UserPlus size={14} />
              </Link>
            </p>
          </div>
        </div>
      </form>
    </div>
  );
};

export default Login;