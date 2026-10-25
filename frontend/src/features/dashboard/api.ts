import { useQuery } from "@tanstack/react-query";

import api from "@/lib/api";

export interface DashboardClass {
  id: string;
  section: string;
  academic_year: string;
  student_count: number;
  status: "pending" | "released";
  released_at: string | null;
}

export interface DashboardCourse {
  id: string;
  code: string;
  name: string;
  semester: string;
  classes: DashboardClass[];
}

export interface DashboardRelease extends DashboardClass {
  course_id: string;
  course_code: string;
  course_name: string;
}

interface DashboardSummary {
  course_count: number;
  class_count: number;
  pending_class_count: number;
  courses: DashboardCourse[];
  recently_released: DashboardRelease[];
}

export function useDashboard(userId: string | undefined) {
  return useQuery({
    queryKey: ["dashboard", "summary", userId],
    queryFn: async () => (await api.get<DashboardSummary>("/dashboard/summary")).data,
    enabled: Boolean(userId),
    staleTime: 30_000,
    retry: 1,
  });
}
