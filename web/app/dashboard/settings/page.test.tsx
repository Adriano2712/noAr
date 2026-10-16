import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SettingsPage from "./page";
import { setAuthToken } from "@/lib/api/client";
import { AuthProvider } from "@/lib/auth/AuthContext";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}));

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

const BASE_USER = {
  id: "1",
  email: "me@example.com",
  telegram_chat_id: null,
  webhook_url: null,
  created_at: "2026-01-01T00:00:00Z",
};

describe("SettingsPage", () => {
  beforeEach(() => {
    window.localStorage.setItem("noar.token", "token-123");
  });

  afterEach(() => {
    window.localStorage.clear();
    setAuthToken(null);
    vi.unstubAllGlobals();
  });

  it("prefills the form from the current user and saves changes", async () => {
    const user = userEvent.setup();
    let currentUser = { ...BASE_USER };

    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = input instanceof Request ? input.url : String(input);
      const method = input instanceof Request ? input.method : (init?.method ?? "GET");

      if (url.includes("/auth/me") && method === "GET") {
        return jsonResponse(currentUser);
      }
      if (url.includes("/auth/me") && method === "PATCH") {
        const bodyText = input instanceof Request ? await input.text() : String(init?.body);
        currentUser = { ...currentUser, ...JSON.parse(bodyText) };
        return jsonResponse(currentUser);
      }
      throw new Error(`unexpected request: ${method} ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthProvider>
        <SettingsPage />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByText("me@example.com")).toBeInTheDocument());

    const chatIdInput = screen.getByLabelText("Telegram chat ID");
    await user.type(chatIdInput, "123456789");
    await user.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => expect(screen.getByText("Configurações salvas.")).toBeInTheDocument());
    expect(currentUser.telegram_chat_id).toBe("123456789");
  });
});
