import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Deploy bang Docker (xem frontend/Dockerfile): output standalone gom san
  // node_modules can thiet, khong phai COPY ca thu muc node_modules vao image.
  output: "standalone",
};

export default nextConfig;
