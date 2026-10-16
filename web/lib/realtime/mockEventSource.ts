/**
 * jsdom (the test environment) doesn't implement `EventSource`. This stub
 * stands in for it so components that call `useMonitorEvents` can render in
 * tests without crashing, and tests that care about streaming can grab the
 * latest instance and call `.emit(...)` to simulate a server-sent message.
 */
export class MockEventSource {
  static instances: MockEventSource[] = [];

  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  readyState = 0;
  closed = false;
  readonly url: string;

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  close(): void {
    this.closed = true;
    this.readyState = 2;
  }

  emit(data: unknown): void {
    this.onmessage?.(new MessageEvent("message", { data: JSON.stringify(data) }));
  }
}

export function installMockEventSource(): void {
  MockEventSource.instances = [];
  Object.defineProperty(globalThis, "EventSource", {
    value: MockEventSource,
    writable: true,
    configurable: true,
  });
}
