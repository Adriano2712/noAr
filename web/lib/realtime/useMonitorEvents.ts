"use client";

import { useEffect } from "react";
import type { components } from "@/lib/api/schema";

export interface MonitorEvent {
  monitor_id: string;
  state: components["schemas"]["MonitorState"];
}

/**
 * Subscribes to one of the backend's SSE endpoints (`/monitors/stream` or
 * `/status/{owner_id}/stream`) and calls `onEvent` for each monitor state
 * change. Pass `url: null` to stay disconnected (e.g. while auth is still
 * loading); the connection is reopened whenever `url` changes and closed on
 * unmount.
 */
export function useMonitorEvents(url: string | null, onEvent: (event: MonitorEvent) => void): void {
  useEffect(() => {
    if (!url) return;

    const source = new EventSource(url);
    source.onmessage = (message: MessageEvent<string>) => {
      try {
        onEvent(JSON.parse(message.data) as MonitorEvent);
      } catch {
        // A malformed payload shouldn't take down the page it's updating.
      }
    };

    return () => source.close();
  }, [url, onEvent]);
}
