/**
 * Detail mata kuliah dan kelas yang terlihat oleh pengguna saat ini.
 * Hak edit mata kuliah dibedakan dari hak baca dosen yang memiliki penugasan kelas.
 */
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { PageHeader, QueryState } from "@/features/academic/Management";
import {
  useAcademicQuery,
  type Course,
  type AcademicClass,
} from "@/features/academic/api";
import { useAuth } from "@/features/auth/useAuth";
import { ClassDialog } from "@/features/classes/ClassDialog";
import { CourseDialog } from "./CourseDialog";
import { CourseClassesTable } from "./CourseClassesTable";

/**
 * Muat metadata terlebih dahulu lalu kelompokkan daftar kelas pada mata kuliah tujuan.
 */
export function CourseDetailPage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const course = useAcademicQuery<Course>(`/courses/${courseId}`);
  const classes = useAcademicQuery<AcademicClass[]>(
    "/classes",
    Boolean(course.data) && !course.error,
  );
  const [classDialog, setClassDialog] = useState<{
    class_?: AcademicClass;
    deleting?: boolean;
  } | null>(null);
  const [editCourse, setEditCourse] = useState(false);
  if (course.isPending || course.error) return <QueryState query={course} />;
  const data = course.data!;
  const rows = classes.data?.filter((row) => row.course_id === data.id) ?? [];
  return (
    <section className="mx-auto max-w-5xl">
      <nav aria-label="Breadcrumb" className="mb-5 text-sm">
        <Link className="underline underline-offset-4" to="/courses">
          Mata kuliah
        </Link>
        <span aria-hidden="true"> / </span>
        <span>{data.code}</span>
      </nav>
      <PageHeader
        description={`${data.code} · ${data.credits} SKS · Semester ${data.semester}`}
        title={data.name}
      >
        <div className="flex flex-wrap gap-2">
          {(user?.role === "superadmin" || user?.id === data.created_by) && (
            <Button onClick={() => setEditCourse(true)} variant="outline">
              Edit mata kuliah
            </Button>
          )}
          <Button onClick={() => setClassDialog({})}>
            <Plus data-icon="inline-start" />
            Tambah kelas
          </Button>
        </div>
      </PageHeader>
      <h2 className="mb-4 text-base font-semibold">Daftar kelas</h2>
      <CourseClassesTable
        rows={rows}
        isPending={classes.isPending}
        isFetching={classes.isFetching}
        error={classes.error}
        onRefresh={() => classes.refetch()}
        onEdit={(class_) => setClassDialog({ class_ })}
        onDelete={(class_) => setClassDialog({ class_, deleting: true })}
      />
      {classDialog && (
        <ClassDialog
          {...classDialog}
          afterDelete={() => navigate(`/courses/${data.id}`)}
          close={() => setClassDialog(null)}
          courseId={data.id}
        />
      )}
      {editCourse && (
        <CourseDialog close={() => setEditCourse(false)} course={data} />
      )}
    </section>
  );
}
