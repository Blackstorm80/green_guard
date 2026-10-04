import { useState } from "react";
import { Save, UserCheck, UserX } from "lucide-react";
import { api } from "../../services/api";
import { useAuth } from "../../context/AuthContext";
import { useRequete } from "../../lib/hooks";
import { LIBELLES_ROLES, ROLES, peut } from "../../lib/referentiels";
import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Alert, Badge, Card } from "../../components/ui/Card";

const chargerMembres = (signal) => api.getMembres(signal);

/** Organisation de l'utilisateur : nom (modifiable par l'admin) et membres (rôles gérés par l'admin). */
export default function Organisation() {
  const { user, rafraichirUtilisateur } = useAuth();
  const estAdmin = peut(user, "membres");
  const { donnees: membres, setDonnees: setMembres, chargement, erreur } = useRequete(chargerMembres, []);
  const [nom, setNom] = useState(user?.organisation?.nom ?? "");
  const [enregistrement, setEnregistrement] = useState(false);
  const [message, setMessage] = useState(null);

  const renommer = async (e) => {
    e.preventDefault();
    setEnregistrement(true);
    setMessage(null);
    try {
      await api.updateOrganisation({ nom: nom.trim() });
      await rafraichirUtilisateur();
      setMessage({ ton: "succes", texte: "Nom de l'organisation enregistré." });
    } catch (err) {
      setMessage({ ton: "danger", texte: err.message });
    } finally {
      setEnregistrement(false);
    }
  };

  const modifierMembre = async (membre, changement) => {
    setMessage(null);
    try {
      const maj = await api.updateMembre(membre.id, changement);
      setMembres((liste) => liste.map((m) => (m.id === maj.id ? maj : m)));
      // Ses propres droits ont changé : le menu et les actions doivent suivre
      if (maj.id === user?.id) await rafraichirUtilisateur();
    } catch (err) {
      setMessage({ ton: "danger", texte: err.message });
    }
  };

  return (
    <Card aria-labelledby="titre-organisation">
      <h2 id="titre-organisation" className="text-lg font-semibold text-fg">Organisation</h2>

      {estAdmin ? (
        <form onSubmit={renommer} className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
          <Field label="Nom de l'organisation" className="flex-1" maxLength={120} required
                 value={nom} onChange={(e) => setNom(e.target.value)} />
          <Button type="submit" icone={Save} chargement={enregistrement}
                  disabled={!nom.trim() || nom.trim() === user?.organisation?.nom}>
            Enregistrer
          </Button>
        </form>
      ) : (
        <p className="mt-2 font-medium text-fg">{user?.organisation?.nom}</p>
      )}

      {message && <Alert ton={message.ton} className="mt-4">{message.texte}</Alert>}
      {erreur && <Alert ton="danger" className="mt-4">{erreur}</Alert>}

      <div className="relative mt-6 overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-sm">
          <caption className="mb-2 text-left font-semibold text-fg">Membres ({membres.length})</caption>
          <thead className="border-b border-line bg-surface-raised text-fg-muted">
            <tr>
              <th scope="col" className="px-3 py-2 font-semibold">Nom</th>
              <th scope="col" className="px-3 py-2 font-semibold">Adresse e-mail</th>
              <th scope="col" className="px-3 py-2 font-semibold">Rôle</th>
              <th scope="col" className="px-3 py-2 font-semibold">Statut</th>
              {estAdmin && <th scope="col" className="px-3 py-2"><span className="sr-only">Actions</span></th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {chargement && (
              <tr><td colSpan={5} className="px-3 py-4 text-center text-fg-muted" role="status">Chargement…</td></tr>
            )}
            {membres.map((membre) => (
              <tr key={membre.id} className="text-fg-soft">
                <td className="px-3 py-2 font-medium text-fg">{membre.name}</td>
                <td className="break-all px-3 py-2">{membre.email}</td>
                <td className="px-3 py-2">
                  {estAdmin ? (
                    <select
                      aria-label={`Rôle de ${membre.name}`}
                      value={membre.role}
                      onChange={(e) => modifierMembre(membre, { role: e.target.value })}
                      className="rounded-[var(--radius-control)] border border-line-strong bg-surface px-2 py-1 text-fg focus:outline-none focus-visible:ring-2 focus-visible:ring-focus/40"
                    >
                      {ROLES.map((role) => <option key={role} value={role}>{LIBELLES_ROLES[role]}</option>)}
                    </select>
                  ) : (LIBELLES_ROLES[membre.role] ?? membre.role)}
                </td>
                <td className="px-3 py-2">
                  <Badge ton={membre.is_active ? "succes" : "neutre"}>{membre.is_active ? "Actif" : "Désactivé"}</Badge>
                </td>
                {estAdmin && (
                  <td className="px-3 py-2 text-right">
                    <Button variante="fantome" taille="sm" icone={membre.is_active ? UserX : UserCheck}
                            onClick={() => modifierMembre(membre, { is_active: !membre.is_active })}
                            aria-label={`${membre.is_active ? "Désactiver" : "Réactiver"} ${membre.name}`}>
                      {membre.is_active ? "Désactiver" : "Réactiver"}
                    </Button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
