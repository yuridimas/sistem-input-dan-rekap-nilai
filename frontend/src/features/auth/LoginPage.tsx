/**
 * Halaman login yang dipasang App sebelum kelompok route terlindungi.
 * Setelah token disimpan, profil dimuat ulang sebelum pengguna diarahkan ke tujuan lokal.
 */
import { useState, type FormEvent } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { ArrowRight, BookOpenCheck, Eye, EyeOff, GraduationCap, ShieldCheck } from "lucide-react";
import axios from "axios";

import { Button } from "@/components/ui/button";
import api from "@/lib/api";
import { authQueryKey, fetchCurrentUser, useAuth } from "@/features/auth/useAuth";
import { useAuthStore } from "@/stores/authStore";

/**
 * Pasangan token yang diterima endpoint login untuk mengganti sesi pada store.
 */
interface TokenResponse {
  access_token: string;
  refresh_token: string;
}

/**
 * Pisahkan kredensial salah dari gangguan jaringan tanpa menampilkan objek error mentah.
 */
function loginError(error: unknown) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401) return "Email atau kata sandi tidak sesuai.";
    if (!error.response) return "Tidak dapat terhubung ke server. Periksa koneksi Anda.";
  }
  return "Login belum berhasil. Silakan coba lagi.";
}

/**
 * Pilih tujuan lokal dari state router; tolak URL absolut dan path protocol-relative.
 * @returns Path internal atau /dashboard jika state tidak valid; tidak melakukan navigasi.
 */
function returnPath(state: unknown) {
  const from = (state as { from?: { pathname?: unknown; search?: unknown; hash?: unknown } } | null)?.from;
  // Tolak //host agar tujuan setelah login tidak menjadi redirect ke origin lain.
  if (typeof from?.pathname !== "string" || !from.pathname.startsWith("/") || from.pathname.startsWith("//")) {
    return "/dashboard";
  }
  return `${from.pathname}${typeof from.search === "string" ? from.search : ""}${typeof from.hash === "string" ? from.hash : ""}`;
}

/**
 * Kelola input dan request sesi; tampilkan loading sampai hidrasi/profil selesai.
 */
