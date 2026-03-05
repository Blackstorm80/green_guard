// front_end/src/Pages/login/Login.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../services/api";
import { Lock, AtSign, Eye, EyeOff } from "lucide-react";

const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@greenguard.com");
  const [password, setPassword] =useState("password");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.login(email, password);
      navigate("/"); // Redirection vers le dashboard après succès
    } catch (err) {
      setError(err.message || "Une erreur est survenue.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900 bg-cover bg-center animate-in fade-in duration-500" style={{ backgroundImage: 'url("/path/to/your/background-image.jpg")' }}>
        <div className="w-full max-w-md">
            <form
              onSubmit={handleLogin}
              className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/50 rounded-2xl shadow-2xl p-8 space-y-6"
            >
                <div className="text-center">
                    <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-green-800 rounded-2xl flex items-center justify-center shadow-lg mx-auto mb-4">
                        <span className="text-white font-bold text-4xl">G</span>
                    </div>
                    <h1 className="text-3xl font-bold text-white">Green Guard</h1>
                    <p className="text-slate-400">Connectez-vous pour piloter vos espaces.</p>
                </div>
                
                <div className="relative">
                    <AtSign className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={20}/>
                    <input
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className="w-full bg-gray-800/50 border border-slate-700 rounded-lg pl-11 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all"
                    />
                </div>

                <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={20}/>
                    <input
                        type={showPassword ? "text" : "password"}
                        placeholder="Mot de passe"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        className="w-full bg-gray-800/50 border border-slate-700 rounded-lg pl-11 pr-11 py-3 text-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all"
                    />
                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                        {showPassword ? <EyeOff size={20}/> : <Eye size={20}/>}
                    </button>
                </div>

                {error && <p className="text-red-500 text-sm text-center">{error}</p>}

                <div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-teal-600 hover:bg-teal-500 disabled:bg-teal-800 disabled:cursor-not-allowed text-white font-bold py-3 rounded-lg shadow-lg transition-all duration-300"
                    >
                        {loading ? "Connexion..." : "Se connecter"}
                    </button>
                </div>
                <p className="text-center text-xs text-slate-500">
                    Problème de connexion ? Contactez le support.
                </p>
            </form>
        </div>
    </div>
  );
};

export default Login;
