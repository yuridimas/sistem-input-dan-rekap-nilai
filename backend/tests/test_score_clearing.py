"""Clearing draft scores preserves atomicity and release protections.

Penghapusan skor draft yang atomik dan proteksi rilis.

Memerlukan PostgreSQL disposable yang dimigrasi; beberapa skenario
melakukan commit nyata.
"""

from decimal import Decimal
import uuid

import pytest

from tests.test_scores import grading_context, score_payload
from tests.test_finalization import fill_scores, mock_publisher


@pytest.mark.asyncio
async def test_clear_and_upsert_recalculate_preserving_omitted_and_zero(grading_context):
    """Null, nol, dan field absen dibedakan dalam patch yang sama."""
    client, class_id, enrollments, components, (owner, _, _), _db = grading_context
    url = f"/enrollments/{enrollments[0]}/scores"
    assert (await client.put(url, headers=owner, json=score_payload(components))).status_code == 200
    response = await client.put(url, headers=owner, json={components[0]["id"]: None, components[1]["id"]: "0"})
    assert response.status_code == 200, response.text
    assert Decimal(response.json()["final_score"]) == Decimal("36")
    row = (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()["grades"][0]
    assert components[0]["id"] not in row["scores"]
    assert Decimal(row["scores"][components[1]["id"]]) == 0
    assert Decimal(row["scores"][components[2]["id"]]) == 90


@pytest.mark.asyncio
async def test_clear_absent_scores_is_idempotent_and_blocks_release(grading_context, monkeypatch):
    """Hapus skor absen tanpa membuat kelas lengkap."""
    client, class_id, enrollments, components, (owner, _, _), _db = grading_context
    mock_publisher(monkeypatch)
    for _ in range(2):
        response = await client.put(f"/enrollments/{enrollments[0]}/scores", headers=owner,
                                    json={components[0]["id"]: None})
        assert response.status_code == 200, response.text
        assert Decimal(response.json()["final_score"]) == 0
    response = await client.post(f"/classes/{class_id}/finalize", headers=owner)
    assert response.status_code == 422
    assert len(response.json()["detail"]["missing"]) == len(components) * len(enrollments)


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", ["101", "-1", "0.001", "NaN", True])
async def test_clear_with_invalid_score_does_not_delete_anything(grading_context, invalid):
    """Batalkan penghapusan jika patch lainnya invalid."""
    client, class_id, enrollments, components, (owner, _, _), _db = grading_context
    url = f"/enrollments/{enrollments[0]}/scores"
    await client.put(url, headers=owner, json=score_payload(components))
    response = await client.put(url, headers=owner, json={components[0]["id"]: None, components[1]["id"]: invalid})
    assert response.status_code == 422
    row = (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()["grades"][0]
    assert Decimal(row["scores"][components[0]["id"]]) == 80
    assert Decimal(row["final_score"]) == 81


@pytest.mark.asyncio
async def test_clear_requires_access_and_known_component(grading_context):
    """Hapus tetap memeriksa pemilik dan komponen kelas yang tepat."""
    client, class_id, enrollments, components, (owner, other, admin), _db = grading_context
    url = f"/enrollments/{enrollments[0]}/scores"
    payload = {components[0]["id"]: None}
    assert (await client.put(url, json=payload)).status_code == 401
    assert (await client.put(url, headers=other, json=payload)).status_code == 403
    assert (await client.put(url, headers=owner, json={str(uuid.uuid4()): None})).status_code == 422
    assert (await client.put(url, headers=admin, json=payload)).status_code == 200


@pytest.mark.asyncio
async def test_finalized_score_cannot_be_cleared(grading_context, monkeypatch):
    """Skor rilis tidak boleh dikosongkan melalui payload null."""
    client, class_id, enrollments, components, (owner, _, admin), _db = grading_context
    mock_publisher(monkeypatch)
    await fill_scores(grading_context)
    assert (await client.post(f"/classes/{class_id}/finalize", headers=owner)).status_code == 202
    for headers in (owner, admin):
        response = await client.put(f"/enrollments/{enrollments[0]}/scores", headers=headers,
                                    json={components[0]["id"]: None})
        assert response.status_code == 409
