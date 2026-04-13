/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    proxyTimeout: 120_000,
  },
  webpack: (config) => {
    config.watchOptions = {
      poll: 1000,
      aggregateTimeout: 300,
    };
    return config;
  },
  async rewrites() {
    const backendUrl = process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://backend:8000";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
