"""Release audit, delivery, failure handling, and administrator retry.

Status persisten pengiriman dan pemulihan admin.

Memerlukan PostgreSQL disposable yang dimigrasi; beberapa skenario
melakukan commit nyata.
"""

import asyncio
import smtplib
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import delete, select, update

from app.database import AsyncSessionLocal
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.student import Student
from tests.test_finalization import fill_scores, mock_publisher
from tests.test_finalization_concurrency import release_context
from tests.test_scores import grading_context


async def release(grading_context, monkeypatch):
    """Siapkan nilai final untuk skenario pengiriman."""
    client, class_id, enrollments, _components, (owner, _, _), db = grading_context
    mock_publisher(monkeypatch)
    student_ids = select(Enrollment.student_id).where(Enrollment.class_id == uuid.UUID(class_id))
    await db.execute(update(Student).where(Student.id.in_(student_ids)).values(email="student@example.com"))
    await db.commit()
    await fill_scores(grading_context)
    response = await client.post(f"/classes/{class_id}/finalize", headers=owner)
    assert response.status_code == 202, response.text
    return response


@pytest.mark.asyncio
async def test_release_creates_queued_notifications_and_admin_filters(grading_context, monkeypatch):
    """Catat notifikasi queued untuk audit dan filter admin."""
    client, _class_id, _enrollments, _components, (owner, _, admin), _db = grading_context
    await release(grading_context, monkeypatch)
    response = await client.get("/admin/notifications?status=queued", headers=admin)
    assert response.status_code == 200, response.text
    rows = [row for row in response.json() if row["student_email"] == "student@example.com"]
    assert len(rows) >= 2
    assert all(row["status"] == "queued" and row["sent_at"] is None for row in rows)
    assert all(row["id"] and row["grade_id"] and row["created_at"] for row in rows)
    assert (await client.get("/admin/notifications", headers=owner)).status_code == 403
    assert (await client.get("/admin/notifications")).status_code == 401
    assert (await client.get("/admin/notifications?status=unknown", headers=admin)).status_code == 422


@pytest.mark.asyncio
async def test_mock_delivery_marks_sent_and_duplicate_delivery_is_skipped(grading_context, monkeypatch):
    """Task duplikat tidak boleh mengirim ulang setelah sukses tercatat.
    """
    from app.config import Settings
    from app.models.notification import Notification
    from app.services.notifications import deliver_grade

    _client, _class, enrollments, _components, _headers, db = grading_context
    await release(grading_context, monkeypatch)
    monkeypatch.setattr("app.services.mailer.get_settings", lambda: Settings(_env_file=None, smtp_host=""))
    monkeypatch.setattr(smtplib, "SMTP", lambda *args, **kwargs: pytest.fail("Mock must not connect to SMTP"))
    grade = (await db.execute(select(Grade).where(Grade.enrollment_id == uuid.UUID(enrollments[0])))).scalar_one()
    result = await deliver_grade(db, grade.id, final_attempt=False)
    assert result["status"] == "sent"
    notification = (await db.execute(select(Notification).where(Notification.grade_id == grade.id))).scalar_one()
    await db.refresh(grade)
    assert notification.status == "sent" and notification.error_message is None
    assert notification.sent_at == grade.release_notified_at
    assert (await deliver_grade(db, grade.id, final_attempt=False))["status"] == "already_sent"


