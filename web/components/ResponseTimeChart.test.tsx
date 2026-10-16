import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResponseTimeChart } from "./ResponseTimeChart";
import type { components } from "@/lib/api/schema";

type Check = components["schemas"]["CheckRead"];

function makeCheck(overrides: Partial<Check> = {}): Check {
  return {
    id: "1",
    started_at: "2026-01-01T00:00:00Z",
    finished_at: "2026-01-01T00:00:01Z",
    success: true,
    status_code: 200,
    response_time_ms: 120,
    error_message: null,
    ...overrides,
  };
}

describe("ResponseTimeChart", () => {
  it("shows an empty state when there is no response time data", () => {
    render(<ResponseTimeChart checks={[]} />);

    expect(screen.getByText(/ainda não há checagens/i)).toBeInTheDocument();
  });

  it("renders without crashing when given checks with response times", () => {
    const { container } = render(
      <ResponseTimeChart
        checks={[makeCheck({ id: "1" }), makeCheck({ id: "2", response_time_ms: 200 })]}
      />
    );

    expect(container.querySelector(".recharts-responsive-container")).toBeInTheDocument();
  });
});
