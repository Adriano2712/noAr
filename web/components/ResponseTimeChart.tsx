"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { components } from "@/lib/api/schema";

type Check = components["schemas"]["CheckRead"];

interface ResponseTimeChartProps {
  checks: Check[];
}

export function ResponseTimeChart({ checks }: ResponseTimeChartProps) {
  const data = [...checks]
    .filter((check) => check.response_time_ms !== null)
    .reverse()
    .map((check) => ({
      time: new Date(check.started_at).toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      }),
      responseTimeMs: check.response_time_ms,
    }));

  if (data.length === 0) {
    return (
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Ainda não há checagens com tempo de resposta registrado.
      </p>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            className="stroke-zinc-200 dark:stroke-zinc-800"
          />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 12 }}
            tickLine={false}
            className="fill-zinc-500 dark:fill-zinc-400"
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickLine={false}
            width={48}
            className="fill-zinc-500 dark:fill-zinc-400"
            label={{ value: "ms", angle: -90, position: "insideLeft", fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{ fontSize: 12 }}
            formatter={(value) => [`${value} ms`, "Tempo de resposta"]}
          />
          <Line
            type="monotone"
            dataKey="responseTimeMs"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
