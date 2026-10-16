import { expect, test } from "@playwright/test";

test("register, create a monitor, pause/resume it, then delete it", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;

  await page.goto("/register");
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Senha").fill("a-strong-password");
  await page.getByRole("button", { name: "Criar conta" }).click();

  await expect(page).toHaveURL("/dashboard");
  await expect(page.getByText(email)).toBeVisible();

  await page.getByLabel("Nome").fill("Exemplo E2E");
  await page.getByLabel("URL").fill("https://example.com");
  await page.getByRole("button", { name: "Adicionar monitor" }).click();

  const monitorRow = page.locator("li", { hasText: "Exemplo E2E" });
  await expect(monitorRow).toBeVisible();
  await expect(monitorRow.getByText("Desconhecido")).toBeVisible();

  await monitorRow.getByRole("button", { name: "Pausar" }).click();
  await expect(monitorRow.getByText("Pausado")).toBeVisible();

  await monitorRow.getByRole("button", { name: "Retomar" }).click();
  await expect(monitorRow.getByText("Desconhecido")).toBeVisible();

  await monitorRow.getByRole("button", { name: "Excluir" }).click();
  await expect(page.getByText("Exemplo E2E")).not.toBeVisible();
  await expect(page.getByText(/nenhum monitor/i)).toBeVisible();
});
