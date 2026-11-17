import type { NextConfig } from "next";

// When BACKEND_URL is set (the public deployment), the frontend forwards /api/* to the backend
// on the server side. Browsers then only talk to the frontend's own address, which avoids
// networks whose DNS blocks or cannot resolve the backend's address. Set NEXT_PUBLIC_API_URL="/"
// alongside it so the browser calls the same origin.
const backendUrl = process.env.BACKEND_URL?.replace(/\/$/, "");

const nextConfig: NextConfig = {
  async rewrites() {
    return backendUrl ? [{ source: "/api/:path*", destination: `${backendUrl}/api/:path*` }] : [];
  },
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
