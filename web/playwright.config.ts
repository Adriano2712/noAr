import { defineConfig } from "@playwright/test";

const PORT = 3100;
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? `http://localhost:${PORT}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  // Run e2e against a production build, not `next dev`: the dev server's
  // Turbopack/HMR file watcher was triggering Fast Refresh mid-test (file
  // activity on the Docker bind mount is enough to trip it), which remounts
  // the DOM out from under Playwright and makes elements flicker
  // "not visible" mid-interaction. A prod build has no HMR, so this whole
  // class of flakiness disappears. Needs `task up` for api/db separately;
  // this only manages the frontend process, on its own port so it doesn't
  // collide with the dev server in docker-compose.
  webServer: {
    command: `npm run build && npm run start -- -p ${PORT}`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
});
