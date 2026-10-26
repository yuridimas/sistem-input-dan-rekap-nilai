"""Unit audit metadata komentar tanpa koneksi DB.

Unit test memakai dependency palsu/data lokal tanpa DB atau SMTP nyata.
"""
from scripts.verify_comments import find_missing_comments


def test_find_missing_comments_reports_table_and_column():
    """Laporkan tabel sekali meskipun banyak kolom kosong."""
    rows = [
        {
            "table_schema": "public",
            "table_name": "courses",
            "table_comment": None,
            "column_name": "name",
            "column_comment": "Nama mata kuliah",
        },
        {
            "table_schema": "public",
            "table_name": "courses",
            "table_comment": None,
            "column_name": "code",
            "column_comment": "   ",
        },
    ]

    assert find_missing_comments(rows) == [
        "table public.courses has no comment",
        "column public.courses.code has no comment",
    ]


def test_find_missing_comments_accepts_indonesian_comments():
    """Terima komentar Indonesia yang sudah terisi."""
    rows = [
        {
            "table_schema": "public",
            "table_name": "courses",
            "table_comment": "Tabel mata kuliah",
            "column_name": "name",
            "column_comment": "Nama mata kuliah",
        }
    ]

    assert find_missing_comments(rows) == []
