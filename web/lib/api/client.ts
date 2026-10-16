import createClient from "openapi-fetch";
import type { paths } from "./schema";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const api = createClient<paths>({
  baseUrl: API_BASE_URL,
  // Resolve fetch at call time, not at client-creation time: openapi-fetch
  // would otherwise capture whatever `globalThis.fetch` was when this
  // module first loaded, which breaks tests that stub fetch per test.
  fetch: (...args: Parameters<typeof fetch>) => globalThis.fetch(...args),
});

let authToken: string | null = null;

export function setAuthToken(token: string | null): void {
  authToken = token;
}

api.use({
  onRequest({ request }) {
    if (authToken) {
      request.headers.set("Authorization", `Bearer ${authToken}`);
    }
    return request;
  },
});
