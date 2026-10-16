import { API_BASE_URL } from "./client";
import type { components } from "./schema";

type Token = components["schemas"]["Token"];

/**
 * /auth/login takes OAuth2's form-urlencoded body (FastAPI's
 * OAuth2PasswordRequestForm), not JSON, so it doesn't fit the generated
 * JSON client — this is the one endpoint that talks to the API directly.
 */
export async function login(email: string, password: string): Promise<Token> {
  const body = new URLSearchParams({ username: email, password });

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  if (!response.ok) {
    throw new Error("E-mail ou senha incorretos.");
  }

  return (await response.json()) as Token;
}
