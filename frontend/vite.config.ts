/**
 * Konfigurasi dev/build Vite untuk React dan pipeline Tailwind.
 * Alias @ sama dengan konfigurasi TypeScript agar import sumber konsisten saat build.
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    host: true,
  },
});
