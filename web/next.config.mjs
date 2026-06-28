/** @type {import("next").NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // BFF proxy: the browser hits the web origin at /api/*, which Next forwards
    // server-to-server to FastAPI. API_BASE_URL is set per-environment (the
    // compose network resolves `api`); fall back to localhost for `next dev`.
    const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiBaseUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
