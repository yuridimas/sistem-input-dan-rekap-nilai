import { useState } from "react";
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

export function ClassDetailPage() {
  const { classId } = useParams();
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const query = useAcademicQuery<AcademicClass>(`/classes/${classId}`);
  const course = useAcademicQuery<Course>(
    `/courses/${query.data?.course_id}`,
    Boolean(query.data) && !query.error,
  );
  const [dialog, setDialog] = useState<{ deleting?: boolean } | null>(null);
  if (query.isPending || query.error) return <QueryState query={query} />;
  if (course.isPending || course.error) return <QueryState query={course} />;
  const data = query.data!;
  return (
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
            Kelas ini sudah memiliki nilai yang difinalisasi. Daftar mahasiswa
            dan komponen penilaian tidak dapat diubah.
          </AlertDescription>
        </Alert>
      )}
      <Tabs
        onValueChange={(value) =>
          setParams(value === "components" ? { tab: "components" } : {})
        }
        value={params.get("tab") === "components" ? "components" : "students"}
      >
        <TabsList className="mb-4 max-w-full">
          <TabsTrigger value="students">Mahasiswa</TabsTrigger>
          <TabsTrigger value="components">Komponen Penilaian</TabsTrigger>
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
  );
}