@pytest.mark.asyncio
async def test_delivery_failure_tracks_error_and_admin_retry_refreshes_address(grading_context, monkeypatch):
    """Retry dengan alamat terbaru dan hapus error sebelumnya."""
    from app.models.notification import Notification
    from app.services.notifications import deliver_grade

    client, _class, enrollments, _components, (owner, _, admin), db = grading_context
    await release(grading_context, monkeypatch)
    grade = (await db.execute(select(Grade).where(Grade.enrollment_id == uuid.UUID(enrollments[0])))).scalar_one()

    def unavailable(_message):
        """Simulasikan dependency yang tidak tersedia."""
        raise smtplib.SMTPException("SMTP unavailable")

    monkeypatch.setattr("app.services.mailer.send_grade_email", unavailable)
    assert (await deliver_grade(db, grade.id, final_attempt=False))["status"] == "retry"
    notification = (await db.execute(select(Notification).where(Notification.grade_id == grade.id))).scalar_one()
    assert notification.status == "queued" and "SMTP unavailable" in notification.error_message
    assert (await deliver_grade(db, grade.id, final_attempt=True))["status"] == "failed"
    assert notification.status == "failed" and notification.sent_at is None
    student_id = await db.scalar(select(Enrollment.student_id).where(Enrollment.id == uuid.UUID(enrollments[0])))
    await db.execute(update(Student).where(Student.id == student_id).values(email="corrected@example.com"))
    await db.commit()
    published = []

    async def publish(ids):
        """Kendalikan hasil publish dalam skenario test."""
        assert not db.in_transaction()
        published.extend(ids)
        return len(ids)

    monkeypatch.setattr("app.services.notifications.publish_grade_releases", publish)
    path = f"/admin/notifications/{notification.id}/retry"
    assert (await client.post(path, headers=owner)).status_code == 403
    response = await client.post(path, headers=admin)
    assert response.status_code == 202, response.text
    assert response.json()["status"] == "queued" and response.json()["student_email"] == "corrected@example.com"
    assert published == [grade.id]
    monkeypatch.setattr("app.services.mailer.send_grade_email", lambda _message: None)
    assert (await deliver_grade(db, grade.id, final_attempt=True))["status"] == "sent"
    assert (await client.post(path, headers=admin)).status_code == 409
    assert (await client.post(f"/admin/notifications/{uuid.uuid4()}/retry", headers=admin)).status_code == 404


