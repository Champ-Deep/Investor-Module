import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// /api is proxied to the backend so the app is same-origin in preview (no CORS / port coupling).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: true,
    // The preview panel reaches Vite through a generated hostname; allow it (avoids
    // Vite's "Blocked request. This host is not allowed." 403).
    allowedHosts: true,
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET || "http://localhost:8123",
        changeOrigin: true,
      },
    },
  },
});
