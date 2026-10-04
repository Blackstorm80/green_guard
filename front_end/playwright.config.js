import { defineConfig, devices } from "@playwright/test";

/**
 * Tests de bout en bout : un vrai navigateur rejoue les parcours critiques contre une pile
 * démarrée (docker compose en CI). E2E_BASE_URL permet de viser une autre pile locale.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 7_000 },
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://localhost:3000",
    locale: "fr-FR",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "bureau", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] }, testMatch: /parcours\.spec\.js/ },
  ],
});
