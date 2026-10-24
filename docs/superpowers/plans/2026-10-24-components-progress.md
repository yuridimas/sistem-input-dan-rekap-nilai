# Component Implementation Progress

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md)

## Resume Point

- Tasks 1–8 already have implementation commits. On resumption, the existing Task 8 edits were retained: only superadmins may update/delete shared student records; enrollment operations retain class IDs across rollback and map dependent deletion conflicts to 409.
- Task 8 integration tests now cover the retained student authorization policy.
- Task 9 implements components across model, migration, schema, repository, service, and router layers.
- Next task: **Task 10 — Score entry + auto final score (draft)**. Tasks 10–23 remain pending.

## Component API Contract

- `GET /classes/{id}/components`: ordered component list; a new class returns `[]`.
- `POST /classes/{id}/components`: JSON array of new components, saved atomically. The complete resulting configuration must have positive weights totaling exactly 100 and at least one UTS and UAS.
- `PUT /classes/{id}/components`: atomically replaces the complete configuration. Include existing component IDs to retain them; omit an ID to add a component; omit a previous row to remove it. Unknown or duplicate IDs return 422.
- `PATCH /components/{id}` and `DELETE /components/{id}`: validate the resulting complete configuration. Use PUT for coordinated weight changes or removals that need reweighting.

Example initial POST body:

```json
[
  {"name": "UTS", "category": "uts", "weight": "40.00"},
  {"name": "UAS", "category": "uas", "weight": "60.00"}
]
```

## Decisions and Verification

- Ruling: add atomic PUT beyond the original endpoint list. Single-row operations cannot transition between two valid configurations when every saved set must total 100. Retaining IDs preserves future score references. The frontend component editor must submit coordinated changes using this endpoint.
- Ruling: POST accepts an array so a new class can receive its required UTS/UAS components in one valid transaction.
- Mutations lock the class, reload its current owner, then authorize. A component removed before its lock is obtained returns 404. Class lecturers and superadmins may manage components; other lecturers receive 403.
- Decimal fields reject excessive precision before database rounding; 99.9999 is rejected. Migration `0004_components` includes Indonesian comments on the table and every column.
- RED → GREEN: missing component routes; atomic replacement; ownership change before locking; removal before locking.
- Verification: backend pytest suite passes; `alembic upgrade head` succeeds; `alembic check` reports no new upgrade operations. Docker startup was unavailable because Docker Desktop was not running.
