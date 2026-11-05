from datetime import datetime, timezone
import re

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
