/**
 * Entrypoint Vite untuk memasang App dan stylesheet global ke elemen root.
 * StrictMode membantu mendeteksi lifecycle yang tidak tahan pemasangan ulang saat development.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
