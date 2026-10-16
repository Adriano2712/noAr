import { expect, test } from "@playwright/test";

test("saves notification settings and they persist after reload", async ({ page }) => {
  const email = `e2e-settings-${Date.now()}@example.com`;

  await page.goto("/register");
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Senha").fill("a-strong-password");
  await page.getByRole("button", { name: "Criar conta" }).click();
  await expect(page).toHaveURL("/dashboard");

  await page.getByRole("link", { name: "Notificações" }).click();
  await expect(page).toHaveURL("/dashboard/settings");

  await page.getByLabel("Telegram chat ID").fill("123456789");
  await page.getByLabel("Webhook URL").fill("https://example.com/hook");
  await page.getByRole("button", { name: "Salvar" }).click();

  await expect(page.getByText("Configurações salvas.")).toBeVisible();

  await page.reload();
  await expect(page.getByLabel("Telegram chat ID")).toHaveValue("123456789");
  await expect(page.getByLabel("Webhook URL")).toHaveValue("https://example.com/hook");
});
