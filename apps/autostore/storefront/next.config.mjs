/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow importing the shared .mjs pricing/checkout core from TS files.
  experimental: { esmExternals: true },
};

export default nextConfig;
