import type { components } from "@/lib/api/schema";

type Incident = components["schemas"]["IncidentRead"];

function formatDuration(startedAt: string, resolvedAt: string | null): string {
  const start = new Date(startedAt).getTime();
  const end = resolvedAt ? new Date(resolvedAt).getTime() : Date.now();
  const minutes = Math.max(0, Math.round((end - start) / 60_000));
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h${remainingMinutes.toString().padStart(2, "0")}min`;
}

export function IncidentList({ incidents }: { incidents: Incident[] }) {
  if (incidents.length === 0) {
    return (
      <p className="text-sm text-zinc-600 dark:text-zinc-400">Nenhum incidente registrado.</p>
    );
  }

  return (
    <ul className="flex flex-col gap-2">
      {incidents.map((incident) => (
        <li
          key={incident.id}
          className="flex items-center justify-between rounded-md border border-zinc-200 px-4 py-2 text-sm dark:border-zinc-800"
        >
          <span className="text-zinc-700 dark:text-zinc-300">
            {new Date(incident.started_at).toLocaleString("pt-BR")}
          </span>
          <span className="flex items-center gap-2">
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                incident.resolved_at
                  ? "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                  : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
              }`}
            >
              {incident.resolved_at ? "Resolvido" : "Em aberto"}
            </span>
            <span className="text-zinc-500 dark:text-zinc-400">
              {formatDuration(incident.started_at, incident.resolved_at)}
            </span>
          </span>
        </li>
      ))}
    </ul>
  );
}
