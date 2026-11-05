"""CLI planning stays database-free and writes a secret-free manifest."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.seeding.config import resolve_config
from app.seeding.manifest import write_manifest
from app.seeding.scenarios import build_plan


def test_plan_needs_no_database_or_password(tmp_path):
    env = {key: value for key, value in os.environ.items()
           if key not in {"DATABASE_URL", "REDIS_URL", "SEED_PASSWORD", "SMTP_HOST"}}
    result = subprocess.run(
        [sys.executable, "-m", "app.seeding", "plan", "--dataset", "review-manual",
         "--seed", "20261105", "--output-dir", str(tmp_path)],
        env=env, capture_output=True, text=True, check=True,
    )
    output = json.loads(result.stdout)
    manifest = Path(output["manifest"])
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["status"] == "planned"
    assert len(data["cases"]) >= 5 * len(data["case_counts"])
    assert "password_hash" not in manifest.read_text(encoding="utf-8")


def test_invalid_dataset_is_rejected(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "app.seeding", "plan", "--dataset", "Bad_Name",
         "--output-dir", str(tmp_path)], capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert not list(tmp_path.glob("**/manifest.json"))


def test_apply_refuses_pytest_database_before_connecting(tmp_path):
    env = {**os.environ,
           "DATABASE_URL": "postgresql+asyncpg://test:test@127.0.0.1/grades_test",
           "APP_ENV": "development", "SMTP_HOST": "", "SEED_PASSWORD": "test-only"}
    result = subprocess.run(
        [sys.executable, "-m", "app.seeding", "apply", "--dataset", "must-not-apply",
         "--seed", "4", "--output-dir", str(tmp_path)],
        env=env, capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "database manual terpisah" in result.stdout
    assert not list(tmp_path.glob("**/manifest.json"))


def test_apply_requires_an_explicit_safe_environment(tmp_path):
    env = {**os.environ,
           "DATABASE_URL": "postgresql+asyncpg://test:test@127.0.0.1/manual_fixture",
           "SMTP_HOST": ""}
    env.pop("APP_ENV", None)
    result = subprocess.run(
        [sys.executable, "-m", "app.seeding", "apply", "--dataset", "missing-env",
         "--output-dir", str(tmp_path)],
        env=env, capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "APP_ENV" in result.stdout
    assert not list(tmp_path.glob("**/manifest.json"))


def test_manifest_will_not_replace_a_different_dataset_fingerprint(tmp_path):
    first = build_plan(resolve_config(dataset="same-dataset", seed=11))
    second = build_plan(resolve_config(dataset="same-dataset", seed=12))
    target = write_manifest(tmp_path, first)
    original = target.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="another fingerprint"):
        write_manifest(tmp_path, second)
    assert target.read_text(encoding="utf-8") == original
