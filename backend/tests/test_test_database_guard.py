from pathlib import Path
import subprocess
import sys

import pytest

from tests.support.database_guard import configure_test_environment


@pytest.mark.parametrize("updates", [
    {"TEST_DATABASE_URL": None},
    {"TEST_DATABASE_DISPOSABLE": "0"},
    {"TEST_DATABASE_URL": "postgresql://u:p@host/grades_test"},
    {"TEST_DATABASE_URL": "postgresql+asyncpg://u:p@host/grades"},
    {"TEST_REDIS_URL": "http://redis"},
])
def test_requires_explicit_disposable_target(updates):
    env = {
        "TEST_DATABASE_URL": "postgresql+asyncpg://u:p@host/grades_test",
        "TEST_REDIS_URL": "redis://redis:6379/0",
        "TEST_DATABASE_DISPOSABLE": "1",
        **updates,
    }
    for key, value in updates.items():
        if value is None:
            env.pop(key, None)
    with pytest.raises(RuntimeError):
        configure_test_environment(env)


def test_redirects_all_test_connections():
    env = {
        "DATABASE_URL": "postgresql+asyncpg://human:secret@db/grades",
        "REDIS_URL": "redis://manual/0",
        "TEST_DATABASE_URL": "postgresql+asyncpg://test:test@pg/grades_test",
        "TEST_REDIS_URL": "redis://test-redis:6379/0",
        "TEST_DATABASE_DISPOSABLE": "1",
    }
    configure_test_environment(env, enforce_import_order=False)
    assert env["DATABASE_URL"] == env["TEST_DATABASE_URL"]
    assert env["REDIS_URL"] == env["TEST_REDIS_URL"]
    assert env["SMTP_HOST"] == ""
    assert "secret" not in repr(env)


def test_guard_fails_before_pytest_collection(tmp_path):
    sentinel = tmp_path / "collected.txt"
    test_file = tmp_path / "test_collection_sentinel.py"
    test_file.write_text(
        f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('collected')\n"
        "def test_sentinel(): pass\n", encoding="utf-8",
    )
    env = {k: v for k, v in __import__("os").environ.items() if not k.startswith("TEST_")}
    env["PYTHONPATH"] = str(Path(__file__).parents[1])
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "tests.conftest", "-q", str(test_file)],
        env=env, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert not sentinel.exists()
