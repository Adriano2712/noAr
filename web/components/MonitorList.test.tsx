import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MonitorList } from "./MonitorList";
import type { components } from "@/lib/api/schema";

type Monitor = components["schemas"]["MonitorRead"];

function makeMonitor(overrides: Partial<Monitor> = {}): Monitor {
  return {
    id: "1",
    name: "Example",
    url: "https://example.com",
    interval_seconds: 60,
    timeout_seconds: 10,
    fail_threshold: 3,
    state: "up",
    consecutive_failures: 0,
    consecutive_successes: 1,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("MonitorList", () => {
  it("shows an empty state when there are no monitors", () => {
    render(
      <MonitorList monitors={[]} onPause={vi.fn()} onResume={vi.fn()} onDelete={vi.fn()} />
    );

    expect(screen.getByText(/nenhum monitor/i)).toBeInTheDocument();
  });

  it("renders each monitor with its state", () => {
    render(
      <MonitorList
        monitors={[
          makeMonitor({ name: "A" }),
          makeMonitor({ id: "2", name: "B", state: "down" }),
        ]}
        onPause={vi.fn()}
        onResume={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
    expect(screen.getByText("Fora do ar")).toBeInTheDocument();
  });

  it("calls onPause for a running monitor and onResume for a paused one", () => {
    const onPause = vi.fn();
    const onResume = vi.fn();
    render(
      <MonitorList
        monitors={[
          makeMonitor({ id: "1", state: "up" }),
          makeMonitor({ id: "2", state: "paused" }),
        ]}
        onPause={onPause}
        onResume={onResume}
        onDelete={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Pausar" }));
    expect(onPause).toHaveBeenCalledWith("1");

    fireEvent.click(screen.getByRole("button", { name: "Retomar" }));
    expect(onResume).toHaveBeenCalledWith("2");
  });

  it("calls onDelete with the monitor id", () => {
    const onDelete = vi.fn();
    render(
      <MonitorList
        monitors={[makeMonitor({ id: "42" })]}
        onPause={vi.fn()}
        onResume={vi.fn()}
        onDelete={onDelete}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Excluir" }));
    expect(onDelete).toHaveBeenCalledWith("42");
  });
});
