import { expect, test } from "@playwright/test";
import { inscrireEtConnecter, MOT_DE_PASSE, ouvrirMenuSiBesoin } from "./outils";

test.describe("Parcours critiques", () => {
  test("une route protégée renvoie vers la connexion", async ({ page }) => {
    await page.goto("/rapports");
    await expect(page).toHaveURL(/\/login$/);
    await expect(page).toHaveTitle("Connexion · GreenGuard");
  });

  test("identifiants incorrects : message d'erreur sans connexion", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Adresse e-mail").fill("inconnu@example.com");
    await page.getByRole("textbox", { name: "Mot de passe", exact: true }).fill(MOT_DE_PASSE);
    await page.getByRole("button", { name: "Se connecter" }).click();
    await expect(page.getByRole("alert")).toContainText("incorrect");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("inscription, tableau de bord vide, déconnexion", async ({ page, context }) => {
    await inscrireEtConnecter(page);
    await expect(page.getByRole("heading", { level: 1, name: "Tableau de bord" })).toBeVisible();
    await expect(page.getByText("Aucun espace vert enregistré pour le moment.")).toBeVisible();

    // La session vit dans un cookie httpOnly : rien n'est lisible côté JavaScript
    expect(await page.evaluate(() => document.cookie)).toBe("");
    const cookies = await context.cookies();
    expect(cookies.find((c) => c.name === "gg_session")?.httpOnly).toBe(true);

    await ouvrirMenuSiBesoin(page);
    await page.getByRole("button", { name: "Se déconnecter" }).click();
    await expect(page).toHaveURL(/\/login$/);
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("créer, modifier puis supprimer un espace vert", async ({ page }) => {
    await inscrireEtConnecter(page);
    await page.goto("/espaces");
    await page.getByRole("button", { name: "Ajouter un espace" }).first().click();

    const dialogue = page.getByRole("dialog", { name: "Nouvel espace vert" });
    await expect(dialogue).toBeVisible();
    await expect(dialogue.getByLabel(/Nom de l'espace/)).toBeFocused();
    await dialogue.getByLabel(/Nom de l'espace/).fill("Parc E2E");
    await dialogue.getByLabel("Ville ou commune").fill("Lyon");
    await dialogue.getByLabel(/Latitude/).fill("45.7640");
    await dialogue.getByLabel(/Longitude/).fill("4.8357");
    await dialogue.getByRole("button", { name: "Enregistrer l'espace" }).click();
    await expect(dialogue).toBeHidden();

    const carte = page.getByRole("button", { name: "Modifier Parc E2E" });
    await expect(carte).toBeVisible();
    await carte.click();
    const edition = page.getByRole("dialog", { name: "Modifier « Parc E2E »" });
    await edition.getByLabel(/^Nom/).fill("Parc E2E renommé");
    await edition.getByRole("button", { name: "Enregistrer", exact: true }).click();
    await expect(page.getByRole("button", { name: "Modifier Parc E2E renommé" })).toBeVisible();

    await page.getByRole("button", { name: "Modifier Parc E2E renommé" }).click();
    const suppression = page.getByRole("dialog");
    await suppression.getByRole("button", { name: "Supprimer l'espace" }).click();
    await suppression.getByRole("button", { name: "Oui, supprimer" }).click();
    await expect(page.getByText("Aucun espace vert pour le moment")).toBeVisible();
  });

  test("la modale se ferme avec Échap et rend le focus", async ({ page }) => {
    await inscrireEtConnecter(page);
    await page.goto("/espaces");
    const ouvrir = page.getByRole("button", { name: "Ajouter un espace" }).first();
    await ouvrir.click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).toBeHidden();
    await expect(ouvrir).toBeFocused();
  });

  test("le choix du thème est conservé après rechargement", async ({ page }) => {
    await inscrireEtConnecter(page);
    await page.goto("/parametres");
    await page.getByText("Sombre", { exact: true }).click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await page.getByText("Clair", { exact: true }).click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  });

  test("page inconnue : 404 dans l'application", async ({ page }) => {
    await inscrireEtConnecter(page);
    await page.goto("/cette-page-n-existe-pas");
    await expect(page.getByRole("heading", { name: "Page introuvable" })).toBeVisible();
  });
});
