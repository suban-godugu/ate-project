/** @type {import('next').NextConfig} */
const nextConfig = {
  // Namespace Next.js assets and routes when proxied through VERILUMEN :3000.
  basePath: process.env.NEXT_EMBED_BASE_PATH || "/embed/scan",
  reactStrictMode: true,
  // Hide Next.js "N" floating badge when embedded in VERILUMEN
  devIndicators: false,
  typescript: { ignoreBuildErrors: true },
  eslint: { ignoreDuringBuilds: true },
  async rewrites() {
    const backend =
      process.env.ATE_API_PROXY ||
      process.env.BACKEND_URL ||
      "http://127.0.0.1:18030";
    return [
      { source: "/api/:path*", destination: `${backend}/api/:path*` },
      { source: "/docs", destination: `${backend}/docs` },
      { source: "/docs/:path*", destination: `${backend}/docs/:path*` },
      { source: "/openapi.json", destination: `${backend}/openapi.json` },
      { source: "/redoc", destination: `${backend}/redoc` },
    ];
  },
};

export default nextConfig;
