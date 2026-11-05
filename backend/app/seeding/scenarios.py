"""Deterministic relational seed graph and labeled positive/negative requests."""

from dataclasses import dataclass
from decimal import Decimal
import hashlib
from importlib.metadata import version
import json
import random
import uuid
from typing import Any, Literal

from faker import Faker
from sqlalchemy.orm import DeclarativeBase

from app.models.class_ import Class
from app.models.component import Component, ComponentCategory
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.grade import Grade, GradeStatus
from app.models.notification import Notification, NotificationStatus
from app.models.ranking import Ranking
from app.models.score import Score
from app.models.student import Student
from app.models.user import User, UserRole
from app.services.grade import calculate_final_score
from app.seeding.config import SeedConfig
from app.seeding.factories import make_factory


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    operation: tuple[str, str] | None
    manual_support: Literal["ui", "api", "automated-only"]
    mutates: bool
    expected_status: int | None
    automation_reference: str | None = None


@dataclass(frozen=True)
class CaseSample:
    sample_id: str
    case_id: str
    actor_key: str | None
    method: str
    path: str
    payload: Any
    expected_status: int
    assertion_keys: tuple[str, ...]
    resources: dict[str, Any]


@dataclass(frozen=True)
class SeedPlan:
    config: SeedConfig
    anchor_id: uuid.UUID
    objects: tuple[DeclarativeBase, ...]
    samples: tuple[CaseSample, ...]
    counts: dict[str, int]
    case_counts: dict[str, int]
    fingerprint: str
    components_by_class: dict[uuid.UUID, tuple[Component, ...]]