@pytest.mark.asyncio
async def test_broker_failure_is_persisted_without_undoing_release(grading_context, monkeypatch):
    """Catat broker gagal tanpa membatalkan rilis committed."""
    from app.celery_app import celery_app
    from app.models.notification import Notification

    client, class_id, enrollments, _components, (owner, _, admin), db = grading_context
    await fill_scores(grading_context)

    def offline(*args, **kwargs):
        """Simulasikan transport gagal tanpa jaringan."""
        raise ConnectionError("broker offline")

    monkeypatch.setattr(celery_app, "send_task", offline)
    response = await client.post(f"/classes/{class_id}/finalize", headers=owner)
    assert response.status_code == 202 and response.json()["notified"] == 0
    grade_ids = select(Grade.id).where(Grade.enrollment_id.in_([uuid.UUID(value) for value in enrollments]))
    rows = (await db.execute(select(Notification).where(Notification.grade_id.in_(grade_ids)))).scalars().all()
    assert len(rows) == 2 and all(row.status == "failed" and row.error_message for row in rows)
    response = await client.post(f"/admin/notifications/{rows[0].id}/retry", headers=admin)
    assert response.status_code == 202 and response.json()["status"] == "failed"
    assert all(row["status"] == "finalized" for row in (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()["grades"])


@pytest.mark.asyncio
async def test_missing_recipient_fails_without_smtp_and_queued_retry_is_recoverable(grading_context, monkeypatch):
    """Tolak alamat kosong dan izinkan pemulihan queued."""
    from app.models.notification import Notification
    from app.services.notifications import deliver_grade

    client, class_id, enrollments, _components, (owner, _, admin), db = grading_context
    mock_publisher(monkeypatch)
    await fill_scores(grading_context)
    await client.post(f"/classes/{class_id}/finalize", headers=owner)
    grade = (await db.execute(select(Grade).where(Grade.enrollment_id == uuid.UUID(enrollments[0])))).scalar_one()
    monkeypatch.setattr("app.services.mailer.send_grade_email", lambda _message: pytest.fail("No recipient"))
    result = await deliver_grade(db, grade.id, final_attempt=False)
    assert result["status"] == "failed"
    notification = (await db.execute(select(Notification).where(Notification.grade_id == grade.id))).scalar_one()
    assert notification.status == "failed" and notification.error_message
    queued = (await db.execute(select(Notification).where(Notification.grade_id != grade.id,
                                                         Notification.grade_id.in_(select(Grade.id).where(Grade.enrollment_id == uuid.UUID(enrollments[1])))))).scalar_one()

    async def publish(ids):
        """Kendalikan hasil publish dalam skenario test."""
        return len(ids)

    monkeypatch.setattr("app.services.notifications.publish_grade_releases", publish)
    assert (await client.post(f"/admin/notifications/{queued.id}/retry", headers=admin)).status_code == 202


@pytest.mark.asyncio
async def test_eager_task_sends_once_and_exhausts_three_retries(release_context, monkeypatch):
    """Akhiri pengiriman setelah tiga retry gagal."""
    from app.models.notification import Notification
    from app.tasks.notifications import send_grade_release_email

    client, class_id, enrollment_id, _components, headers, _nim, _published, _course, _user = release_context
    async with AsyncSessionLocal() as db:
        student_id = await db.scalar(select(Enrollment.student_id).where(Enrollment.id == enrollment_id))
        await db.execute(update(Student).where(Student.id == student_id).values(email="eager@example.com"))
        await db.commit()
    assert (await client.post(f"/classes/{class_id}/finalize", headers=headers)).status_code == 202
    async with AsyncSessionLocal() as db:
        grade_id = await db.scalar(select(Grade.id).where(Grade.enrollment_id == enrollment_id))
    calls = []

    def unavailable(message):
        """Simulasikan dependency yang tidak tersedia."""
        calls.append(message)
        raise smtplib.SMTPException("eager failure")

    monkeypatch.setattr("app.services.mailer.send_grade_email", unavailable)
    result = await asyncio.to_thread(send_grade_release_email.apply, args=[str(grade_id)], throw=False)
    assert result.result["status"] == "failed" and len(calls) == 4
    async with AsyncSessionLocal() as db:
        notification = (await db.execute(select(Notification).where(Notification.grade_id == grade_id))).scalar_one()
        assert notification.status == "failed" and "eager failure" in notification.error_message
        # Simulate an old queued Task 11 message without a pre-created notification record.
        await db.execute(delete(Notification).where(Notification.grade_id == grade_id))
        await db.commit()
    monkeypatch.setattr("app.services.mailer.send_grade_email", lambda message: calls.append(message))
    result = await asyncio.to_thread(send_grade_release_email.apply, args=[str(grade_id)], throw=False)
    assert result.result["status"] == "sent" and len(calls) == 5
    assert calls[-1].final_score == Decimal("81")
    result = await asyncio.to_thread(send_grade_release_email.apply, args=[str(grade_id)], throw=False)
    assert result.result["status"] == "already_sent" and len(calls) == 5


@pytest.mark.asyncio
async def test_notification_comments_and_draft_messages_are_ignored(grading_context, monkeypatch):
    """Periksa metadata dan abaikan pengiriman nilai draft."""
    from sqlalchemy import text
    from app.models.notification import Notification
    from app.services.notifications import deliver_grade

    _client, _class, enrollments, _components, _headers, db = grading_context
    await fill_scores(grading_context)
    grade_id = await db.scalar(select(Grade.id).where(Grade.enrollment_id == uuid.UUID(enrollments[0])))
    monkeypatch.setattr("app.services.mailer.send_grade_email", lambda _message: pytest.fail("Draft sent"))
    assert (await deliver_grade(db, grade_id, final_attempt=False))["status"] == "ignored"
    assert (await deliver_grade(db, uuid.uuid4(), final_attempt=False))["status"] == "ignored"
    assert await db.scalar(select(Notification.id).where(Notification.grade_id == grade_id)) is None
    comments = (await db.execute(text("""
        SELECT col_description('notifications'::regclass, attnum) FROM pg_attribute
        WHERE attrelid = 'notifications'::regclass AND attnum > 0 AND NOT attisdropped
    """))).scalars().all()
    assert len(comments) == 8 and all(comments)
    assert await db.scalar(text("SELECT obj_description('notifications'::regclass, 'pg_class')"))


@pytest.mark.asyncio
async def test_real_celery_worker_processes_queued_grade(release_context, monkeypatch):
    """Uji kontrak task/broker melalui worker lintas proses."""
    from celery.contrib.testing.worker import start_worker
    from app.celery_app import celery_app
    from app.models.notification import Notification
    from app.tasks.notifications import send_grade_release_email

    client, class_id, enrollment_id, _components, headers, _nim, _published, _course, _user = release_context
    async with AsyncSessionLocal() as db:
        student_id = await db.scalar(select(Enrollment.student_id).where(Enrollment.id == enrollment_id))
        await db.execute(update(Student).where(Student.id == student_id).values(email="worker@example.com"))
        await db.commit()
    assert (await client.post(f"/classes/{class_id}/finalize", headers=headers)).status_code == 202
    async with AsyncSessionLocal() as db:
        grade_id = await db.scalar(select(Grade.id).where(Grade.enrollment_id == enrollment_id))
    calls = []
    monkeypatch.setattr("app.services.mailer.send_grade_email", lambda message: calls.append(message))
    monkeypatch.setitem(celery_app.conf, "broker_url", "memory://")
    monkeypatch.setattr(celery_app.amqp, "_producer_pool", None)
    queue_name = f"test-notifications-{uuid.uuid4().hex}"
    worker = start_worker(celery_app, pool="solo", queues=[queue_name], perform_ping_check=False,
                          shutdown_timeout=10, loglevel="ERROR")
    await asyncio.to_thread(worker.__enter__)
    try:
        await asyncio.to_thread(send_grade_release_email.apply_async, args=[str(grade_id)],
                                queue=queue_name, ignore_result=True)

        async def wait_until_sent():
            """Tunggu catatan pengiriman hingga batas waktu test."""
            while True:
                async with AsyncSessionLocal() as db:
                    status = await db.scalar(select(Notification.status).where(Notification.grade_id == grade_id))
                if status == "sent":
                    return
                await asyncio.sleep(0.05)

        await asyncio.wait_for(wait_until_sent(), timeout=10)
        assert len(calls) == 1 and calls[0].grade_id == grade_id
    finally:
        await asyncio.to_thread(worker.__exit__, None, None, None)


@pytest.mark.asyncio
async def test_duplicate_task_deliveries_are_serialized(release_context, monkeypatch):
    """Serialisasikan task duplikat sebelum batas SMTP."""
    from app.tasks.notifications import send_grade_release_email

    client, class_id, enrollment_id, _components, headers, _nim, _published, _course, _user = release_context
    async with AsyncSessionLocal() as db:
        student_id = await db.scalar(select(Enrollment.student_id).where(Enrollment.id == enrollment_id))
        await db.execute(update(Student).where(Student.id == student_id).values(email="duplicate@example.com"))
        await db.commit()
    await client.post(f"/classes/{class_id}/finalize", headers=headers)
    async with AsyncSessionLocal() as db:
        grade_id = await db.scalar(select(Grade.id).where(Grade.enrollment_id == enrollment_id))
    calls = []
    monkeypatch.setattr("app.services.mailer.send_grade_email", lambda message: calls.append(message))
    first, second = await asyncio.gather(*[
        asyncio.to_thread(send_grade_release_email.apply, args=[str(grade_id)], throw=False)
        for _ in range(2)
    ])
    assert {first.result["status"], second.result["status"]} == {"sent", "already_sent"}
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_terminal_failure_requires_manual_retry(grading_context, monkeypatch):
    """Batasi pemulihan kegagalan terminal pada admin."""
    from app.services.notifications import deliver_grade

    _client, _class, enrollments, _components, _headers, db = grading_context
    await release(grading_context, monkeypatch)
    grade_id = await db.scalar(select(Grade.id).where(Grade.enrollment_id == uuid.UUID(enrollments[0])))

    def fail(_message):
        """Suntik kegagalan untuk menguji penanganan error."""
        raise smtplib.SMTPException("terminal failure")

    monkeypatch.setattr("app.services.mailer.send_grade_email", fail)
    assert (await deliver_grade(db, grade_id, final_attempt=True))["status"] == "failed"
    monkeypatch.setattr("app.services.mailer.send_grade_email", lambda _message: pytest.fail("Failed task redelivered"))
    assert (await deliver_grade(db, grade_id, final_attempt=False))["status"] == "failed"


@pytest.mark.asyncio
async def test_stale_enqueue_failure_cannot_cancel_newer_retry(release_context, monkeypatch):
    """Gagal enqueue generasi lama tidak boleh menimpa dispatch baru."""
    from app.models.notification import Notification
    from app.services.notifications import retry_notification

    client, class_id, enrollment_id, _components, headers, _nim, _published, _course, _user = release_context
    await client.post(f"/classes/{class_id}/finalize", headers=headers)
    async with AsyncSessionLocal() as db:
        grade_id = await db.scalar(select(Grade.id).where(Grade.enrollment_id == enrollment_id))
        notification_id = await db.scalar(select(Notification.id).where(Notification.grade_id == grade_id))
    first_waiting, second_finished = asyncio.Event(), asyncio.Event()
    calls = 0

    async def publish(ids):
        """Kendalikan hasil publish dalam skenario test."""
        nonlocal calls
        calls += 1
        if calls == 1:
            first_waiting.set()
            await second_finished.wait()
            return 0
        return 1

    monkeypatch.setattr("app.services.notifications.publish_grade_releases", publish)

    async def retry_once():
        """Kendalikan kegagalan sementara untuk uji retry."""
        async with AsyncSessionLocal() as db:
            return await retry_notification(db, notification_id)

    first = asyncio.create_task(retry_once())
    try:
        await asyncio.wait_for(first_waiting.wait(), timeout=10)
        assert (await retry_once()).status == "queued"
        second_finished.set()
        await asyncio.wait_for(first, timeout=10)
        async with AsyncSessionLocal() as db:
            assert await db.scalar(select(Notification.status).where(Notification.id == notification_id)) == "queued"
    finally:
        second_finished.set()
        if not first.done():
            first.cancel()
        await asyncio.gather(first, return_exceptions=True)


@pytest.mark.asyncio
async def test_old_automatic_retry_token_cannot_affect_manual_recovery(release_context, monkeypatch):
    """Abaikan token retry dari generasi lama."""
    from app.models.notification import Notification
    from app.services.notifications import retry_notification
    from app.tasks.notifications import send_grade_release_email

    client, class_id, enrollment_id, _components, headers, _nim, _published, _course, _user = release_context
    await client.post(f"/classes/{class_id}/finalize", headers=headers)
    async with AsyncSessionLocal() as db:
        grade_id = await db.scalar(select(Grade.id).where(Grade.enrollment_id == enrollment_id))
        notification = (await db.execute(select(Notification).where(Notification.grade_id == grade_id))).scalar_one()
        old_token = notification.dispatch_token

        async def publish(ids):
            """Kendalikan hasil publish dalam skenario test."""
            return len(ids)

        monkeypatch.setattr("app.services.notifications.publish_grade_releases", publish)
        notification = await retry_notification(db, notification.id)
        assert notification.dispatch_token != old_token
    monkeypatch.setattr("app.services.mailer.send_grade_email", lambda _message: pytest.fail("Stale generation delivered"))
    result = await asyncio.to_thread(send_grade_release_email.apply, args=[str(grade_id)],
                                     kwargs={"dispatch_token": str(old_token)}, throw=False)
    assert result.result["status"] == "ignored"
    async with AsyncSessionLocal() as db:
        assert await db.scalar(select(Notification.status).where(Notification.grade_id == grade_id)) == "queued"
