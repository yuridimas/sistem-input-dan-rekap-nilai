import { lazy, Suspense, useState } from "react";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader, QueryState } from "@/features/academic/Management";
import {
  useAcademicQuery,
  type AcademicClass,
  type Course,
} from "@/features/academic/api";
import { ComponentEditor } from "@/features/components/ComponentEditor";
import { ClassDialog } from "./ClassDialog";
import { Roster } from "./Roster";
import { GradeEntryGrid } from "@/features/grades/GradeEntryGrid";
import { GradeNavigationGuard } from "@/features/grades/GradeNavigationGuard";
import { useGradeEntry } from "@/features/grades/hooks";

const ClassAnalyticsPanel = lazy(() =>
  import("@/features/analytics/ClassAnalyticsPanel").then((module) => ({
    default: module.ClassAnalyticsPanel,
  })),
);

export function ClassDetailPage() {
  const { classId } = useParams();
  return <ClassDetailContent key={classId} />;
}

function ClassDetailContent() {
  const { classId } = useParams();
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const query = useAcademicQuery<AcademicClass>(`/classes/${classId}`);
  const course = useAcademicQuery<Course>(
    `/courses/${query.data?.course_id}`,
    Boolean(query.data) && !query.error,
  );
  const [dialog, setDialog] = useState<{ deleting?: boolean } | null>(null);
  const activeTab = ["components", "grades", "analytics"].includes(
    params.get("tab") ?? "",
  )
    ? params.get("tab")!
    : "students";
  const grades = useGradeEntry(
    classId!,
    activeTab === "grades" && Boolean(query.data) && !query.error,
  );
  const statusQuery =
    query.isPending || query.error
      ? query
      : course.isPending || course.error
        ? course
        : null;
  const data = query.data!;
  return (
    <>
      <GradeNavigationGuard classId={classId!} entry={grades} />
      {statusQuery ? (
        <QueryState query={statusQuery} />
      ) : (
        <section className="mx-auto max-w-5xl">
          <nav
            aria-label="Breadcrumb"
            className="mb-5 flex flex-wrap gap-2 text-sm"
          >
            <Link className="underline underline-offset-4" to="/courses">
              Mata kuliah
            </Link>
            <span aria-hidden="true">/</span>
            <Link
              className="underline underline-offset-4"
              to={`/courses/${data.course_id}`}
            >
              {course.data?.code}
            </Link>
            <span aria-hidden="true">/</span>
            <span>Kelas {data.section}</span>
          </nav>
          <PageHeader
            description={`${course.data?.name} · ${data.academic_year}`}
            title={`Kelas ${data.section}`}
          >
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => setDialog({})} variant="outline">
                Edit kelas
              </Button>
              <Button
                onClick={() => setDialog({ deleting: true })}
                variant="destructive"
              >
                Hapus kelas
              </Button>
            </div>
          </PageHeader>
          {data.has_finalized_grades && (
            <Alert className="mb-5">
              <AlertTitle>Roster dan komponen terkunci</AlertTitle>
              <AlertDescription>
                Kelas ini sudah memiliki nilai yang difinalisasi. Daftar
                mahasiswa dan komponen penilaian tidak dapat diubah.
              </AlertDescription>
            </Alert>
          )}
          <Tabs
            onValueChange={(value) =>
              setParams(value === "students" ? {} : { tab: String(value) })
            }
            value={activeTab}
          >
            <TabsList className="mb-4 h-auto max-w-full flex-wrap">
              <TabsTrigger value="students">Mahasiswa</TabsTrigger>
              <TabsTrigger value="components">Komponen Penilaian</TabsTrigger>
              <TabsTrigger value="grades">Nilai</TabsTrigger>
              <TabsTrigger value="analytics">Analisis</TabsTrigger>
            </TabsList>
            <TabsContent value="students">
              <Roster
                classId={data.id}
                key={data.id}
                locked={data.has_finalized_grades}
              />
            </TabsContent>
            <TabsContent value="components">
              <ComponentEditor
                classId={data.id}
                locked={data.has_finalized_grades}
              />
            </TabsContent>
            <TabsContent value="grades">
              <GradeEntryGrid entry={grades} />
            </TabsContent>
            <TabsContent value="analytics">
              <Suspense
                fallback={
                  <div
                    className="h-24 animate-pulse rounded-md border bg-muted/40"
                    role="status"
                  >
                    Memuat analisis…
                  </div>
                }
              >
                <ClassAnalyticsPanel
                  classId={data.id}
                  hasUnsavedChanges={
                    grades.engine.hasChanges() || grades.snapshot.saving
                  }
                />
              </Suspense>
            </TabsContent>
          </Tabs>
          {dialog && (
            <ClassDialog
              {...dialog}
              afterDelete={() => navigate(`/courses/${data.course_id}`)}
              class_={data}
              close={() => setDialog(null)}
              courseId={data.course_id}
            />
          )}
        </section>
      )}
    </>
  );
}
