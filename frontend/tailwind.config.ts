/**
 * Konfigurasi pencarian utility Tailwind pada HTML entrypoint dan sumber TS/TSX.
 * Token tema aplikasi berada pada src/index.css yang diproses plugin Tailwind Vite.
 */
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {},
  },
};

export default config;
