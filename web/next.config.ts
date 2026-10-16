import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Every page here is "use client" + runtime auth + runtime API calls, so
  // there is no static content for Cache Components / PPR to help with --
  // only friction (it blocked the build on any dynamic route segment, e.g.
  // app/dashboard/monitors/[id]).
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
