"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { MonitorForm } from "@/components/MonitorForm";
import { MonitorList } from "@/components/MonitorList";
import { api } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/AuthContext";
import type { components } from "@/lib/api/schema";

type Monitor = components["schemas"]["MonitorRead"];

export default function DashboardPage() {
  const { user, isLoading: isAuthLoading, logout } = useAuth();
  const router = useRouter();
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [isLoadingMonitors, setIsLoadingMonitors] = useState(true);

  const loadMonitors = useCallback(async () => {
    const { data } = await api.GET("/monitors");
    setMonitors(data ?? []);
    setIsLoadingMonitors(false);
  }, []);

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.replace("/login");
    }
  }, [isAuthLoading, user, router]);

  useEffect(() => {
    if (user) {
      // Fetch-on-mount (and when the user becomes available): the standard
      // pattern for loading data a component needs as soon as it can.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadMonitors();
    }
  }, [user, loadMonitors]);

  async function handleCreate(input: { name: string; url: string }): Promise<void> {
    const { error } = await api.POST("/monitors", {
      body: {
        name: input.name,
        url: input.url,
        interval_seconds: 60,
        timeout_seconds: 10,
        fail_threshold: 3,
      },
    });
    if (error) {
      throw new Error("Não foi possível criar o monitor. Verifique a URL.");
    }
    await loadMonitors();
  }

  async function handlePause(id: string): Promise<void> {
    await api.POST("/monitors/{monitor_id}/pause", { params: { path: { monitor_id: id } } });
    await loadMonitors();
  }

  async function handleResume(id: string): Promise<void> {
    await api.POST("/monitors/{monitor_id}/resume", { params: { path: { monitor_id: id } } });
    await loadMonitors();
  }

  async function handleDelete(id: string): Promise<void> {
    await api.DELETE("/monitors/{monitor_id}", { params: { path: { monitor_id: id } } });
    await loadMonitors();
  }

  if (isAuthLoading || !user) {
    return null;
  }

  return (
    <main className="flex flex-1 flex-col gap-8 bg-zinc-50 px-6 py-10 dark:bg-black">
      <div className="mx-auto flex w-full max-w-2xl items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-black dark:text-white">Meus monitores</h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">{user.email}</p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/dashboard/settings"
            className="rounded-md border border-zinc-300 px-3 py-1 text-sm dark:border-zinc-700"
          >
            Notificações
          </Link>
          <button
            onClick={logout}
            className="rounded-md border border-zinc-300 px-3 py-1 text-sm dark:border-zinc-700"
          >
            Sair
          </button>
        </div>
      </div>

      <div className="mx-auto flex w-full max-w-2xl flex-col gap-6">
        <MonitorForm onCreate={handleCreate} />
        {isLoadingMonitors ? (
          <p className="text-sm text-zinc-600 dark:text-zinc-400">Carregando...</p>
        ) : (
          <MonitorList
            monitors={monitors}
            onPause={handlePause}
            onResume={handleResume}
            onDelete={handleDelete}
          />
        )}
      </div>
    </main>
  );
}
