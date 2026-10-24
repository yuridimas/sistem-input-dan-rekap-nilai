"""Shared validation rules without database or service dependencies."""

from decimal import Decimal

from fastapi import HTTPException

from app.schemas.component import ComponentCreate


def validate_configuration(components: list[ComponentCreate]) -> None:
    if sum((component.weight for component in components), Decimal("0")) != Decimal("100"):
        raise HTTPException(422, "Jumlah bobot komponen harus tepat 100%")
    categories = {component.category for component in components}
    if not {"uts", "uas"}.issubset(categories):
        raise HTTPException(422, "Komponen wajib mencakup minimal satu UTS dan satu UAS")
