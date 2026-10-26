"""Component configuration, exact weights, and class access boundaries.

Keutuhan konfigurasi komponen dan proteksi perubahan paralel.

Memerlukan PostgreSQL disposable yang dimigrasi; beberapa skenario
melakukan commit nyata.
"""

import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_db
from app.main import app
from app.models.class_ import Class
from app.models.course import Course
from app.models.user import User
from app.services.auth import create_access_token
from app.services.auth import decode_token


def component_set(uts="30", uas="40", tugas="30"):
    """Bangun kategori wajib dengan bobot yang dapat diubah."""
    return [
        {"name": "Tugas", "category": "tugas", "weight": tugas, "order_index": 0},
        {"name": "UTS", "category": "uts", "weight": uts, "order_index": 1},
        {"name": "UAS", "category": "uas", "weight": uas, "order_index": 2},
    ]


@pytest_asyncio.fixture(loop_scope="session")
async def component_context():
    """Isolasi commit endpoint melalui transaksi savepoint."""
    # API commits use savepoints; all data is rolled back at fixture teardown.
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with AsyncSession(
            bind=connection, expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        ) as db:
            suffix = uuid.uuid4().hex
            users = [
                User(email=f"{role}-{index}-{suffix}@example.com", full_name=role,
                     password_hash="unused", role=role)
                for index, role in enumerate(["lecturer", "lecturer", "superadmin"])
            ]
            db.add_all(users)
            await db.flush()
            course = Course(code=f"CMP-{suffix}", name="Komponen", credits=3,
                            semester="2026/1", created_by=users[0].id)
            db.add(course)
            await db.flush()
            class_ = Class(course_id=course.id, section="A", academic_year="2026/2027",
                           lecturer_id=users[0].id)
            db.add(class_)
            await db.commit()

            async def override_db():
                """Pinjamkan session fixture ke dependency endpoint."""
                yield db

            app.dependency_overrides[get_db] = override_db
            headers = [
                {"Authorization": "Bearer " + create_access_token(str(user.id), user.role)}
                for user in users
            ]
            try:
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    yield client, str(class_.id), headers, db
            finally:
                app.dependency_overrides.pop(get_db, None)
        await transaction.rollback()


@pytest.mark.asyncio
async def test_components_create_list_update_and_reject_invalid_delete(component_context):
    """Pertahankan konfigurasi valid selama mutasi komponen."""
    client, class_id, (owner, _, admin), _db = component_context
    url = f"/classes/{class_id}/components"
    assert (await client.get(url, headers=owner)).json() == []
    response = await client.post(url, headers=owner, json=component_set())
    assert response.status_code == 201, response.text
    rows = response.json()
    assert sum(Decimal(row["weight"]) for row in rows) == Decimal("100")
    assert [row["category"] for row in rows] == ["tugas", "uts", "uas"]
    assert all(row["class_id"] == class_id and row["created_at"] for row in rows)
    assert Decimal(rows[0]["max_score"]) == Decimal("100")
    path = f"/components/{rows[0]['id']}"
    response = await client.patch(path, headers=owner, json={"name": " Tugas mandiri "})
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Tugas mandiri"
    assert (await client.get(url, headers=admin)).status_code == 200

    # Invalid projected configurations must leave the existing set intact.
    for payload in ({"weight": "29.99"}, {"category": "custom", "weight": "30"}):
        target = f"/components/{rows[1]['id']}" if "category" in payload else path
        assert (await client.patch(target, headers=owner, json=payload)).status_code == 422
    assert (await client.delete(path, headers=owner)).status_code == 422
    assert len((await client.get(url, headers=owner)).json()) == 3
    # Appending a second full set would exceed 100%.
    assert (await client.post(url, headers=owner, json=component_set())).status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    component_set(tugas="29.99"),
    component_set(tugas="29.9999"),
    component_set(tugas="30.0001"),
    component_set(tugas="0", uts="60"),
    component_set(tugas="-1", uts="61"),
    component_set(tugas="NaN"),
    component_set(tugas="Infinity"),
    [{"name": "UAS", "category": "uas", "weight": "100"}],
    [{"name": "UTS", "category": "uts", "weight": "100"}],
    [{"name": " ", "category": "uts", "weight": "50"},
     {"name": "UAS", "category": "uas", "weight": "50"}],
    [{"name": "UTS", "category": "uts", "weight": "50", "max_score": 0},
     {"name": "UAS", "category": "uas", "weight": "50"}],
    [{"name": "UTS", "category": "lain", "weight": "50"},
     {"name": "UAS", "category": "uas", "weight": "50"}],
    [],
])
async def test_components_reject_invalid_sets_atomically(component_context, payload):
    """Tolak konfigurasi invalid tanpa insert parsial."""
    client, class_id, (owner, _, _), _db = component_context
    url = f"/classes/{class_id}/components"
    response = await client.post(url, headers=owner, json=payload)
    assert response.status_code == 422, response.text
    assert (await client.get(url, headers=owner)).json() == []


