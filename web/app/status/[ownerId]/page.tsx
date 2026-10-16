"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { MonitorStateBadge } from "@/components/MonitorStateBadge";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type PublicMonitor = components["schemas"]["PublicMonitorRead"];

function bannerClassName(monitors: PublicMonitor[]): string {
  if (monitors.length === 0) {
    return "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";
  }
  if (monitors.some((monitor) => monitor.state === "down")) {
    return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
  }
  if (monitors.every((monitor) => monitor.state === "up")) {
    return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
  }
  return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
}

function bannerText(monitors: PublicMonitor[]): string {
  if (monitors.length === 0) {
    return "Nenhum serviço público nesta página.";
  }
  if (monitors.some((monitor) => monitor.state === "down")) {
    return "Alguns serviços estão fora do ar";
  }
  if (monitors.every((monitor) => monitor.state === "up")) {
    return "Tudo operacional";
  }
  return "Status desconhecido";
}

export default function StatusPage() {
  const params = useParams<{ ownerId: string }>();
  const [monitors, setMonitors] = useState<PublicMonitor[] | null>(null);

  useEffect(() => {
    // Fetch-on-mount for this page's (public, no auth) data.
    api
      .GET("/status/{owner_id}", { params: { path: { owner_id: params.ownerId } } })
      .then(({ data }) => setMonitors(data?.monitors ?? []));
  }, [params.ownerId]);

  if (monitors === null) {
    return null;
  }

  return (
    <main className="flex flex-1 flex-col items-center gap-8 bg-zinc-50 px-6 py-10 dark:bg-black">
      <div className="w-full max-w-2xl">
        <h1 className="mb-4 text-2xl font-semibold text-black dark:text-white">Status</h1>

        <div className={`mb-6 rounded-md px-4 py-3 text-sm font-medium ${bannerClassName(monitors)}`}>
          {bannerText(monitors)}
        </div>

        <ul className="flex flex-col gap-3">
          {monitors.map((monitor) => (
            <li
              key={monitor.id}
              className="flex items-center justify-between rounded-md border border-zinc-200 p-4 dark:border-zinc-800"
            >
              <div>
                <p className="font-medium text-black dark:text-white">{monitor.name}</p>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">{monitor.url}</p>
              </div>
              <div className="flex items-center gap-3">
                {monitor.uptime_percentage !== null && (
                  <span className="text-sm text-zinc-500 dark:text-zinc-400">
                    {monitor.uptime_percentage}% uptime
                  </span>
                )}
                <MonitorStateBadge state={monitor.state} />
              </div>
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}
