from datetime import datetime, timezone
import re
import uuid

import pytest

from app.seeding.config import resolve_config
from app.seeding.scenarios import CASE_CATALOG, build_plan, canonical_plan


def test_replays_same_config():
    config = resolve_config(dataset="manual-v1", seed=20261105)
    assert canonical_plan(build_plan(config)) == canonical_plan(build_plan(config))


def test_each_case_has_multiple_samples_and_mandatory_boundaries():
    plan = build_plan(resolve_config(dataset="manual-v1", seed=17))
    assert plan.samples
    assert all(count >= 5 for count in plan.case_counts.values())
    assert {sample.case_id for sample in plan.samples} == set(plan.case_counts)
    assert sum(plan.counts.values()) == len(plan.objects)
    assert len({obj.id for obj in plan.objects}) == len(plan.objects)
    payloads = [repr(sample.payload) for sample in plan.samples]
    assert len(set(payloads)) > 1
    assert {"score.zero", "score.maximum", "grade.fail-boundary", "grade.pass-boundary", "score.clear"} <= set(plan.case_counts)
    for group in plan.components_by_class.values():
        assert sum((row.weight for row in group), start=0) == 100


def test_graph_has_multiple_courses_classes_and_rosters_within_bounds():
    from collections import Counter

    from app.models.class_ import Class
    from app.models.course import Course
    from app.models.enrollment import Enrollment
    from app.models.student import Student

    plan = build_plan(resolve_config(dataset="multi-course-graph", seed=2718))
    courses = [row for row in plan.objects if isinstance(row, Course)]
    classes = [row for row in plan.objects if isinstance(row, Class)]
    students = {row.id for row in plan.objects if isinstance(row, Student)}
    enrollments = [row for row in plan.objects if isinstance(row, Enrollment)]
    course_by_id = {row.id: row for row in courses}
    class_by_id = {row.id: row for row in classes}
    enrollment_by_id = {row.id: row for row in enrollments}
    class_counts = Counter(row.course_id for row in classes)
    roster_counts = Counter(row.class_id for row in enrollments)

    assert 5 <= len(courses) <= 15
    assert all(2 <= class_counts[course.id] <= 5 for course in courses)
    assert all(5 <= roster_counts[record.id] <= 15 for record in classes)
    assert all(enrollment.student_id in students for enrollment in enrollments)
    assert all(item.course_id in course_by_id for item in classes)
    for sample in plan.samples:
        class_id = uuid.UUID(sample.resources["class_id"])
        enrollment = enrollment_by_id[uuid.UUID(sample.resources["enrollment_id"])]
        assert sample.resources["course_id"] == str(class_by_id[class_id].course_id)
        assert enrollment.class_id == class_id
        assert enrollment.student_id == uuid.UUID(sample.resources["student_id"])


def test_manifest_exposes_total_academic_graph_counts():
    from app.seeding.manifest import manifest_data

    plan = build_plan(resolve_config(dataset="manifest-multi-course", seed=2718))
    counts = manifest_data(plan)["counts"]

    assert 5 <= counts["courses"] <= 15
    assert counts["classes"] >= 2 * counts["courses"]
    assert 5 * counts["classes"] <= counts["enrollments"] <= 15 * counts["classes"]
    assert counts["students"] == counts["enrollments"]


def test_graph_reserves_capacity_for_the_foreign_lecturer_class():
    from collections import Counter

    from app.models.class_ import Class
    from app.models.course import Course

    plan = build_plan(resolve_config(
        dataset="foreign-class-capacity", seed=14, min_samples=7, max_samples=7,
    ))
    courses = [row for row in plan.objects if isinstance(row, Course)]
    classes = [row for row in plan.objects if isinstance(row, Class)]
    classes_per_course = Counter(row.course_id for row in classes)

    assert all(2 <= classes_per_course[course.id] <= 5 for course in courses)


def test_light_load_profile_stays_under_explicit_row_ceiling():
    plan = build_plan(resolve_config(dataset="light-load-check", profile="light-load", seed=11))
    assert all(10 <= count <= 30 for count in plan.case_counts.values())
    assert sum(plan.counts.values()) == len(plan.objects) <= 100_000


def test_catalog_always_contains_required_negative_causes():
    plan = build_plan(resolve_config(dataset="negative-coverage", seed=20261105))
    required = {
        "auth.login.bad", "course.create.invalid", "class.foreign.read",
        "enrollment.duplicate", "student.update.denied",
        "component.weight.below", "component.invalid.null", "score.negative",
        "score.over_max", "score.too_precise", "finalize.missing_score",
        "finalize.repeat", "reports.draft.denied", "notifications.retry.sent",
        "users.denied",
    }
    assert required <= set(plan.case_counts)


@pytest.mark.parametrize("kwargs", [
    {"min_samples": 4}, {"min_samples": 10, "max_samples": 5}, {"max_rows": 100001},
    {"dataset": "Bad_Name"}, {"profile": "huge"},
])
def test_rejects_invalid_profile_config(kwargs):
    with pytest.raises(ValueError):
        resolve_config(dataset=kwargs.pop("dataset", "manual-v1"), **kwargs)


def test_reference_time_is_fixed_and_timezone_aware():
    config = resolve_config(dataset="manual-v1", seed=3)
    assert config.reference_time == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert config.generator_version == "3"


def test_catalog_paths_match_real_api_operations():
    from app.main import app

    operations = {
        (method.upper(), re.sub(r"\{[^}]+\}", "{}", path))
        for path, methods in app.openapi()["paths"].items()
        for method in methods
        if method in {"get", "post", "put", "patch", "delete"}
    }
    for case in CASE_CATALOG:
        method, path = case.operation
        normalized = re.sub(r"\$\{[A-Z_]+\}", "{}", path)
        assert (method, normalized) in operations, case.case_id

    covered = {
        (method, re.sub(r"\{[^}]+\}", "{}", re.sub(r"\$\{[A-Z_]+\}", "{}", path)))
        for case in CASE_CATALOG for method, path in [case.operation]
    }
    assert operations <= covered, sorted(operations - covered)
