import { Link } from "react-router-dom";

export default function PageIntrouvable() {
  return (
    <section className="flex flex-col items-center justify-center text-center py-24 space-y-4">
      <p className="text-6xl font-black text-fg-subtle">404</p>
      <h1 className="text-2xl font-bold text-fg">Page introuvable</h1>
      <p className="text-fg-muted max-w-md">Cette adresse ne correspond à aucune page de GreenGuard.</p>
      <Link
        to="/dashboard"
        className="mt-2 bg-primary hover:bg-primary-hover text-on-accent px-5 py-2 rounded-xl font-bold focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
      >
        Retour au tableau de bord
      </Link>
    </section>
  );
}