@pytest.mark.asyncio
async def test_components_require_class_owner_or_admin(component_context):
    """Batasi konfigurasi pada pemilik kelas atau admin."""
    client, class_id, (owner, other, admin), _db = component_context
    url = f"/classes/{class_id}/components"
    assert (await client.get(url)).status_code == 401
    assert (await client.post(url, headers=other, json=component_set())).status_code == 403
    assert (await client.get(url, headers=other)).status_code == 403
    response = await client.post(url, headers=admin, json=component_set())
    assert response.status_code == 201, response.text
    path = f"/components/{response.json()[0]['id']}"
    assert (await client.patch(path, headers=other, json={"name": "X"})).status_code == 403
    assert (await client.delete(path, headers=other)).status_code == 403
    assert (await client.patch(path, headers=admin, json={"name": "Admin"})).status_code == 200
    assert (await client.get(f"/classes/{uuid.uuid4()}/components", headers=owner)).status_code == 404
    assert (await client.patch(f"/components/{uuid.uuid4()}", headers=owner, json={})).status_code == 404


@pytest.mark.asyncio
async def test_components_decimal_roundtrip_and_comments(component_context):
    """Pertahankan Decimal dan metadata setelah persistence."""
    client, class_id, (owner, _, _), db = component_context
    response = await client.post(f"/classes/{class_id}/components", headers=owner,
                                 json=component_set(uts="33.33", uas="33.34", tugas="33.33"))
    assert response.status_code == 201, response.text
    assert sum(Decimal(row["weight"]) for row in response.json()) == Decimal("100.00")
    result = await db.execute(text("""
        SELECT col_description('components'::regclass, attnum)
        FROM pg_attribute WHERE attrelid = 'components'::regclass
        AND attnum > 0 AND NOT attisdropped
    """))
    comments = result.scalars().all()
    assert len(comments) == 8 and all(comments)
    assert await db.scalar(text("SELECT obj_description('components'::regclass, 'pg_class')"))


@pytest.mark.asyncio
async def test_components_replace_set_preserves_ids_and_is_atomic(component_context):
    """Pertahankan ID saat mengganti konfigurasi atomik."""
    client, class_id, (owner, other, _), _db = component_context
    url = f"/classes/{class_id}/components"
    rows = (await client.post(url, headers=owner, json=component_set())).json()
    replacement = [
        {"id": rows[1]["id"], "name": "UTS baru", "category": "uts", "weight": "45"},
        {"id": rows[2]["id"], "name": "UAS baru", "category": "uas", "weight": "45"},
        {"name": "Praktikum", "category": "custom", "weight": "10"},
    ]
    assert (await client.put(url, headers=other, json=replacement)).status_code == 403
    invalid = [dict(row) for row in replacement]
    invalid[0]["weight"] = "44.99"
    assert (await client.put(url, headers=owner, json=invalid)).status_code == 422
    assert (await client.get(url, headers=owner)).json() == rows
    unknown = [dict(row) for row in replacement]
    unknown[0]["id"] = str(uuid.uuid4())
    assert (await client.put(url, headers=owner, json=unknown)).status_code == 422
    duplicate = [dict(row) for row in replacement]
    duplicate[1]["id"] = duplicate[0]["id"]
    assert (await client.put(url, headers=owner, json=duplicate)).status_code == 422
    response = await client.put(url, headers=owner, json=replacement)
    assert response.status_code == 200, response.text
    updated = response.json()
    assert {row["id"] for row in updated}.issuperset({rows[1]["id"], rows[2]["id"]})
    assert rows[0]["id"] not in {row["id"] for row in updated}
    assert sum(Decimal(row["weight"]) for row in updated) == Decimal("100")
    assert (await client.get(url, headers=owner)).json() == updated


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [{"name": None}, {"weight": None}, {"max_score": "0"},
                                         {"name": " "}, {"weight": "29.9999"}])
