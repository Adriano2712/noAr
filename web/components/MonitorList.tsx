import type { components } from "@/lib/api/schema";
import { MonitorStateBadge } from "./MonitorStateBadge";

type Monitor = components["schemas"]["MonitorRead"];

interface MonitorListProps {
  monitors: Monitor[];
  onPause: (id: string) => Promise<void>;
  onResume: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export function MonitorList({ monitors, onPause, onResume, onDelete }: MonitorListProps) {
  if (monitors.length === 0) {
    return (
      <p className="text-sm text-zinc-600 dark:text-zinc-400">Nenhum monitor cadastrado ainda.</p>
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {monitors.map((monitor) => (
        <li
          key={monitor.id}
          className="flex flex-col gap-2 rounded-md border border-zinc-200 p-4 dark:border-zinc-800 sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-black dark:text-white">{monitor.name}</span>
              <MonitorStateBadge state={monitor.state} />
            </div>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">{monitor.url}</p>
          </div>
          <div className="flex gap-2">
            {monitor.state === "paused" ? (
              <button
                onClick={() => onResume(monitor.id)}
                className="rounded-md border border-zinc-300 px-3 py-1 text-sm dark:border-zinc-700"
              >
                Retomar
              </button>
            ) : (
              <button
                onClick={() => onPause(monitor.id)}
                className="rounded-md border border-zinc-300 px-3 py-1 text-sm dark:border-zinc-700"
              >
                Pausar
              </button>
            )}
            <button
              onClick={() => onDelete(monitor.id)}
              className="rounded-md border border-red-300 px-3 py-1 text-sm text-red-700 dark:border-red-900 dark:text-red-400"
            >
              Excluir
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
