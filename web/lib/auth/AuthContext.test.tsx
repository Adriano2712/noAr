import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "./AuthContext";

function TestConsumer() {
  const { user, isLoading, login, logout } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="user">{user?.email ?? "none"}</span>
      <button onClick={() => login("a@example.com", "password123")}>login</button>
      <button onClick={() => logout()}>logout</button>
    </div>
  );
}

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("AuthContext", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("starts with no user and finishes loading when there is no stored token", async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId("loading")).toHaveTextContent("false"));
    expect(screen.getByTestId("user")).toHaveTextContent("none");
  });

  it("logs in, stores the token, and exposes the current user", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = input instanceof Request ? input.url : String(input);
      if (url.includes("/auth/login")) {
        return jsonResponse({ access_token: "token-123", token_type: "bearer" });
      }
      if (url.includes("/auth/me")) {
        return jsonResponse({
          id: "1",
          email: "a@example.com",
          created_at: "2026-01-01T00:00:00Z",
        });
      }
      throw new Error(`unexpected request: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByTestId("loading")).toHaveTextContent("false"));

    await act(async () => {
      screen.getByRole("button", { name: "login" }).click();
    });

    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("a@example.com"));
    expect(window.localStorage.getItem("noar.token")).toBe("token-123");
  });

  it("logout clears the user and the stored token", async () => {
    window.localStorage.setItem("noar.token", "existing-token");
    const fetchMock = vi.fn(async () =>
      jsonResponse({ id: "1", email: "a@example.com", created_at: "2026-01-01T00:00:00Z" })
    );
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("a@example.com"));

    await act(async () => {
      screen.getByRole("button", { name: "logout" }).click();
    });

    expect(screen.getByTestId("user")).toHaveTextContent("none");
    expect(window.localStorage.getItem("noar.token")).toBeNull();
  });
});
