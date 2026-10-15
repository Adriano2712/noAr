export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 bg-zinc-50 px-6 text-center dark:bg-black">
      <h1 className="text-4xl font-semibold tracking-tight text-black dark:text-zinc-50">
        NoAr
      </h1>
      <p className="max-w-md text-lg text-zinc-600 dark:text-zinc-400">
        Monitor de disponibilidade de sites e APIs.
      </p>
    </main>
  );
}
