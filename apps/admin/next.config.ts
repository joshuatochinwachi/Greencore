import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@greencore/shared-types"],
};

export default nextConfig;
