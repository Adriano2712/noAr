import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { IncidentList } from "./IncidentList";
import type { components } from "@/lib/api/schema";

type Incident = components["schemas"]["IncidentRead"];

function makeIncident(overrides: Partial<Incident> = {}): Incident {
  return {
    id: "1",
    started_at: "2026-01-01T00:00:00Z",
    resolved_at: null,
    ...overrides,
  };
}

describe("IncidentList", () => {
  it("shows an empty state when there are no incidents", () => {
    render(<IncidentList incidents={[]} />);

    expect(screen.getByText(/nenhum incidente/i)).toBeInTheDocument();
  });

  it("labels an open incident and shows its running duration", () => {
    const startedAt = new Date(Date.now() - 90 * 60_000).toISOString();
    render(<IncidentList incidents={[makeIncident({ started_at: startedAt })]} />);

    expect(screen.getByText("Em aberto")).toBeInTheDocument();
    expect(screen.getByText("1h30min")).toBeInTheDocument();
  });

  it("labels a resolved incident and shows its total duration", () => {
    const startedAt = new Date("2026-01-01T00:00:00Z");
    const resolvedAt = new Date(startedAt.getTime() + 10 * 60_000);
    render(
      <IncidentList
        incidents={[
          makeIncident({
            started_at: startedAt.toISOString(),
            resolved_at: resolvedAt.toISOString(),
          }),
        ]}
      />
    );

    expect(screen.getByText("Resolvido")).toBeInTheDocument();
    expect(screen.getByText("10 min")).toBeInTheDocument();
  });
});
