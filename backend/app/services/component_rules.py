"""Shared validation rules without database or service dependencies.

Validasi konfigurasi bersama untuk service components, scores, dan
finalisasi.

Aturan ini tidak menulis database sehingga seluruh konfigurasi dapat
diperiksa sebelum mutasi.
"""

from decimal import Decimal

from fastapi import HTTPException

from app.schemas.component import ComponentCreate


def validate_configuration(components: list[ComponentCreate]) -> None:
    """Validasi bobot penuh dan keberadaan kategori ujian wajib.

    Args:
        components: Konfigurasi komponen kelas yang menjadi dasar
            penilaian.

    Raises:
        HTTPException: 422 jika bobot bukan 100 persen atau kategori
            uts/uas tidak ada.
    """
    if sum((component.weight for component in components), Decimal("0")) != Decimal("100"):
        raise HTTPException(422, "Jumlah bobot komponen harus tepat 100%")
    categories = {component.category for component in components}
    if not {"uts", "uas"}.issubset(categories):
        raise HTTPException(422, "Komponen wajib mencakup minimal satu UTS dan satu UAS")
