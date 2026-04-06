import { useAuth } from "../../context/AuthContext";
import { Lock, AtSign, Eye, EyeOff, Loader2 } from "lucide-react";
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
      // Le login du contexte gère déjà tout (appel api + stockage token)
      await login(email, password);
      navigate("/dashboard"); 
    } catch (err) {
      setError(err.message || "Identifiants incorrects.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950">
      <form onSubmit={handleLogin} className="bg-slate-900 border border-slate-800 rounded-3xl p-8 space-y-6 w-full max-w-md shadow-2xl">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-white font-bold text-4xl italic">G</span>
          </div>
          <h1 className="text-3xl font-black text-white italic">Green Guard</h1>
        </div>

        <div className="space-y-4">
          <div className="relative">
            <AtSign className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-white focus:ring-2 focus:ring-green-500 outline-none transition-all" placeholder="Email" required />
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-11 py-3 text-white focus:ring-2 focus:ring-green-500 outline-none transition-all" placeholder="Mot de passe" required />
            <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        {error && <p className="text-red-500 text-xs text-center font-bold uppercase">{error}</p>}

        <button type="submit" disabled={loading} className="w-full bg-green-600 hover:bg-green-500 text-white font-black py-4 rounded-xl uppercase tracking-widest text-xs flex items-center justify-center gap-2 transition-all">
          {loading ? <Loader2 className="animate-spin" size={18} /> : "Accéder au dashboard"}
        </button>
      </form>
    </div>
  );
};

export default Login;