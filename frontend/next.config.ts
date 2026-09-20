import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Playwright uses an isolated build directory so it can run while the
  // developer's normal Next server is already using .next/dev/lock.
  distDir: process.env.NEXT_DIST_DIR || ".next",
  // Keep Turbopack scoped to this frontend when the repository also has a
  // package-lock.json at its root.
  turbopack: {
    root: process.cwd(),
  },
  // Deploy bang Docker (xem frontend/Dockerfile): output standalone gom san
  // node_modules can thiet, khong phai COPY ca thu muc node_modules vao image.
  output: "standalone",
};

export default nextConfig;
