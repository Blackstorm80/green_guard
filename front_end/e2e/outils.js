import { expect } from "@playwright/test";

export const MOT_DE_PASSE = "E2e-motdepasse-solide-42";

export const emailUnique = () =>
  `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;

/** Inscrit un compte neuf puis s'y connecte ; renvoie son e-mail. */
export async function inscrireEtConnecter(page, nom = "Testeur E2E") {
  const email = emailUnique();
  await page.goto("/register");
  await page.getByLabel("Nom complet").fill(nom);
  await page.getByLabel("Adresse e-mail").fill(email);
  await page.getByRole("textbox", { name: "Mot de passe", exact: true }).fill(MOT_DE_PASSE);
  await page.getByLabel("Confirmation du mot de passe").fill(MOT_DE_PASSE);
  await page.getByRole("button", { name: "Créer mon compte" }).click();
  await expect(page.getByText("Votre compte est prêt")).toBeVisible();

  await page.goto("/login");
  await page.getByLabel("Adresse e-mail").fill(email);
  await page.getByRole("textbox", { name: "Mot de passe", exact: true }).fill(MOT_DE_PASSE);
  await page.getByRole("button", { name: "Se connecter" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  return email;
}

/** Ouvre le menu latéral s'il est replié (mobile). */
export async function ouvrirMenuSiBesoin(page) {
  const bouton = page.getByRole("button", { name: "Ouvrir le menu" });
  if (await bouton.isVisible()) await bouton.click();
}
