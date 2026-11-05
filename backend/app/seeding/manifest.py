"""Secret-free, human-readable seed plan artifacts."""

import json
from importlib.metadata import version
import os
from pathlib import Path
import tempfile
from typing import Any

from app.seeding.scenarios import SeedPlan
from app.seeding.scenarios import CASE_CATALOG


def manifest_data(plan: SeedPlan, status: str = "planned", observed: dict[str, Any] | None = None) -> dict[str, Any]:
    data = {
        "dataset": plan.config.dataset,
        "profile": plan.config.profile,
        "seed": plan.config.seed,
        "generator_version": plan.config.generator_version,
        "dependencies": {"Faker": version("Faker"), "polyfactory": version("polyfactory")},
        "reference_time": plan.config.reference_time.isoformat(),
        "actor_accounts": {
            "superadmin": {"email": f"admin-{plan.config.dataset}@example.test", "password": "<SEED_PASSWORD>"},
            "lecturer": {"email": f"lecturer-{plan.config.dataset}@example.test", "password": "<SEED_PASSWORD>"},
            "foreign_lecturer": {"email": f"foreign-{plan.config.dataset}@example.test", "password": "<SEED_PASSWORD>"},
        },
        "fingerprint": plan.fingerprint,
        "status": status,
        "counts": plan.counts,
        "case_counts": plan.case_counts,
        "catalog": [
            {"case_id": case.case_id, "operation": case.operation,
             "manual_support": case.manual_support, "mutates": case.mutates,
             "expected_status": case.expected_status,
             "automation_reference": case.automation_reference}
            for case in CASE_CATALOG
        ],
        "cases": [
            {"sample_id": sample.sample_id, "case_id": sample.case_id,
             "actor": sample.actor_key, "method": sample.method,
             "path": sample.path, "payload": sample.payload,
             "resources": sample.resources,
             "expected_status": sample.expected_status}
            for sample in plan.samples
        ],
    }
    if observed is not None:
        data["observed"] = observed
    return data


def load_manifest(path: Path) -> dict[str, Any] | None:
    """Read an existing manifest without changing its contents."""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(directory: Path, plan: SeedPlan, status: str = "planned",
                   observed: dict[str, Any] | None = None) -> Path:
    """Atomically write the JSON manifest below the selected root."""
    target_dir = directory / plan.config.dataset
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "manifest.json"
    if target.exists():
        previous = json.loads(target.read_text(encoding="utf-8"))
        if previous.get("fingerprint") != plan.fingerprint:
            raise ValueError("manifest dataset exists with another fingerprint; use a new dataset name")
        if previous.get("status") in {"applied", "created", "existing"} and status in {"planned", "missing", "incomplete"}:
            status = "applied"
    content = json.dumps(manifest_data(plan, status, observed), ensure_ascii=False, indent=2) + "\n"
    fd, temporary = tempfile.mkstemp(dir=target_dir, prefix=".manifest-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target
