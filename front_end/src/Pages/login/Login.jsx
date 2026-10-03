import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AtSign, Eye, EyeOff, Lock } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useTitrePage } from "../../lib/hooks";
import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Alert } from "../../components/ui/Card";
import AuthLayout from "./AuthLayout";

const Login = () => {
  useTitrePage("Connexion");
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
      // Retour à la page demandée avant la redirection vers la connexion
      navigate(location.state?.from || "/dashboard", { replace: true });
    } catch (err) {
      setError(err.message || "Identifiants incorrects.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout titre="Connexion" sousTitre="Suivez la santé et les besoins en eau de vos espaces verts.">
      <form onSubmit={handleLogin} className="space-y-5" noValidate={false}>
        <Field
          label="Adresse e-mail"
          type="email"
          icone={AtSign}
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Field label="Mot de passe" icone={Lock} required>
          {(props) => (
            <div className="relative">
              <input
                {...props}
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className={`${props.className} pr-11`}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
                aria-pressed={showPassword}
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1.5 text-fg-muted hover:text-fg"
              >
                {showPassword ? <EyeOff size={18} aria-hidden /> : <Eye size={18} aria-hidden />}
              </button>
            </div>
          )}
        </Field>

        {error && <Alert ton="danger">{error}</Alert>}

        <Button type="submit" chargement={loading} className="w-full" taille="lg">
          {loading ? "Connexion…" : "Se connecter"}
        </Button>
      </form>

      <p className="mt-6 border-t border-line pt-5 text-center text-sm text-fg-muted">
        Pas encore de compte ?{" "}
        <Link to="/register" className="font-semibold text-success underline-offset-4 hover:underline">
          Créer un compte
        </Link>
      </p>
    </AuthLayout>
  );
};

export default Login;