async def test_components_invalid_patch_leaves_data_unchanged(component_context, payload):
    """Tolak patch invalid sebelum mutasi field lainnya."""
    client, class_id, (owner, _, _), _db = component_context
    url = f"/classes/{class_id}/components"
    rows = (await client.post(url, headers=owner, json=component_set())).json()
    response = await client.patch(f"/components/{rows[0]['id']}", headers=owner, json=payload)
    assert response.status_code == 422, response.text
    assert (await client.get(url, headers=owner)).json() == rows


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["create", "update", "delete", "replace"])
async def test_components_check_current_owner_after_class_lock(component_context, monkeypatch, operation):
    """Periksa pemilik terbaru setelah lock kelas."""
    from app.repositories import component as repo

    client, class_id, (owner, other, _), db = component_context
    url = f"/classes/{class_id}/components"
    rows = (await client.post(url, headers=owner, json=component_set())).json()
    other_id = uuid.UUID(decode_token(other["Authorization"].split()[1])["sub"])
    original_lock = repo.lock_class

    async def transfer_before_lock(session, target_id):
        """Pindahkan pemilik sebelum lock diambil."""
        # Simulate an admin reassignment committed before the mutation's lock.
        await db.execute(
            update(Class).where(Class.id == target_id).values(lecturer_id=other_id)
            .execution_options(synchronize_session=False)
        )
        await db.flush()
        await original_lock(session, target_id)

    monkeypatch.setattr(repo, "lock_class", transfer_before_lock)
    if operation == "create":
        response = await client.post(url, headers=owner, json=component_set())
    elif operation == "update":
        response = await client.patch(f"/components/{rows[0]['id']}", headers=owner,
                                      json={"name": "Tidak boleh berubah"})
    elif operation == "delete":
        response = await client.delete(f"/components/{rows[0]['id']}", headers=owner)
    else:
        response = await client.put(url, headers=owner, json=component_set())
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_component_removed_before_lock_returns_not_found(component_context, monkeypatch):
    """Tolak mutasi komponen yang terhapus sebelum lock."""
    from app.models.component import Component
    from app.repositories import component as repo

    client, class_id, (owner, _, _), db = component_context
    rows = (await client.post(f"/classes/{class_id}/components", headers=owner,
                              json=component_set())).json()
    target_id = uuid.UUID(rows[0]["id"])
    original_lock = repo.lock_class

    async def replace_before_lock(session, target_class_id):
        """Hapus komponen lewat penggantian sebelum lock."""
        # A concurrent valid set replacement removes Tugas and reweights UTS/UAS.
        await db.execute(delete(Component).where(Component.id == target_id)
                         .execution_options(synchronize_session=False))
        await db.execute(update(Component).where(Component.class_id == target_class_id)
                         .values(weight=Decimal("50")))
        await db.flush()
        await original_lock(session, target_class_id)

    monkeypatch.setattr(repo, "lock_class", replace_before_lock)
    response = await client.patch(f"/components/{target_id}", headers=owner, json={"name": "X"})
    assert response.status_code == 404, response.text
