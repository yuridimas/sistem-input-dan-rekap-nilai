"""Verify that application tables and columns have database comments.

Audit komentar tabel/kolom PostgreSQL, bukan komentar pada source code.

CLI membaca konfigurasi backend dan mengembalikan exit code untuk
pemeriksaan deployment.
"""

import asyncio
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings


# Katalog pg_class/pg_attribute menyimpan komentar; kolom dropped dan alembic_version diabaikan.
COMMENTS_QUERY = text(
    """
    SELECT
        tables.table_schema,
        tables.table_name,
        pg_catalog.obj_description(relations.oid, 'pg_class') AS table_comment,
        columns.column_name,
        pg_catalog.col_description(relations.oid, attributes.attnum) AS column_comment
    FROM information_schema.tables AS tables
    JOIN information_schema.columns AS columns
      ON columns.table_schema = tables.table_schema
     AND columns.table_name = tables.table_name
    JOIN pg_catalog.pg_namespace AS namespaces
      ON namespaces.nspname = tables.table_schema
    JOIN pg_catalog.pg_class AS relations
      ON relations.relnamespace = namespaces.oid
     AND relations.relname = tables.table_name
    JOIN pg_catalog.pg_attribute AS attributes
      ON attributes.attrelid = relations.oid
     AND attributes.attname = columns.column_name
     AND NOT attributes.attisdropped
    WHERE tables.table_schema = 'public'
      AND tables.table_type = 'BASE TABLE'
      AND tables.table_name <> 'alembic_version'
    ORDER BY tables.table_name, columns.ordinal_position
    """
)


def find_missing_comments(rows: Sequence[Mapping[str, object]]) -> list[str]:
    """Laporkan tabel sekali dan setiap kolom berkomentar kosong.

    Return application tables and columns whose comments are null or
    blank.

    Membaca rows tanpa mutasi atau akses DB.

    Args:
        rows: Baris katalog berisi nama tabel/kolom beserta komentarnya.

    Returns:
        Daftar pesan bisa kosong.
    """
    missing: list[str] = []
    checked_tables: set[tuple[str, str]] = set()

    for row in rows:
        schema = str(row["table_schema"])
        table = str(row["table_name"])
        table_key = (schema, table)
        if table_key not in checked_tables:
            checked_tables.add(table_key)
            if not str(row["table_comment"] or "").strip():
                missing.append(f"table {schema}.{table} has no comment")

        column = str(row["column_name"])
        if not str(row["column_comment"] or "").strip():
            missing.append(f"column {schema}.{table}.{column} has no comment")

    return missing


async def verify_database() -> int:
    """Audit komentar katalog public dan tolak schema kosong.

    Hanya SELECT DB dan output stdout/stderr, engine ditutup.

    Returns:
        Exit code 0 sukses, 1 gagal.
    """
    engine = create_async_engine(get_settings().database_url)
    try:
        async with engine.connect() as connection:
            result = await connection.execute(COMMENTS_QUERY)
            rows = result.mappings().all()
    except Exception as exc:
        print(
            f"Could not inspect database ({type(exc).__name__}); check DATABASE_URL and database availability.",
            file=sys.stderr,
        )
        return 1
    finally:
        await engine.dispose()

    if not rows:
        print("No application tables found in public schema.", file=sys.stderr)
        return 1

    missing = find_missing_comments(rows)
    if missing:
        print("Database comments are missing:", file=sys.stderr)
        for item in missing:
            print(f"- {item}", file=sys.stderr)
        return 1

    table_count = len({(row["table_schema"], row["table_name"]) for row in rows})
    print(f"Verified comments for {table_count} application tables and {len(rows)} columns.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(verify_database()))
