"use client";

import { useState, type FormEvent } from "react";

interface MonitorFormProps {
  onCreate: (input: { name: string; url: string }) => Promise<void>;
}

export function MonitorForm({ onCreate }: MonitorFormProps) {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await onCreate({ name, url });
      setName("");
      setUrl("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar o monitor.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <label className="flex flex-1 flex-col gap-1 text-sm text-zinc-700 dark:text-zinc-300">
        Nome
        <input
          required
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Meu site"
          className="rounded-md border border-zinc-300 px-3 py-2 text-black dark:border-zinc-700 dark:bg-zinc-900 dark:text-white"
        />
      </label>
      <label className="flex flex-1 flex-col gap-1 text-sm text-zinc-700 dark:text-zinc-300">
        URL
        <input
          type="url"
          required
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://meusite.com"
          className="rounded-md border border-zinc-300 px-3 py-2 text-black dark:border-zinc-700 dark:bg-zinc-900 dark:text-white"
        />
      </label>
      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-md bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-white dark:text-black"
      >
        {isSubmitting ? "Adicionando..." : "Adicionar monitor"}
      </button>
      {error && <p className="text-sm text-red-600 dark:text-red-400 sm:w-full">{error}</p>}
    </form>
  );
}
