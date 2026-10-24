import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<div>Login</div>} />
          <Route path="/dashboard" element={<div>Dashboard</div>} />
          <Route path="*" element={<div>404 - Halaman tidak ditemukan</div>} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
