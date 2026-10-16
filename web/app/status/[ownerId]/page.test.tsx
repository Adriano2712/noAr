import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import StatusPage from "./page";

vi.mock("next/navigation", () => ({
  useParams: () => ({ ownerId: "owner-1" }),
}));

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("StatusPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows an empty-state banner when there are no public monitors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse({ monitors: [] }))
    );

    render(<StatusPage />);

    await waitFor(() =>
      expect(screen.getByText("Nenhum serviço público nesta página.")).toBeInTheDocument()
    );
  });

  it("shows 'Tudo operacional' when every monitor is up", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        jsonResponse({
          monitors: [
            {
              id: "1",
              name: "Example",
              url: "https://example.com",
              state: "up",
              uptime_percentage: 99.5,
            },
          ],
        })
      )
    );

    render(<StatusPage />);

    await waitFor(() => expect(screen.getByText("Tudo operacional")).toBeInTheDocument());
    expect(screen.getByText("Example")).toBeInTheDocument();
    expect(screen.getByText("99.5% uptime")).toBeInTheDocument();
  });

  it("shows a down warning when any monitor is down", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        jsonResponse({
          monitors: [
            {
              id: "1",
              name: "A",
              url: "https://a.example.com",
              state: "up",
              uptime_percentage: 100,
            },
            {
              id: "2",
              name: "B",
              url: "https://b.example.com",
              state: "down",
              uptime_percentage: 50,
            },
          ],
        })
      )
    );

    render(<StatusPage />);

    await waitFor(() =>
      expect(screen.getByText("Alguns serviços estão fora do ar")).toBeInTheDocument()
    );
  });
});
