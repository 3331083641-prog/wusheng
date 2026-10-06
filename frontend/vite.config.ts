import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          charts: ["recharts"],
          motion: ["framer-motion"],
          react: ["react", "react-dom", "react-router-dom"],
        },
      },
    },
  },
  server: {
    port: Number(process.env.WUSHENG_VITE_PORT || 5173),
    strictPort: true,
    proxy: {
      "/api": {
        target: process.env.WUSHENG_API_TARGET || "http://127.0.0.1:8000",
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
      "/uploads": process.env.WUSHENG_API_TARGET || "http://127.0.0.1:8000",
    },
  },
});
