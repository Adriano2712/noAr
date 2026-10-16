import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useMonitorEvents } from "./useMonitorEvents";
import { MockEventSource } from "./mockEventSource";

describe("useMonitorEvents", () => {
  beforeEach(() => {
    MockEventSource.instances = [];
  });

  it("does not open a connection when url is null", () => {
    renderHook(() => useMonitorEvents(null, vi.fn()));
    expect(MockEventSource.instances).toHaveLength(0);
  });

  it("opens a connection to the given url and forwards parsed messages", () => {
    const onEvent = vi.fn();
    renderHook(() => useMonitorEvents("http://api.test/monitors/stream?token=abc", onEvent));

    expect(MockEventSource.instances).toHaveLength(1);
    const source = MockEventSource.instances[0]!;
    expect(source.url).toBe("http://api.test/monitors/stream?token=abc");

    source.emit({ monitor_id: "m1", state: "down" });

    expect(onEvent).toHaveBeenCalledWith({ monitor_id: "m1", state: "down" });
  });

  it("ignores a malformed message instead of throwing", () => {
    const onEvent = vi.fn();
    renderHook(() => useMonitorEvents("http://api.test/monitors/stream", onEvent));

    const source = MockEventSource.instances[0]!;
    expect(() => source.onmessage?.(new MessageEvent("message", { data: "not json" }))).not.toThrow();
    expect(onEvent).not.toHaveBeenCalled();
  });

  it("closes the connection on unmount", () => {
    const { unmount } = renderHook(() =>
      useMonitorEvents("http://api.test/monitors/stream", vi.fn())
    );
    const source = MockEventSource.instances[0]!;

    unmount();

    expect(source.closed).toBe(true);
  });

  it("closes the old connection and opens a new one when the url changes", () => {
    const { rerender } = renderHook(({ url }) => useMonitorEvents(url, vi.fn()), {
      initialProps: { url: "http://api.test/monitors/stream?token=a" },
    });
    const first = MockEventSource.instances[0]!;

    rerender({ url: "http://api.test/monitors/stream?token=b" });

    expect(first.closed).toBe(true);
    expect(MockEventSource.instances).toHaveLength(2);
    expect(MockEventSource.instances[1]!.url).toBe("http://api.test/monitors/stream?token=b");
  });
});
