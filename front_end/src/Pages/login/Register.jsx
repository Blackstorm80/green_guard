import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AtSign, Building2, CheckCircle2, Lock, User } from "lucide-react";
import { api } from "../../services/api";
import { useTitrePage } from "../../lib/hooks";
import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Alert } from "../../components/ui/Card";
import AuthLayout from "./AuthLayout";

const LONGUEUR_MIN = 12;

const Register = () => {
  useTitrePage("Créer un compte");
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ name: "", email: "", password: "", confirmPassword: "", organisation: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const maj = (champ) => (e) => setFormData({ ...formData, [champ]: e.target.value });
  const confirmationKo = formData.confirmPassword && formData.confirmPassword !== formData.password;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      return setError("Les mots de passe ne correspondent pas.");
    }
    setLoading(true);
    setError("");
    try {
      await api.register({
        name: formData.name, email: formData.email, password: formData.password,
        organisation: formData.organisation.trim(),
      });
      setSuccess(true);
      setTimeout(() => navigate("/login"), 2500);
    } catch (err) {
      setError(err.message || "Erreur lors de l'inscription.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <AuthLayout titre="Compte créé">
        <div role="status" className="space-y-3 text-center">
          <CheckCircle2 className="mx-auto text-success" size={56} aria-hidden />
          <p className="text-fg-soft">Votre compte est prêt. Redirection vers la connexion…</p>
          <Link to="/login" className="font-semibold text-success hover:underline">Se connecter maintenant</Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout titre="Créer un compte" sousTitre="Quelques informations suffisent pour commencer.">
      <form onSubmit={handleSubmit} className="space-y-5">
        <Field label="Nom complet" icone={User} autoComplete="name" value={formData.name} onChange={maj("name")} required />
        <Field label="Nom de votre collectivité" icone={Building2} autoComplete="organization" maxLength={120}
               aide="Facultatif. Votre organisation est créée avec vous comme administrateur."
               value={formData.organisation} onChange={maj("organisation")} />
        <Field label="Adresse e-mail" type="email" icone={AtSign} autoComplete="email" value={formData.email}
               onChange={maj("email")} required />
        <Field label="Mot de passe" type="password" icone={Lock} autoComplete="new-password" minLength={LONGUEUR_MIN}
               aide={`${LONGUEUR_MIN} caractères minimum.`} value={formData.password} onChange={maj("password")} required />
        <Field label="Confirmation du mot de passe" type="password" icone={Lock} autoComplete="new-password"
               minLength={LONGUEUR_MIN} value={formData.confirmPassword} onChange={maj("confirmPassword")}
               erreur={confirmationKo ? "Les deux mots de passe sont différents." : undefined} required />

        {error && <Alert ton="danger">{error}</Alert>}

        <Button type="submit" chargement={loading} className="w-full" taille="lg">
          {loading ? "Création…" : "Créer mon compte"}
        </Button>
      </form>

      <p className="mt-6 border-t border-line pt-5 text-center text-sm text-fg-muted">
        Déjà inscrit ?{" "}
        <Link to="/login" className="font-semibold text-success underline-offset-4 hover:underline">Se connecter</Link>
      </p>
    </AuthLayout>
  );
};

export default Register;
