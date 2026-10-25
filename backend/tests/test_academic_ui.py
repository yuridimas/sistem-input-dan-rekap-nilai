"""Backend contracts required by the academic management screens."""

import pytest

from tests.test_dashboard import dashboard_context


@pytest.mark.asyncio
async def test_assigned_course_read_access_does_not_grant_write_access(dashboard_context):
    client, _, _, courses, _, headers, _ = dashboard_context
    response = await client.get("/courses", headers=headers[0])
    assert response.status_code == 200
    ids = [course["id"] for course in response.json()]
    assert set(ids) == {str(course.id) for course in courses}
    assert len(ids) == len(set(ids))
    assigned = f"/courses/{courses[0].id}"
    assert (await client.get(assigned, headers=headers[0])).status_code == 200
    assert (await client.patch(assigned, headers=headers[0], json={"name": "Denied"})).status_code == 403
    assert (await client.delete(assigned, headers=headers[0])).status_code == 403
    assert (await client.get(f"/courses/{courses[1].id}", headers=headers[1])).status_code == 403
    assert (await client.get(assigned, headers=headers[3])).status_code == 403
    assert (await client.patch(f"/courses/{courses[2].id}", headers=headers[0], json={"name": "Owned"})).status_code == 200
    assert (await client.patch(assigned, headers=headers[2], json={"name": "Admin"})).status_code == 200


@pytest.mark.asyncio
async def test_class_lock_flag_covers_partial_finalizations_and_write_responses(dashboard_context):
    client, _, _, courses, classes, headers, _ = dashboard_context
    response = await client.get("/classes", headers=headers[0])
    assert response.status_code == 200
    rows = {row["id"]: row for row in response.json()}
    assert [rows[str(classes[i].id)]["has_finalized_grades"] for i in (0, 2, 3, 4, 5)] == [False, False, False, True, True]
    for index in (0, 4, 5):
        response = await client.get(f"/classes/{classes[index].id}", headers=headers[0])
        assert response.json()["has_finalized_grades"] == (index != 0)
    response = await client.patch(f"/classes/{classes[4].id}", headers=headers[0], json={"section": "ZZ"})
    assert response.status_code == 200
    assert response.json()["has_finalized_grades"] is True
    response = await client.post("/classes", headers=headers[0], json={
        "course_id": str(courses[0].id), "section": "NEW", "academic_year": "2027/2028",
    })
    assert response.status_code == 201
    assert response.json()["has_finalized_grades"] is False


@pytest.mark.asyncio
async def test_student_patch_clears_explicit_email_and_preserves_omitted_email(dashboard_context):
    client, _, _, _, classes, headers, _ = dashboard_context
    roster = (await client.get(f"/classes/{classes[2].id}/roster", headers=headers[0])).json()
    student_id = roster[0]["student"]["id"]
    url = f"/students/{student_id}"
    response = await client.patch(url, headers=headers[2], json={"email": "student@example.com"})
    assert response.json()["email"] == "student@example.com"
    response = await client.patch(url, headers=headers[2], json={"full_name": "Updated"})
    assert response.json()["email"] == "student@example.com"
    response = await client.patch(url, headers=headers[2], json={"email": None})
    assert response.status_code == 200
    assert response.json()["email"] is None
    response = await client.patch(url, headers=headers[0], json={"email": "forbidden@example.com"})
    assert response.status_code == 403
