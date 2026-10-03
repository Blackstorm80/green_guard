import { Logo } from "../../components/ui/Logo";

/** Gabarit des pages publiques (connexion, inscription). */
export default function AuthLayout({ titre, sousTitre, children }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-4 py-10">
      <div className="w-full max-w-md space-y-6">
        <div className="flex justify-center">
          <Logo />
        </div>
        <div className="rounded-[var(--radius-card)] border border-line bg-surface p-6 shadow-xl sm:p-8">
          <h1 className="text-2xl font-bold text-fg">{titre}</h1>
          {sousTitre && <p className="mt-1 text-sm text-fg-muted">{sousTitre}</p>}
          <div className="mt-6">{children}</div>
        </div>
      </div>
    </main>
  );
}
