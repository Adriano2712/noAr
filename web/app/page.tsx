import Link from "next/link";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 bg-zinc-50 px-6 text-center dark:bg-black">
      <h1 className="text-4xl font-semibold tracking-tight text-black dark:text-zinc-50">
        NoAr
      </h1>
      <p className="max-w-md text-lg text-zinc-600 dark:text-zinc-400">
        Monitor de disponibilidade de sites e APIs.
      </p>
      <div className="flex gap-4">
        <Link
          href="/login"
          className="rounded-md bg-black px-4 py-2 text-sm font-medium text-white dark:bg-white dark:text-black"
        >
          Entrar
        </Link>
        <Link
          href="/register"
          className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-black dark:border-zinc-700 dark:text-white"
        >
          Criar conta
        </Link>
      </div>
    </main>
  );
}
