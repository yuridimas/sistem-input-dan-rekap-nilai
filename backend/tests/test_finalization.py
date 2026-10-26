"""Finalization transaction, sequential ranking, and release boundaries.

Transaksi rilis, ranking, dan batas enqueue.

Memerlukan PostgreSQL disposable yang dimigrasi; beberapa skenario
melakukan commit nyata.
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import delete, select, text, update
from sqlalchemy.exc import IntegrityError

from app.models.component import Component
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.student import Student
from app.services.auth import decode_token
from tests.test_scores import grading_context, score_payload


async def fill_scores(context, values=("80", "70", "90")):
    """Isi seluruh roster agar skenario dapat mencapai batas finalisasi.
    """
    client, _class_id, enrollments, components, (owner, _, _), _db = context
    for enrollment in enrollments:
        response = await client.put(f"/enrollments/{enrollment}/scores", headers=owner,
                                    json=score_payload(components, values))
        assert response.status_code == 200, response.text


def mock_publisher(monkeypatch):
    """Catat enqueue tanpa broker Redis nyata."""
    published = []

    async def publish(grade_ids):
        """Kendalikan hasil publish dalam skenario test."""
        published.extend(grade_ids)
        return len(grade_ids)

    monkeypatch.setattr("app.services.grade.publish_grade_releases", publish, raising=False)
    return published


@pytest.mark.asyncio
async def test_finalize_lists_every_missing_score_without_writes(grading_context, monkeypatch):
    """Laporkan semua skor kosong tanpa rilis parsial."""
    client, class_id, enrollments, components, (owner, _, _), db = grading_context
    published = mock_publisher(monkeypatch)
    await client.put(f"/enrollments/{enrollments[0]}/scores", headers=owner,
                     json={components[0]["id"]: "0"})
    response = await client.post(f"/classes/{class_id}/finalize", headers=owner)
    assert response.status_code == 422, response.text
    roster = (await client.get(f"/classes/{class_id}/roster", headers=owner)).json()
    assert response.json()["detail"]["missing"] == [
        {"student_nim": entry["student"]["nim"], "component_name": component["name"]}
        for index, entry in enumerate(roster) for component in components
        if index != 0 or component["id"] != components[0]["id"]
    ]
    grades = (await db.execute(select(Grade).where(Grade.enrollment_id.in_(
        [uuid.UUID(value) for value in enrollments]
    )))).scalars().all()
    assert all(grade.status == "draft" for grade in grades)
    assert published == []


@pytest.mark.asyncio
@pytest.mark.parametrize("release_as_admin", [False, True])
async def test_finalize_success_ties_and_release_metadata(grading_context, monkeypatch, release_as_admin):
    """Rilis total, ranking, pelaku, dan waktu secara konsisten."""
    client, class_id, enrollments, _components, (owner, _, admin), db = grading_context
    published = mock_publisher(monkeypatch)
    assert (await client.get(f"/classes/{class_id}/ranking", headers=owner)).json() == []
    await fill_scores(grading_context)
    # Ensure finalization recomputes the grade rather than trusting an outdated cached total.
    await db.execute(update(Grade).where(Grade.enrollment_id.in_([uuid.UUID(value) for value in enrollments]))
                     .values(final_score=Decimal("1")))
    await db.commit()
    release_headers = admin if release_as_admin else owner
    response = await client.post(f"/classes/{class_id}/finalize", headers=release_headers)
    assert response.status_code == 202, response.text
    assert response.json() == {"finalized_count": 2, "notified": 2}
    grades = (await db.execute(select(Grade).where(Grade.enrollment_id.in_(
        [uuid.UUID(value) for value in enrollments]
    )))).scalars().all()
    owner_id = uuid.UUID(decode_token(release_headers["Authorization"].split()[1])["sub"])
    assert all(grade.status == "finalized" and grade.final_score == Decimal("81") for grade in grades)
    assert all(grade.finalized_by == owner_id and grade.finalized_at for grade in grades)
    assert len({grade.finalized_at for grade in grades}) == 1
    assert all(grade.release_notified_at is None for grade in grades)
    assert set(published) == {grade.id for grade in grades}
    response = await client.get(f"/classes/{class_id}/ranking", headers=admin)
    assert response.status_code == 200, response.text
    rows = response.json()
    assert [row["rank"] for row in rows] == [1, 2]
    assert [row["enrollment_id"] for row in rows] == enrollments
    assert all(Decimal(row["final_score"]) == Decimal("81") for row in rows)
    assert rows[0]["student"]["nim"] < rows[1]["student"]["nim"]
    assert (await client.post(f"/classes/{class_id}/finalize", headers=admin)).status_code == 409
    assert len(published) == 2


@pytest.mark.asyncio
async def test_ranking_orders_scores_before_nim_and_zero_is_complete(grading_context, monkeypatch):
    """Urutkan skor lalu NIM dan anggap nol sebagai lengkap."""
    client, class_id, enrollments, components, (owner, _, _), _db = grading_context
    mock_publisher(monkeypatch)
    await fill_scores(grading_context, ("0", "0", "0"))
    await client.put(f"/enrollments/{enrollments[1]}/scores", headers=owner,
                     json=score_payload(components, ("100", "100", "100")))
    response = await client.post(f"/classes/{class_id}/finalize", headers=owner)
    assert response.status_code == 202, response.text
    rows = (await client.get(f"/classes/{class_id}/ranking", headers=owner)).json()
    assert [row["enrollment_id"] for row in rows] == list(reversed(enrollments))
    assert [Decimal(row["final_score"]) for row in rows] == [Decimal("100"), Decimal("0")]


@pytest.mark.asyncio
async def test_finalized_class_locks_roster_scores_and_components(grading_context, monkeypatch):
    """Bekukan roster, skor, dan komponen setelah rilis."""
    client, class_id, enrollments, components, (owner, _, admin), db = grading_context
    mock_publisher(monkeypatch)
    await fill_scores(grading_context)
    assert (await client.post(f"/classes/{class_id}/finalize", headers=owner)).status_code == 202
    for headers in (owner, admin):
        response = await client.post(f"/classes/{class_id}/enrollments", headers=headers,
                                     json={"nim": f"locked-{uuid.uuid4().hex}"})
        assert response.status_code == 409, response.text
        assert (await client.delete(f"/classes/{class_id}/enrollments/{enrollments[0]}", headers=headers)).status_code == 409
        assert (await client.put(f"/enrollments/{enrollments[0]}/scores", headers=headers,
                                 json={components[0]["id"]: "100"})).status_code == 409
        assert (await client.patch(f"/components/{components[0]['id']}", headers=headers,
                                   json={"name": "X"})).status_code == 409
    assert len((await client.get(f"/classes/{class_id}/roster", headers=owner)).json()) == 2


@pytest.mark.asyncio
async def test_finalize_and_ranking_access(grading_context):
    """Jaga batas akses rilis dan ranking berdasarkan pemilik."""
    client, class_id, _enrollments, _components, (owner, other, _), _db = grading_context
    for suffix in ("finalize", "ranking"):
        method = client.post if suffix == "finalize" else client.get
        assert (await method(f"/classes/{class_id}/{suffix}")).status_code == 401
        assert (await method(f"/classes/{class_id}/{suffix}", headers=other)).status_code == 403
        assert (await method(f"/classes/{uuid.uuid4()}/{suffix}", headers=owner)).status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", ["empty", "components"])
async def test_finalize_rejects_empty_or_invalid_configuration(grading_context, monkeypatch, invalid):
    """Tolak rilis kelas kosong atau konfigurasi invalid."""
    client, class_id, enrollments, _components, (owner, _, _), db = grading_context
    published = mock_publisher(monkeypatch)
    if invalid == "empty":
        await db.execute(delete(Enrollment).where(Enrollment.class_id == uuid.UUID(class_id)))
    else:
        await db.execute(update(Component).where(Component.class_id == uuid.UUID(class_id)).values(weight=Decimal("1")))
    await db.commit()
    response = await client.post(f"/classes/{class_id}/finalize", headers=owner)
    assert response.status_code == 422, response.text
    assert published == []


@pytest.mark.asyncio
async def test_ranking_failure_rolls_back_finalization(grading_context, monkeypatch):
    """Rollback seluruh finalisasi ketika ranking gagal."""
    from app.repositories import ranking as ranking_repo

    client, class_id, enrollments, _components, (owner, _, _), db = grading_context
    published = mock_publisher(monkeypatch)
    await fill_scores(grading_context)

    async def fail(*args, **kwargs):
        """Suntik kegagalan untuk menguji penanganan error."""
        raise IntegrityError("INSERT rankings", {}, Exception("simulated failure"))

    monkeypatch.setattr(ranking_repo, "create_for_class", fail)
    response = await client.post(f"/classes/{class_id}/finalize", headers=owner)
    assert response.status_code == 409, response.text
    rows = (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()["grades"]
    assert all(row["status"] == "draft" for row in rows)
    assert (await client.get(f"/classes/{class_id}/ranking", headers=owner)).json() == []
    assert published == []


@pytest.mark.asyncio
async def test_finalization_uses_current_owner_after_lock(grading_context, monkeypatch):
    """Periksa pemilik terbaru setelah menunggu lock."""
    from app.models.class_ import Class
    from app.repositories import component as component_repo

    client, class_id, _enrollments, _components, (owner, other, _), db = grading_context
    await fill_scores(grading_context)
    original_lock = component_repo.lock_class
    other_id = uuid.UUID(decode_token(other["Authorization"].split()[1])["sub"])

    async def transfer(session, target_id):
        """Ganti pemilik pada batas lock untuk menguji otorisasi."""
        await db.execute(update(Class).where(Class.id == target_id).values(lecturer_id=other_id)
                         .execution_options(synchronize_session=False))
        await original_lock(session, target_id)

    monkeypatch.setattr(component_repo, "lock_class", transfer)
    response = await client.post(f"/classes/{class_id}/finalize", headers=owner)
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_ranking_database_comments(grading_context):
    """Pastikan metadata ranking dapat diaudit dari DB."""
    db = grading_context[-1]
    comments = (await db.execute(text("""
        SELECT col_description('rankings'::regclass, attnum)
        FROM pg_attribute WHERE attrelid = 'rankings'::regclass AND attnum > 0 AND NOT attisdropped
    """))).scalars().all()
    assert len(comments) == 5 and all(comments)
    assert await db.scalar(text("SELECT obj_description('rankings'::regclass, 'pg_class')"))


@pytest.mark.asyncio
async def test_failed_enrollment_does_not_leave_new_student(grading_context, monkeypatch):
    """Rollback profil baru saat pendaftaran gagal."""
    from app.repositories import enrollment as enrollment_repo

    client, class_id, _enrollments, _components, (owner, _, _), db = grading_context
    nim = f"atomic-{uuid.uuid4().hex}"

    async def fail(*args, **kwargs):
        """Suntik kegagalan untuk menguji penanganan error."""
        raise IntegrityError("INSERT enrollments", {}, Exception("simulated conflict"))

    monkeypatch.setattr(enrollment_repo, "add", fail)
    response = await client.post(f"/classes/{class_id}/enrollments", headers=owner, json={"nim": nim})
    assert response.status_code == 409, response.text
    assert (await db.execute(select(Student).where(Student.nim == nim))).scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_broker_failure_does_not_undo_release(grading_context, monkeypatch):
    """Broker gagal tidak mengembalikan hasil committed ke status draft.
    """
    from app.celery_app import celery_app

    client, class_id, _enrollments, _components, (owner, _, _), _db = grading_context
    await fill_scores(grading_context)
    calls = []

    def unavailable(*args, **kwargs):
        """Simulasikan dependency yang tidak tersedia."""
        calls.append(args)
        raise ConnectionError("broker offline")

    monkeypatch.setattr(celery_app, "send_task", unavailable)
    response = await client.post(f"/classes/{class_id}/finalize", headers=owner)
    assert response.status_code == 202, response.text
    assert response.json() == {"finalized_count": 2, "notified": 0}
    assert len(calls) == 1
    rows = (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()["grades"]
    assert all(row["status"] == "finalized" for row in rows)
    assert len((await client.get(f"/classes/{class_id}/ranking", headers=owner)).json()) == 2


@pytest.mark.asyncio
async def test_publisher_runs_only_after_commit(grading_context, monkeypatch):
    """Worker baru diberi task setelah nilai dapat dibaca koneksi lain.
    """
    client, class_id, _enrollments, _components, (owner, _, _), db = grading_context
    await fill_scores(grading_context)

    async def publish(ids):
        """Kendalikan hasil publish dalam skenario test."""
        assert not db.in_transaction()
        return len(ids)

    monkeypatch.setattr("app.services.grade.publish_grade_releases", publish)
    assert (await client.post(f"/classes/{class_id}/finalize", headers=owner)).status_code == 202


@pytest.mark.asyncio
async def test_finalize_creates_missing_grade_from_complete_scores(grading_context, monkeypatch):
    """Rilis skor lengkap meskipun total draft belum ada."""
    client, class_id, enrollments, _components, (owner, _, _), db = grading_context
    mock_publisher(monkeypatch)
    await fill_scores(grading_context)
    await db.execute(delete(Grade).where(Grade.enrollment_id == uuid.UUID(enrollments[0])))
    await db.commit()
    response = await client.post(f"/classes/{class_id}/finalize", headers=owner)
    assert response.status_code == 202, response.text
    rows = (await client.get(f"/classes/{class_id}/ranking", headers=owner)).json()
    assert len(rows) == 2 and all(Decimal(row["final_score"]) == Decimal("81") for row in rows)


@pytest.mark.asyncio
async def test_queue_contract_partial_failure_and_thread_offload(monkeypatch, caplog):
    """Uji prefix enqueue sukses dan offload publisher."""
    import threading
    from app.celery_app import celery_app
    from app.services.release_notifications import GRADE_RELEASE_TASK, publish_grade_releases

    ids = [uuid.uuid4() for _ in range(3)]
    calls = []
    main_thread = threading.get_ident()

    def send(name, *, args, retry):
        """Amati task yang diterima dan thread publisher."""
        assert threading.get_ident() != main_thread
        assert name == GRADE_RELEASE_TASK and retry is False
        calls.append(args)
        if len(calls) == 2:
            raise ConnectionError("broker offline")

    monkeypatch.setattr(celery_app, "send_task", send)
    assert await publish_grade_releases(ids) == 1
    assert calls == [[str(ids[0])], [str(ids[1])]]
    assert str(ids[1]) in caplog.text and str(ids[2]) in caplog.text
    assert celery_app.conf.broker_connection_timeout == 1
    assert celery_app.conf.broker_transport_options["socket_timeout"] == 1
    assert celery_app.conf.broker_transport_options["socket_connect_timeout"] == 1
    assert celery_app.conf.task_publish_retry is False
