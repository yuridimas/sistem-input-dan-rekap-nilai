"""Command line interface for planning and appending manual seed datasets."""

import argparse
import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from app.seeding.config import resolve_config
from app.seeding.manifest import load_manifest, write_manifest
from app.seeding.scenarios import build_plan


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("plan", "apply", "inspect"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--dataset", required=True)
        sub.add_argument("--profile", choices=("manual", "light-load"), default="manual")
        sub.add_argument("--seed", type=int)
        sub.add_argument("--min-samples", type=int)
        sub.add_argument("--max-samples", type=int)
        sub.add_argument("--max-rows", type=int)
        sub.add_argument("--reference-time", help="ISO-8601 timestamp with timezone")
        sub.add_argument("--output-dir", type=Path, default=Path(".artifacts/seeding"))
    return parser


def _safe_database_url() -> str:
    from app.config import get_settings

    settings = get_settings()
    parsed = urlsplit(settings.database_url)
    database = parsed.path.lstrip("/").lower()
    environment = os.getenv("APP_ENV", "").lower()
    if environment not in {"development", "local", "test"}:
        raise ValueError("APP_ENV harus secara eksplisit development, local, atau test untuk memakai seeder")
    if "database_url" not in settings.model_fields_set:
        raise ValueError("DATABASE_URL harus ditentukan secara eksplisit sebelum memakai seeder")
    if settings.smtp_host:
        raise ValueError("Seeder menolak SMTP aktif")
    if not parsed.hostname or not database or database.endswith("_test") or database in {"postgres", "template0", "template1"}:
        raise ValueError("Seeder memerlukan database manual terpisah yang bukan database test")
    if environment == "test" and database != "manual_fixture":
        raise ValueError("APP_ENV=test hanya boleh memakai database khusus manual_fixture")
    return settings.database_url


async def _persist(command: str, plan, password: str | None, *, refuse_rebuild: bool = False):
    if command == "apply" and not password:
        raise ValueError("SEED_PASSWORD wajib diisi untuk apply")
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.seeding.dataset import apply_plan, inspect_plan

    engine = create_async_engine(_safe_database_url())
    try:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            if command == "apply":
                state = await inspect_plan(session, plan)
                if state.status == "incomplete":
                    if refuse_rebuild:
                        raise ValueError("dataset yang pernah di-apply memiliki row hilang; seeder menolak recreate")
                    return state
                if refuse_rebuild and state.status != "existing":
                    raise ValueError("dataset yang pernah di-apply memiliki row hilang; seeder menolak recreate")
                return await apply_plan(session, plan, password=password)
            return await inspect_plan(session, plan)
    finally:
        await engine.dispose()


def main() -> int:
    args = _parser().parse_args()
    try:
        reference_time = (datetime.fromisoformat(args.reference_time.replace("Z", "+00:00"))
                          if args.reference_time else None)
        config = resolve_config(dataset=args.dataset, profile=args.profile,
                                seed=args.seed, min_samples=args.min_samples,
                                max_samples=args.max_samples, max_rows=args.max_rows,
                                reference_time=reference_time)
        plan = build_plan(config)
        manifest_path = args.output_dir / config.dataset / "manifest.json"
        previous_manifest = load_manifest(manifest_path)
        if previous_manifest and previous_manifest.get("fingerprint") != plan.fingerprint:
            raise ValueError("manifest dataset exists with another fingerprint; use a new dataset name")
        if args.command == "plan":
            output = write_manifest(args.output_dir, plan)
            print(json.dumps({"seed": config.seed, "fingerprint": plan.fingerprint,
                              "counts": plan.counts, "manifest": str(output)}, indent=2))
            return 0
        _safe_database_url()
        password = os.getenv("SEED_PASSWORD")
        if args.command == "apply":
            if not password:
                raise ValueError("SEED_PASSWORD wajib diisi untuk apply")
            write_manifest(args.output_dir, plan, "planned")
        result = asyncio.run(_persist(args.command, plan, password,
                                      refuse_rebuild=bool(previous_manifest and previous_manifest.get("status") in {"applied", "created", "existing"})))
        manifest_status = "applied" if args.command == "apply" and result.status in {"created", "existing"} else result.status
        write_manifest(args.output_dir, plan, manifest_status,
                       observed={"status": result.status, "missing": result.missing})
        print(json.dumps({"status": result.status, "fingerprint": result.fingerprint,
                          "counts": result.counts, "missing": result.missing}, indent=2))
        return 0
    except (ValueError, RuntimeError) as error:
        print(f"error: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
