import { expect, test } from "@playwright/test";

test("a monitor marked public shows up on the account's status page", async ({ page, browser }) => {
  const email = `e2e-status-${Date.now()}@example.com`;

  await page.goto("/register");
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Senha").fill("a-strong-password");
  await page.getByRole("button", { name: "Criar conta" }).click();
  await expect(page).toHaveURL("/dashboard");

  await page.getByLabel("Nome").fill("Status E2E");
  await page.getByLabel("URL").fill("https://example.com");
  await page.getByRole("button", { name: "Adicionar monitor" }).click();

  await page.getByRole("link", { name: "Status E2E" }).click();
  await expect(page.getByRole("heading", { name: "Status E2E" })).toBeVisible();

  const statusLink = page.getByRole("link", { name: /\/status\// });

  // Still private: the dashboard's own status link is shown only after the
  // monitor is made public, so there's nothing to check on a fresh page yet.
  await expect(statusLink).toHaveCount(0);

  await page.getByRole("button", { name: "Tornar público" }).click();
  await expect(page.getByRole("button", { name: "Tornar privado" })).toBeVisible();

  const statusUrl = await statusLink.getAttribute("href");
  expect(statusUrl).toBeTruthy();

  // A genuinely separate browser context (no shared storage/cookies with
  // the logged-in page): the status page must not need that session.
  const publicContext = await browser.newContext();
  const publicPage = await publicContext.newPage();
  await publicPage.goto(statusUrl ?? "");

  await expect(publicPage.getByText("Status E2E")).toBeVisible();

  // The status page fetches once on load and never polls, so a freshly
  // created monitor can still read "unknown" if the worker (its own poll
  // loop, independent of this page) hasn't checked it yet -- reload until
  // it has, instead of assuming the race always resolves before we look.
  await expect(async () => {
    await publicPage.reload();
    await expect(publicPage.getByText("Tudo operacional")).toBeVisible({ timeout: 2000 });
  }).toPass({ timeout: 45_000 });

  await publicContext.close();
});
