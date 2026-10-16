import type { components } from "@/lib/api/schema";

type MonitorState = components["schemas"]["MonitorState"];

const STYLES: Record<MonitorState, string> = {
  up: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  down: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  paused: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  unknown: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
};

const LABELS: Record<MonitorState, string> = {
  up: "No ar",
  down: "Fora do ar",
  paused: "Pausado",
  unknown: "Desconhecido",
};

export function MonitorStateBadge({ state }: { state: MonitorState }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STYLES[state]}`}>
      {LABELS[state]}
    </span>
  );
}
