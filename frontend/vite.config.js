import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig(({ command, mode }) => ({
  // Build mode "preview" → base /api/preview-site/ (embedded in SaaS backend)
  // Default (prod, Railway, zayado.net) → base "/"
  base: process.env.VITE_BASE_PATH || (mode === "preview" ? "/api/preview-site/" : "/"),
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: { host: "0.0.0.0", port: 3000, allowedHosts: true, hmr: { clientPort: 443 } },
  preview: { host: "0.0.0.0", port: 4173, allowedHosts: true },
  build: { outDir: "dist", sourcemap: false },
}));
