"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/AuthContext";

export default function SettingsPage() {
  const { user, isLoading: isAuthLoading, refreshUser } = useAuth();
  const router = useRouter();
  const [telegramChatId, setTelegramChatId] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.replace("/login");
    }
  }, [isAuthLoading, user, router]);

  useEffect(() => {
    if (user) {
      // Prefill the form once the user resolves -- synchronizing local form
      // state with data from AuthContext, not a reaction to render state.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTelegramChatId(user.telegram_chat_id ?? "");
      setWebhookUrl(user.webhook_url ?? "");
    }
  }, [user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);
    setIsSubmitting(true);
    try {
      const { error: apiError } = await api.PATCH("/auth/me", {
        body: {
          telegram_chat_id: telegramChatId.trim() === "" ? null : telegramChatId.trim(),
          webhook_url: webhookUrl.trim() === "" ? null : webhookUrl.trim(),
        },
      });
      if (apiError) {
        throw new Error("Não foi possível salvar. Verifique a URL do webhook.");
      }
      await refreshUser();
      setSuccessMessage("Configurações salvas.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Algo deu errado.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isAuthLoading || !user) {
    return null;
  }

  return (
    <main className="flex flex-1 flex-col items-center gap-8 bg-zinc-50 px-6 py-10 dark:bg-black">
      <div className="w-full max-w-sm">
        <Link href="/dashboard" className="text-sm text-zinc-600 underline dark:text-zinc-400">
          ← Voltar
        </Link>

        <h1 className="mt-4 mb-6 text-2xl font-semibold text-black dark:text-white">
          Notificações
        </h1>

        <p className="mb-6 text-sm text-zinc-600 dark:text-zinc-400">
          Você sempre recebe por e-mail em <strong>{user.email}</strong> quando um monitor cai ou
          volta ao ar. Os canais abaixo são opcionais.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1 text-sm text-zinc-700 dark:text-zinc-300">
            Telegram chat ID
            <input
              value={telegramChatId}
              onChange={(event) => setTelegramChatId(event.target.value)}
              placeholder="Ex.: 123456789"
              className="rounded-md border border-zinc-300 px-3 py-2 text-black dark:border-zinc-700 dark:bg-zinc-900 dark:text-white"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-zinc-700 dark:text-zinc-300">
            Webhook URL
            <input
              type="url"
              value={webhookUrl}
              onChange={(event) => setWebhookUrl(event.target.value)}
              placeholder="https://..."
              className="rounded-md border border-zinc-300 px-3 py-2 text-black dark:border-zinc-700 dark:bg-zinc-900 dark:text-white"
            />
          </label>
          {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
          {successMessage && (
            <p className="text-sm text-green-700 dark:text-green-400">{successMessage}</p>
          )}
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-md bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-white dark:text-black"
          >
            {isSubmitting ? "Salvando..." : "Salvar"}
          </button>
        </form>
      </div>
    </main>
  );
}
