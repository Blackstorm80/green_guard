import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { inscrireEtConnecter } from "./outils";

/** Audit axe-core WCAG 2.1 A/AA : aucune violation « serious » ou « critical » tolérée. */
async function auditer(page, contexte) {
  const resultat = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  const graves = resultat.violations.filter((v) => ["serious", "critical"].includes(v.impact));
  const detail = (n) => `${n.target.join(" ")} : ${(n.failureSummary ?? "").split("\n").pop().trim()}`;
  const resume = graves.map((v) => `${v.id} (${v.impact}) : ${v.help} — ${v.nodes.map(detail).join(" | ")}`);
  expect(resume, `Violations d'accessibilité sur ${contexte}`).toEqual([]);
}

for (const theme of ["clair", "sombre"]) {
  test.describe(`Accessibilité — thème ${theme}`, () => {
    test.beforeEach(async ({ page }) => {
      await page.addInitScript((t) => localStorage.setItem("greenguard:theme", t), theme);
    });

    test("pages publiques", async ({ page }) => {
      for (const chemin of ["/login", "/register"]) {
        await page.goto(chemin);
        await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
        await auditer(page, `${chemin} (${theme})`);
      }
    });

    test("pages de l'application", async ({ page }) => {
      await inscrireEtConnecter(page);
      const pages = [
        ["/dashboard", "Tableau de bord"],
        ["/espaces", "Espaces et zones"],
        ["/catalogues", "Catalogue botanique"],
        ["/rapports", "Rapports"],
        ["/parametres", "Paramètres"],
      ];
      for (const [chemin, titre] of pages) {
        await page.goto(chemin);
        await expect(page.getByRole("heading", { level: 1, name: titre })).toBeVisible();
        await page.waitForLoadState("networkidle");
        await auditer(page, `${chemin} (${theme})`);
      }
    });

    test("modale d'ajout d'espace", async ({ page }) => {
      await inscrireEtConnecter(page);
      await page.goto("/espaces");
      await page.getByRole("button", { name: "Ajouter un espace" }).first().click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await auditer(page, `modale d'ajout (${theme})`);
    });
  });
}