export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { user, isLoading, hasTokens } = useAuth();
  const setTokens = useAuthStore((state) => state.setTokens);
  const clear = useAuthStore((state) => state.clear);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (isLoading) {
    return <div className="grid min-h-screen place-items-center text-sm text-muted-foreground" role="status">Memeriksa sesi…</div>;
  }
  if (user && !submitting) return <Navigate to={returnPath(location.state)} replace />;

  /**
   * Kirim kredensial, ganti token, lalu muat profil agar sesi baru tidak memakai role lama.
   * Error membersihkan token/cache auth; efek HTTP, storage, dan navigasi ditangani di sini.
   */
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const { data } = await api.post<TokenResponse>("/auth/login", { email: email.trim(), password });
      setTokens(data.access_token, data.refresh_token);
      const currentUser = await queryClient.fetchQuery({
        queryKey: authQueryKey,
        queryFn: fetchCurrentUser,
        staleTime: 0,
      });
      useAuthStore.getState().setUser(currentUser);
      navigate(returnPath(location.state), { replace: true });
    } catch (loginFailure) {
      clear();
      queryClient.removeQueries({ queryKey: authQueryKey });
      setError(loginError(loginFailure));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-background lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(28rem,0.82fr)]">
      <section className="relative hidden min-h-screen overflow-hidden bg-slate-950 px-12 py-10 text-white lg:flex lg:flex-col lg:justify-between xl:px-20">
        <div className="absolute -right-32 top-1/4 size-96 rounded-full border border-white/10" aria-hidden="true" />
        <div className="absolute -right-20 top-[31%] size-72 rounded-full border border-white/10" aria-hidden="true" />
        <Brand light />
        <div className="relative z-10 max-w-xl pb-10">
          <div className="mb-6 inline-flex size-12 items-center justify-center rounded-2xl border border-white/15 bg-white/5 text-amber-300">
            <BookOpenCheck className="size-6" aria-hidden="true" />
          </div>
          <p className="mb-3 text-sm font-medium uppercase tracking-[0.18em] text-slate-300">Ruang kerja akademik</p>
          <h1 className="text-4xl font-semibold leading-tight tracking-tight xl:text-5xl">Kelola nilai dengan lebih terarah.</h1>
          <p className="mt-5 max-w-lg text-base leading-7 text-slate-300">Satu tempat untuk mengatur kelas, mencatat penilaian, dan menyiapkan rekap hasil belajar.</p>
          <div className="mt-10 flex items-center gap-3 text-sm text-slate-300">
            <ShieldCheck className="size-5 text-emerald-300" aria-hidden="true" />
            Akses aman untuk pengelola dan dosen
          </div>
        </div>
        <p className="text-xs text-slate-400">Sistem Input &amp; Rekap Nilai</p>
      </section>

      <section className="flex min-h-screen flex-col px-5 py-7 sm:px-10 lg:justify-center lg:px-14 xl:px-24">
        <div className="mb-12 lg:hidden"><Brand /></div>
        <div className="mx-auto w-full max-w-md">
          <div className="mb-8">
            <p className="text-sm font-medium text-primary">Selamat datang kembali</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight">Masuk ke akun Anda</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">Gunakan email dan kata sandi yang terdaftar untuk melanjutkan.</p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="email">Email</label>
              <input
                autoComplete="username"
                autoFocus
                className="h-11 w-full rounded-lg border border-input bg-background px-3.5 text-sm outline-none transition focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
                id="email"
                name="email"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="nama@kampus.ac.id"
                required
                type="email"
                value={email}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="password">Kata sandi</label>
              <div className="relative">
                <input
                  autoComplete="current-password"
                  className="h-11 w-full rounded-lg border border-input bg-background px-3.5 pr-12 text-sm outline-none transition focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
                  id="password"
                  name="password"
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  type={showPassword ? "text" : "password"}
                  value={password}
                />
                <button
                  aria-label={showPassword ? "Sembunyikan kata sandi" : "Tampilkan kata sandi"}
                  className="absolute inset-y-0 right-0 flex w-11 items-center justify-center rounded-r-lg text-muted-foreground outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
                  onClick={() => setShowPassword((visible) => !visible)}
                  type="button"
                >
                  {showPassword ? <EyeOff className="size-4" aria-hidden="true" /> : <Eye className="size-4" aria-hidden="true" />}
                </button>
              </div>
            </div>

            {error && <p className="rounded-lg border border-destructive/20 bg-destructive/5 px-3.5 py-3 text-sm text-destructive" role="alert">{error}</p>}

            <Button className="h-11 w-full justify-between px-4 text-sm" disabled={submitting || !hasTokens && isLoading} type="submit">
              <span>{submitting ? "Memproses…" : "Masuk"}</span>
              <ArrowRight className="size-4" aria-hidden="true" />
            </Button>
          </form>

          <p className="mt-8 text-center text-xs leading-5 text-muted-foreground">Akses aplikasi hanya untuk pengguna yang memiliki akun.</p>
          <div className="mt-12 border-t border-border pt-5 text-center text-xs text-muted-foreground">© 2026 Sistem Input &amp; Rekap Nilai</div>
        </div>
      </section>
    </main>
  );
}

/**
 * Gunakan identitas aplikasi yang sama untuk panel desktop dan form mobile.
 */
function Brand({ light = false }: { light?: boolean }) {
  return (
    <Link className="relative z-10 inline-flex w-fit items-center gap-3 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring" to="/login">
      <span className={`grid size-10 place-items-center rounded-xl ${light ? "bg-white/10 text-amber-300" : "bg-primary text-primary-foreground"}`}>
        <GraduationCap className="size-5" aria-hidden="true" />
      </span>
      <span>
        <span className={`block text-sm font-semibold ${light ? "text-white" : "text-foreground"}`}>Sistem Nilai</span>
        <span className={`block text-xs ${light ? "text-slate-400" : "text-muted-foreground"}`}>Akademik</span>
      </span>
    </Link>
  );
}