_CASES: tuple[tuple[str, str, str, int, bool, str, Any], ...] = (
    ("health.ready", "GET", "/health", 200, False, "", None),
    ("auth.me", "GET", "/auth/me", 200, False, "lecturer", None),
    ("auth.login.good", "POST", "/auth/login", 200, False, "lecturer", {"email": "${ACTOR_EMAIL}", "password": "${SEED_PASSWORD}"}),
    ("auth.login.bad", "POST", "/auth/login", 401, False, "lecturer", {"email": "${ACTOR_EMAIL}", "password": "${INVALID_PASSWORD}"}),
    ("course.list", "GET", "/courses", 200, False, "lecturer", None),
    ("course.create.invalid", "POST", "/courses", 422, False, "lecturer", {"code": "", "name": ""}),
    ("class.list", "GET", "/classes", 200, False, "lecturer", None),
    ("class.foreign.read", "GET", "/classes/${FOREIGN_CLASS_ID}", 403, False, "lecturer", None),
    ("class.roster", "GET", "/classes/${CLASS_ID}/roster", 200, False, "lecturer", None),
    ("enrollment.duplicate", "POST", "/classes/${CLASS_ID}/enrollments", 409, True, "lecturer", {"nim": "${EXISTING_NIM}"}),
    ("student.directory", "GET", "/students", 200, False, "lecturer", None),
    ("student.email.clear", "PATCH", "/students/${STUDENT_ID}", 200, True, "superadmin", {"email": None}),
    ("student.update.denied", "PATCH", "/students/${STUDENT_ID}", 403, True, "lecturer", {"full_name": "Denied"}),
    ("component.list", "GET", "/classes/${CLASS_ID}/components", 200, False, "lecturer", None),
    ("component.weight.below", "PATCH", "/components/${COMPONENT_ID}", 422, True, "lecturer", {"weight": "0"}),
    ("component.invalid.null", "PATCH", "/components/${COMPONENT_ID}", 422, True, "lecturer", {"name": None}),
    ("grades.grid", "GET", "/classes/${CLASS_ID}/grades", 200, False, "lecturer", None),
    ("score.zero", "PUT", "/enrollments/${ENROLLMENT_ID}/scores", 200, True, "lecturer", {"${COMPONENT_ID}": "0.00"}),
    ("score.maximum", "PUT", "/enrollments/${ENROLLMENT_ID}/scores", 200, True, "lecturer", {"${COMPONENT_ID}": "100.00"}),
    ("score.clear", "PUT", "/enrollments/${ENROLLMENT_ID}/scores", 200, True, "lecturer", {"${COMPONENT_ID}": None}),
    ("score.negative", "PUT", "/enrollments/${ENROLLMENT_ID}/scores", 422, True, "lecturer", {"${COMPONENT_ID}": "-0.01"}),
    ("score.over_max", "PUT", "/enrollments/${ENROLLMENT_ID}/scores", 422, True, "lecturer", {"${COMPONENT_ID}": "100.01"}),
    ("score.too_precise", "PUT", "/enrollments/${ENROLLMENT_ID}/scores", 422, True, "lecturer", {"${COMPONENT_ID}": "1.001"}),
    ("grade.fail-boundary", "GET", "/classes/${CLASS_ID}/grades", 200, False, "lecturer", None),
    ("grade.pass-boundary", "GET", "/classes/${CLASS_ID}/grades", 200, False, "lecturer", None),
    ("finalize.complete", "POST", "/classes/${READY_CLASS_ID}/finalize", 202, True, "lecturer", None),
    ("finalize.missing_score", "POST", "/classes/${INCOMPLETE_CLASS_ID}/finalize", 422, True, "lecturer", None),
    ("finalize.repeat", "POST", "/classes/${FINAL_CLASS_ID}/finalize", 409, True, "lecturer", None),
    ("ranking.read", "GET", "/classes/${FINAL_CLASS_ID}/ranking", 200, False, "lecturer", None),
    ("history.read", "GET", "/students/${STUDENT_ID}/history", 200, False, "lecturer", None),
    ("dashboard.summary", "GET", "/dashboard/summary", 200, False, "lecturer", None),
    ("reports.student.pdf", "GET", "/reports/student/${ENROLLMENT_ID}/pdf", 200, False, "lecturer", None),
    ("reports.class.xlsx", "GET", "/reports/class/${FINAL_CLASS_ID}/xlsx", 200, False, "lecturer", None),
    ("reports.draft.denied", "GET", "/reports/class/${INCOMPLETE_CLASS_ID}/pdf", 409, False, "lecturer", None),
    ("notifications.list", "GET", "/admin/notifications", 200, False, "superadmin", None),
    ("notifications.retry.sent", "POST", "/admin/notifications/${SENT_NOTIFICATION_ID}/retry", 409, True, "superadmin", None),
    ("notifications.retry.failed", "POST", "/admin/notifications/${FAILED_NOTIFICATION_ID}/retry", 202, True, "superadmin", None),
    ("users.list", "GET", "/admin/users", 200, False, "superadmin", None),
    ("users.denied", "GET", "/admin/users", 403, False, "lecturer", None),
)

