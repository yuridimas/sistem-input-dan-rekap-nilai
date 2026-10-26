/**
 * Konfigurasi unit/integration UI dengan React di jsdom.
 * Alias sumber menyamai Vite; setup memasang matcher dan cleanup DOM setelah setiap test.
 */
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(import.meta.dirname, "./src") } },
  test: { environment: "jsdom", setupFiles: ["./src/test/setup.ts"] },
});
