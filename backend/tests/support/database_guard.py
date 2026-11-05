"""Require explicit, isolated service targets before pytest imports the app."""

from collections.abc import MutableMapping

from sqlalchemy.engine import make_url

_BOUND_MODULES = {"app.database", "app.celery_app", "app.services.auth"}
_REQUIRED = ("TEST_DATABASE_URL", "TEST_REDIS_URL", "TEST_DATABASE_DISPOSABLE")


def configure_test_environment(env: MutableMapping[str, str], *, enforce_import_order: bool = True) -> None:
    """Validate disposable targets and redirect all app connections to them.

    This function does not import application modules or open connections.
    """
    import sys

    bound = sorted(_BOUND_MODULES.intersection(sys.modules))
    if enforce_import_order and bound:
        raise RuntimeError("pytest target guard loaded after application runtime modules")

    missing = [key for key in _REQUIRED if not env.get(key)]
    if missing:
        raise RuntimeError("pytest requires TEST_DATABASE_URL, TEST_REDIS_URL and TEST_DATABASE_DISPOSABLE=1")
    if env["TEST_DATABASE_DISPOSABLE"] != "1":
        raise RuntimeError("pytest requires explicit TEST_DATABASE_DISPOSABLE=1")

    try:
        url = make_url(env["TEST_DATABASE_URL"])
    except Exception as exc:
        raise RuntimeError("TEST_DATABASE_URL is invalid") from exc
    if url.drivername != "postgresql+asyncpg" or not (url.database or "").endswith("_test"):
        raise RuntimeError("TEST_DATABASE_URL must target PostgreSQL async database ending in _test")

    redis_url = env["TEST_REDIS_URL"]
    if not redis_url.startswith("redis://") or not url.database:
        raise RuntimeError("TEST_REDIS_URL must be a Redis URL")

    env["DATABASE_URL"] = env["TEST_DATABASE_URL"]
    env["REDIS_URL"] = redis_url
    env["SMTP_HOST"] = ""
