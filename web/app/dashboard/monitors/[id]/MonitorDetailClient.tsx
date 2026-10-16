"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { IncidentList } from "@/components/IncidentList";
import { MonitorStateBadge } from "@/components/MonitorStateBadge";
import { ResponseTimeChart } from "@/components/ResponseTimeChart";
import { API_BASE_URL, api } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/AuthContext";
import { useMonitorEvents, type MonitorEvent } from "@/lib/realtime/useMonitorEvents";
import type { components } from "@/lib/api/schema";

type Monitor = components["schemas"]["MonitorRead"];
type Check = components["schemas"]["CheckRead"];
type Incident = components["schemas"]["IncidentRead"];

function uptimePercentage(checks: Check[]): number | null {
  if (checks.length === 0) return null;
  const successCount = checks.filter((check) => check.success).length;
  return Math.round((successCount / checks.length) * 1000) / 10;
}

export function MonitorDetailClient({ monitorId }: { monitorId: string }) {
  const { user, token, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();
  const [monitor, setMonitor] = useState<Monitor | null>(null);
  const [checks, setChecks] = useState<Check[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(true);

  const loadData = useCallback(async () => {
    const [monitorRes, checksRes, incidentsRes] = await Promise.all([
      api.GET("/monitors/{monitor_id}", { params: { path: { monitor_id: monitorId } } }),
      api.GET("/monitors/{monitor_id}/checks", {
        params: { path: { monitor_id: monitorId }, query: { limit: 100 } },
      }),
      api.GET("/monitors/{monitor_id}/incidents", {
        params: { path: { monitor_id: monitorId } },
      }),
    ]);
    setMonitor(monitorRes.data ?? null);
    setChecks(checksRes.data ?? []);
    setIncidents(incidentsRes.data ?? []);
    setIsLoadingData(false);
  }, [monitorId]);

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.replace("/login");
    }
  }, [isAuthLoading, user, router]);

  useEffect(() => {
    if (user) {
      // Fetch-on-mount for the monitor's detail data, same pattern as the
      // dashboard list (see app/dashboard/page.tsx).
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadData();
    }
  }, [user, loadData]);

  const handleMonitorEvent = useCallback(
    (event: MonitorEvent) => {
      if (event.monitor_id === monitorId) {
        loadData();
      }
    },
    [monitorId, loadData]
  );

  useMonitorEvents(
    token ? `${API_BASE_URL}/monitors/stream?token=${encodeURIComponent(token)}` : null,
    handleMonitorEvent
  );

  async function handleTogglePublic(): Promise<void> {
    if (!monitor) return;
    await api.PATCH("/monitors/{monitor_id}", {
      params: { path: { monitor_id: monitorId } },
      body: { is_public: !monitor.is_public },
    });
    await loadData();
  }

  if (isAuthLoading || !user || isLoadingData || !monitor) {
    return null;
  }

  const uptime = uptimePercentage(checks);

  return (
    <main className="flex flex-1 flex-col gap-8 bg-zinc-50 px-6 py-10 dark:bg-black">
      <div className="mx-auto flex w-full max-w-2xl flex-col gap-6">
        <Link href="/dashboard" className="text-sm text-zinc-600 underline dark:text-zinc-400">
          ← Voltar
        </Link>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-black dark:text-white">{monitor.name}</h1>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">{monitor.url}</p>
          </div>
          <div className="flex items-center gap-3">
            <MonitorStateBadge state={monitor.state} />
            <button
              onClick={handleTogglePublic}
              className="rounded-md border border-zinc-300 px-3 py-1 text-sm dark:border-zinc-700"
            >
              {monitor.is_public ? "Tornar privado" : "Tornar público"}
            </button>
          </div>
        </div>

        {monitor.is_public && (
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Visível em{" "}
            <Link href={`/status/${user.id}`} className="underline" target="_blank">
              /status/{user.id}
            </Link>
          </p>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-md border border-zinc-200 p-4 dark:border-zinc-800">
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Uptime (últimas {checks.length} checagens)
            </p>
            <p className="text-2xl font-semibold text-black dark:text-white">
              {uptime === null ? "—" : `${uptime}%`}
            </p>
          </div>
          <div className="rounded-md border border-zinc-200 p-4 dark:border-zinc-800">
            <p className="text-xs text-zinc-500 dark:text-zinc-400">Incidentes</p>
            <p className="text-2xl font-semibold text-black dark:text-white">
              {incidents.length}
            </p>
          </div>
        </div>

        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-medium text-black dark:text-white">Tempo de resposta</h2>
          <ResponseTimeChart checks={checks} />
        </section>

        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-medium text-black dark:text-white">Incidentes</h2>
          <IncidentList incidents={incidents} />
        </section>
      </div>
    </main>
  );
}
