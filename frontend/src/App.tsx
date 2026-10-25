import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { Layout } from "@/components/Layout";
import { PlaceholderPage } from "@/components/PlaceholderPage";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { LoginPage } from "@/features/auth/LoginPage";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/dashboard" element={<PlaceholderPage dashboard title="Dashboard" />} />
              <Route path="/courses" element={<PlaceholderPage title="Mata Kuliah" />} />
              <Route element={<ProtectedRoute allowedRoles={["superadmin"]} />}>
                <Route path="/users" element={<PlaceholderPage title="Pengguna" />} />
              </Route>
            </Route>
          </Route>
          <Route path="*" element={<main className="grid min-h-screen place-items-center px-5"><section className="text-center"><p className="text-sm font-medium text-muted-foreground">404</p><h1 className="mt-2 text-2xl font-semibold">Halaman tidak ditemukan</h1><p className="mt-2 text-sm text-muted-foreground">Periksa kembali alamat halaman yang Anda buka.</p></section></main>} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
