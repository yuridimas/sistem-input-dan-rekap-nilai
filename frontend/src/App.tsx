import {
  createBrowserRouter,
  createRoutesFromElements,
  RouterProvider,
  Route,
  Navigate,
} from "react-router-dom";
import { lazy } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { Layout } from "@/components/Layout";
import { PlaceholderPage } from "@/components/PlaceholderPage";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { LoginPage } from "@/features/auth/LoginPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
const CoursesPage = lazy(() =>
  import("@/features/courses/CoursesPage").then((module) => ({
    default: module.CoursesPage,
  })),
);
const CourseDetailPage = lazy(() =>
  import("@/features/courses/CourseDetailPage").then((module) => ({
    default: module.CourseDetailPage,
  })),
);
const ClassDetailPage = lazy(() =>
  import("@/features/classes/ClassDetailPage").then((module) => ({
    default: module.ClassDetailPage,
  })),
);
const StudentsPage = lazy(() =>
  import("@/features/students/StudentsPage").then((module) => ({
    default: module.StudentsPage,
  })),
);
const StudentDetailPage = lazy(() =>
  import("@/features/analytics/StudentDetailPage").then((module) => ({
    default: module.StudentDetailPage,
  })),
);
const NotificationsPage = lazy(() =>
  import("@/features/notifications/NotificationsPage").then((module) => ({
    default: module.NotificationsPage,
  })),
);

const queryClient = new QueryClient();

const router = createBrowserRouter(
  createRoutesFromElements(
    <>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/courses" element={<CoursesPage />} />
          <Route path="/courses/:courseId" element={<CourseDetailPage />} />
          <Route path="/classes/:classId" element={<ClassDetailPage />} />
          <Route path="/students" element={<StudentsPage />} />
          <Route path="/students/:studentId" element={<StudentDetailPage />} />
          <Route element={<ProtectedRoute allowedRoles={["superadmin"]} />}>
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route
              path="/users"
              element={<PlaceholderPage title="Pengguna" />}
            />
          </Route>
        </Route>
      </Route>
      <Route
        path="*"
        element={
          <main className="grid min-h-screen place-items-center px-5">
            <section className="text-center">
              <p className="text-sm font-medium text-muted-foreground">404</p>
              <h1 className="mt-2 text-2xl font-semibold">
                Halaman tidak ditemukan
              </h1>
              <p className="mt-2 text-sm text-muted-foreground">
                Periksa kembali alamat halaman yang Anda buka.
              </p>
            </section>
          </main>
        }
      />
    </>,
  ),
);

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