CASE_CATALOG = tuple(
    CaseSpec(case_id, (method, path), "api", mutates, status)
    for case_id, method, path, status, mutates, _actor, _payload in _CASES
) + (
    CaseSpec("users.get", ("GET", "/admin/users/${USER_ID}"), "automated-only", False, None, "tests/test_users.py"),
    CaseSpec("users.patch", ("PATCH", "/admin/users/${USER_ID}"), "automated-only", True, None, "tests/test_users.py"),
    CaseSpec("users.delete", ("DELETE", "/admin/users/${USER_ID}"), "automated-only", True, None, "tests/test_users.py"),
    CaseSpec("users.post", ("POST", "/admin/users"), "automated-only", True, None, "tests/test_users.py"),
    CaseSpec("courses.get", ("GET", "/courses/${COURSE_ID}"), "automated-only", False, None, "tests/test_courses.py"),
    CaseSpec("courses.patch", ("PATCH", "/courses/${COURSE_ID}"), "automated-only", True, None, "tests/test_courses.py"),
    CaseSpec("courses.delete", ("DELETE", "/courses/${COURSE_ID}"), "automated-only", True, None, "tests/test_courses.py"),
    CaseSpec("classes.get", ("GET", "/classes/${CLASS_ID}"), "automated-only", False, None, "tests/test_classes.py"),
    CaseSpec("classes.post", ("POST", "/classes"), "automated-only", True, None, "tests/test_classes.py"),
    CaseSpec("classes.patch", ("PATCH", "/classes/${CLASS_ID}"), "automated-only", True, None, "tests/test_classes.py"),
    CaseSpec("classes.delete", ("DELETE", "/classes/${CLASS_ID}"), "automated-only", True, None, "tests/test_classes.py"),
    CaseSpec("enrollment.delete", ("DELETE", "/classes/${CLASS_ID}/enrollments/${ENROLLMENT_ID}"), "automated-only", True, None, "tests/test_classes.py"),
    CaseSpec("students.post", ("POST", "/students"), "automated-only", True, None, "tests/test_students.py"),
    CaseSpec("students.get", ("GET", "/students/${STUDENT_ID}"), "automated-only", False, None, "tests/test_students.py"),
    CaseSpec("students.delete", ("DELETE", "/students/${STUDENT_ID}"), "automated-only", True, None, "tests/test_students.py"),
    CaseSpec("components.post", ("POST", "/classes/${CLASS_ID}/components"), "automated-only", True, None, "tests/test_components.py"),
    CaseSpec("components.put", ("PUT", "/classes/${CLASS_ID}/components"), "automated-only", True, None, "tests/test_components.py"),
    CaseSpec("components.delete", ("DELETE", "/components/${COMPONENT_ID}"), "automated-only", True, None, "tests/test_components.py"),
    CaseSpec("auth.refresh", ("POST", "/auth/refresh"), "automated-only", False, None, "tests/test_auth.py"),
    CaseSpec("reports.class.pdf", ("GET", "/reports/class/${FINAL_CLASS_ID}/pdf"), "automated-only", False, None, "tests/test_reports.py"),
)
GENERATED_CASES = tuple(case for case in CASE_CATALOG if case.manual_support == "api")


def _uid(namespace: uuid.UUID, key: str) -> uuid.UUID:
    return uuid.uuid5(namespace, key)


