import path from "node:path";

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output for lean Docker images.
  output: "standalone",
  // The monorepo root is two levels up; pin tracing root to silence lockfile warnings.
  outputFileTracingRoot: path.join(__dirname, "../../"),
  typescript: {
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