def build_plan(config: SeedConfig) -> SeedPlan:
    """Build a valid reusable academic graph and independent request samples."""
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, f"grades-seed:{config.dataset}")
    rng = random.Random(config.seed)
    fake = Faker(locale="id_ID")
    fake.seed_instance(config.seed)
    objects: list[DeclarativeBase] = []
    def uid(key: str) -> uuid.UUID:
        return _uid(namespace, key)

    admin = User(id=uid("admin"), email=f"admin-{config.dataset}@example.test", password_hash="${SEED_PASSWORD_HASH}", full_name="Administrator Seed", role=UserRole.SUPERADMIN.value, is_active=True)
    lecturer = User(id=uid("lecturer"), email=f"lecturer-{config.dataset}@example.test", password_hash="${SEED_PASSWORD_HASH}", full_name=fake.name(), role=UserRole.LECTURER.value, is_active=True)
    foreign_lecturer = User(id=uid("foreign-lecturer"), email=f"foreign-{config.dataset}@example.test", password_hash="${SEED_PASSWORD_HASH}", full_name=fake.name(), role=UserRole.LECTURER.value, is_active=True)
    course = Course(id=uid("course"), code=f"SEED-{config.dataset[:30]}", name="Pengantar Sistem Informasi", credits=3, semester="2026/1", created_by=lecturer.id, created_at=config.reference_time)
    foreign_class = Class(id=uid("foreign-class"), course_id=course.id, section="FOREIGN", lecturer_id=foreign_lecturer.id, academic_year="2026/2027", created_at=config.reference_time)
    objects.extend([admin, lecturer, foreign_lecturer, course, foreign_class])
    case_counts: dict[str, int] = {}
    samples: list[CaseSample] = []
    components_by_class: dict[uuid.UUID, tuple[Component, ...]] = {}
    student_factory = make_factory(Student, config.seed)
    global_sample = 0
    for case_id, method, path, status, _mutates, actor, payload in _CASES:
        sample_count = random.Random(int(hashlib.sha256(f"{config.seed}:{case_id}".encode()).hexdigest(), 16)).randint(config.min_samples, config.max_samples)
        case_counts[case_id] = sample_count
        for index in range(sample_count):
            key = f"sample:{global_sample}"
            sample_class = Class(id=uid(f"class:{key}"), course_id=course.id, section=f"S{global_sample}", lecturer_id=lecturer.id, academic_year="2026/2027", created_at=config.reference_time)
            components = [
                Component(id=uid(f"component:{key}:assignment"), class_id=sample_class.id, name="Tugas", category=ComponentCategory.TUGAS.value, weight=Decimal("30.00"), max_score=Decimal("100.00"), order_index=0, created_at=config.reference_time),
                Component(id=uid(f"component:{key}:midterm"), class_id=sample_class.id, name="UTS", category=ComponentCategory.UTS.value, weight=Decimal("30.00"), max_score=Decimal("100.00"), order_index=1, created_at=config.reference_time),
                Component(id=uid(f"component:{key}:final"), class_id=sample_class.id, name="UAS", category=ComponentCategory.UAS.value, weight=Decimal("40.00"), max_score=Decimal("100.00"), order_index=2, created_at=config.reference_time),
            ]
            components_by_class[sample_class.id] = tuple(components)
            objects.extend([sample_class, *components])
            student = student_factory.build(id=uid(f"student:{key}"), nim=f"{config.dataset.upper()}-{global_sample:05d}", full_name=fake.name(), email=f"student-{global_sample}-{config.dataset}@example.test", created_at=config.reference_time)
            enrollment = Enrollment(id=uid(f"enrollment:{key}"), class_id=sample_class.id, student_id=student.id, enrolled_at=config.reference_time)
            if case_id in {"grade.fail-boundary", "grade.pass-boundary"}:
                boundary_score = Decimal("44.99") if case_id == "grade.fail-boundary" else Decimal("45.00")
                score_values = {components[0].id: boundary_score, components[1].id: boundary_score, components[2].id: boundary_score}
            else:
                score_values = {components[0].id: Decimal(rng.randrange(0, 101)), components[1].id: Decimal(rng.randrange(0, 101)), components[2].id: Decimal(rng.randrange(0, 101))}
                if case_id == "score.zero":
                    score_values[components[0].id] = Decimal("0.00")
                elif case_id == "score.maximum":
                    score_values[components[0].id] = Decimal("100.00")
            if case_id == "finalize.missing_score":
                score_values.pop(components[-1].id)
            objects.append(student)
            objects.append(enrollment)
            objects.extend(Score(id=uid(f"score:{key}:{component_id}"), enrollment_id=enrollment.id, component_id=component_id, score=value, entered_by=lecturer.id, entered_at=config.reference_time, updated_at=config.reference_time) for component_id, value in score_values.items())
            final_score = calculate_final_score(components, score_values)
            final_cases = {"finalize.repeat", "ranking.read", "history.read", "reports.student.pdf", "reports.class.xlsx", "notifications.retry.sent", "notifications.retry.failed"}
            finalized = case_id in final_cases
            grade_id = uid(f"grade:{key}")
            objects.append(Grade(id=grade_id, enrollment_id=enrollment.id, final_score=final_score, status=GradeStatus.FINALIZED.value if finalized else GradeStatus.DRAFT.value, finalized_at=config.reference_time if finalized else None, finalized_by=lecturer.id if finalized else None, release_notified_at=config.reference_time if case_id == "notifications.retry.sent" else None))
            if finalized:
                objects.append(Ranking(id=uid(f"ranking:{key}"), class_id=sample_class.id, enrollment_id=enrollment.id, rank=1, computed_at=config.reference_time))
            sample_payload = payload
            if isinstance(payload, dict):
                sample_payload = {k.replace("${COMPONENT_ID}", str(components[index % len(components)].id)): v for k, v in payload.items()}
                for key_name, value in list(sample_payload.items()):
                    if value == "${ACTOR_EMAIL}":
                        sample_payload[key_name] = lecturer.email if case_id == "auth.login.good" else f"unknown-{config.dataset}-{index}@example.test"
                    elif value == "${INVALID_PASSWORD}":
                        sample_payload[key_name] = "invalid-password-for-test"
                    elif value == "${SEED_PASSWORD}":
                        sample_payload[key_name] = "<SEED_PASSWORD>"
                    elif value == "${EXISTING_NIM}":
                        sample_payload[key_name] = student.nim
            sample_path = (path.replace("${CLASS_ID}", str(sample_class.id)).replace("${STUDENT_ID}", str(student.id)).replace("${ENROLLMENT_ID}", str(enrollment.id)).replace("${READY_CLASS_ID}", str(sample_class.id)).replace("${INCOMPLETE_CLASS_ID}", str(sample_class.id)).replace("${FINAL_CLASS_ID}", str(sample_class.id)))
            sample_path = sample_path.replace("${COMPONENT_ID}", str(components[index % len(components)].id))
            sample_path = sample_path.replace("${FOREIGN_CLASS_ID}", str(foreign_class.id))
            notification_id = None
            if case_id == "notifications.retry.sent":
                notification = Notification(id=uid(f"notification:{key}"), grade_id=grade_id, student_email=student.email, status=NotificationStatus.SENT.value, sent_at=config.reference_time)
                objects.append(notification)
                notification_id = str(notification.id)
                sample_path = sample_path.replace("${SENT_NOTIFICATION_ID}", str(notification.id))
            elif case_id == "notifications.retry.failed":
                notification = Notification(id=uid(f"notification:{key}"), grade_id=grade_id, student_email=student.email, status=NotificationStatus.FAILED.value, error_message="Simulasi kegagalan pengiriman")
                objects.append(notification)
                notification_id = str(notification.id)
                sample_path = sample_path.replace("${FAILED_NOTIFICATION_ID}", str(notification.id))
            assertions = {
                "enrollment.duplicate": ("status", "roster_unchanged"),
                "student.update.denied": ("status", "student_unchanged"),
                "component.weight.below": ("status", "component_unchanged"),
                "component.invalid.null": ("status", "component_unchanged"),
                "score.negative": ("status", "score_unchanged"),
                "score.over_max": ("status", "score_unchanged"),
                "score.too_precise": ("status", "score_unchanged"),
                "finalize.missing_score": ("status", "grade_remains_draft"),
                "finalize.repeat": ("status", "grade_remains_final"),
            }.get(case_id, ("status",))
            resources = {"class_id": str(sample_class.id), "foreign_class_id": str(foreign_class.id),
                         "student_id": str(student.id), "nim": student.nim,
                         "enrollment_id": str(enrollment.id),
                         "component_ids": [str(component.id) for component in components]}
            if notification_id:
                resources["notification_id"] = notification_id
            samples.append(CaseSample(f"{case_id}:{index:03d}", case_id, actor or None, method, sample_path, sample_payload, status, assertions, resources))
            global_sample += 1
    counts: dict[str, int] = {}
    for obj in objects:
        counts[obj.__tablename__] = counts.get(obj.__tablename__, 0) + 1
    total_rows = sum(counts.values())
    if total_rows > config.max_rows:
        raise ValueError(f"planned dataset has {total_rows} rows, above max_rows={config.max_rows}")
    dependencies = {"faker": version("Faker"), "polyfactory": version("polyfactory")}
    catalog = [(case.case_id, case.operation, case.manual_support, case.mutates,
                case.expected_status, case.automation_reference) for case in CASE_CATALOG]
    fingerprint = hashlib.sha256(json.dumps({"dataset": config.dataset, "profile": config.profile, "seed": config.seed, "min_samples": config.min_samples, "max_samples": config.max_samples, "reference_time": config.reference_time.isoformat(), "generator_version": config.generator_version, "dependencies": dependencies, "counts": counts, "cases": case_counts, "catalog": catalog}, sort_keys=True).encode()).hexdigest()
    return SeedPlan(config, uid("admin"), tuple(objects), tuple(samples), counts, case_counts, fingerprint, components_by_class)


def canonical_plan(plan: SeedPlan) -> dict[str, Any]:
    """Stable summary suitable for replay assertions and manifest output."""
    return {"fingerprint": plan.fingerprint, "counts": plan.counts, "case_counts": plan.case_counts,
            "samples": [(s.sample_id, s.case_id, s.method, s.path, s.payload, s.expected_status, s.resources) for s in plan.samples]}
